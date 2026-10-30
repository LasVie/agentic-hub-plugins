"""Exercise the real plugin-owned loopback service and Node bridge, without a model.

All writes and listeners belong to temporary test workspaces. These tests do not
install the plugin or represent a running WorkSwarm chat/tool-dispatch test.
"""
import copy
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "plugins/offline-optics-lab/offline-optics-lab"


def load_runtime(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    return module


lab = load_runtime(PAYLOAD / "runtime/lab.py", "optics_runtime_tests")
SCENE = {
    "schema_version": 1,
    "title": "中文直线光路",
    "objects": [
        {"id": "光源", "type": "SingleRay", "p1": {"x": 100, "y": 100},
         "p2": {"x": 200, "y": 100}, "brightness": 1},
        {"id": "探测器", "type": "Detector", "p1": {"x": 400, "y": 20},
         "p2": {"x": 400, "y": 200}, "bins": 10, "twoSided": True},
    ],
}


class RuntimeIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="offline-optics-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.workspace = str(Path(self.temp.name).resolve())
        self.state_dir = Path(self.workspace) / ".offline-optics-lab"
        self.node = lab.select_node()
        self.started = lab.local_lab({"workspace": self.workspace, "action": "start",
                                      "confirmed": True, "node_path": self.node})
        self.assertTrue(self.started["ok"], self.started)
        self.url = urlsplit(self.started["url"])
        self.addCleanup(self.stop)

    def stop(self):
        result = lab.local_lab({"workspace": self.workspace, "action": "stop", "confirmed": True})
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["running"], result)

    def request(self, suffix="", value=None, *, headers=None, raw=None, path=None, method=None):
        payload = json.dumps(value, ensure_ascii=False).encode() if value is not None else raw
        request_headers = {"Content-Type": "application/json"} if payload is not None else {}
        request_headers.update(headers or {})
        conn = http.client.HTTPConnection("127.0.0.1", self.url.port, timeout=15)
        try:
            conn.request(method or ("POST" if payload is not None else "GET"),
                         path or self.url.path + suffix, payload, request_headers)
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def json_request(self, *args, **kwargs):
        code, headers, body = self.request(*args, **kwargs)
        return code, headers, json.loads(body)

    def test_real_service_runs_real_trace_and_chinese_page(self):
        code, headers, body = self.request()
        self.assertEqual(code, 200)
        self.assertIn("离线光学实验室", body.decode("utf-8"))
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(headers["Cache-Control"], "no-store")
        code, _, result = self.json_request("api/simulate", {"scene": SCENE})
        self.assertEqual(code, 200)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(result["detectors"][0]["hits"], 1)
        self.assertAlmostEqual(abs(result["detectors"][0]["power"]), 1)
        self.assertFalse(result["stats"]["truncated"])
        self.assertFalse((self.state_dir / "scene.json").exists())

    def test_serves_bundled_examples_and_license(self):
        code, _, response = self.json_request("api/examples")
        self.assertEqual(code, 200)
        self.assertTrue(response["ok"])
        self.assertEqual(response["examples"], json.loads((PAYLOAD / "engine/examples.json").read_text()))
        code, _, body = self.request("licenses.txt")
        self.assertEqual(code, 200)
        self.assertEqual(body, (PAYLOAD / "licenses/ray-optics/LICENSE").read_bytes())

    def test_save_persists_across_stop_and_restart_without_changing_scene(self):
        _, _, empty = self.json_request("api/state")
        self.assertIsNone(empty["scene"])
        code, _, saved = self.json_request("api/state", {"scene": SCENE})
        self.assertEqual(code, 200)
        self.assertTrue(saved["ok"], saved)
        path = self.state_dir / "scene.json"
        original = path.read_bytes()
        self.assertEqual(saved["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.state_dir.stat().st_mode & 0o777, 0o700)
        _, _, before = self.json_request("api/state")
        self.stop()
        restarted = lab.local_lab({"workspace": self.workspace, "action": "start", "confirmed": True})
        self.assertTrue(restarted["ok"], restarted)
        self.assertNotEqual(restarted["session_id"], self.started["session_id"])
        self.assertFalse(restarted["reused"])
        self.url = urlsplit(restarted["url"])
        _, _, after = self.json_request("api/state")
        self.assertEqual(after["scene"], before["scene"])
        self.assertEqual(path.read_bytes(), original)

    def test_same_workspace_reuses_one_session(self):
        again = lab.local_lab({"workspace": self.workspace, "action": "start", "confirmed": True})
        current = lab.local_lab({"workspace": self.workspace, "action": "status"})
        self.assertTrue(again["ok"], again)
        self.assertTrue(again["reused"])
        self.assertEqual(again["session_id"], self.started["session_id"])
        self.assertEqual(current["url"], self.started["url"])
        self.assertEqual(current["runtime_id"], self.started["runtime_id"])

    def test_unsafe_http_requests_do_not_read_or_write_state(self):
        for path in ("/", "/wrong/api/health", self.url.path + "../runtime/lab.py"):
            self.assertEqual(self.request(path=path)[0], 404)
        self.assertEqual(self.request("api/state", headers={"Host": "attacker.example"})[0], 403)
        self.assertEqual(self.request("api/state", {"scene": SCENE},
                                      headers={"Origin": "https://attacker.example"})[0], 403)
        self.assertEqual(self.request("api/state", {"scene": SCENE},
                                      headers={"Origin": "null"})[0], 403)
        self.assertFalse((self.state_dir / "scene.json").exists())

    def test_malformed_and_oversized_requests_report_failure(self):
        for body, headers in ((b"{broken", {}),
                              (b"{}", {"Content-Type": "text/plain"}),
                              (b"x" * (128 * 1024 + 1), {})):
            code, _, response = self.json_request("api/state", raw=body, headers=headers)
            self.assertEqual(code, 400)
            self.assertFalse(response["ok"])
        code, _, response = self.json_request("api/simulate", {"scene": SCENE, "output_path": "/tmp/no"})
        self.assertEqual(code, 400)
        self.assertFalse(response["ok"])
        self.assertFalse((self.state_dir / "scene.json").exists())

    def test_invalid_scene_does_not_replace_saved_scene(self):
        _, _, response = self.json_request("api/state", {"scene": SCENE})
        self.assertTrue(response["ok"], response)
        path = self.state_dir / "scene.json"
        original = path.read_bytes()
        invalid = copy.deepcopy(SCENE)
        invalid["objects"][0]["type"] = "UnboundedExternalScript"
        _, _, rejected = self.json_request("api/state", {"scene": invalid})
        self.assertFalse(rejected["ok"], rejected)
        self.assertEqual(path.read_bytes(), original)
        self.assertRegex(rejected["error"]["message"], "[\u4e00-\u9fff]")

    def test_corrupt_saved_record_is_preserved(self):
        path = self.state_dir / "scene.json"
        damaged = b"{\"version\":\"1.0.0\",unfinished"
        path.write_bytes(damaged)
        code, _, loaded = self.json_request("api/state")
        self.assertEqual(code, 400)
        self.assertFalse(loaded["ok"])
        code, _, save = self.json_request("api/state", {"scene": SCENE})
        self.assertEqual(code, 400)
        self.assertFalse(save["ok"])
        self.assertEqual(path.read_bytes(), damaged)

    def test_symlink_saved_record_cannot_modify_another_file(self):
        target = Path(self.workspace) / "keep.json"
        original = b'{"unrelated":"preserve"}'
        target.write_bytes(original)
        (self.state_dir / "scene.json").symlink_to(target)
        code, _, response = self.json_request("api/state", {"scene": SCENE})
        self.assertEqual(code, 400)
        self.assertFalse(response["ok"])
        self.assertEqual(target.read_bytes(), original)
        self.assertTrue((self.state_dir / "scene.json").is_symlink())

    def test_other_installation_cannot_adopt_or_stop_live_session(self):
        alternate = Path(self.workspace) / "alternate-install"
        shutil.copytree(PAYLOAD, alternate, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        other = load_runtime(alternate / "runtime/lab.py", "optics_other_install_test")
        original = (self.state_dir / "session.json").read_bytes()
        for action in ("status", "start", "stop"):
            result = other.local_lab({"workspace": self.workspace, "action": action, "confirmed": True})
            self.assertFalse(result["ok"], result)
            self.assertEqual(result["error"]["code"], "foreign_session")
        self.assertEqual((self.state_dir / "session.json").read_bytes(), original)
        _, _, live = self.json_request("api/health")
        self.assertTrue(live["running"])
        self.assertEqual(live["session_id"], self.started["session_id"])


class RuntimeInputs(unittest.TestCase):
    def test_confirmation_and_workspace_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="offline-optics-inputs-") as temp:
            work = str(Path(temp).resolve())
            for action in ("start", "stop"):
                denied = lab.local_lab({"workspace": work, "action": action})
                self.assertFalse(denied["ok"])
                self.assertEqual(denied["error"]["code"], "confirmation_required")
            self.assertFalse((Path(work) / ".offline-optics-lab").exists())
            alias = Path(work) / "alias"
            alias.symlink_to(work, target_is_directory=True)
            for value in ("relative", str(alias), str(Path(work) / "missing")):
                result = lab.local_lab({"workspace": value, "action": "start", "confirmed": True})
                self.assertFalse(result["ok"], result)
            self.assertFalse(lab.local_lab({"workspace": work, "action": "status"})["running"])

    def test_missing_node_does_not_create_session_or_claim_success(self):
        with tempfile.TemporaryDirectory(prefix="offline-optics-no-node-") as temp:
            work = str(Path(temp).resolve())
            missing = str(Path(work) / "not-installed-node")
            result = lab.local_lab({"workspace": work, "action": "start", "confirmed": True,
                                    "node_path": missing})
            self.assertFalse(result["ok"], result)
            self.assertEqual(result["error"]["code"], "node_unavailable")
            self.assertFalse((Path(work) / ".offline-optics-lab/session.json").exists())
            trace = lab.engine_call({"scene": SCENE, "node_path": missing})
            self.assertFalse(trace["ok"], trace)
            self.assertEqual(trace["error"]["code"], "node_unavailable")


if __name__ == "__main__":
    unittest.main()
