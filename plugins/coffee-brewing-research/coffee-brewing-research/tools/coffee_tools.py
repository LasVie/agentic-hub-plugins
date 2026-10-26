"""Native Percolate client; hosted implementation/data are not distributed.

Workflow adapted from Percolate 1.0.0, Copyright (c) 2026 Timberline Ventures LLC.
Chinese native integration, validation and bounded calls added 2026-10-26.
Full upstream MIT text: licenses/timberline-percolate/LICENSE.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
from jsonschema.validators import validator_for
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openjiuwen.core.foundation.tool import Tool, ToolCard

ENDPOINT = "https://mcp.percolateapp.com/mcp"
TIMEOUT_SECONDS = 60
CATALOG = json.loads(Path(__file__).with_name("tool_catalog.json").read_text(encoding="utf-8"))


def _error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


def _invalid(inputs: Any, schema: dict) -> str | None:
    if not isinstance(inputs, dict):
        return "参数必须是 JSON 对象，字段直接传入，不套 arguments。"
    if set(inputs) - set(schema.get("properties", {})):
        return "包含未声明的参数；只传工具定义中的字段，不附带私密资料或连接设置。"
    if next(validator_for(schema)(schema).iter_errors(inputs), None):
        return "参数类型、必填项、枚举或范围不符合说明；价格用美元，limit 为 1–10 的整数。"
    for value in inputs.values():
        if isinstance(value, float) and not math.isfinite(value):
            return "价格必须是有限的非负数，不能使用 NaN 或无穷大。"
        if isinstance(value, str) and not value.strip():
            return "已提供的文字参数不能为空或只有空格；无筛选条件时请省略该字段。"
        if isinstance(value, list) and any(not item.strip() for item in value if isinstance(item, str)):
            return "风味列表中的每个文字项都必须有实际内容。"
    if "price_min" in inputs and "price_max" in inputs and inputs["price_min"] > inputs["price_max"]:
        return "price_min 不能大于 price_max；未自动交换预算或执行查询。"
    return None


def _data(result: Any) -> Any:
    if result.structuredContent is not None:
        return result.structuredContent
    texts = [item.text for item in result.content if getattr(item, "type", None) == "text"]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except (ValueError, TypeError):
            pass
    return result.model_dump(mode="json", exclude_none=True)


async def _exchange(remote_name: str, arguments: dict) -> dict:
    async with streamablehttp_client(ENDPOINT, timeout=20, sse_read_timeout=45) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            initialized = await session.initialize()
            cursor = None
            remote = None
            for _ in range(3):
                page = await session.list_tools(cursor=cursor)
                remote = next((tool for tool in page.tools if tool.name == remote_name), None)
                if remote is not None or not page.nextCursor:
                    break
                cursor = page.nextCursor
            if remote is None:
                return _error("TOOL_UNAVAILABLE", "当前远端未提供该工具；未调用其他工具或自动重试。")
            if next(validator_for(remote.inputSchema)(remote.inputSchema).iter_errors(arguments), None):
                return _error("REMOTE_SCHEMA_CHANGED", "远端参数定义已经变化；查询尚未执行，请更新插件。")
            result = await session.call_tool(remote_name, arguments=arguments)
            data = _data(result)
            if result.isError:
                return _error("SERVICE_ERROR", "服务未完成本次查询；保留原始错误和等待提示，未自动重试。", data=data)
            return {
                "ok": True,
                "tool": remote_name,
                "source": ENDPOINT,
                "server_version": initialized.serverInfo.version,
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "message": "已取得 Percolate 实际返回；请用中文整理，保留来源、价格单位及配方或热度方法的限定。",
                "data": data,
            }


def _http_error(error: BaseException) -> httpx.HTTPStatusError | None:
    pending, seen = [error], set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if isinstance(item, httpx.HTTPStatusError):
            return item
        pending.extend(getattr(item, "exceptions", ()))
        for child in (item.__cause__, item.__context__):
            if child is not None:
                pending.append(child)
    return None


async def call_coffee_tool(remote_name: str, inputs: Any) -> dict:
    entry = CATALOG.get(remote_name)
    if entry is None:
        return _error("UNKNOWN_TOOL", "插件没有声明该工具。")
    invalid = _invalid(inputs, entry["input_schema"])
    if invalid:
        return _error("INVALID_ARGUMENTS", invalid)
    try:
        return await asyncio.wait_for(_exchange(remote_name, deepcopy(inputs)), timeout=TIMEOUT_SECONDS)
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        return _error("TIMEOUT", "服务未在规定时间内完成；已停止等待，未自动重试。")
    except Exception as exc:
        http_error = _http_error(exc)
        if http_error is not None:
            status = http_error.response.status_code
            if status == 429:
                retry = http_error.response.headers.get("Retry-After")
                try:
                    seconds = float(retry)
                    retry = seconds if math.isfinite(seconds) and seconds >= 0 else None
                except (TypeError, ValueError):
                    retry = None
                return _error("RATE_LIMITED", "服务限制了本次请求；请按等待提示稍后手动查询，未自动重试。", retry_after_seconds=retry)
            if status in (401, 403):
                return _error("SERVICE_ACCESS_REQUIRED", "公开服务暂不允许此次访问；未登录、申请密钥或绕过限制。", status_code=status)
            return _error("CONNECTION_FAILED", "远端 HTTP 请求未完成；请检查服务状态，未自动重试。", status_code=status)
        # Never expose request bodies, exception text, local paths or credentials.
        return _error("CONNECTION_FAILED", "无法连接公开 MCP 服务；请检查网络或服务状态，未自动重试。")


class CoffeeTool(Tool):
    remote_name = ""

    def __init__(self) -> None:
        entry = CATALOG[self.remote_name]
        super().__init__(ToolCard(
            id="coffee_" + self.remote_name,
            name="coffee_" + self.remote_name,
            description=entry["description_zh"],
            input_params=deepcopy(entry["input_schema"]),
            # Public lookups still update upstream logs/usage; do not auto-replay.
            idempotent=False,
            parallel_safe=False,
        ))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_coffee_tool(self.remote_name, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class SearchCoffeesTool(CoffeeTool):
    remote_name = "search_coffees"


class GetCoffeeTool(CoffeeTool):
    remote_name = "get_coffee"


class FindSimilarTool(CoffeeTool):
    remote_name = "find_similar"


class RecommendationsTool(CoffeeTool):
    remote_name = "get_recommendations"


class CompareCoffeesTool(CoffeeTool):
    remote_name = "compare_coffees"


class TrendingCoffeesTool(CoffeeTool):
    remote_name = "trending_coffees"


class DialInSuggestionTool(CoffeeTool):
    remote_name = "dial_in_suggestion"


class WhatToBrewTool(CoffeeTool):
    remote_name = "what_to_brew"


TOOL_TYPES = (SearchCoffeesTool, GetCoffeeTool, FindSimilarTool, RecommendationsTool,
              CompareCoffeesTool, TrendingCoffeesTool, DialInSuggestionTool, WhatToBrewTool)
