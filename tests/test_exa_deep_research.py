"""Native tool regressions; network is replaced only at the transport boundary."""
import asyncio
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

PAYLOAD = Path(os.environ.get("EXA_TEST_PAYLOAD", str(Path(__file__).resolve().parents[1] / "plugins/exa-deep-research/exa-deep-research")))
spec = importlib.util.spec_from_file_location("exa_tools_under_test", PAYLOAD / "tools/exa_tools.py")
adapter = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(adapter)
except ModuleNotFoundError as exc:
    if not exc.name.startswith(("openjiuwen", "mcp", "jsonschema")):
        raise
    adapter = None

@unittest.skipUnless(adapter is not None, "Requires the real openJiuwen host, MCP SDK and jsonschema")
class ExaToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_search_never_contacts_service(self):
        with patch.object(adapter, "_exchange", new_callable=AsyncMock) as exchange:
            for inputs in ({"query": ""}, {"query": "x", "numResults": 0}, {"query": "x", "numResults": True}, {"query": "x", "extra": 1}):
                result = await adapter.ExaSearchTool().invoke(inputs)
                self.assertEqual(result["error"]["code"], "INVALID_INPUT")
            exchange.assert_not_awaited()

    async def test_fetch_rejects_file_and_credential_urls(self):
        with patch.object(adapter, "_exchange", new_callable=AsyncMock) as exchange:
            for urls in ([], ["file:///secret.txt"], ["https://user:password@example.com"], ["https://[bad"]):
                self.assertEqual((await adapter.ExaFetchTool().invoke({"urls": urls}))["error"]["code"], "INVALID_INPUT")
            exchange.assert_not_awaited()

    async def test_paid_action_requires_explicit_true_and_key(self):
        with patch.dict(os.environ, {"EXA_API_KEY": ""}), patch.object(adapter, "_exchange", new_callable=AsyncMock) as exchange:
            tool = adapter.ExaResearchTool()
            self.assertEqual((await tool.invoke({"arguments": {"query": "test"}}))["error"]["code"], "PAID_ACTION_REQUIRES_APPROVAL")
            self.assertEqual((await tool.invoke({"arguments": {"query": "test"}, "allow_paid": "true"}))["error"]["code"], "PAID_ACTION_REQUIRES_APPROVAL")
            self.assertEqual((await tool.invoke({"arguments": {"query": "test"}, "allow_paid": True}))["error"]["code"], "EXA_API_KEY_REQUIRED")
            exchange.assert_not_awaited()

    async def test_research_rejects_ambiguous_run_before_network(self):
        with patch.dict(os.environ, {"EXA_API_KEY": "test-key"}), patch.object(adapter, "_exchange", new_callable=AsyncMock) as exchange:
            result = await adapter.ExaResearchTool().invoke({"arguments": {"query": "test", "runId": "run_123"}, "allow_paid": True})
            self.assertEqual(result["error"]["code"], "INVALID_INPUT")
            exchange.assert_not_awaited()

    async def test_remote_error_and_structured_data_are_preserved(self):
        expected = {"ok": False, "tool": "web_search_exa", "result": {"isError": True, "content": [{"type": "text", "text": "Rate limited"}], "structuredContent": {"code": 429}}}
        with patch.object(adapter, "_exchange", new=AsyncMock(return_value=expected)) as exchange:
            result = await adapter.ExaSearchTool().invoke({"query": "test"})
            self.assertEqual(result, expected)
            self.assertEqual(exchange.call_args.args[1], {"query": "test", "numResults": 5})

    async def test_key_redacted_in_nested_remote_output(self):
        key = "private-test-key"
        with patch.dict(os.environ, {"EXA_API_KEY": key}), patch.object(adapter, "_exchange", new=AsyncMock(return_value={"ok": False, "result": {"content": [{"text": "upstream echoed " + key}]}})):
            result = await adapter.ExaSearchTool().invoke({"query": "test"})
            self.assertNotIn(key, str(result))
            self.assertIn("[REDACTED]", str(result))

    async def test_exception_group_does_not_expose_key_or_request(self):
        with patch.object(adapter, "_exchange", new=AsyncMock(side_effect=ExceptionGroup("secret-header", [ValueError("private-body")]))):
            result = await adapter.ExaSearchTool().invoke({"query": "test"})
            self.assertEqual(result["error"]["code"], "EXA_CONNECTION_FAILED")
            self.assertNotIn("secret-header", str(result))
            self.assertNotIn("private-body", str(result))

    async def test_timeout_is_ambiguous_and_not_retried(self):
        async def wait(*args):
            await asyncio.sleep(1)
        with patch.object(adapter, "TIMEOUT_SECONDS", 0.01), patch.object(adapter, "_exchange", new=AsyncMock(side_effect=wait)) as exchange:
            result = await adapter.ExaSearchTool().invoke({"query": "test"})
            self.assertEqual(result["error"]["code"], "TIMEOUT")
            exchange.assert_awaited_once()

    async def test_stream_yields_one_result(self):
        with patch.object(adapter, "_exchange", new=AsyncMock(return_value={"ok": True, "result": {"content": []}})):
            results = [item async for item in adapter.ExaFetchTool().stream({"urls": ["https://example.com"]})]
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0]["ok"])

if __name__ == "__main__":
    unittest.main()
