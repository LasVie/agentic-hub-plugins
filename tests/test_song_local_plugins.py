"""Meaningful account-free runtime regressions; no network/model/service accounts."""
import base64, contextlib, hashlib, importlib.util, io, json, math, os, struct, sys, tempfile, unittest, wave
from pathlib import Path
R=Path(__file__).resolve().parents[1]

@contextlib.contextmanager
def immutable_payload_import():
    # Imports must not add __pycache__ to the source used by the package contract.
    previous=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True
        yield
    finally:
        sys.dont_write_bytecode=previous

def package(slug):
    name='song_'+slug.replace('-','_');path=Path(os.environ.get('SONG_PAYLOAD_ROOT',R/'plugins'))
    root=path/slug/slug if not os.environ.get('SONG_PAYLOAD_ROOT') else path/slug
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,root/'__init__.py',submodule_search_locations=[str(root)])
        with immutable_payload_import():
            loaded=importlib.util.module_from_spec(spec);sys.modules[name]=loaded;spec.loader.exec_module(loaded)
    return name,root

def module(slug,suffix):
    with immutable_payload_import():
        name,_=package(slug);return __import__(name+'.'+suffix,fromlist=['*'])

class VaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.b=module('dsh-vault','runtime.bridge')
        self.q={'directory':str(self.root/'vault'),'master_password':'Synthetic-test-only-password'}
        self.assertTrue(self.call('init')['ok'])
    def tearDown(self):self.tmp.cleanup()
    def call(self,a,**kw):return self.b.run_node(dict(self.q,action=a,**kw))
    def put(self):return self.call('put',id='demo',credential={'label':'虚构测试','username':'nobody@example.invalid','secret':'NEVER-REAL-SECRET','totp_secret':'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'})
    def test_encrypted_crud_and_mask(self):
        self.assertTrue(self.put()['ok']);raw=(self.root/'vault/vault.json').read_text()
        self.assertNotIn('NEVER-REAL-SECRET',raw);self.assertNotIn('虚构测试',raw)
        got=self.call('get',id='demo');self.assertEqual(got['entry']['secret'],'********')
        self.assertEqual(len(self.call('list',query='虚构')['entries']),1)
        self.assertEqual(self.call('list',query='absent')['entries'],[])
        self.assertFalse(self.call('remove',id='demo')['ok']);self.assertTrue(self.call('remove',id='demo',confirm=True)['ok']);self.assertFalse(self.call('get',id='demo')['ok'])
    def test_wrong_password_and_tamper_leave_data_unchanged(self):
        self.put();path=self.root/'vault/vault.json';original=path.read_bytes()
        self.assertFalse(self.call('list',master_password='Incorrect-test-password')['ok']);self.assertEqual(path.read_bytes(),original)
        obj=json.loads(original);c=obj['encrypted']['dataHex'];obj['encrypted']['dataHex']=('0' if c[0]!='0' else '1')+c[1:];path.write_text(json.dumps(obj));changed=path.read_bytes()
        self.assertFalse(self.call('list')['ok']);self.assertEqual(path.read_bytes(),changed)
    def test_overwrite_requires_explicit_flag_and_fresh_nonce(self):
        self.put();path=self.root/'vault/vault.json';before=json.loads(path.read_text())
        self.assertFalse(self.put()['ok']);self.assertTrue(self.call('put',id='demo',overwrite=True,credential={'label':'更新','secret':'Synthetic-updated'})['ok'])
        after=json.loads(path.read_text());self.assertNotEqual(before['encrypted']['ivHex'],after['encrypted']['ivHex']);self.assertEqual(self.call('get',id='demo')['entry']['label'],'更新')
    def test_rfc_known_totp_vector(self):
        self.put();self.assertEqual(self.call('totp',id='demo',now_ms=59000)['code'],'287082')
    def test_reinit_rejected_and_file_permissions(self):
        path=self.root/'vault/vault.json';original=path.read_bytes();self.assertFalse(self.call('init')['ok']);self.assertEqual(original,path.read_bytes())
        if os.name!='nt':self.assertEqual(path.stat().st_mode&0o777,0o600)
    def test_resource_parameters_rejected(self):
        path=self.root/'vault/vault.json';obj=json.loads(path.read_text());obj['kdf']['n']=2**30;path.write_text(json.dumps(obj));self.assertFalse(self.call('list')['ok'])

