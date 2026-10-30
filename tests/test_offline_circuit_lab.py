"""Real loopback-server tests for the plugin-owned runtime, no model calls."""
import importlib.util
import http.client
import json
from pathlib import Path
import tempfile
import time
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / 'plugins/offline-circuit-lab/offline-circuit-lab/runtime/lab.py'
spec = importlib.util.spec_from_file_location('test_circuit_lab_runtime', FILE)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

DIVIDER = {'components': [
    {'id':'V1','type':'V','a':'1','b':'0','value':5},
    {'id':'R1','type':'R','a':'1','b':'2','value':1000},
    {'id':'R2','type':'R','a':'2','b':'0','value':1000}],
    'duration_ms':1,'step_us':10,'probe':'2'}


class LabIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = str(Path(self.temp.name).resolve())
        self.start = lab.local_lab({'workspace':self.workspace,'action':'start','confirmed':True})
        self.assertTrue(self.start['ok'], self.start)
        self.url = urlsplit(self.start['url'])

    def tearDown(self):
        lab.local_lab({'workspace':self.workspace,'action':'stop','confirmed':True})
        self.temp.cleanup()

    def request(self, path, value=None, headers=None, method=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.url.port, timeout=4)
        h = {'Content-Type':'application/json'} if value is not None else {}
        h.update(headers or {})
        conn.request(method or ('POST' if value is not None else 'GET'), path,
                     json.dumps(value).encode() if value is not None else None, h)
        response = conn.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        conn.close()
        return result

    def test_serves_actual_chinese_ui_and_numerical_measurement(self):
        code, headers, data = self.request(self.url.path)
        self.assertEqual(code,200)
        self.assertIn('离线电路实验室',data.decode())
        self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
        code, _, license_body = self.request(self.url.path+'license.txt')
        self.assertEqual(code,200)
        self.assertEqual(license_body,(FILE.parents[1]/'licenses/circuitjs/LICENSE').read_bytes())
        code, _, body = self.request(self.url.path+'api/simulate',{'circuit':DIVIDER})
        result = json.loads(body)
        self.assertTrue(result['ok'],result)
        self.assertAlmostEqual(result['samples'][-1]['voltages']['2'],2.5,places=6)
        self.assertAlmostEqual(result['samples'][-1]['currents']['R1'],.0025,places=8)

    def test_save_reopen_and_failed_save_preserves_graph(self):
        _,_,body=self.request(self.url.path+'api/load')
        self.assertIsNone(json.loads(body)['circuit'])
        _,_,body=self.request(self.url.path+'api/save',{'circuit':DIVIDER})
        self.assertTrue(json.loads(body)['ok'])
        saved=Path(self.workspace)/'.offline-circuit-lab/circuit.json'
        original=saved.read_bytes()
        _,_,body=self.request(self.url.path+'api/save',{'circuit':{'components':[]}})
        self.assertFalse(json.loads(body)['ok'])
        self.assertEqual(saved.read_bytes(),original)
        _,_,body=self.request(self.url.path+'api/load')
        self.assertEqual(json.loads(body)['circuit'],DIVIDER)
        self.assertEqual(saved.stat().st_mode & 0o777,0o600)

    def test_private_session_same_start_and_rejects_cross_origin(self):
        again=lab.local_lab({'workspace':self.workspace,'action':'start','confirmed':True})
        self.assertEqual(again['session_id'],self.start['session_id'])
        self.assertTrue(again['reused'])
        for path in ['/','/wrong/api/health',self.url.path+'../runtime/lab.py']:
            self.assertEqual(self.request(path)[0],404)
        self.assertEqual(self.request(self.url.path+'api/load',headers={'Host':'attacker.example'})[0],403)
        self.assertEqual(self.request(self.url.path+'api/save',{'circuit':DIVIDER},headers={'Origin':'https://attacker.example'})[0],403)
        self.assertFalse((Path(self.workspace)/'.offline-circuit-lab/circuit.json').exists())

    def test_no_overwrite_of_symlinked_state(self):
        outside=Path(self.workspace)/'keep.json'
        outside.write_text('{"keep":true}')
        (Path(self.workspace)/'.offline-circuit-lab/circuit.json').symlink_to(outside)
        code,_,body=self.request(self.url.path+'api/save',{'circuit':DIVIDER})
        self.assertEqual(code,400)
        self.assertFalse(json.loads(body)['ok'])
        self.assertEqual(outside.read_text(),'{"keep":true}')

    def test_request_limits_and_real_stop(self):
        code,_,body=self.request(self.url.path+'api/simulate',{'circuit':DIVIDER,'extra':'x'*140000})
        self.assertEqual(code,400)
        self.assertFalse(json.loads(body)['ok'])
        reply=lab.local_lab({'workspace':self.workspace,'action':'stop','confirmed':True})
        self.assertTrue(reply['ok'])
        for _ in range(25):
            if not lab.local_lab({'workspace':self.workspace,'action':'status'})['running']:
                break
            time.sleep(.05)
        self.assertFalse(lab.local_lab({'workspace':self.workspace,'action':'status'})['running'])

    def test_immediate_restart_uses_new_live_session(self):
        stopped=lab.local_lab({'workspace':self.workspace,'action':'stop','confirmed':True})
        self.assertTrue(stopped['ok'],stopped)
        restarted=lab.local_lab({'workspace':self.workspace,'action':'start','confirmed':True})
        self.assertTrue(restarted['ok'],restarted)
        self.assertFalse(restarted['reused'])
        self.assertNotEqual(restarted['session_id'],self.start['session_id'])
        time.sleep(.3)
        self.assertEqual(lab.local_lab({'workspace':self.workspace,'action':'status'})['session_id'],restarted['session_id'])


class LabInput(unittest.TestCase):
    def test_confirmation_and_path_boundaries(self):
        with tempfile.TemporaryDirectory() as t:
            work=str(Path(t).resolve())
            self.assertFalse(lab.local_lab({'workspace':work,'action':'start'})['ok'])
            self.assertFalse((Path(work)/'.offline-circuit-lab').exists())
            alias=Path(work)/'alias'; alias.symlink_to(work,target_is_directory=True)
            self.assertFalse(lab.local_lab({'workspace':str(alias),'action':'start','confirmed':True})['ok'])
            self.assertFalse(lab.local_lab({'workspace':'relative','action':'status'})['ok'])
            self.assertEqual(lab.local_lab({'workspace':work,'action':'status'})['running'],False)

if __name__ == '__main__':
    unittest.main()
