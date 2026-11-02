"""Business-boundary checks: validation, provenance, remote changes and failures."""
import asyncio
from contextlib import asynccontextmanager
import copy
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from jsonschema import Draft202012Validator

PAYLOAD = Path(os.environ.get('BIORXIV_TEST_PAYLOAD') or Path(__file__).resolve().parents[1] / 'biorxiv-catalog')
spec = importlib.util.spec_from_file_location('biorxiv_under_test', PAYLOAD / 'tools/biorxiv_tools.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def response(data=None, failed=False, text=''):
    return SimpleNamespace(structuredContent=data, isError=failed, content=[SimpleNamespace(type='text', text=text)] if text else [])

class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_seven_actual_native_tools_and_valid_schemas(self):
        manifest = json.loads((PAYLOAD / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['tools']), 7)
        self.assertEqual({c.__name__ for c in m.TOOL_TYPES}, {t['class'] for t in manifest['tools']})
        self.assertEqual(len({c.remote_name for c in m.TOOL_TYPES}), 7)
        for cls in m.TOOL_TYPES:
            card = cls().card
            self.assertEqual(card.name, 'biorxiv_' + cls.remote_name)
            self.assertRegex(card.description, '[\u4e00-\u9fff]')
            Draft202012Validator.check_schema(card.input_params)

    async def test_invalid_arguments_never_reach_network(self):
        cases = [('search_preprints', []), ('search_preprints', {'arguments': {}}),
                 ('search_preprints', {'date_from':'2024-01-08','date_to':'2024-01-01'}),
                 ('search_preprints', {'date_from':'2024-02-30','date_to':'2024-03-01'}),
                 ('search_preprints', {'date_from':'20240101','date_to':'2024-01-01'}),
                 ('search_preprints', {'date_from':'2024-01-01'}),
                 ('search_preprints', {'recent_days':5,'recent_count':2}),
                 ('search_preprints', {'recent_days': True}),
                 ('search_preprints', {'recent_days':5,'limit':0}),
                 ('search_preprints', {'date_from':'2020-01-01','date_to':'2024-01-01'}),
                 ('search_by_funder', {'funder_ror_id':'00k4n6c32','date_from':'2024-01-01','date_to':'2024-02-01'}),
                 ('search_by_funder', {'funder_ror_id':'中文机构','date_from':'2025-05-01','date_to':'2025-05-02'}),
                 ('get_preprint', {'doi':'not-a-doi'}), ('get_preprint', {'doi':'https://example.org/10.1101/123'}),
                 ('get_categories', {'private_note':'中文私密内容'}),
                 ('search_published_preprints', {'recent_days':5,'publisher':'Nature'})]
        with patch.object(m, 'exchange', new_callable=AsyncMock) as call:
            for name,args in cases:
                result = await m.call_biorxiv_tool(name,args)
                self.assertEqual(result['error']['code'], 'INVALID_ARGUMENTS', (name,args,result))
                self.assertNotIn('中文私密内容', str(result))
            call.assert_not_awaited()

    async def test_aliases_are_explicit_and_input_is_not_mutated(self):
        args = {'recent_days':3,'category':'生物信息学','server':'生物预印本','limit':2}
        original = copy.deepcopy(args)
        with patch.object(m, 'exchange', new_callable=AsyncMock, return_value={'ok':True}) as exchange:
            self.assertTrue((await m.call_biorxiv_tool('search_preprints',args))['ok'])
            sent = exchange.await_args.args[1]
            self.assertEqual(sent, {'recent_days':3,'category':'bioinformatics','server':'biorxiv','limit':2})
        self.assertEqual(args,original)

    async def test_inconsistent_total_is_preserved_and_warned(self):
        data = {'success':True,'results':[{'doi':'10.1101/1'},{'doi':'10.1101/2'}],'count':2,'total':0}
        result = m.summarize_response('search_preprints',{},response(data),'3.2.0')
        self.assertTrue(result['ok'])
        self.assertEqual(result['received_count'],2)
        self.assertEqual(result['data'],data)
        self.assertTrue(any('total' in s for s in result['warnings_zh']))

    async def test_empty_results_are_not_connection_failures(self):
        data = {'success':True,'results':[],'count':0,'total':0}
        result = m.summarize_response('search_preprints',{},response(data),'3.2.0')
        self.assertTrue(result['ok'])
        self.assertEqual(result['received_count'],0)

    async def test_missing_statistical_period_and_metric_are_not_invented(self):
        data = {'success':True,'results':[{'month':'','full_text_views':0,'pdf_downloads':12}]}
        result = m.summarize_response('get_usage_statistics',{'interval':'yearly'},response(data),'3.2.0')
        self.assertEqual(result['data'],data)
        self.assertTrue(any('期间' in w for w in result['warnings_zh']))
        self.assertTrue(any('摘要浏览' in w for w in result['warnings_zh']))
        self.assertNotIn('year',result['data']['results'][0])

    async def test_upstream_failure_and_malformed_response_never_become_success(self):
        for r in (response({'success':False,'error':'synthetic upstream failure'}), response(None,True,'synthetic error')):
            result = m.summarize_response('get_categories',{},r,'3.2.0')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error']['code'],'SERVICE_ERROR')
        self.assertEqual(m.summarize_response('get_categories',{},response(None,False,'not JSON'),'3.2.0')['error']['code'],'UPSTREAM_FORMAT_ERROR')

    async def test_oversized_source_data_is_not_silently_truncated(self):
        result = m.summarize_response('get_preprint',{},response({'abstract':'x'*(m.MAX_RESPONSE_BYTES+1)}),'3.2.0')
        self.assertEqual(result['error']['code'],'RESPONSE_TOO_LARGE')

    async def test_access_and_limit_errors_preserve_status_without_private_details(self):
        for status,code in ((401,'AUTH_REQUIRED'),(403,'ACCESS_DENIED'),(429,'RATE_LIMITED')):
            req = httpx.Request('POST',m.ENDPOINT,headers={'Authorization':'secret-not-to-expose'})
            resp = httpx.Response(status,request=req,headers={'Retry-After':'120'})
            exc = httpx.HTTPStatusError('private path/token',request=req,response=resp)
            result = m.connection_error(ExceptionGroup('transport',[exc]))
            self.assertEqual(result['error']['code'],code)
            self.assertEqual(result['error']['http_status'],status)
            self.assertEqual(result['error']['retry_after_seconds'],120)
            self.assertNotIn('secret-not-to-expose',str(result))
            self.assertNotIn('private path/token',str(result))

    async def test_timeout_and_cancellation_are_not_retried(self):
        async def delayed(*args):
            await asyncio.sleep(1)
        with patch.object(m,'TIMEOUT_SECONDS',0.01),patch.object(m,'exchange',side_effect=delayed) as exchange:
            self.assertEqual((await m.call_biorxiv_tool('get_categories',{}))['error']['code'],'TIMEOUT')
            self.assertEqual(exchange.call_count,1)
        with patch.object(m,'exchange',side_effect=asyncio.CancelledError):
            with self.assertRaises(asyncio.CancelledError):
                await m.call_biorxiv_tool('get_categories',{})

    async def test_changed_remote_interface_blocks_execution(self):
        @asynccontextmanager
        async def transport(*args,**kwargs):
            yield (None,None,None)
        class Session:
            def __init__(self,*args,**kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self,*args): pass
            async def initialize(self): return SimpleNamespace(serverInfo=SimpleNamespace(version='test'))
            async def list_tools(self,**kwargs): return SimpleNamespace(tools=tools,nextCursor=None)
            call_tool = AsyncMock()
        for variant,code in (('missing','TOOL_UNAVAILABLE'),('unsafe','REMOTE_SAFETY_CHANGED'),('schema','REMOTE_SCHEMA_CHANGED')):
            tools = [] if variant=='missing' else [SimpleNamespace(name='get_categories',annotations=SimpleNamespace(readOnlyHint=variant!='unsafe',destructiveHint=False),inputSchema={'type':'object','required':['new_required']})]
            with patch.object(m,'streamablehttp_client',transport),patch.object(m,'ClientSession',Session):
                result = await m.exchange('get_categories',{})
            self.assertEqual(result['error']['code'],code)
            Session.call_tool.assert_not_awaited()

    async def test_stream_yields_one_actual_result(self):
        with patch.object(m,'call_biorxiv_tool',new_callable=AsyncMock,return_value={'ok':True,'data':{'synthetic':True}}) as call:
            items = [value async for value in m.CategoriesTool().stream({})]
            self.assertEqual(items,[{'ok':True,'data':{'synthetic':True}}])
            call.assert_awaited_once_with('get_categories',{})

if __name__ == '__main__':
    unittest.main(verbosity=2)
