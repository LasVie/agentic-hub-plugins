"""Actual subprocess, private lifecycle, HTTP authorization and cancellation tests."""
from concurrent.futures import ThreadPoolExecutor
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

PAYLOAD = Path(__file__).resolve().parents[1] / "plugins/solid-mesh-workbench/solid-mesh-workbench"
SPEC = importlib.util.spec_from_file_location("solid_mesh_test_runtime", PAYLOAD / "runtime/runtime.py")
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)
NODE = os.environ.get("SOLID_MESH_TEST_NODE") or shutil.which("node")
PROJECT = {"schema": "solid-mesh-workbench/v1", "units": "mm", "operation": "union",
           "a": {"kind": "box", "size": [10, 10, 10]},
           "b": {"kind": "box", "size": [10, 10, 10], "translate": [5, 0, 0]}}


class PrivateWorkspace(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="solid-mesh-runtime-test-")
        self.workspace = Path(self.temporary.name).resolve()
        self.inputs = {"workspace": str(self.workspace), "confirmed": True}
        if NODE:
            self.inputs["node_path"] = NODE

    def tearDown(self):
        # Only this fixture's ownership-checked service is eligible to stop.
        runtime.lifecycle({**self.inputs, "action": "stop"})
        self.temporary.cleanup()

    def lifecycle(self, action, **extra):
        return runtime.lifecycle({**self.inputs, "action": action, **extra})


class StateBoundaries(PrivateWorkspace):
    def test_status_and_unconfirmed_start_do_not_write(self):
        self.assertEqual(self.lifecycle("status")["running"], False)
        self.assertFalse(self.lifecycle("start", confirmed=False)["ok"])
        self.assertEqual(list(self.workspace.iterdir()), [])
        self.assertFalse(self.lifecycle([])["ok"])
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_symlink_workspace_and_existing_broad_directory_are_preserved(self):
        link = self.workspace / "linked"
        link.symlink_to(self.workspace, target_is_directory=True)
        self.assertFalse(runtime.lifecycle({**self.inputs, "action": "start", "workspace": str(link)})["ok"])
        state = self.workspace / runtime.STATE_DIR
        state.mkdir(mode=0o755)
        before = stat.S_IMODE(state.stat().st_mode)
        self.assertFalse(self.lifecycle("start")["ok"])
        self.assertEqual(stat.S_IMODE(state.stat().st_mode), before)
        state.rmdir()

    def test_malformed_state_is_neither_replaced_nor_deleted(self):
        state = self.workspace / runtime.STATE_DIR
        state.mkdir(mode=0o700)
        record = state / "server.json"
        record.write_text('{"version":"another-install"}')
        record.chmod(0o600)
        before = record.read_bytes()
        for action in ("status", "start", "stop"):
            self.assertFalse(self.lifecycle(action)["ok"])
            self.assertEqual(record.read_bytes(), before)
        record.unlink()

    def test_state_symlink_fifo_and_hardlink_are_rejected_without_reading(self):
        state = self.workspace / runtime.STATE_DIR
        state.mkdir(mode=0o700)
        target = self.workspace / "unrelated.txt"
        target.write_text("保留原始文件")
        target.chmod(0o600)
        record = state / "server.json"
        record.symlink_to(target)
        self.assertFalse(self.lifecycle("status")["ok"])
        record.unlink()
        os.mkfifo(record, mode=0o600)
        started = time.monotonic()
        self.assertFalse(self.lifecycle("status")["ok"])
        self.assertLess(time.monotonic() - started, 1)
        record.unlink()
        os.link(target, record)
        self.assertFalse(self.lifecycle("stop")["ok"])
        self.assertEqual(target.read_text(), "保留原始文件")
        record.unlink()


