"""Behavioral tests for the finite queue and public local transport."""
import copy
import hashlib
import heapq
import http.client
import importlib.util
import json
import os
from pathlib import Path
import random
import stat
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT = Path(os.environ.get('QUEUE_PAYLOAD', Path(__file__).resolve().parents[1] / 'queue-capacity-workbench')).resolve()
sys.dont_write_bytecode = True


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'runtime' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load('queue_test_runtime', 'runtime.py')
worker = load('queue_test_worker', 'worker.py')


def fixture(capacities=None):
    return {'schema': 'queue-capacity-workbench/v1', 'name': '中文验收场景', 'units': 'minutes',
            'capacities': capacities or [1, 2],
            'jobs': [{'id': f'作业{i+1}', 'arrival': i, 'service': 4} for i in range(4)]}


class QueueModel(unittest.TestCase):
    def test_exact_fixture_and_boundary_finish(self):
        data = worker.calculate(fixture())
        for run, starts, completion, mean, peak in zip(data['runs'], [[0,4,8,12],[0,1,4,5]], [16,9], [4.5,1], [3,2]):
            self.assertEqual([j['start'] for j in run['jobs']], starts)
            self.assertEqual(run['metrics']['completion_time'], completion)
            self.assertEqual(run['metrics']['mean_wait'], mean)
            self.assertEqual(run['metrics']['max_queue'], peak)
            self.assertEqual(run['events'][-1]['completed'], 4)
            self.assertEqual(run['events'][-1]['time'], completion)
        self.assertEqual(data['engine'], 'SimPy 4.1.2')

    def test_fifo_ties_zero_wait_and_integer_ticks(self):
        p = fixture([1]); p['jobs'] = [{'id': str(i), 'arrival': 0, 'service': .001} for i in range(10)]
        run = worker.calculate(p)['runs'][0]
        self.assertEqual([j['start'] for j in run['jobs']], [i/1000 for i in range(10)])
        self.assertEqual(run['events'][-1]['time'], .01)
        p['capacities'] = [32]
        self.assertEqual(worker.calculate(p)['runs'][0]['metrics']['max_queue'], 0)

    def test_seeded_independent_oracle_and_conservation(self):
        rng = random.Random(5137)
        for _ in range(70):
            p = fixture([rng.randint(1, 8)])
            p['jobs'] = [{'id': f'工单{i}', 'arrival': rng.randint(0, 25)/10, 'service': rng.randint(1, 40)/10} for i in range(rng.randint(1, 35))]
            data = worker.calculate(p); self.assertEqual(data, worker.calculate(p))
            run = data['runs'][0]; count = p['capacities'][0]
            free = [0] * count; heapq.heapify(free); expected = {}
            for _, j in sorted(enumerate(p['jobs']), key=lambda x: (x[1]['arrival'], x[0])):
                begin = max(round(j['arrival']*1000), heapq.heappop(free)); end = begin + round(j['service']*1000)
                heapq.heappush(free, end); expected[j['id']] = (begin/1000, end/1000)
            for j in run['jobs']:
                self.assertEqual((j['start'], j['finish']), expected[j['id']])
            live, waiting, done = set(), set(), set()
            for seq, event in enumerate(run['events'], 1):
                identifier = event['job_id']; kind = event['kind']
                if kind == 'arrival': waiting.add(identifier)
                elif kind == 'start': waiting.remove(identifier); live.add(identifier)
                else: live.remove(identifier); done.add(identifier)
                self.assertEqual(event['seq'], seq)
                self.assertEqual((event['waiting'], event['active'], event['completed']), (len(waiting), len(live), len(done)))
                self.assertLessEqual(len(live), count)
            self.assertEqual(len(done), len(p['jobs']))
            self.assertFalse(live | waiting)

    def test_bounds_and_unsafe_fields(self):
        bad = []
        for capacities in [[], [0], [33], [True], [1,1], list(range(1,10))]:
            p=fixture(); p['capacities']=capacities; bad.append(p)
        for field, value in [('arrival',-1),('service',0),('service',True),('service',float('nan')),('arrival',float('inf')),('service',.0001),('service','4'),('id','\nfoo')]:
            p=fixture(); p['jobs'][0][field]=value;bad.append(p)
        for extra in ['script','html','python','resource_url']:
            p=fixture();p[extra]='__import__("os").system("anything")';bad.append(p)
        for jobs in [[], fixture()['jobs']*126, [fixture()['jobs'][0]]*2]:
            p=fixture();p['jobs']=jobs;bad.append(p)
        for p in bad:
            with self.subTest(p=p), self.assertRaises(ValueError): worker.calculate(p)
        p=fixture([32]);p['jobs']=[{'id':str(i),'arrival':0,'service':1000} for i in range(500)]
        self.assertEqual(worker.calculate(p)['runs'][0]['events'][-1]['completed'],500)

    def test_csv_formula_and_literal_html_text(self):
        p=fixture();p['jobs'][0]['id']=' =HYPERLINK("x")';p['name']='<script>只是文本</script>'
        r=worker.calculate(p)
        self.assertIn("' =HYPERLINK",r['csv']);self.assertEqual(r['project']['name'],p['name'])

    def test_worker_real_child_and_malformed_json(self):
        good=runtime.engine_call({'project':fixture()});self.assertTrue(good['ok']);self.assertEqual(good['runs'][1]['metrics']['mean_wait'],1)
        self.assertFalse(runtime.engine_call({'project':fixture(),'extra':True})['ok'])
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'[]',b'\xff',b'{'*5000,b' '* (256*1024+1)]:
            r=subprocess.run([sys.executable,'-I','-B',str(ROOT/'runtime/worker.py')],input=raw,capture_output=True,timeout=15)
            result=json.loads(r.stdout);self.assertFalse(result['ok']);self.assertRegex(result['error'],r'[\u4e00-\u9fff]')