class PianoTests(unittest.TestCase):
    def setUp(self):self.b=module('dsh-pianist','runtime.bridge')
    def score(self,**kw):return self.b.run_node(dict(title='中文旋律',bpm=120,notes=[{'midi':69,'start_beat':0,'beats':1,'velocity':.7}],**kw))
    def test_audio_has_expected_format_duration_and_nonzero_signal(self):
        out=self.score();self.assertTrue(out['ok'],out)
        with wave.open(io.BytesIO(base64.b64decode(out['wav_base64']))) as f:
            self.assertEqual((f.getnchannels(),f.getsampwidth(),f.getframerate()),(1,2,22050));samples=struct.unpack('<'+'h'*f.getnframes(),f.readframes(f.getnframes()))
            self.assertAlmostEqual(len(samples)/22050,.85,places=3)
        self.assertGreater(max(map(abs,samples)),1000)
        # A4 synthesized fundamental: use autocorrelation near 440 Hz, not file existence.
        x=samples[3000:7000];best=max(range(45,56),key=lambda lag:sum(x[i]*x[i+lag] for i in range(len(x)-lag)))
        self.assertLess(abs(22050/best-440),15)
    def test_transposition_changes_score_and_timeline(self):
        out=self.score(transpose=3);self.assertTrue(out['ok'],out);self.assertEqual(out['score']['tracks'][0]['voices'][0]['events'][0]['midi'],72)
        self.assertEqual([e['midi'] for e in out['timeline'] if e['type']=='noteOn'],[72])
    def test_invalid_midi_duration_and_transpose_rejected(self):
        for notes in [[{'midi':109,'start_beat':0,'beats':1}],[{'midi':60,'start_beat':0,'beats':0}],[{'midi':60,'start_beat':95,'beats':16}]]:
            out=self.b.run_node({'bpm':30,'notes':notes});self.assertFalse(out['ok']);self.assertRegex(out['message'],'[\u4e00-\u9fff]')
        self.assertFalse(self.b.run_node({'notes':[{'midi':108,'start_beat':0,'beats':1}],'transpose':1})['ok'])
    def test_polyphony_and_stable_output(self):
        q={'title':'和弦','bpm':120,'notes':[{'midi':m,'start_beat':0,'beats':1} for m in [60,64,67]]}
        one=self.b.run_node(q);two=self.b.run_node(q);self.assertTrue(one['ok'],one);self.assertEqual(one['wav_base64'],two['wav_base64']);self.assertEqual(one['note_count'],3)

class LifeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.m=module('dsh-simulated-life','runtime.life');self.b=module('dsh-simulated-life','runtime.bridge')
    def tearDown(self):self.tmp.cleanup()
    def test_window_session_dedup_reaction_and_original_fields(self):
        self.m.seed_demo(self.root);one=self.m.context(self.root,'a');self.assertTrue(one['ok'],one);self.assertEqual(one['event_count'],2);self.assertTrue(one['should_inject']);self.assertNotIn('已过期的早餐',one['context'])
        two=self.m.context(self.root,'a');self.assertFalse(two['should_inject']);self.assertEqual(two['notice'],'');self.assertIn('图书馆',two['context'])
        self.assertTrue(self.m.context(self.root,'b')['should_inject'])
        f=next((self.root/'.life').glob('*/events.json'));before=json.loads(f.read_text())
        result=self.m.react(self.root,{'event_id':'demo-library','feeling':'好奇','thought':'观察星空','action_text':'预约观星'});self.assertTrue(result['ok'])
        after=json.loads(f.read_text());self.assertEqual(before['events'][1:],after['events'][1:]);self.assertEqual({k:v for k,v in before['events'][0].items() if k!='react'},{k:v for k,v in after['events'][0].items() if k!='react'})
        three=self.m.context(self.root,'a');self.assertEqual(three['updated_count'],1);self.assertIn('好奇',three['notice'])
        self.assertTrue(self.m.context(self.root,'a',True)['should_inject'])
    def test_missing_corrupt_files_and_invalid_reaction(self):
        self.assertEqual(self.m.context(self.root,'a')['event_count'],0)
        path=self.root/'.life/261022';path.mkdir(parents=True);(path/'events.json').write_text('{broken')
        self.assertEqual(self.m.context(self.root,'a')['event_count'],0)
        with self.assertRaises(self.b.PluginError):self.m.react(self.root,{'event_id':'none'})
    def test_exact_time_window_and_future_skew(self):
        now=1700000000000;from datetime import datetime,timezone
        events=[]
        for i,delta in enumerate([-86400001,-86400000,300000,300001]):events.append({'id':str(i),'title':'边界','time':datetime.fromtimestamp((now+delta)/1000,timezone.utc).isoformat(),'description':'虚构'})
        path=self.root/'.life/231114';path.mkdir(parents=True);(path/'events.json').write_text(json.dumps({'events':events}))
        out=self.m.context(self.root,'a',now_ms=now);self.assertTrue(out['ok'],out);self.assertEqual([x['id'] for x in out['events']],['1','2'])
    @unittest.skipIf(os.name=='nt','POSIX symlink fixture')
    def test_symbolic_links_are_rejected(self):
        external=self.root/'external';external.mkdir();(self.root/'.life').symlink_to(external,target_is_directory=True)
        self.assertFalse(self.m.context(self.root,'a')['ok'])
        with self.assertRaises(self.b.PluginError):self.b.safe_path(self.root,'../escape')
    def test_demo_never_overwrites_existing_file(self):
        self.m.seed_demo(self.root);f=next((self.root/'.life').glob('*/events.json'));original=f.read_bytes()
        with self.assertRaises(self.b.PluginError):self.m.seed_demo(self.root)
        self.assertEqual(original,f.read_bytes())
if __name__=='__main__':unittest.main()