@unittest.skipUnless(NODE, "Set SOLID_MESH_TEST_NODE to an existing Node.js 22+ executable")
class EngineProcessTests(PrivateWorkspace):
    def fake_engine(self, source):
        root = self.workspace / "synthetic-payload"
        (root / "engine").mkdir(parents=True)
        (root / "engine/cli.mjs").write_text(source, encoding="utf-8")
        return root

    def test_actual_engine_volume_and_invalid_mesh(self):
        result = runtime.engine_call({"project": PROJECT, "node_path": NODE})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["version"], "1.0.0")
        self.assertAlmostEqual(result["metrics"]["volume_mm3"], 1500)
        bad = {**PROJECT, "a": {"kind": "obj", "text": "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"}}
        result = runtime.engine_call({"project": bad, "node_path": NODE})
        self.assertFalse(result["ok"])
        self.assertIsInstance(result["error"], str)

    def test_oversize_nonfinite_and_unknown_fields_rejected(self):
        for inputs in ({"project": {"x": "x" * (runtime.MAX_INPUT + 1)}, "node_path": NODE},
                       {"project": {"x": float("nan")}, "node_path": NODE},
                       {"project": PROJECT, "node_path": NODE, "shell": "x"}):
            self.assertFalse(runtime.engine_call(inputs)["ok"])

    def test_child_environment_excludes_inherited_hooks_and_credentials(self):
        root = self.fake_engine("process.stdin.resume(); process.stdin.on('end',()=>console.log(JSON.stringify({ok:true,leaked:['NODE_OPTIONS','NODE_PATH','OPENAI_API_KEY','HTTPS_PROXY','PYTHONPATH'].filter(x=>process.env[x])}))); ")
        values = {name: "must-not-enter-child" for name in ("NODE_OPTIONS", "NODE_PATH", "OPENAI_API_KEY", "HTTPS_PROXY", "PYTHONPATH")}
        with patch.object(runtime, "ROOT", root), patch.dict(os.environ, values):
            result = runtime.run_engine({}, NODE)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["leaked"], [])

    def test_timeout_and_cancel_reap_owned_child(self):
        root = self.fake_engine("process.stdin.resume(); setInterval(()=>{},1000);")
        actual_popen = subprocess.Popen
        children = []

        def capture(*args, **kwargs):
            child = actual_popen(*args, **kwargs)
            children.append(child)
            return child

        with patch.object(runtime, "ROOT", root), patch.object(runtime, "ENGINE_TIMEOUT", 0.15), patch.object(runtime.subprocess, "Popen", capture):
            result = runtime.run_engine({}, NODE)
        self.assertTrue(result.get("timed_out"), result)
        self.assertIsNotNone(children[-1].poll())
        cancelled = threading.Event()
        timer = threading.Timer(0.12, cancelled.set)
        timer.start()
        try:
            with patch.object(runtime, "ROOT", root), patch.object(runtime.subprocess, "Popen", capture):
                result = runtime.run_engine({}, NODE, cancelled)
        finally:
            timer.join()
        self.assertTrue(result.get("cancelled"), result)
        self.assertIsNotNone(children[-1].poll())

    def test_output_overflow_and_invalid_json_are_not_success(self):
        root = self.fake_engine("process.stdout.write('x'.repeat(200000)); setInterval(()=>{},1000);")
        with patch.object(runtime, "ROOT", root), patch.object(runtime, "MAX_OUTPUT", 65536):
            self.assertFalse(runtime.run_engine({}, NODE)["ok"])
        (root / "engine/cli.mjs").write_text("console.log('{\"ok\":true,\"ok\":false}');")
        with patch.object(runtime, "ROOT", root):
            self.assertFalse(runtime.run_engine({}, NODE)["ok"])


