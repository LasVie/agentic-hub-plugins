"""No-model local-host acceptance probe; real mail calls require an explicit flag.

Run with the existing isolated host's Python (httpx + websockets). No transcripts,
mail, authorization URLs or token data are written to disk.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import uuid

import httpx
import websockets

SLUG = "gmail-readonly"
WEB = "http://127.0.0.1:6411"


async def management(method: str, params: dict) -> dict:
    async with websockets.connect(WEB.replace("http", "ws") + "/ws", origin=WEB) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        rid = "gmail-management-" + uuid.uuid4().hex
        await ws.send(json.dumps({"type": "req", "id": rid, "method": method, "params": params}))
        while True:
            message = json.loads(await asyncio.wait_for(ws.recv(), 90))
            if message.get("id") == rid:
                return message


async def tool_rpc(method: str, params: dict) -> dict:
    # The existing gateway does not whitelist mcp_app.*; use the actual running
    # AgentServer's supported RPC, not a standalone SDK harness or model call.
    async with websockets.connect("ws://127.0.0.1:28430", additional_headers={"X-Jiuwen-Connection-Role": "rpc"}) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        rid = "gmail-tool-" + uuid.uuid4().hex
        await ws.send(json.dumps({"request_id": rid, "channel_id": "web", "req_method": method, "params": params}))
        while True:
            message = json.loads(await asyncio.wait_for(ws.recv(), 90))
            if message.get("request_id") == rid and message.get("is_final"):
                return message


async def run(args) -> dict:
    if args.action == "import":
        if args.zip is None:
            raise ValueError("请用 --zip 指定 ZIP。")
        async with httpx.AsyncClient() as client:
            response = await client.post(WEB + "/file-api/mcp/local-import", headers={"Origin": WEB, "X-Jiuwenswarm-Local-Import": "1"}, files={"file": (args.zip.name, args.zip.read_bytes(), "application/zip")}, timeout=30)
            value = response.json()
            item = value.get("item", {})
            return {"http_status": response.status_code, "item": {k: item.get(k) for k in ("id", "name", "display_name", "version", "source", "connection_state")}, "error": value.get("error")}
    if args.action == "card":
        return await management("mcp.show", {"id": "local-test:" + SLUG})
    if args.action in ("connect", "disconnect"):
        return await management("mcp." + args.action, {"name": SLUG})
    if args.action == "tools":
        return await tool_rpc("mcp_app.list_tools", {"server": SLUG})
    if args.action == "invalid-input":
        # Validation runs before credentials/network; safe even if logged in.
        return await tool_rpc("mcp_app.call_tool", {"server": SLUG, "tool": "gmail_search_messages", "arguments": {"max_results": 0}})
    if args.action == "missing-auth":
        root = Path.home() / ".local/share/agentic-hub/gmail-readonly"
        if (root / "token.json").exists() or (root / "login.json").exists():
            raise ValueError("存在登录凭据或待完成登录，拒绝执行无凭据检查；不会读取邮箱。")
        return await tool_rpc("mcp_app.call_tool", {"server": SLUG, "tool": "gmail_search_messages", "arguments": {"query": "subject:连接器未授权检查", "max_results": 1}})
    if not args.authorized:
        raise ValueError("真实邮箱测试需要用户明确授权账号和消息范围，再传 --authorized。")
    if args.action == "search":
        if args.newest_five:
            if args.query:
                raise ValueError("--newest-five 不应与 --query 混用。")
            query = ""
        elif not args.query:
            raise ValueError("手工测试要求 --query 明确限定授权范围。")
        else:
            query = args.query
        tool, arguments = "gmail_search_messages", {"query": query, "max_results": 5}
    elif args.action == "read-message":
        tool, arguments = "gmail_read_message", {"message_id": args.id, "max_chars": 3000}
    else:
        tool, arguments = "gmail_read_thread", {"thread_id": args.id, "max_messages": 5, "max_chars": 6000}
    return await tool_rpc("mcp_app.call_tool", {"server": SLUG, "tool": tool, "arguments": arguments})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="本机真实后端测试；不调用模型，不保存邮箱结果。")
    parser.add_argument("action", choices=["import", "card", "connect", "disconnect", "tools", "invalid-input", "missing-auth", "search", "read-message", "read-thread"])
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--query")
    parser.add_argument("--newest-five", action="store_true", help="用户已授权当前账号最新5封邮件；空查询列出最多5个标识。")
    parser.add_argument("--id")
    parser.add_argument("--authorized", action="store_true", help="用户已明确授权本次测试账号及消息范围。")
    try:
        print(json.dumps(asyncio.run(run(parser.parse_args())), ensure_ascii=False))
    except Exception:
        # Connection exceptions may carry host/session internals; do not dump.
        raise SystemExit("测试未完成；请检查参数、授权范围及本机后端。未输出私有错误详情。")
