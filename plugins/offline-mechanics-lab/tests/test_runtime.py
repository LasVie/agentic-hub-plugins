"""Real loopback/service/process regressions; isolated copies and disposable state."""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from urllib.parse import urlsplit


PAYLOAD = Path(__file__).resolve().parents[1] / "offline-mechanics-lab"
PLAN = {"schema_version": 1, "engine_version": "0.20.0", "title": "中文测试场景", "gravity": 100, "duration": 1,
        "bodies": [{"id": "b1", "label": "测试物体", "shape": "rectangle", "x": 100, "y": 100,
                    "width": 50, "height": 50, "radius": 24, "angle": 0, "vx": 0, "vy": 0, "mass": 1,
                    "static": False, "rotationLocked": False, "friction": 0, "frictionAir": 0, "restitution": 0}], "constraints": []}


def load_lab(payload):
    spec = importlib.util.spec_from_file_location("mechanics_lab_test_" + str(hash(str(payload))),
                                                 payload / "runtime/lab.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="mechanics-runtime-test-", dir=str(Path(tempfile.gettempdir()).resolve()))
        self.root = Path(self.scratch.name)
        self.payload = self.root / "plugin"
        shutil.copytree(PAYLOAD, self.payload, ignore=shutil.ignore_patterns("__pycache__"))
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.lab = load_lab(self.payload)
        self.live = None

    def tearDown(self):
        if self.live:
            stopped = self.lab.local_lab({"action": "stop", "workspace": str(self.workspace), "confirmed": True})
            self.assertTrue(stopped["ok"], stopped)
        self.scratch.cleanup()

    def launch(self):
        self.live = self.lab.local_lab({"action": "start", "workspace": str(self.workspace), "confirmed": True})
        self.assertTrue(self.live["ok"], self.live)
        self.assertTrue(self.live["running"], self.live)
        self.url = urlsplit(self.live["url"])
        return self.live

    def request(self, endpoint="api/health", value=None, *, method=None, path=None, headers=None, raw=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.url.port, timeout=15)
        body = raw if raw is not None else json.dumps(value).encode() if value is not None else None
        request_headers = {"Content-Type": "application/json"} if body is not None else {}
        request_headers.update(headers or {})
        try:
            conn.request(method or ("POST" if body is not None else "GET"), path or self.url.path + endpoint,
                         body=body, headers=request_headers)
            response = conn.getresponse()
            data = response.read()
            return response.status, dict(response.getheaders()), data
        finally:
            conn.close()

    def test_explicit_start_reuse_status_stop_preserves_state(self):
        status = self.lab.local_lab({"action": "status", "workspace": str(self.workspace)})
        self.assertTrue(status["ok"])
        self.assertFalse(status["running"])
        self.assertFalse((self.workspace / ".offline-mechanics-lab").exists())
        refused = self.lab.local_lab({"action": "start", "workspace": str(self.workspace)})
        self.assertEqual(refused["error"]["code"], "confirmation_required")
        live = self.launch()
        again = self.lab.local_lab({"action": "start", "workspace": str(self.workspace), "confirmed": True})
        self.assertTrue(again["reused"])
        self.assertEqual(again["session_id"], live["session_id"])
        self.assertEqual(again["url"], live["url"])
        stopped = self.lab.local_lab({"action": "stop", "workspace": str(self.workspace), "confirmed": True})
        self.assertTrue(stopped["ok"], stopped)
        self.assertFalse(stopped["running"])
        self.assertTrue((self.workspace / ".offline-mechanics-lab/session.json").is_file())

    def test_save_roundtrip_and_overwrite_requires_explicit_confirmation(self):
        self.launch()
        code, _, data = self.request("api/save", {"scene": PLAN})
        self.assertEqual(code, 200)
        saved = json.loads(data)
        self.assertTrue(saved["ok"], saved)
        state_path = self.workspace / ".offline-mechanics-lab/scene.json"
        before = state_path.read_bytes()
        self.assertEqual(state_path.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("bodies", json.loads(before))  # only normalized input, no stale outputs
        changed = {**PLAN, "title": "修改后的场景"}
        code, _, data = self.request("api/save", {"scene": changed})
        self.assertEqual(code, 409)
        self.assertEqual(json.loads(data)["error"]["code"], "overwrite_confirmation")
        self.assertEqual(state_path.read_bytes(), before)
        code, _, data = self.request("api/save", {"scene": changed, "overwrite": True})
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(data)["ok"])
        code, _, data = self.request("api/saved")
        self.assertEqual(json.loads(data)["scene"]["title"], "修改后的场景")

    def test_forbidden_origin_host_and_missing_token(self):
        self.launch()
        for headers in ({"Origin": "https://example.org"}, {"Origin": "null"}, {"Host": "attacker.example"}):
            code, _, data = self.request("api/save", {"scene": PLAN}, headers=headers)
            self.assertEqual(code, 403)
            self.assertEqual(json.loads(data)["error"]["code"], "forbidden")
        code, _, _ = self.request(path="/api/health")
        self.assertEqual(code, 404)
        code, _, _ = self.request("../runtime/lab.py")
        self.assertEqual(code, 404)

    def test_static_assets_security_headers_and_no_traversal(self):
        self.launch()
        code, headers, data = self.request("")
        self.assertEqual(code, 200)
        self.assertIn("离线力学实验室", data.decode())
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for endpoint in ("engine.js", "worker.js", "matter.js", "app.js", "style.css", "licenses.txt", "notices.md"):
            self.assertEqual(self.request(endpoint)[0], 200, endpoint)
        for path in ("%2e%2e/runtime/lab.py", "runtime/lab.py", "api/health?x=1"):
            self.assertEqual(self.request(path)[0], 404)

    def test_invalid_http_and_scene_envelope_return_errors(self):
        self.launch()
        for payload in (b"{broken}", b"null", b"[]"):
            code, _, data = self.request("api/save", raw=payload)
            self.assertEqual(code, 400)
            self.assertFalse(json.loads(data)["ok"])
        code, _, data = self.request("api/save", {"scene": {**PLAN, "engine_version": "bad"}})
        self.assertEqual(code, 400)
        result = json.loads(data)
        self.assertFalse(result["ok"])
        self.assertRegex(result["error"]["message"], "[\u4e00-\u9fff]")
        self.assertEqual(self.request("api/save", raw=b"x", headers={"Content-Type": "text/plain"})[0], 400)
        utf16 = json.dumps({"scene": PLAN}).encode("utf-16")
        self.assertEqual(self.request("api/save", raw=utf16)[0], 400)
        self.assertEqual(self.request("api/save", raw=b" " * 32769)[0], 400)

    def test_corrupt_saved_record_is_preserved(self):
        self.launch()
        state_path = self.workspace / ".offline-mechanics-lab/scene.json"
        state_path.write_bytes(b"{broken}")
        code, _, data = self.request("api/save", {"scene": PLAN, "overwrite": True})
        self.assertEqual(code, 400)
        self.assertFalse(json.loads(data)["ok"])
        self.assertEqual(state_path.read_bytes(), b"{broken}")
        self.assertEqual(self.request("api/saved")[0], 400)

    def test_symlink_workspace_state_and_saved_target_are_refused(self):
        link = self.root / "link"
        link.symlink_to(self.workspace, target_is_directory=True)
        refused = self.lab.local_lab({"action": "start", "workspace": str(link), "confirmed": True})
        self.assertEqual(refused["error"]["code"], "unsafe_path")
        target = self.root / "other-data"
        target.mkdir(mode=0o700)
        state = self.workspace / ".offline-mechanics-lab"
        state.symlink_to(target, target_is_directory=True)
        refused = self.lab.local_lab({"action": "start", "workspace": str(self.workspace), "confirmed": True})
        self.assertEqual(refused["error"]["code"], "unsafe_path")
        state.unlink()  # test-owned symlink only
        self.launch()
        protected = self.root / "protected.json"
        protected.write_text('{"keep": true}')
        (state / "scene.json").symlink_to(protected)
        code, _, data = self.request("api/save", {"scene": PLAN, "overwrite": True})
        self.assertEqual(code, 400)
        self.assertFalse(json.loads(data)["ok"])
        self.assertEqual(protected.read_text(), '{"keep": true}')

    def test_foreign_install_session_is_not_replaced_or_stopped(self):
        self.launch()
        foreign = self.root / "another-install"
        shutil.copytree(self.payload, foreign)
        second = load_lab(foreign)
        session = self.workspace / ".offline-mechanics-lab/session.json"
        before = session.read_bytes()
        for action in ("start", "stop", "status"):
            result = second.local_lab({"action": action, "workspace": str(self.workspace), "confirmed": True})
            self.assertEqual(result["error"]["code"], "foreign_session")
        self.assertEqual(session.read_bytes(), before)
        self.assertTrue(self.lab.local_lab({"action": "status", "workspace": str(self.workspace)})["running"])



if __name__ == "__main__":
    unittest.main()
