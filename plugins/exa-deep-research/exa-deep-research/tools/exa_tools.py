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
                return _error("TOOL_DISCOVERY_LIMIT", "工具发现超过十页，已停止继续翻页。")
            tool = next((item for item in tools if item.name == remote_name), None)
            if tool is None:
                return _error("TOOL_UNAVAILABLE", f"Exa 未声明工具 {remote_name}。")
            schema = tool.inputSchema
            args = dict(arguments)
            # The hosted service (3.5.0 at testing) adds a required objective;
            # pinned upstream 3.4.2 did not require it. A query is a safe default.
            if remote_name == "web_search_exa" and "objective" in schema.get("required", []):
                args.setdefault("objective", args.get("query", ""))
            errors = sorted(Draft202012Validator(schema).iter_errors(args), key=lambda item: str(item.path))
            if errors:
                # Do not echo validation exception text: it can include inputs.
                return _error("INVALID_ARGUMENTS", "参数不符合 Exa 当前模式，请根据返回的 schema 修正。", schema=schema)
            result = await session.call_tool(remote_name, arguments=args)
            data = result.model_dump(mode="json", exclude_none=True)
            return {"ok": not bool(result.isError), "tool": remote_name, "result": data}


async def call_exa(remote_name: str, arguments: dict, *, allow_paid: bool = False) -> dict:
    if remote_name not in {"web_search_exa", "web_fetch_exa", "web_search_advanced_exa", "agent_run"}:
        return _error("INVALID_TOOL", "不支持的 Exa 工具。")
    if not isinstance(arguments, dict):
        return _error("INVALID_INPUT", "arguments 必须是对象。")
    key = os.environ.get("EXA_API_KEY", "").strip()
    if remote_name == "agent_run":
        if allow_paid is not True:
            return _error("PAID_ACTION_REQUIRES_APPROVAL", "请先取得用户对本次托管研究的明确授权，再设置 allow_paid=true。")
        if not key:
            return _error("EXA_API_KEY_REQUIRED", "托管研究前，请在宿主环境中配置 EXA_API_KEY；不要将密钥放入聊天或插件文件。")
        query, run_id = arguments.get("query"), arguments.get("runId")
        if bool(query) == bool(run_id):
            return _error("INVALID_INPUT", "query 与 runId 必须且只能提供一个。")
    try:
        result = await asyncio.wait_for(_exchange(remote_name, arguments, key), timeout=TIMEOUT_SECONDS)
        return _redact(result, key)
    except asyncio.TimeoutError:
        return _error("TIMEOUT", "Exa 未在 60 秒内完成。远端执行状态可能不确定，请勿盲目重复研究任务。")
    except asyncio.CancelledError:
        raise
    except Exception:
        # HTTP/MCP ExceptionGroups may include headers, keys or request bodies.
        return _error("EXA_CONNECTION_FAILED", "Exa 连接失败，请检查网络、凭据或额度限制；本次未自动重试。")


class ExaSearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_search", name="exa_search",
            description="使用 Exa 语义搜索公开网页，返回来源 URL 与内容。",
            input_params={"type": "object", "properties": {
                "query": {"type": "string", "minLength": 1},
                "objective": {"type": "string"},
                "numResults": {"type": "integer", "minimum": 1, "maximum": 25},
            }, "required": ["query"], "additionalProperties": False}, idempotent=True,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        if not isinstance(inputs, dict) or not isinstance(inputs.get("query"), str) or not inputs["query"].strip():
            return _error("INVALID_INPUT", "query 必须是非空字符串。")
        if set(inputs) - {"query", "objective", "numResults"}:
            return _error("INVALID_INPUT", "包含未知的搜索参数。")
        n = inputs.get("numResults", 5)
        if type(n) is not int or not 1 <= n <= 25:
            return _error("INVALID_INPUT", "numResults 必须是 1 到 25 的整数。")
        return await call_exa("web_search_exa", {**inputs, "numResults": n})

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class ExaFetchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_fetch", name="exa_fetch", description="通过 Exa 读取公开网页 URL 的内容；不读取本地文件。",
            input_params={"type": "object", "properties": {
                "urls": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10},
                "maxCharacters": {"type": "integer", "minimum": 1, "maximum": 20000},
            }, "required": ["urls"], "additionalProperties": False}, idempotent=True,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        from urllib.parse import urlsplit
        if not isinstance(inputs, dict) or set(inputs) - {"urls", "maxCharacters"}:
            return _error("INVALID_INPUT", "请提供 urls，可选参数为 maxCharacters。")
        urls = inputs.get("urls")
        if not isinstance(urls, list) or not 1 <= len(urls) <= 10:
            return _error("INVALID_INPUT", "请提供 1 到 10 个公开 HTTP(S) URL。")
        try:
            valid = all(isinstance(url, str) and urlsplit(url).scheme in {"http", "https"}
                        and urlsplit(url).hostname and not urlsplit(url).username and not urlsplit(url).password for url in urls)
        except ValueError:
            valid = False
        if not valid:
            return _error("INVALID_INPUT", "URL 必须使用 HTTP(S)、包含主机名且不得包含凭据。")
        count = inputs.get("maxCharacters", 3000)
        if type(count) is not int or not 1 <= count <= 20000:
            return _error("INVALID_INPUT", "maxCharacters 必须是 1 到 20000 的整数。")
        return await call_exa("web_fetch_exa", {"urls": urls, "maxCharacters": count})

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class ExaAdvancedSearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_search_advanced", name="exa_search_advanced",
            description="使用域名、日期或类别条件进行 Exa 搜索。传入上游参数；模式校验失败时返回当前 schema 供修正。",
            input_params={"type": "object", "properties": {"arguments": {"type": "object"}}, "required": ["arguments"], "additionalProperties": False},
            idempotent=True,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        if not isinstance(inputs, dict) or set(inputs) != {"arguments"}:
            return _error("INVALID_INPUT", "请提供 arguments 对象。")
        return await call_exa("web_search_advanced_exa", inputs["arguments"])

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class ExaResearchTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="exa_research", name="exa_research",
            description="执行或续接认证计费 Exa Agent 研究；须配置 EXA_API_KEY，且用户明确授权覆盖本次调用。",
            input_params={"type": "object", "properties": {
                "arguments": {"type": "object"}, "allow_paid": {"type": "boolean", "default": False},
            }, "required": ["arguments"], "additionalProperties": False}, parallel_safe=False,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        if not isinstance(inputs, dict) or set(inputs) - {"arguments", "allow_paid"} or "arguments" not in inputs:
            return _error("INVALID_INPUT", "请提供 arguments，可选参数为 allow_paid。")
        return await call_exa("agent_run", inputs["arguments"], allow_paid=inputs.get("allow_paid", False))

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)
