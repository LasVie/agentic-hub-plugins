"""Real CLI/oracle, parser-boundary and owned transport tests."""
import copy
import csv
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

ROOT = Path(os.environ.get("ALLOCATION_PAYLOAD", Path(__file__).resolve().parents[1] / "offline-allocation-workbench")).resolve()
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("allocation_test_runtime", ROOT / "runtime/runtime.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
engine, model = runtime.engine, runtime.model


def fixture():
    return model.examples()["资源选择"]


def oracle(project):
    # Enumerate independent subsets, without using the LP builder or CLI parser.
    best = None
    for mask in range(1 << len(project["jobs"])):
        chosen = [job for i, job in enumerate(project["jobs"]) if mask & (1 << i)]
        if len(chosen) < project["min_jobs"]:
            continue
        if any(sum(j["uses"][r["id"]] for j in chosen) > r["capacity"] for r in project["resources"]):
            continue
        value = sum(j["value"] for j in chosen)
        best = value if best is None else max(best, value)
    return best


class AllocationEngine(unittest.TestCase):
    def test_fixture_expansion_and_impossible(self):
        for name, value, selected in [("资源选择", 14, {"C", "D"}), ("设备扩容", 17, {"B", "C"})]:
            p = model.examples()[name]
            response = engine.calculate(p)
            self.assertTrue(response["ok"], response)
            r = response["result"]
            self.assertEqual(r["status"], "optimal")
            self.assertEqual(r["objective"], value)
            self.assertEqual(set(r["selected_ids"]), selected)
            self.assertEqual(oracle(p), value)
            self.assertTrue(r["constraints_verified"])
            self.assertTrue(r["optimality_proven"])
            self.assertEqual(r["mip_gap"], 0)
            self.assertEqual(r["dual_bound"], value)
            self.assertEqual(r["input_sha256"], model.project_hash(p))
        impossible = engine.calculate(model.examples()["不可行示例"])
        self.assertTrue(impossible["ok"], impossible)
        self.assertEqual(impossible["result"]["status"], "infeasible")
        self.assertIsNone(impossible["result"]["objective"])
        self.assertNotIn("csv", impossible)

    def test_seeded_independent_subsets(self):
        rng = random.Random(20261112)
        for case in range(60):
            resources = [{"id": f"r{k}", "name": f"资源{k}", "capacity": rng.randrange(0, 25)} for k in range(rng.randrange(1, 5))]
            jobs = [{"id": f"j{i}", "name": f"作业{i}", "value": rng.randrange(0, 25),
                     "uses": {r["id"]: rng.randrange(0, 15) for r in resources}} for i in range(rng.randrange(1, 10))]
            p = {"schema": model.SCHEMA, "name": "独立枚举", "resources": resources, "jobs": jobs,
                 "min_jobs": rng.randrange(0, len(jobs) + 1)}
            expected = oracle(p)
            actual = engine.calculate(p)
            self.assertTrue(actual["ok"], (case, actual))
            r = actual["result"]
            self.assertEqual(r["objective"], expected, (case, p, r))
            self.assertEqual(r["status"], "infeasible" if expected is None else "optimal")
            if expected is not None:
                picked = [j for j in jobs if j["id"] in r["selected_ids"]]
                self.assertGreaterEqual(len(picked), p["min_jobs"])
                self.assertEqual(sum(j["value"] for j in picked), expected)
                for resource in resources:
                    self.assertLessEqual(sum(j["uses"][resource["id"]] for j in picked), resource["capacity"])

    def test_boundaries_labels_and_csv_safety(self):
        p = fixture()
        p["name"] = '<script>只是项目名</script>'
        p["resources"][0]["name"] = '=资源'
        p["jobs"][0]["id"] = 'x0\"; system()'
        p["jobs"][0]["name"] = ' =HYPERLINK("x")'
        r = engine.calculate(p)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["result"]["objective"], 14)
        rows = list(csv.reader(io.StringIO(r["csv"])))
        self.assertEqual(rows[0][5], "'=资源")
        self.assertTrue(rows[1][1].startswith("' =HYPERLINK"))
        self.assertNotIn('system()', engine.lp_text(p))
        p = fixture()
        p["resources"] = [{"id": f"r{i}", "name": f"资源{i}", "capacity": 1000000} for i in range(8)]
        p["jobs"] = [{"id": f"j{i}", "name": f"作业{i}", "value": 1000000, "uses": {r["id"]: 1 for r in p["resources"]}} for i in range(100)]
        p["min_jobs"] = 100
        r = engine.calculate(p)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["result"]["objective"], 100000000)
        self.assertEqual(len(r["result"]["selected_ids"]), 100)

    def test_invalid_declarative_inputs(self):
        bad = []
        for field, value in [("value", True), ("value", -1), ("value", 1.5), ("value", "5"), ("name", "\n"), ("value", 1000001)]:
            p = fixture(); p["jobs"][0][field] = value; bad.append(p)
        for extra in ["script", "html", "solver_options", "path", "lp", "command"]:
            p = fixture(); p[extra] = "do not execute"; bad.append(p)
        for jobs in [[], fixture()["jobs"] * 26, [fixture()["jobs"][0]] * 2]:
            p = fixture(); p["jobs"] = jobs; bad.append(p)
        for resources in [[], fixture()["resources"] * 5]:
            p = fixture(); p["resources"] = resources; bad.append(p)
        p = fixture(); p["jobs"][0]["uses"]["outside"] = 1; bad.append(p)
        p = fixture(); p["jobs"][0]["uses"]["labour"] = float('nan'); bad.append(p)
        p = fixture(); p["min_jobs"] = 5; bad.append(p)
        for p in bad:
            with self.subTest(p=p), self.assertRaises(model.InputError):
                model.validate(p)
        for raw in [b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'['*5000, b' '*262145]:
            with self.assertRaises(model.InputError): model.strict_json(raw)

    def test_untrusted_solution_status_and_values(self):
        # Injected protocol responses exercise no solver and prove the guard
        # never promotes missing/fractional/over-budget solutions to optimal.
        p = fixture()
        template = "Model status\n{status}\n\n# Primal solution values\nFeasible\n\nObjective 14\n# Columns 4\nx0 0\nx1 0\nx2 1\nx3 1\nObjective_bound 14\nMIP_rel_gap 0\n"
        feasible = engine.parse_solution(template.format(status="Time limit reached"), p)
        self.assertEqual(feasible["status"], "feasible")
        self.assertFalse(feasible["optimality_proven"])
        self.assertIsNone(feasible["dual_bound"])
        self.assertIsNone(feasible["mip_gap"])
        for raw in [template.format(status="Optimal").replace('x2 1', 'x2 0.5'),
                    template.format(status="Optimal").replace('Objective 14', 'Objective 15'),
                    template.format(status="Optimal").replace('MIP_rel_gap 0', 'MIP_rel_gap 0.1'),
                    template.format(status="Optimal").replace('x0 0', 'x0 1'),
                    template.format(status="Infeasible"), 'Model status\nOptimal\n', '']:
            with self.assertRaises((model.InputError, ValueError)):
                engine.parse_solution(raw, p)
        cancelled = threading.Event(); cancelled.set()
        self.assertEqual(engine.calculate(p, cancelled)["error"]["code"], "cancelled")

    def test_real_owned_child_cancellation_and_wall_limit(self):
        real_popen = subprocess.Popen
        children = []
        event = threading.Event()
        def launched(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append((child, Path(kwargs['cwd'])))
            event.set()
            return child
        with patch.object(engine.subprocess, 'Popen', launched):
            result = engine.calculate(fixture(), event)
        self.assertEqual(result['error']['code'], 'cancelled')
        self.assertTrue(all(p.poll() is not None and not cwd.exists() for p, cwd in children))
        with patch.object(engine, 'WALL_SECONDS', 0):
            result = engine.calculate(fixture())
        self.assertEqual(result['error']['code'], 'resource_limit')
        self.assertTrue(result['timed_out'])

    def test_binary_hash_guard_and_os_network_denial(self):
        with patch.object(engine, 'BINARY_SHA256', '0' * 64), patch.object(engine.subprocess, 'Popen') as popen:
            self.assertFalse(engine.calculate(fixture())['ok'])
            popen.assert_not_called()
        listener = socket.socket(); listener.bind(('127.0.0.1', 0)); listener.listen(1)
        port = listener.getsockname()[1]
        try:
            script = f"import socket; socket.create_connection(('127.0.0.1',{port}),timeout=1)"
            checked = subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',
                                      sys.executable,'-I','-B','-c',script], capture_output=True, timeout=3)
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn(b'Operation not permitted', checked.stderr)
        finally:
            listener.close()


