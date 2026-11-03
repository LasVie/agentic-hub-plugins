"""Real-engine functional tests for five independent development workbenches."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import sys
sys.dont_write_bytecode=True
from urllib.request import Request, ProxyHandler, build_opener
from urllib.error import HTTPError

REPO=Path(__file__).resolve().parents[1]
DEFS=json.loads((REPO/'tools/dev_five_config.json').read_text())

def node_available():
    import subprocess
    for p in [os.environ.get('JIUWEN_NODE_BINARY'),shutil.which('node'),'/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node']:
        try:
            if p and int(subprocess.check_output([p,'--version'],text=True).strip().lstrip('v').split('.')[0])>=22:return True
        except (OSError,ValueError,subprocess.SubprocessError):pass
    return False

@unittest.skipUnless(node_available(),'Real-engine suite requires Node.js22+')
class DevelopmentWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (REPO/'.research').mkdir(exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(prefix='dev-workbenches-',dir=REPO/'.research')
        cls.work=Path(cls.temp.name).resolve();cls.launchers={};cls.urls={}
        for d in DEFS:
            slug=d['slug'];p=Path(os.environ.get('DEV_WORKBENCH_PAYLOAD_ROOT',str(REPO/'plugins')))/slug/slug/'runtime/launcher.py'
            spec=importlib.util.spec_from_file_location('verify_'+slug.replace('-','_'),p)
            mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);cls.launchers[slug]=mod
            result=mod.run({'workspace':str(cls.work),'action':'start','confirmed':True})
            if not result.get('ok'):raise RuntimeError(slug+': '+str(result))
            cls.urls[slug]=result['url']
    @classmethod
    def tearDownClass(cls):
        for mod in cls.launchers.values():mod.run({'workspace':str(cls.work),'action':'stop','confirmed':True})
        cls.temp.cleanup()
    def op(self,slug,op,**args):
        return self.launchers[slug].run({'workspace':str(self.work),'action':'operate','confirmed':True,'params':{'op':op,**args}})
    def good(self,result):
        self.assertTrue(result.get('ok'),str(result)[:2000]);return result
    def test_01_lifecycle_and_confirmation(self):
        for slug,mod in self.launchers.items():
            with self.subTest(slug=slug):
                self.assertTrue(mod.run({'workspace':str(self.work),'action':'status'})['running'])
                self.assertFalse(mod.run({'workspace':str(self.work),'action':'stop'})['ok'])
                self.assertTrue(mod.run({'workspace':str(self.work),'action':'start','confirmed':True})['reused'])
    def test_02_mock_actual_http_scenarios(self):
        s='api-mock-lab';self.good(self.op(s,'demo'))
        for scenario,status in [('normal',200),('slow',200),('error',503)]:
            self.good(self.op(s,'start',scenario=scenario));r=self.good(self.op(s,'probe',method='GET',path='/api/products'))
            self.assertEqual(r['status'],status)
            if scenario=='slow':self.assertGreaterEqual(r['elapsedMs'],300)
            if status==200:self.assertEqual(json.loads(r['body'])['items'][0]['name'],'机械键盘')
        self.good(self.op(s,'stop'));self.assertFalse(self.op(s,'probe',path='/api/products')['ok'])
    def test_03_openapi_is_real_and_external_refs_rejected(self):
        s='api-mock-lab';schema={'openapi':'3.0.0','info':{'title':'测试接口','version':'1.0.0'},'paths':{'/hello':{'get':{'responses':{'200':{'description':'ok','content':{'application/json':{'example':{'message':'你好'}}}}}}}}}
        self.good(self.op(s,'import-openapi',source=json.dumps(schema)))
        self.good(self.op(s,'start',scenario='normal'));r=self.good(self.op(s,'probe',path='/hello'));self.assertEqual(json.loads(r['body'])['message'],'你好');self.good(self.op(s,'stop'))
        schema['paths']['/hello']['get']['responses']['200']={'$ref':'https://example.invalid/private'}
        self.assertFalse(self.op(s,'import-openapi',source=json.dumps(schema))['ok'])
    def test_04_mock_invalid_definition_preserves_saved_project(self):
        self.good(self.op('api-mock-lab','demo'));before=(self.work/'.api-mock-lab/mock.json').read_bytes()
        self.assertFalse(self.op('api-mock-lab','save',spec={'routes':[]})['ok'])
        self.assertEqual(before,(self.work/'.api-mock-lab/mock.json').read_bytes())
    def test_05_page_project_is_persistent_and_exportable(self):
        project={'pages':[{'id':'home','component':{'type':'wrapper','components':[{'tagName':'h1','content':'中文标题'}]}}]}
        r=self.good(self.op('visual-web-studio','save',project=project,html='<h1>中文标题</h1>',css='h1{color:green}'))
        self.assertEqual(r['summary']['pages'],1)
        self.assertEqual(self.good(self.op('visual-web-studio','load'))['project'],project)
        self.assertIn('中文标题',(self.work/'.visual-web-studio/website.html').read_text())
        self.assertFalse(self.op('visual-web-studio','save',project={},html='',css='')['ok'])
    def test_06_postgres_real_jsonb_write_and_restart(self):
        s='postgres-local-lab';self.good(self.op(s,'sample',project='alpha'))
        r=self.good(self.op(s,'query',project='alpha',sql="SELECT name,metadata->>'stock' AS stock FROM demo_products WHERE id=1"))
        self.assertEqual(r['result']['rows'][0],{'name':'机械键盘','stock':'12'})
        self.good(self.op(s,'query',project='alpha',sql="INSERT INTO demo_products VALUES(99,'持久化测试',1,'{}')"))
        mod=self.launchers[s];self.good(mod.run({'workspace':str(self.work),'action':'stop','confirmed':True}));self.good(mod.run({'workspace':str(self.work),'action':'start','confirmed':True}))
        r=self.good(self.op(s,'query',project='alpha',sql='SELECT name FROM demo_products WHERE id=99'));self.assertEqual(r['result']['rows'][0]['name'],'持久化测试')
    def test_07_postgres_isolation_error_and_export(self):
        s='postgres-local-lab';self.good(self.op(s,'sample',project='separate'))
        r=self.good(self.op(s,'query',project='separate',sql='SELECT count(*)::int AS n FROM demo_products'));self.assertEqual(r['result']['rows'][0]['n'],3)
        self.assertFalse(self.op(s,'query',project='separate',sql='SELECT broken syntax')['ok'])
        self.good(self.op(s,'query',project='separate',sql='SELECT 42 AS answer'))
        r=self.good(self.op(s,'export',project='separate'));self.assertTrue((self.work/'.postgres-local-lab'/r['result']['filename']).is_file())
    def test_08_actual_rollup_statistics_and_comparison(self):
        s='bundle-insight';a=self.good(self.op(s,'build-demo',name='small',large=False));b=self.good(self.op(s,'build-demo',name='large',large=True))
        self.assertGreater(b['summary']['renderedLength'],a['summary']['renderedLength'])
        self.assertGreater(a['summary']['modules'],0)
        r=self.good(self.op(s,'compare',before='small',after='large'));self.assertTrue(any(x['delta']>0 for x in r['changes']))
        self.assertIn('实际构建',(self.work/'.bundle-insight/report-small.html').read_text())
    def test_09_bundle_invalid_input_does_not_create_snapshot(self):
        self.assertFalse(self.op('bundle-insight','import',name='invalid',data={'estimated':999})['ok'])
        self.assertFalse((self.work/'.bundle-insight/snapshot-invalid.json').exists())
        self.assertFalse(self.op('bundle-insight','build-demo',name='../unsafe',large=False)['ok'])
    def test_10_gltf_real_optimization_and_persistence(self):
        s='web3d-asset-lab';r=self.good(self.op(s,'demo'));self.assertEqual(r['before']['nodes'],16)
        r=self.good(self.op(s,'optimize'));self.assertLess(r['after']['bytes'],r['before']['bytes']);self.assertEqual(r['after']['nodes'],16)
        self.assertEqual(r['after']['animations'],r['before']['animations'])
        r2=self.good(self.op(s,'load'));self.assertEqual(r2['after'],r['after'])
        before=(self.work/'.web3d-asset-lab/original.glb').read_bytes();self.assertFalse(self.op(s,'import',data='bm90IGEgZ2xi')['ok']);self.assertEqual(before,(self.work/'.web3d-asset-lab/original.glb').read_bytes())
    def test_11_cross_origin_and_health_ownership(self):
        opener=build_opener(ProxyHandler({}))
        for slug,mod in self.launchers.items():
            status=mod.run({'workspace':str(self.work),'action':'status'});url=status['url']
            with self.subTest(slug=slug):
                with self.assertRaises(HTTPError) as err:opener.open(Request(url+'/api/operate',data=b'{"op":"demo"}',headers={'Content-Type':'application/json','Origin':'https://example.invalid'}))
                self.assertEqual(err.exception.code,403)
                with self.assertRaises(HTTPError) as err:opener.open(url+'/health')
                self.assertEqual(err.exception.code,403)
    def test_12_foreign_record_and_symlink_refused(self):
        other=self.work/'other';other.mkdir();state=other/'.api-mock-lab';state.mkdir();(state/'service.json').write_text(json.dumps({'slug':'api-mock-lab','payload':'/foreign/installation','url':'http://127.0.0.1:1','nonce':'x'}))
        self.assertFalse(self.launchers['api-mock-lab'].run({'workspace':str(other),'action':'start','confirmed':True})['ok'])
        linked=self.work/'linked';linked.symlink_to(other,target_is_directory=True)
        self.assertFalse(self.launchers['api-mock-lab'].run({'workspace':str(linked),'action':'start','confirmed':True})['ok'])
    def test_13_binary_and_large_result_never_enter_host_messages(self):
        import base64
        raw=b'local-model-bytes'*100000
        result=self.launchers['web3d-asset-lab'].compact_result({'ok':True,'version':'1.0.2','original':base64.b64encode(raw).decode(),'before':{'bytes':len(raw),'nodes':16},'rows':list(range(100))})
        self.assertLess(len(json.dumps(result).encode()),16000)
        self.assertTrue(result['original']['binary_omitted'])
        self.assertEqual(result['original']['bytes'],len(raw))
        self.assertEqual(result['before']['nodes'],16)
        self.assertEqual(len(result['rows']),30)
    def test_14_duplicate_module_parts_compare_symmetrically(self):
        s='bundle-insight';self.good(self.op(s,'build-demo',name='duplicate_seed',large=False))
        data=json.loads((self.work/'.bundle-insight/snapshot-duplicate_seed.json').read_text())
        part=dict(next(iter(data['nodeParts'].values())))
        data['nodeParts']['second_chunk_part']={**part,'renderedLength':11,'gzipLength':4,'brotliLength':3}
        self.good(self.op(s,'import',name='duplicate_before',data=data))
        self.good(self.op(s,'import',name='duplicate_after',data=data))
        r=self.good(self.op(s,'compare',before='duplicate_before',after='duplicate_after'))
        self.assertEqual(r['before'],r['after'])
        self.assertTrue(all(row['delta']==0 for row in r['changes']))

if __name__=='__main__':unittest.main(verbosity=2)
