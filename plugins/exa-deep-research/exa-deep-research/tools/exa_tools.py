"""Native openJiuwen tools for the official Exa MCP service.

The transport design follows exa-labs/exa-mcp-server 3.4.2 (MIT).
No Exa server implementation or third-party runtime is vendored here.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, AsyncIterator

from jsonschema import Draft202012Validator
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openjiuwen.core.foundation.tool import Tool, ToolCard

BASE_URL = "https://mcp.exa.ai/mcp"
TIMEOUT_SECONDS = 60


def _error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


def _redact(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [_redact(item, secret) for item in value]
    if isinstance(value, dict):
        return {key: _redact(item, secret) for key, item in value.items()}
    return value


async def _exchange(remote_name: str, arguments: dict, key: str) -> dict:
    # Select only this tool. Including agent_run in an anonymous server URL
    # changes connection authentication, even for unrelated search calls.
    url = BASE_URL if remote_name in {"web_search_exa", "web_fetch_exa"} else f"{BASE_URL}?tools={remote_name}"
    headers = {"x-exa-source": "agentic-hub-plugins"}
    if key:
        headers["x-api-key"] = key
    async with streamablehttp_client(
        url, headers=headers, timeout=30, sse_read_timeout=TIMEOUT_SECONDS,
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = []
            cursor = None
            for _ in range(10):
                page = await session.list_tools(cursor=cursor)
                tools.extend(page.tools)
                cursor = page.nextCursor
                if not cursor:
                    break
            else:
                return _error("TOOL_DISCOVERY_LIMIT", "Tool discovery exceeded ten pages.")
            tool = next((item for item in tools if item.name == remote_name), None)
            if tool is None:
                return _error("TOOL_UNAVAILABLE", f"Exa did not advertise {remote_name}.")
            schema = tool.inputSchema
            args = dict(arguments)
            # The hosted service (3.5.0 at testing) adds a required objective;
            # pinned upstream 3.4.2 did not require it. A query is a safe default.
            if remote_name == "web_search_exa" and "objective" in schema.get("required", []):
                args.setdefault("objective", args.get("query", ""))
            errors = sorted(Draft202012Validator(schema).iter_errors(args), key=lambda item: str(item.path))
            if errors:
                # Do not echo validation exception text: it can include inputs.
                return _error("INVALID_ARGUMENTS", "Arguments do not match Exa's current schema.", schema=schema)
            result = await session.call_tool(remote_name, arguments=args)
            data = result.model_dump(mode="json", exclude_none=True)
            return {"ok": not bool(result.isError), "tool": remote_name, "result": data}


async def call_exa(remote_name: str, arguments: dict, *, allow_paid: bool = False) -> dict:
    if remote_name not in {"web_search_exa", "web_fetch_exa", "web_search_advanced_exa", "agent_run"}:
        return _error("INVALID_TOOL", "Unsupported Exa tool.")
    if not isinstance(arguments, dict):
        return _error("INVALID_INPUT", "arguments must be an object.")
    key = os.environ.get("EXA_API_KEY", "").strip()
    if remote_name == "agent_run":
        if allow_paid is not True:
            return _error("PAID_ACTION_REQUIRES_APPROVAL", "Obtain user approval for this managed research call, then set allow_paid=true.")
        if not key:
            return _error("EXA_API_KEY_REQUIRED", "Set EXA_API_KEY in the host environment before managed research. Do not put it in chat or package files.")
        query, run_id = arguments.get("query"), arguments.get("runId")
        if bool(query) == bool(run_id):
            return _error("INVALID_INPUT", "Provide exactly one of query or runId.")
    try:
        result = await asyncio.wait_for(_exchange(remote_name, arguments, key), timeout=TIMEOUT_SECONDS)
        return _redact(result, key)
    except asyncio.TimeoutError:
        return _error("TIMEOUT", "Exa did not finish within 60 seconds. Execution status may be unknown; do not blindly repeat a research run.")
    except asyncio.CancelledError:
        raise
    except Exception:
        # HTTP/MCP ExceptionGroups may include headers, keys or request bodies.
        return _error("EXA_CONNECTION_FAILED", "Exa connection failed. Check network access, credentials or rate limits; no automatic retry was made.")


class ExaSearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_search", name="exa_search",
            description="Search the open web using Exa semantic search; returns source URLs and content.",
            input_params={"type": "object", "properties": {
                "query": {"type": "string", "minLength": 1},
                "objective": {"type": "string"},
                "numResults": {"type": "integer", "minimum": 1, "maximum": 25},
            }, "required": ["query"], "additionalProperties": False}, idempotent=True,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        if not isinstance(inputs, dict) or not isinstance(inputs.get("query"), str) or not inputs["query"].strip():
            return _error("INVALID_INPUT", "query must be a nonempty string.")
        if set(inputs) - {"query", "objective", "numResults"}:
            return _error("INVALID_INPUT", "Unknown search argument.")
        n = inputs.get("numResults", 5)
        if type(n) is not int or not 1 <= n <= 25:
            return _error("INVALID_INPUT", "numResults must be an integer from 1 to 25.")
        return await call_exa("web_search_exa", {**inputs, "numResults": n})

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class ExaFetchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_fetch", name="exa_fetch", description="Read public webpage URLs as Exa content. This does not read local files.",
            input_params={"type": "object", "properties": {
                "urls": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10},
                "maxCharacters": {"type": "integer", "minimum": 1, "maximum": 20000},
            }, "required": ["urls"], "additionalProperties": False}, idempotent=True,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        from urllib.parse import urlsplit
        if not isinstance(inputs, dict) or set(inputs) - {"urls", "maxCharacters"}:
            return _error("INVALID_INPUT", "Provide urls and optional maxCharacters.")
        urls = inputs.get("urls")
        if not isinstance(urls, list) or not 1 <= len(urls) <= 10:
            return _error("INVALID_INPUT", "Provide 1 to 10 public HTTP(S) URLs.")
        try:
            valid = all(isinstance(url, str) and urlsplit(url).scheme in {"http", "https"}
                        and urlsplit(url).hostname and not urlsplit(url).username and not urlsplit(url).password for url in urls)
        except ValueError:
            valid = False
        if not valid:
            return _error("INVALID_INPUT", "URLs must use HTTP(S), have a host, and contain no credentials.")
        count = inputs.get("maxCharacters", 3000)
        if type(count) is not int or not 1 <= count <= 20000:
            return _error("INVALID_INPUT", "maxCharacters must be an integer from 1 to 20000.")
        return await call_exa("web_fetch_exa", {"urls": urls, "maxCharacters": count})

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class ExaAdvancedSearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_search_advanced", name="exa_search_advanced",
            description="Exa search with domain/date/category filters. Pass upstream arguments; a schema error returns the current schema for correction.",
            input_params={"type": "object", "properties": {"arguments": {"type": "object"}}, "required": ["arguments"], "additionalProperties": False},
            idempotent=True,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        if not isinstance(inputs, dict) or set(inputs) != {"arguments"}:
            return _error("INVALID_INPUT", "Provide an arguments object.")
        return await call_exa("web_search_advanced_exa", inputs["arguments"])

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class ExaResearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_research", name="exa_research",
            description="Run or resume authenticated, billable Exa Agent research. Requires EXA_API_KEY and explicit user approval for each invocation.",
            input_params={"type": "object", "properties": {
                "arguments": {"type": "object"}, "allow_paid": {"type": "boolean", "default": False},
            }, "required": ["arguments"], "additionalProperties": False}, parallel_safe=False,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        if not isinstance(inputs, dict) or set(inputs) - {"arguments", "allow_paid"} or "arguments" not in inputs:
            return _error("INVALID_INPUT", "Provide arguments and optional allow_paid.")
        return await call_exa("agent_run", inputs["arguments"], allow_paid=inputs.get("allow_paid", False))

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)
