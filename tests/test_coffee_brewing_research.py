"""Actual native SDK contracts; mock only the remote service boundary in unit cases."""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get('COFFEE_TEST_PAYLOAD', str(ROOT/'plugins/coffee-brewing-research/coffee-brewing-research')))
ISOLATED = os.environ.get('COFFEE_NATIVE_ISOLATED') == '1'
adapter = None
if ISOLATED:
    spec = importlib.util.spec_from_file_location('coffee_under_test', PAYLOAD/'tools/coffee_tools.py')
    adapter = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(adapter)
    finally:
        sys.dont_write_bytecode = previous

VALID = {
 'search_coffees': {'category':'espresso','price_max':20,'limit':2},
 'get_coffee': {'id_or_name':'actual-catalog-id'},
 'find_similar': {'coffee':'actual-catalog-id','limit':2},
 'get_recommendations': {'preferences':['chocolate','caramel'],'budget':20,'limit':2},
 'compare_coffees': {'coffee_a':'actual-a','coffee_b':'actual-b'},
 'trending_coffees': {'limit':2},
 'dial_in_suggestion': {'coffee':'actual-catalog-id','brew_method':'V60'},
 'what_to_brew': {'time_of_day':'evening','brew_method':'pourover'},
}


class PackageContract(unittest.TestCase):
    def test_native_identity_and_all_tools(self):
        manifest = json.loads((PAYLOAD/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['id'], 'coffee-brewing-research')
        self.assertEqual(manifest['name'], '咖啡选豆与冲煮')
        self.assertEqual(len(manifest['tools']), 8)
        self.assertFalse(set(manifest) & {'mcps','persona','agent_card','model','subagents','memories','rubrics'})

    def test_evidence_privacy_and_original_license(self):
        skill = (PAYLOAD/'skills/coffee-picks/SKILL.md').read_text(encoding='utf-8')
        for term in ('简体中文','20','retrieved_at','data_last_updated','attribution','一般起点','热度','不发送完整会话','不自动重试'):
            self.assertIn(term, skill)
        license_text = (PAYLOAD/'licenses/timberline-percolate/LICENSE').read_text(encoding='utf-8')
        self.assertIn('Copyright (c) 2026 Timberline Ventures LLC',license_text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"',license_text)


class IsolatedNativeSuite(unittest.TestCase):
    def test_real_sdk_in_fresh_interpreter(self):
        try:
            for name in ('openjiuwen','mcp','jsonschema','httpx'):
                importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            self.skipTest('Actual host SDK/MCP/jsonschema/httpx required')
        research = ROOT/'.research/coffee-brewing-research'
        research.mkdir(parents=True,exist_ok=True)
        env = dict(os.environ,COFFEE_NATIVE_ISOLATED='1',PYTHONUTF8='1')
        with tempfile.TemporaryDirectory(prefix='unit-',dir=research) as directory:
            result = subprocess.run([sys.executable,'-B',str(Path(__file__).resolve())],cwd=directory,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)
        output = result.stdout+result.stderr
        (research/'unit-last.log').write_text(output,encoding='utf-8',newline='\n')
        self.assertEqual(result.returncode,0,output[-7000:])
        self.assertIn('Ran 15 tests',output)
        self.assertNotIn('skipped=',output)


@asynccontextmanager
async def fake_transport(*args,**kwargs):
    yield (object(),object(),lambda:None)


class RemoteSession:
    def __init__(self, result=None, schema=None, missing=False):
        self.result = result
        self.schema = schema
        self.missing = missing
        self.calls = []
    async def __aenter__(self): return self
    async def __aexit__(self,*args): return False
    async def initialize(self): return SimpleNamespace(serverInfo=SimpleNamespace(version='1.0.2'))
    async def list_tools(self,cursor=None):
        schema = self.schema if self.schema is not None else adapter.CATALOG['search_coffees']['input_schema']
        return SimpleNamespace(tools=[] if self.missing else [SimpleNamespace(name='search_coffees',inputSchema=schema)],nextCursor=None)
    async def call_tool(self,name,arguments):
        self.calls.append((name,deepcopy(arguments)))
        return self.result


@unittest.skipUnless(adapter is not None,'Actual native SDK required')
class NativeAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_eight_cards_are_direct_chinese(self):
        names = set()
        manifest = json.loads((PAYLOAD/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual({x['class'] for x in manifest['tools']},{x.__name__ for x in adapter.TOOL_TYPES})
        for cls in adapter.TOOL_TYPES:
            card = cls().card
            names.add(card.name)
            self.assertEqual(card.exposure.value,'direct')
            self.assertRegex(card.description,r'[\u4e00-\u9fff]')
            self.assertFalse(card.idempotent)
            self.assertFalse(card.parallel_safe)
            adapter.validator_for(card.input_params).check_schema(card.input_params)
            for prop in card.input_params['properties'].values():
                self.assertRegex(prop['description'],r'[\u4e00-\u9fff]')
        self.assertEqual(len(names),8)

    async def test_all_tools_route_once_without_input_mutation(self):
        with patch.object(adapter,'_exchange',new=AsyncMock(return_value={'ok':True})) as call:
            for cls in adapter.TOOL_TYPES:
                arguments = deepcopy(VALID[cls.remote_name])
                original = deepcopy(arguments)
                await cls().invoke(arguments)
                self.assertEqual(call.call_args.args,(cls.remote_name,original))
                self.assertEqual(arguments,original)
            self.assertEqual(call.await_count,8)

    async def test_invalid_fields_and_wrapper_are_rejected_before_network(self):
        with patch.object(adapter,'_exchange',new=AsyncMock()) as call:
            for value in (None,[], 'query',{'arguments':{'limit':2}}, {'private_notes':'秘密value'}, {'endpoint':'https://private.invalid'}):
                result = await adapter.SearchCoffeesTool().invoke(value)
                self.assertEqual(result['error']['code'],'INVALID_ARGUMENTS')
                self.assertNotIn('秘密value',str(result))
                self.assertNotIn('private.invalid',str(result))
            call.assert_not_awaited()

    async def test_budget_and_limit_boundaries_are_real_usd(self):
        with patch.object(adapter,'_exchange',new=AsyncMock(return_value={'ok':True})) as call:
            for value in ({'price_max':-1},{'price_max':float('nan')},{'price_max':float('inf')},{'price_max':True},{'price_min':21,'price_max':20},{'limit':0},{'limit':11},{'limit':2.5}):
                self.assertEqual((await adapter.SearchCoffeesTool().invoke(value))['error']['code'],'INVALID_ARGUMENTS')
            call.assert_not_awaited()
            await adapter.SearchCoffeesTool().invoke({'price_max':20,'limit':2})
            self.assertEqual(call.call_args.args[1]['price_max'],20)

    async def test_preferences_required_and_bounded(self):
        with patch.object(adapter,'_exchange',new=AsyncMock()) as call:
            for value in ({},{'preferences':[]},{'preferences':['x']*21},{'preferences':['x'*61]},{'preferences':[' ']},{'preferences':'chocolate'}):
                self.assertEqual((await adapter.RecommendationsTool().invoke(value))['error']['code'],'INVALID_ARGUMENTS')
            call.assert_not_awaited()

    async def test_chinese_input_is_not_silently_substituted(self):
        with patch.object(adapter,'_exchange',new=AsyncMock(return_value={'ok':True})) as call:
            await adapter.SearchCoffeesTool().invoke({'query':'中文原样测试','limit':1})
            self.assertEqual(call.call_args.args[1]['query'],'中文原样测试')
            await adapter.GetCoffeeTool().invoke({'id_or_name':'用户原样名称'})
            self.assertEqual(call.call_args.args[1]['id_or_name'],'用户原样名称')

    async def test_enum_whitespace_and_long_names_fail_locally(self):
        with patch.object(adapter,'_exchange',new=AsyncMock()) as call:
            for name,inputs in [('search_coffees',{'roast_level':'中烘'}),('search_coffees',{'query':' '}),('get_coffee',{'id_or_name':'x'*121}),('what_to_brew',{'time_of_day':'night'})]:
                self.assertEqual((await adapter.call_coffee_tool(name,inputs))['error']['code'],'INVALID_ARGUMENTS')
            call.assert_not_awaited()

    async def test_structured_evidence_dates_null_zero_and_fallback_preserved(self):
        from mcp.types import CallToolResult,TextContent
        data={'price_usd':0,'missing':None,'data_last_updated':'2026-01-01','method':'catalog_popularity','recipe_source':'roast_based','attribution':{'source':'Percolate','retrieved_at':'2026-10-26'}}
        remote=RemoteSession(CallToolResult(content=[TextContent(type='text',text='not the authoritative data')],structuredContent=data))
        with patch.object(adapter,'streamablehttp_client',fake_transport),patch.object(adapter,'ClientSession',return_value=remote):
            result=await adapter.SearchCoffeesTool().invoke({'limit':2})
        self.assertTrue(result['ok'])
        self.assertEqual(result['data'],data)
        self.assertEqual(result['source'],adapter.ENDPOINT)
        self.assertNotEqual(result['fetched_at_utc'],data['data_last_updated'])
        self.assertEqual(len(remote.calls),1)

    async def test_json_text_empty_result_is_success_without_retry(self):
        from mcp.types import CallToolResult,TextContent
        remote=RemoteSession(CallToolResult(content=[TextContent(type='text',text='{"result_count":0,"coffees":[],"attribution":{"source":"Percolate"}}')]))
        with patch.object(adapter,'streamablehttp_client',fake_transport),patch.object(adapter,'ClientSession',return_value=remote):
            result=await adapter.SearchCoffeesTool().invoke({'query':'none','limit':1})
        self.assertTrue(result['ok'])
        self.assertEqual(result['data']['coffees'],[])
        self.assertEqual(remote.calls,[('search_coffees',{'query':'none','limit':1})])

    async def test_remote_errors_preserve_fields_without_retry(self):
        from mcp.types import CallToolResult,TextContent
        remote=RemoteSession(CallToolResult(isError=True,content=[TextContent(type='text',text='{"code":"not_found","retryAfterSeconds":30}')]))
        with patch.object(adapter,'streamablehttp_client',fake_transport),patch.object(adapter,'ClientSession',return_value=remote):
            result=await adapter.SearchCoffeesTool().invoke({})
        self.assertEqual(result['error']['code'],'SERVICE_ERROR')
        self.assertEqual(result['error']['data']['retryAfterSeconds'],30)
        self.assertEqual(len(remote.calls),1)

    async def test_missing_tool_and_schema_change_never_call_remote_tool(self):
        for remote,code in [(RemoteSession(missing=True),'TOOL_UNAVAILABLE'),(RemoteSession(schema={'type':'object','required':['new_required'],'properties':{'new_required':{'type':'string'}}}),'REMOTE_SCHEMA_CHANGED')]:
            with patch.object(adapter,'streamablehttp_client',fake_transport),patch.object(adapter,'ClientSession',return_value=remote):
                result=await adapter.SearchCoffeesTool().invoke({})
            self.assertEqual(result['error']['code'],code)
            self.assertEqual(remote.calls,[])

    async def test_timeout_and_cancellation(self):
        async def slow(*args): await asyncio.sleep(1)
        with patch.object(adapter,'_exchange',side_effect=slow),patch.object(adapter,'TIMEOUT_SECONDS',0.001):
            self.assertEqual((await adapter.SearchCoffeesTool().invoke({}))['error']['code'],'TIMEOUT')
        with patch.object(adapter,'_exchange',new=AsyncMock(side_effect=asyncio.CancelledError)):
            with self.assertRaises(asyncio.CancelledError): await adapter.SearchCoffeesTool().invoke({})

    async def test_http_rate_and_access_errors_are_bounded_and_redacted(self):
        import httpx
        for status,code in [(429,'RATE_LIMITED'),(401,'SERVICE_ACCESS_REQUIRED'),(503,'CONNECTION_FAILED')]:
            response=httpx.Response(status,headers={'Retry-After':'12'},request=httpx.Request('POST','https://secret.invalid/?token=PRIVATE'))
            exc=ExceptionGroup('hidden transport',[httpx.HTTPStatusError('PRIVATE payload',request=response.request,response=response)])
            with patch.object(adapter,'_exchange',new=AsyncMock(side_effect=exc)) as call:
                result=await adapter.SearchCoffeesTool().invoke({})
            self.assertEqual(result['error']['code'],code)
            self.assertNotIn('PRIVATE',str(result))
            call.assert_awaited_once()
            if status==429: self.assertEqual(result['error']['retry_after_seconds'],12)

    async def test_arbitrary_exception_and_tool_name_do_not_leak_or_route(self):
        with patch.object(adapter,'_exchange',new=AsyncMock(side_effect=RuntimeError('PRIVATE local/path'))):
            result=await adapter.SearchCoffeesTool().invoke({})
        self.assertNotIn('PRIVATE',str(result))
        self.assertEqual((await adapter.call_coffee_tool('arbitrary',{}))['error']['code'],'UNKNOWN_TOOL')

    async def test_plain_text_and_stream_preserve_actual_result(self):
        from mcp.types import CallToolResult,TextContent
        raw=CallToolResult(content=[TextContent(type='text',text='实际服务文本')])
        self.assertEqual(adapter._data(raw)['content'][0]['text'],'实际服务文本')
        with patch.object(adapter,'call_coffee_tool',new=AsyncMock(return_value={'ok':True,'data':{'actual':1}})):
            result=[r async for r in adapter.SearchCoffeesTool().stream({})]
        self.assertEqual(result,[{'ok':True,'data':{'actual':1}}])


def load_tests(loader, standard_tests, pattern):
    if ISOLATED:
        return loader.loadTestsFromTestCase(NativeAdapterTests)
    return unittest.TestSuite([loader.loadTestsFromTestCase(PackageContract),loader.loadTestsFromTestCase(IsolatedNativeSuite)])


if __name__ == '__main__':
    unittest.main(defaultTest='NativeAdapterTests' if ISOLATED else None,verbosity=2)
