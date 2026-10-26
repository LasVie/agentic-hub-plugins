"""WorkSwarm adapter for the MIT Cheapest Domains integration workflow.

Upstream workflow: Copyright (c) 2026 Ilios Galil (PerfWebsite).
Adaptation: Chinese native tool cards and bounded MCP calls, 2026-10-26.
The hosted server implementation and data are not included.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, AsyncIterator

from jsonschema import Draft202012Validator
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openjiuwen.core.foundation.tool import Tool, ToolCard

ENDPOINT = "https://cheapest.domains/mcp"
TIMEOUT_SECONDS = 75
CATALOG = json.loads(Path(__file__).with_name("tool_catalog.json").read_text(encoding="utf-8"))
_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")


def _error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


def _invalid(arguments: Any, schema: dict) -> str | None:
    if not isinstance(arguments, dict):
        return "参数必须是 JSON 对象。"
    if next(Draft202012Validator(schema).iter_errors(arguments), None):
        return "参数类型、必填字段或取值不符合工具说明；请检查单位、范围和未知字段。"
    for key in ("name", "tld"):
        if key in arguments and not _LABEL.fullmatch(arguments[key]):
            return f"{key} 必须是 1–63 位 ASCII 字母、数字或中间连字符；不支持中文、点号或多级后缀。"
    if arguments.get("registrar") and arguments.get("registrars"):
        return "registrar 与 registrars 不能同时提供。"
    if arguments.get("includeStale") and arguments.get("view") != "all" and "q" in schema.get("properties", {}):
        return "搜索旧报价时请同时设置 view=all，并在回答中标注过期日期。"
    if "tlds" in arguments:
        tlds = [s.strip() for s in arguments["tlds"].split(",")]
        if not 1 <= len(tlds) <= 20 or any(not _LABEL.fullmatch(s) for s in tlds):
            return "tlds 必须是逗号分隔的 1–20 个单级 ASCII 后缀。"
    if "domains" in arguments:
        domains = [s.strip() for s in arguments["domains"].split(",")]
        if not 1 <= len(domains) <= 10 or len({s.lower() for s in domains}) != len(domains):
            return "domains 必须是逗号分隔的 1–10 个不重复完整域名。"
        if any(len(parts := s.split(".")) != 2 or not all(_LABEL.fullmatch(x) for x in parts) for s in domains):
            return "每个域名必须是 ASCII 名称.单级后缀；不支持中文域名或多级后缀。"
    return None


def _response_data(result: Any) -> tuple[Any, list[str]]:
    structured = getattr(result, "structuredContent", None)
    texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
    if structured is not None:
        return structured, texts
    if len(texts) == 1:
        try:
            return json.loads(texts[0]), []
        except (TypeError, ValueError):
            pass
    return result.model_dump(mode="json", exclude_none=True), texts


async def _exchange(remote_name: str, arguments: dict) -> dict:
    async with streamablehttp_client(ENDPOINT, timeout=30, sse_read_timeout=65) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            init = await session.initialize()
            cursor = None
            remote = None
            for _ in range(5):
                page = await session.list_tools(cursor=cursor)
                remote = next((tool for tool in page.tools if tool.name == remote_name), None)
                if remote is not None or not page.nextCursor:
                    break
                cursor = page.nextCursor
            if remote is None:
                return _error("TOOL_UNAVAILABLE", "远端暂未提供该工具；请检查服务版本，未自动重试。", tool=remote_name)
            # Validate against the actual service as well as the bundled interface.
            if next(Draft202012Validator(remote.inputSchema).iter_errors(arguments), None):
                return _error("REMOTE_SCHEMA_CHANGED", "当前服务参数模式与打包接口不一致，请更新适配器；本次未执行查询。", tool=remote_name)
            result = await session.call_tool(remote_name, arguments=arguments)
            data, texts = _response_data(result)
            if result.isError:
                return _error("SERVICE_ERROR", "服务未完成本次请求；请保留错误代码及等待时间，不要自动重试。", tool=remote_name, data=data)
            response = {
                "ok": True,
                "tool": remote_name,
                "message": "已取得公开服务的实际返回；请用中文整理，并保留来源日期、覆盖范围、未知值和报价限定。",
                "source": ENDPOINT,
                "server_version": init.serverInfo.version,
                "data": data,
            }
            if texts and (arguments.get("format") in {"csv", "markdown"} or remote_name == "open_name_finder"):
                response["formatted_text"] = texts
            if remote_name == "open_name_finder":
                response["form_url"] = "https://www.cheapest.domains/naming"
                response["message"] = "已取得命名工作流；如宿主不支持内嵌表单，请打开 form_url。此操作不进行域名检查或模型推理。"
            return response


async def call_domain_tool(remote_name: str, arguments: Any) -> dict:
    entry = CATALOG.get(remote_name)
    if entry is None:
        return _error("UNKNOWN_TOOL", "此插件不支持该工具。")
    message = _invalid(arguments, entry["input_schema"])
    if message:
        return _error("INVALID_ARGUMENTS", message)
    try:
        return await asyncio.wait_for(_exchange(remote_name, deepcopy(arguments)), TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return _error("TIMEOUT", "服务未在 75 秒内完成；未自动重试，请稍后按需查询。")
    except asyncio.CancelledError:
        raise
    except Exception:
        # Do not expose SDK exception groups, request bodies or environment paths.
        return _error("CONNECTION_FAILED", "无法连接公开 MCP 服务；请检查网络或服务状态，本次未自动重试。")


class DomainTool(Tool):
    remote_name = ""

    def __init__(self) -> None:
        entry = CATALOG[self.remote_name]
        super().__init__(ToolCard(
            id="domain_" + self.remote_name,
            name="domain_" + self.remote_name,
            description=entry["description_zh"],
            input_params=deepcopy(entry["input_schema"]),
            # The remote service explicitly reports accounting/cache writes.
            idempotent=False,
            parallel_safe=False,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_domain_tool(self.remote_name, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class SearchPricesTool(DomainTool):
    remote_name = "search_prices"


class TldPricesTool(DomainTool):
    remote_name = "get_tld_prices"


class RegistrarsTool(DomainTool):
    remote_name = "get_registrars"


class EstimateCostTool(DomainTool):
    remote_name = "estimate_cost"


class RegistrarLinkTool(DomainTool):
    remote_name = "get_registrar_link"


class NamingGuidanceTool(DomainTool):
    remote_name = "get_naming_guidance"


class AvailabilityTool(DomainTool):
    remote_name = "check_availability"


class PopularityTool(DomainTool):
    remote_name = "get_domain_popularity"


class AvailabilityBatchTool(DomainTool):
    remote_name = "check_availability_batch"


class NameFinderTool(DomainTool):
    remote_name = "open_name_finder"


class PriceHistoryTool(DomainTool):
    remote_name = "get_price_history"


class CompareNamesTool(DomainTool):
    remote_name = "compare_domain_names"


TOOL_TYPES = (
    SearchPricesTool, TldPricesTool, RegistrarsTool, EstimateCostTool,
    RegistrarLinkTool, NamingGuidanceTool, AvailabilityTool, PopularityTool,
    AvailabilityBatchTool, NameFinderTool, PriceHistoryTool, CompareNamesTool,
)