class AllocationTransport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="allocation-http-test-", dir="/private/tmp")
        self.workspace = Path(self.temp.name)
        self.args = {"workspace": str(self.workspace)}
        self.opened = None

    def tearDown(self):
        runtime.lifecycle({**self.args, "action": "stop", "confirmed": True})
        self.temp.cleanup()

    def start(self):
        self.opened = runtime.lifecycle({**self.args, "action": "start", "confirmed": True})
        self.assertTrue(self.opened["ok"], self.opened)

    def call(self, route, body=None, headers=None, method=None):
        parsed = urlsplit(self.opened["url"])
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=15)
        defaults = {"Content-Type": "application/json"} if body is not None else {}
        defaults.update(headers or {})
        conn.request(method or ("POST" if body is not None else "GET"), parsed.path.rsplit('/', 1)[0] + '/' + route, body=body, headers=defaults)
        response = conn.getresponse(); data = response.read(); status = response.status; h = dict(response.getheaders()); conn.close()
        return status, data, h

    def post(self, route, body):
        status, data, _ = self.call(route, json.dumps(body, ensure_ascii=False).encode())
        return status, json.loads(data)

    def test_owned_start_stop_restart(self):
        self.assertFalse(runtime.lifecycle({**self.args, "action": "start"})["ok"])
        self.start()
        self.assertTrue(runtime.lifecycle({**self.args, "action": "status"})["running"])
        again = runtime.lifecycle({**self.args, "action": "start", "confirmed": True})
        self.assertEqual(again["session_id"], self.opened["session_id"])
        self.assertTrue(runtime.lifecycle({**self.args, "action": "stop", "confirmed": True})["stopped"])
        previous = self.opened["session_id"]; self.start()
        self.assertNotEqual(previous, self.opened["session_id"])

    def test_transport_and_persistence(self):
        self.start()
        status, data, headers = self.call('index.html')
        self.assertEqual(status, 200)
        self.assertIn("离线资源配置优化台", data.decode())
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
        self.assertEqual(self.call('vendor/highs/bin/highs')[0], 404)
        for route in ['api/bootstrap', 'index.html']:
            self.assertEqual(self.call(route, headers={'Host':'other.invalid'})[0], 403)
            self.assertEqual(self.call(route, headers={'Origin':'https://outside.invalid'})[0], 403)
        self.assertEqual(self.call('api/solve', b'{}', {'Content-Type':'text/plain'})[0], 400)
        self.assertEqual(self.call('api/solve', b'{"project":{},"project":{}}')[0], 400)
        p = model.examples()["设备扩容"]
        status, r = self.post('api/solve', {'request_id':'first', 'project':p})
        self.assertEqual(status, 200); self.assertEqual(r['result']['objective'],17)
        self.assertEqual(self.post('api/solve', {'request_id':'first','project':p})[0],409)
        self.assertEqual(self.post('api/cancel', {'request_id':'late'})[0],200)
        self.assertEqual(self.post('api/solve', {'request_id':'late','project':p})[0],409)
        status, data, _ = self.call('api/bootstrap')
        self.assertEqual(json.loads(data)['project'], p)
        self.assertIsNone(json.loads(data)['result'])
        runtime.lifecycle({**self.args,'action':'stop','confirmed':True}); self.start()
        self.assertEqual(json.loads(self.call('api/bootstrap')[1])['project'],p)
        self.assertEqual(self.post('api/reset',{})[1]['project'],fixture())
        self.assertFalse(self.post('api/project',{'project':{}})[1]['ok'])
        self.assertTrue(self.post('api/project',{'project':p})[1]['ok'])
        self.assertEqual(stat.S_IMODE((self.workspace/runtime.STATE_DIR/'project.json').stat().st_mode),0o600)

    def test_invalid_project_recovery_and_state_ownership(self):
        self.start(); directory=self.workspace/runtime.STATE_DIR
        path=directory/'project.json'; path.write_bytes(b'{broken'); path.chmod(0o600)
        bootstrap=json.loads(self.call('api/bootstrap')[1])
        self.assertTrue(bootstrap['warnings']); self.assertEqual(path.read_bytes(),b'{broken')
        self.assertTrue(self.post('api/reset',{})[1]['ok'])
        backups=list(directory.glob('project.invalid-*.json'))
        self.assertEqual(len(backups),1); self.assertEqual(backups[0].read_bytes(),b'{broken')
        runtime.lifecycle({**self.args,'action':'stop','confirmed':True})
        state=directory/'server.json'; state.write_text('{invalid'); state.chmod(0o600)
        self.assertFalse(runtime.lifecycle({**self.args,'action':'start','confirmed':True})['ok'])
        self.assertEqual(state.read_text(),'{invalid')

    def test_symlink_paths_and_foreign_permissions(self):
        link=self.workspace/'link';link.symlink_to(self.workspace,target_is_directory=True)
        self.assertFalse(runtime.lifecycle({'action':'start','workspace':str(link),'confirmed':True})['ok'])
        directory=self.workspace/runtime.STATE_DIR;directory.mkdir(mode=0o755)
        self.assertFalse(runtime.lifecycle({**self.args,'action':'start','confirmed':True})['ok'])
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode),0o755)


if __name__ == '__main__':
    unittest.main(verbosity=2)