@unittest.skipUnless(NODE, "Set SOLID_MESH_TEST_NODE to an existing Node.js 22+ executable")
class WorkbenchHTTPTests(PrivateWorkspace):
    def start(self):
        result = self.lifecycle("start")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["running"])
        address = urlsplit(result["url"])
        self.port = address.port
        self.prefix = address.path.rsplit("/", 1)[0] + "/"
        return result

    def request(self, route, body=None, *, headers=None, method=None, raw_path=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = dict(headers or {})
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        if body is not None:
            headers.setdefault("Content-Type", "application/json")
        connection.request(method or ("POST" if body is not None else "GET"), raw_path or self.prefix + route, body=data, headers=headers)
        response = connection.getresponse()
        result = (response.status, response.read(), dict(response.getheaders()))
        connection.close()
        return result

    def test_real_lifecycle_apply_reuse_http_calculate_stop_restart(self):
        first = self.start()
        repeated = self.lifecycle("start")
        self.assertEqual(first["session_id"], repeated["session_id"])
        self.assertFalse(repeated["started"])
        self.assertEqual(self.lifecycle("status")["session_id"], first["session_id"])
        code, data, headers = self.request("index.html")
        self.assertEqual(code, 200)
        self.assertIn("立体网格布尔工坊".encode(), data)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        code, data, _ = self.request("api/calculate", {"request_id": "actual-union", "project": PROJECT})
        result = json.loads(data)
        self.assertEqual(code, 200)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["request_id"], "actual-union")
        self.assertAlmostEqual(result["metrics"]["volume_mm3"], 1500)
        self.assertEqual(self.request("api/calculate", {"request_id": "actual-union", "project": PROJECT})[0], 409)
        stopped = self.lifecycle("stop")
        self.assertTrue(stopped["ok"], stopped)
        self.assertFalse(stopped["running"])
        second = self.start()
        self.assertNotEqual(first["session_id"], second["session_id"])
        self.assertNotEqual(first["url"], second["url"])

    def test_ui_stop_and_stale_state_recovery(self):
        first = self.start()
        self.assertEqual(self.request("api/stop", {})[0], 200)
        deadline = time.monotonic() + 4
        while self.lifecycle("status").get("running") and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(self.lifecycle("status").get("running"))
        second = self.start()
        self.assertNotEqual(first["session_id"], second["session_id"])

    def test_http_authorization_navigation_and_allowlist(self):
        self.start()
        for route, headers, raw_path in [
            ("api/health", {"Host": "attacker.invalid"}, None),
            ("api/health", {"Origin": "http://attacker.invalid"}, None),
            ("api/health", {"Sec-Fetch-Site": "cross-site"}, None),
            ("index.html", {"Sec-Fetch-Site": "same-site"}, None),
            ("api/health", {}, "/wrong-token/api/health"),
            ("../manifest.json", {}, None),
            ("%2e%2e/manifest.json", {}, None),
            ("runtime/runtime.py", {}, None),
            ("api/health?leak=1", {}, None),
        ]:
            self.assertIn(self.request(route, headers=headers, raw_path=raw_path)[0], (403, 404))
        navigation = {"Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document", "Sec-Fetch-User": "?1"}
        self.assertEqual(self.request("index.html", headers=navigation)[0], 200)
        self.assertEqual(self.request("api/health", headers=navigation)[0], 403)
        self.assertEqual(self.request("api/session")[0], 200)
        self.assertEqual(self.request("licenses/manifold/LICENSE")[0], 200)

    def test_malformed_and_cross_origin_post_do_not_calculate(self):
        self.start()
        for body in (b"{", b'{"request_id":"x","request_id":"y","project":{}}', b'{"request_id":"x","project":{"x":NaN}}', b"[]"):
            self.assertEqual(self.request("api/calculate", body)[0], 400)
        self.assertEqual(self.request("api/calculate", {"request_id": "x", "project": PROJECT}, headers={"Origin": "null"})[0], 403)
        self.assertEqual(self.request("api/stop", {"path": "/somewhere"})[0], 400)
        self.assertTrue(self.lifecycle("status")["running"])

    def test_cancel_arriving_before_calculate_fences_that_job_only(self):
        self.start()
        response = json.loads(self.request("api/cancel", {"request_id": "cancel-before-start"})[1])
        self.assertTrue(response["cancellation_recorded"])
        self.assertFalse(response["cancelled"])
        code, body, _ = self.request("api/calculate", {"request_id": "cancel-before-start", "project": PROJECT})
        self.assertEqual(code, 409)
        self.assertTrue(json.loads(body)["cancelled"])
        self.assertFalse(json.loads(self.request("api/health")[1])["busy"])
        response = json.loads(self.request("api/calculate", {"request_id": "new-permitted-job", "project": PROJECT})[1])
        self.assertTrue(response["ok"], response)

    def test_foreign_service_identity_is_preserved(self):
        calls = []

        class UnrelatedHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append("GET")
                data = json.dumps({"ok": True, "plugin_id": "some-other-service", "version": "1.0.0", "session_id": "0" * 32}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                calls.append("POST")
                self.send_response(500)
                self.end_headers()

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), UnrelatedHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        directory = runtime.runtime_dir(self.workspace, create=True)
        state = {"root": str(runtime.ROOT), "version": runtime.VERSION, "port": server.server_port,
                 "session_id": "0" * 32, "token": "0" * 64}
        runtime._save_state(directory, state)
        record = directory / "server.json"
        before = record.read_bytes()
        try:
            for action in ("status", "start", "stop"):
                self.assertFalse(self.lifecycle(action)["ok"])
                self.assertEqual(record.read_bytes(), before)
            self.assertNotIn("POST", calls)
            self.assertTrue(thread.is_alive())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            record.unlink()

    def test_busy_cancel_only_matching_job_and_recover(self):
        # A private synthetic payload makes cancellation timing deterministic,
        # while using real Node/Python children and the production HTTP server.
        synthetic = self.workspace / "synthetic-payload"
        shutil.copytree(PAYLOAD / "runtime", synthetic / "runtime")
        (synthetic / "engine").mkdir()
        (synthetic / "engine/cli.mjs").write_text("process.stdin.resume(); setTimeout(()=>console.log(JSON.stringify({ok:true,metrics:{}})),1500);")
        with patch.object(runtime, "ROOT", synthetic):
            try:
                self.start()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    pending = executor.submit(self.request, "api/calculate", {"request_id": "slow-job", "project": {}})
                    deadline = time.monotonic() + 3
                    while not json.loads(self.request("api/health")[1])["busy"] and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(json.loads(self.request("api/health")[1])["busy"])
                    self.assertEqual(self.request("api/calculate", {"request_id": "other-job", "project": {}})[0], 409)
                    self.assertFalse(json.loads(self.request("api/cancel", {"request_id": "wrong-job"})[1])["cancelled"])
                    self.assertTrue(json.loads(self.request("api/cancel", {"request_id": "slow-job"})[1])["cancelled"])
                    result = json.loads(pending.result(timeout=3)[1])
                    self.assertTrue(result.get("cancelled"), result)
                self.assertFalse(json.loads(self.request("api/health")[1])["busy"])
            finally:
                self.assertTrue(self.lifecycle("stop")["ok"])


if __name__ == "__main__":
    unittest.main()
