"""Use the pinned mcp-remote transport and expose selected provider operations."""

import argparse
import asyncio
import json
import os
import shutil
import signal
import sys
from pathlib import Path

from browser_gate import LoginPage

PROVIDER = "miro"
OAUTH_HOSTS = {"miro.com", "mcp.miro.com", "api.miro.com"}
VERSION = "1.0.4"
BRIDGE = "mcp-remote@0.16.6"
URL = "https://mcp.miro.com/"
ALLOW = frozenset("board_search_boards canvas_get_canvas_composer_skill canvas_read_as_svg canvas_create_from_svg".split())
DATA = Path(os.environ.get("JIUWENSWARM_DATA_DIR") or Path.home() / ".jiuwenswarm")
SESSION = DATA / "connector-data" / PROVIDER / "mcp-remote"
VERIFIED = SESSION / "verified-endpoint"


class ConnectorError(Exception):
    pass


def node_tools():
    env = dict(os.environ)
    runtime = Path("/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin")
    if sys.platform == "darwin" and runtime.is_dir():
        env["PATH"] = str(runtime) + os.pathsep + env.get("PATH", "")
    npx = shutil.which("npx", path=env.get("PATH"))
    if not npx:
        raise ConnectorError("找不到 Node.js 的 npx，请安装 Node.js 后重试。")
    return npx, env


def logged_in():
    try:
        if VERIFIED.read_text(encoding="utf-8") != URL:
            return False
    except OSError:
        return False
    for path in SESSION.rglob("*_tokens.json"):
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("access_token"):
                return True
        except (OSError, ValueError, AttributeError):
            continue
    return False


class Session:
    def __init__(self, process):
        self.process = process
        self.request_id = 0

    async def send(self, message):
        data = json.dumps({"jsonrpc": "2.0", **message}, ensure_ascii=False).encode()
        self.process.stdin.write(data + b"\n")
        await self.process.stdin.drain()

    async def ask(self, method, params):
        self.request_id += 1
        key = self.request_id
        await self.send({"id": key, "method": method, "params": params})
        while True:
            line = await self.process.stdout.readline()
            if not line:
                raise ConnectorError("MCP 连接已结束。请检查网络和账号权限。")
            message = json.loads(line)
            if "method" in message and "id" in message:
                await self.send({"id": message["id"], "error": {
                    "code": -32601, "message": "Unsupported client request",
                }})
            if message.get("id") == key and ("result" in message or "error" in message):
                if "error" in message:
                    raise ConnectorError(f"MCP 服务拒绝了 {method}，请核对当前授权和工具参数。")
                return message["result"]

    async def tools(self):
        page = await self.ask("tools/list", {})
        items = list(page.get("tools", []))
        cursor = page.get("nextCursor")
        seen = set()
        while cursor and cursor not in seen and len(seen) < 10:
            seen.add(cursor)
            page = await self.ask("tools/list", {"cursor": cursor})
            items.extend(page.get("tools", []))
            cursor = page.get("nextCursor")
        return [item for item in items if item["name"] in ALLOW]


async def read_authorization(output, page):
    pending = False
    while line := await output.readline():
        value = line.decode("utf-8", errors="replace").strip()
        if pending and value.startswith("https://"):
            page.publish(value)
            pending = False
        elif "Please authorize this client by visiting:" in value:
            pending = True


async def remote(args, page=None):
    npx, env = node_tools()
    SESSION.mkdir(mode=0o700, parents=True, exist_ok=True)
    env.update({
        "MCP_REMOTE_CONFIG_DIR": str(SESSION),
        "npm_config_cache": str(SESSION.parent / "npm-cache"),
        "npm_config_registry": "https://registry.npmjs.org/",
        "npm_config_ignore_scripts": "true",
        "npm_config_update_notifier": "false",
    })
    process = await asyncio.create_subprocess_exec(
        npx, "--yes", "--package", BRIDGE, "mcp-remote", URL,
        "--transport", "http-only", "--protocol", "auto", "--auth-timeout", "150",
        "--static-oauth-client-metadata",
        json.dumps({"client_name": f"WorkSwarm {PROVIDER} Connector"}),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE if page else asyncio.subprocess.DEVNULL,
        limit=4194304, env=env, start_new_session=os.name != "nt",
    )
    reader = asyncio.create_task(read_authorization(process.stderr, page)) if page else None
    try:
        session = Session(process)
        await session.ask("initialize", {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": f"workswarm-{PROVIDER}", "version": VERSION},
        })
        await session.send({"method": "notifications/initialized"})
        if args.command == "login":
            if not await session.tools():
                raise ConnectorError("已连接到服务，但当前账号没有此包需要的工具。")
            VERIFIED.write_text(URL, encoding="utf-8")
            return {"connected": True}
        if args.command == "tools":
            return {"tools": await session.tools()}
        result = await session.ask("tools/call", {"name": args.tool, "arguments": args.arguments})
        if result.get("isError"):
            raise ConnectorError("执行失败，请核对工具参数和资源权限。")
        return result
    finally:
        if process.returncode is None:
            process.stdin.close()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                if os.name == "nt":
                    process.kill()
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                await process.wait()
        if reader is not None:
            reader.cancel()


def object_argument(value):
    try:
        result = json.loads(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("工具参数必须是 JSON 对象。") from error
    if not isinstance(result, dict):
        raise argparse.ArgumentTypeError("工具参数必须是 JSON 对象。")
    return result


def main():
    parser = argparse.ArgumentParser(description=f"使用 {PROVIDER} 官方 MCP")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "version", "status", "login", "logout", "tools"):
        commands.add_parser(name)
    call = commands.add_parser("call")
    call.add_argument("tool", choices=sorted(ALLOW))
    call.add_argument("arguments", type=object_argument)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            node_tools()
            result = {"ready": True}
        elif args.command == "version":
            result = {"version": VERSION}
        elif args.command == "status":
            result = {"connected": logged_in()}
        elif args.command == "logout":
            if SESSION.exists():
                shutil.rmtree(SESSION)
            result = {"connected": False}
        else:
            if args.command != "login" and not logged_in():
                raise ConnectorError("请先在 WorkSwarm 卡片完成授权。")
            if args.command == "login":
                VERIFIED.unlink(missing_ok=True)
                with LoginPage(PROVIDER, OAUTH_HOSTS) as page:
                    if not page.started.wait(timeout=155):
                        raise ConnectorError("等待打开授权入口超时，请重新点击连接。")
                    try:
                        result = asyncio.run(asyncio.wait_for(remote(args, page), 175))
                    except (ConnectorError, ValueError, OSError, asyncio.TimeoutError):
                        page.finish(False)
                        raise
            else:
                result = asyncio.run(asyncio.wait_for(remote(args), 60))
    except (ConnectorError, ValueError, OSError, asyncio.TimeoutError, BrokenPipeError) as error:
        print(str(error) if isinstance(error, ConnectorError) else "无法完成 MCP 请求，请检查网络后重新连接。", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