class LocalTransport(unittest.TestCase):
    def setUp(self):
        self.scratch=tempfile.TemporaryDirectory(prefix='queue-test-',dir='/private/tmp');self.workspace=Path(self.scratch.name)
        self.args={'workspace':str(self.workspace)}
    def tearDown(self):
        runtime.lifecycle({**self.args,'action':'stop','confirmed':True});self.scratch.cleanup()
    def call(self, route, body=None, headers=None, method=None):
        parsed=urlsplit(self.opened['url']); connection=http.client.HTTPConnection(parsed.hostname,parsed.port,timeout=20)
        path=parsed.path.rsplit('/',1)[0]+'/'+route
        defaults={'Content-Type':'application/json'} if body is not None else {}
        defaults.update(headers or {})
        connection.request(method or ('POST' if body is not None else 'GET'),path,body=body,headers=defaults)
        r=connection.getresponse();content=r.read();status=r.status; h=dict(r.getheaders());connection.close();return status,content,h
    def start(self):
        self.opened=runtime.lifecycle({**self.args,'action':'start','confirmed':True});self.assertTrue(self.opened['ok'],self.opened)
    def test_ownership_start_restart_stop(self):
        self.assertFalse(runtime.lifecycle({**self.args,'action':'start'})['ok'])
        self.start();self.assertTrue(self.opened['running'])
        second=runtime.lifecycle({**self.args,'action':'start','confirmed':True});self.assertEqual(second['session_id'],self.opened['session_id'])
        self.assertTrue(runtime.lifecycle({**self.args,'action':'status'})['running'])
        self.assertTrue(runtime.lifecycle({**self.args,'action':'stop','confirmed':True})['stopped'])
        old=self.opened['session_id'];self.start();self.assertNotEqual(old,self.opened['session_id'])
        state=self.workspace/runtime.STATE_DIR/'server.json';self.assertEqual(stat.S_IMODE(state.stat().st_mode),0o600)
    def test_http_calculation_security_and_cancel_fence(self):
        self.start();s,b,h=self.call('index.html');self.assertEqual(s,200);self.assertIn('离线排队容量实验台',b.decode());self.assertIn("default-src 'none'",h['Content-Security-Policy'])
        self.assertEqual(self.call('vendor/simpy/core.py')[0],404)
        self.assertEqual(self.call('api/health',headers={'Origin':'https://external.invalid'})[0],403)
        self.assertEqual(self.call('api/health',headers={'Host':'other.invalid'})[0],403)
        s,b,_=self.call('api/calculate',json.dumps({'request_id':'fixture','project':fixture()},ensure_ascii=False).encode());self.assertEqual(s,200);self.assertEqual(json.loads(b)['runs'][0]['metrics']['completion_time'],16)
        self.assertEqual(self.call('api/calculate',json.dumps({'request_id':'fixture','project':fixture()}).encode())[0],409)
        self.assertEqual(self.call('api/calculate',b'{"request_id":"x","request_id":"y","project":{}}')[0],400)
        self.assertEqual(self.call('api/calculate',b'{}',headers={'Content-Type':'text/plain'})[0],400)
        self.call('api/cancel',b'{"request_id":"late"}')
        self.assertEqual(self.call('api/calculate',json.dumps({'request_id':'late','project':fixture()}).encode())[0],409)
        # Bad input does not poison subsequent valid runs.
        self.assertFalse(json.loads(self.call('api/calculate',b'{"request_id":"bad","project":{}}')[1])['ok'])
        self.assertTrue(json.loads(self.call('api/calculate',json.dumps({'request_id':'next','project':fixture()}).encode())[1])['ok'])
    def test_invalid_owned_state_is_preserved(self):
        directory=self.workspace/runtime.STATE_DIR;directory.mkdir(mode=0o700);state=directory/'server.json';state.write_text('{bad');state.chmod(0o600)
        result=runtime.lifecycle({**self.args,'action':'start','confirmed':True});self.assertFalse(result['ok']);self.assertEqual(state.read_text(),'{bad')
    def test_symlink_workspace_rejected(self):
        link=self.workspace/'link';link.symlink_to(self.workspace,target_is_directory=True)
        self.assertFalse(runtime.lifecycle({'workspace':str(link),'action':'start','confirmed':True})['ok'])


if __name__=='__main__': unittest.main(verbosity=2)
