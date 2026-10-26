"""Native adapter contracts; real SDK types, transport patched only in unit cases."""
import asyncio
from copy import deepcopy
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get('DOMAIN_RESEARCH_TEST_PAYLOAD', str(ROOT / 'plugins/domain-renewal-research/domain-renewal-research')))
ISOLATED = os.environ.get('DOMAIN_RESEARCH_ISOLATED_NATIVE') == '1'
adapter = None
if ISOLATED:
    spec = importlib.util.spec_from_file_location('domain_research_under_test', PAYLOAD / 'tools/domain_tools.py')
    adapter = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(adapter)
    except ModuleNotFoundError as exc:
        if not exc.name.startswith(('openjiuwen', 'mcp', 'jsonschema')):
            raise
        adapter = None
    finally:
        sys.dont_write_bytecode = previous

VALID = {
    'search_prices': {'q': '.com,.org,.dev', 'sort': 'renewal', 'maxRenewalCents': 1500, 'limit': 3},
    'get_tld_prices': {'tld': 'com', 'limit': 3},
    'get_registrars': {},
    'estimate_cost': {'tld': 'com', 'registrar': 'porkbun', 'years': 3},
    'get_registrar_link': {'tld': 'com', 'registrar': 'porkbun', 'name': 'example'},
    'get_naming_guidance': {},
    'check_availability': {'name': 'example', 'tld': 'com'},
    'get_domain_popularity': {'name': 'example', 'tld': 'com'},
    'check_availability_batch': {'name': 'example', 'tlds': 'com,org', 'cachedOnly': True},
    'open_name_finder': {},
    'get_price_history': {'tld': 'com'},
    'compare_domain_names': {'domains': 'example.com,example.org'},
}


class PackageContract(unittest.TestCase):
    def test_no_credentials_hooks_or_persona(self):
        manifest = json.loads((PAYLOAD / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['display_name']['zh'], '域名续费比价')
        self.assertEqual(len(manifest['tools']), 12)
        self.assertFalse(set(manifest) & {'persona', 'agent_card', 'model', 'subagents', 'memories', 'rubrics'})
        self.assertNotIn('mcps', manifest)  # Native cards, no duplicate remote registration.

    def test_chinese_workflow_preserves_evidence_and_scope(self):
        text = (PAYLOAD / 'skills/domain-research/SKILL.md').read_text(encoding='utf-8')
        for required in ('简体中文', 'coverage.partial', 'stale', 'sampled_standard', 'sampled_api', 'retryAfterSeconds', 'CC BY-NC 4.0', 'Cloudflare', 'Vercel'):
            self.assertIn(required, text)
        license_text = (PAYLOAD / 'licenses/cheapest-domains/LICENSE').read_text(encoding='utf-8')
        self.assertIn('Copyright (c) 2026 Ilios Galil (PerfWebsite)', license_text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', license_text)


class IsolatedNativeSuite(unittest.TestCase):
    def test_real_sdk_suite_in_fresh_process(self):
        # Other repository tests alter process-global SDK logging configuration.
        # Test actual native objects in a clean interpreter, without changing it.
        try:
            for package in ('openjiuwen', 'mcp', 'jsonschema'):
                importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            self.skipTest('Requires actual host SDK, MCP and jsonschema')
        research = ROOT / '.research/domain-renewal-research'
        research.mkdir(parents=True, exist_ok=True)
        self.assertTrue(research.resolve().is_relative_to(ROOT.resolve()))
        env = dict(os.environ, DOMAIN_RESEARCH_ISOLATED_NATIVE='1', PYTHONUTF8='1')
        with tempfile.TemporaryDirectory(prefix='native-unit-', dir=research) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(research.resolve()))
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve())], cwd=directory, env=env, text=True, encoding='utf-8', capture_output=True, timeout=120)
        output = result.stdout + result.stderr
        (research / 'isolated-native-suite-last.log').write_text(output, encoding='utf-8')
        self.assertEqual(result.returncode, 0, output[-6000:])
        self.assertIn('Ran 15 tests', output)
        self.assertNotIn('skipped=', output)


