"""Real MCP process protocol check with no Google account or network access."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PAYLOAD = Path(__file__).resolve().parents[1] / "gmail-readonly"


def test_real_stdio_discovery_and_missing_credentials():
    async def check(root):
        params = StdioServerParameters(command=sys.executable, args=["-B", str(PAYLOAD / "server.py")], env={**os.environ, "GMAIL_READONLY_HOME": root})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "Gmail 只读邮件连接器"
                tools = await session.list_tools()
                assert {tool.name for tool in tools.tools} == {"gmail_search_messages", "gmail_read_message", "gmail_read_thread"}
                result = await session.call_tool("gmail_search_messages", {"query": "subject:未授权合成测试", "max_results": 1})
                data = result.structuredContent or json.loads(result.content[0].text)
                assert data["ok"] is False
                assert data["version"] == "1.0.0"
                assert data["error"]["code"] == "not_signed_in"
                invalid = await session.call_tool("gmail_read_message", {"message_id": "../send"})
                data = invalid.structuredContent or json.loads(invalid.content[0].text)
                assert data["error"]["code"] == "invalid_argument"
    with tempfile.TemporaryDirectory(prefix="gmail-stdio-") as root:
        asyncio.run(check(root))