@unittest.skipUnless(adapter is not None, 'Requires actual openJiuwen, MCP SDK and jsonschema')
class NativeAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_cards_are_direct_chinese_and_unique(self):
        manifest = json.loads((PAYLOAD / 'manifest.json').read_text(encoding='utf-8'))
        classes = {entry['class'] for entry in manifest['tools']}
        self.assertEqual(classes, {cls.__name__ for cls in adapter.TOOL_TYPES})
        ids = set()
        for cls in adapter.TOOL_TYPES:
            tool = cls()
            card = tool.card
            self.assertRegex(card.description, r'[\u4e00-\u9fff]')
            self.assertEqual(card.exposure.value, 'direct')
            self.assertFalse(card.idempotent)
            self.assertFalse(card.parallel_safe)
            adapter.Draft202012Validator.check_schema(card.input_params)
            for field in card.input_params['properties'].values():
                self.assertRegex(field['description'], r'[\u4e00-\u9fff]')
            self.assertNotIn(card.id, ids)
            ids.add(card.id)
        self.assertEqual(len(ids), 12)

    async def test_every_declared_tool_routes_once_with_direct_parameters(self):
        with patch.object(adapter, '_exchange', new=AsyncMock(return_value={'ok': True, 'data': {'中文': '证据'}})) as exchange:
            for cls in adapter.TOOL_TYPES:
                inputs = deepcopy(VALID[cls.remote_name])
                original = deepcopy(inputs)
                result = await cls().invoke(inputs)
                self.assertTrue(result['ok'])
                self.assertEqual(exchange.call_args.args, (cls.remote_name, inputs))
                self.assertEqual(inputs, original)
            self.assertEqual(exchange.await_count, 12)

    async def test_invalid_budgets_types_and_nested_arguments_never_connect(self):
        cases = [None, [], {'arguments': VALID['search_prices']}, {'limit': 0}, {'limit': 201}, {'limit': True}, {'maxRenewalCents': -1}, {'maxRenewalCents': 1.5}, {'years': 11}, {'years': True}, {'sort': 'cheapest'}, {'private_project_brief': '私密项目不应外发'}]
        with patch.object(adapter, '_exchange', new=AsyncMock()) as exchange:
            for inputs in cases:
                result = await adapter.SearchPricesTool().invoke(inputs)
                self.assertFalse(result['ok'], inputs)
                self.assertEqual(result['error']['code'], 'INVALID_ARGUMENTS')
                self.assertNotIn('私密项目', json.dumps(result, ensure_ascii=False))
                self.assertRegex(result['error']['message'], r'[\u4e00-\u9fff]')
            exchange.assert_not_awaited()

    async def test_conflicting_filters_and_stale_scope_never_connect(self):
        with patch.object(adapter, '_exchange', new=AsyncMock()) as exchange:
            for inputs in ({'registrar': 'a', 'registrars': 'b'}, {'includeStale': True}, {'includeStale': True, 'view': 'best'}):
                self.assertFalse((await adapter.SearchPricesTool().invoke(inputs))['ok'])
            exchange.assert_not_awaited()

    async def test_chinese_names_bad_labels_and_multilevel_suffixes_rejected(self):
        with patch.object(adapter, '_exchange', new=AsyncMock()) as exchange:
            for name, tld in [('中文测试', 'com'), ('example.com', 'com'), ('-bad', 'com'), ('bad-', 'com'), ('x;echo secret', 'com'), ('a' * 64, 'com'), ('example', 'co.uk')]:
                self.assertFalse((await adapter.AvailabilityTool().invoke({'name': name, 'tld': tld}))['ok'])
            exchange.assert_not_awaited()

    async def test_comparison_and_batch_bounds_rejected_locally(self):
        with patch.object(adapter, '_exchange', new=AsyncMock()) as exchange:
            for domains in ('', 'example.com,EXAMPLE.COM', 'a.co.uk', ','.join('a%d.com' % i for i in range(11))):
                self.assertFalse((await adapter.CompareNamesTool().invoke({'domains': domains}))['ok'])
            for tlds in ('', 'com,', ','.join('com' for _ in range(21))):
                self.assertFalse((await adapter.AvailabilityBatchTool().invoke({'name': 'example', 'tlds': tlds}))['ok'])
            exchange.assert_not_awaited()

    async def test_partial_unknown_stale_and_licensed_data_remain_exact(self):
        evidence = {'coverage': {'partial': True}, 'offers': [{'renewalCents': None, 'stale': True, 'pricingBasis': 'sampled_standard', 'fetchedAt': '2026-10-01T00:00:00Z'}], 'availability': 'unknown', 'premium': None, 'source': {'license': 'CC BY-NC 4.0'}, '说明': '中文来源'}
        expected = {'ok': True, 'data': deepcopy(evidence)}
        with patch.object(adapter, '_exchange', new=AsyncMock(return_value=expected)):
            result = await adapter.SearchPricesTool().invoke({'limit': 3})
            self.assertEqual(result['data'], evidence)

    async def test_service_rate_error_preserves_wait_and_never_retries(self):
        expected = adapter._error('SERVICE_ERROR', '服务限流', data={'error': {'code': 'rate_limited', 'retryAfterSeconds': 60}})
        with patch.object(adapter, '_exchange', new=AsyncMock(return_value=expected)) as exchange:
            self.assertEqual(await adapter.RegistrarsTool().invoke({}), expected)
            self.assertEqual(exchange.await_count, 1)

    async def test_timeout_and_exception_do_not_expose_private_inputs(self):
        for exception, code in ((asyncio.TimeoutError(), 'TIMEOUT'), (RuntimeError('secret-path-and-input'), 'CONNECTION_FAILED')):
            with patch.object(adapter, '_exchange', new=AsyncMock(side_effect=exception)) as exchange:
                result = await adapter.RegistrarsTool().invoke({})
                self.assertEqual(result['error']['code'], code)
                self.assertNotIn('secret-path', str(result))
                self.assertRegex(result['error']['message'], r'[\u4e00-\u9fff]')
                self.assertEqual(exchange.await_count, 1)

    async def test_cancellation_propagates(self):
        with patch.object(adapter, '_exchange', new=AsyncMock(side_effect=asyncio.CancelledError)):
            with self.assertRaises(asyncio.CancelledError):
                await adapter.RegistrarsTool().invoke({})

    async def test_text_json_and_plain_chinese_response_parsing(self):
        from mcp.types import CallToolResult, TextContent
        data, texts = adapter._response_data(CallToolResult(content=[TextContent(type='text', text='{"说明":"中文证据","premium":null}')]))
        self.assertEqual(data, {'说明': '中文证据', 'premium': None})
        self.assertEqual(texts, [])
        data, texts = adapter._response_data(CallToolResult(content=[TextContent(type='text', text='中文表单说明')]))
        self.assertIn('content', data)
        self.assertEqual(texts, ['中文表单说明'])

    async def test_stream_returns_one_actual_invoke_result(self):
        with patch.object(adapter, '_exchange', new=AsyncMock(return_value={'ok': True, 'data': {}})) as exchange:
            results = [item async for item in adapter.RegistrarsTool().stream({})]
            self.assertEqual(results, [{'ok': True, 'data': {}}])
            self.assertEqual(exchange.await_count, 1)

    async def test_arbitrary_remote_tool_is_not_permitted(self):
        with patch.object(adapter, '_exchange', new=AsyncMock()) as exchange:
            self.assertEqual((await adapter.call_domain_tool('buy_domain', {}))['error']['code'], 'UNKNOWN_TOOL')
            exchange.assert_not_awaited()


def load_tests(loader, _tests, _pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(PackageContract))
    suite.addTests(loader.loadTestsFromTestCase(NativeAdapterTests if ISOLATED else IsolatedNativeSuite))
    return suite


if __name__ == '__main__':
    unittest.main(verbosity=2)
