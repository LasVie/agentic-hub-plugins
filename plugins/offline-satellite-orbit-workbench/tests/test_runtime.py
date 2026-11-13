"""独立服务的实际生命周期、静态资源边界与用户点击入口回归测试。"""
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.client
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

PAYLOAD = Path(__file__).resolve().parents[1] / "offline-satellite-orbit-workbench"
SPEC = importlib.util.spec_from_file_location("orbit_runtime_test", PAYLOAD / "tools/runtime.py")
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        # Fixtures are intentionally minimal; browser/engine tests exercise the
        # actual packaged web UI separately. The real server code is unchanged.
        self.temp = tempfile.TemporaryDirectory(prefix="orbit-runtime-test-", dir="/private/tmp" if Path("/private/tmp").exists() else None)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.payload = self.root / "payload"
        for folder in ("tools", "web/vendor", "examples"):
            (self.payload / folder).mkdir(parents=True, exist_ok=True)
        shutil.copy2(PAYLOAD / "tools/server.py", self.payload / "tools/server.py")
        for name, content in {
            "web/index.html": "<!doctype html><title>离线卫星轨道工作台</title>",
            "web/app.js": "const version='1.0.0';", "web/worker.js": "self.onmessage=()=>{};",
            "web/vendor/engine.js": "/* bundled engine fixture */", "web/vendor/_engine.mjs": "export default 1;", "web/style.css": "body{margin:0}",
            "web/example.tle": 'public orbital element fixture',
            "examples/private.tle": 'private TLE fixture',
        }.items():
            (self.payload / name).write_text(content)
        self.root_patch = patch.object(runtime, "ROOT", self.payload)
        self.root_patch.start()

    def tearDown(self):
        runtime.workbench({"action": "stop", "workspace": str(self.workspace), "confirmed": True})
        for identity in list(runtime._CHILDREN):
            runtime.finish_child(identity, terminate=True)
        self.root_patch.stop()
        self.temp.cleanup()

    def call(self, action, **kwargs):
        return runtime.workbench({"action": action, "workspace": str(self.workspace), **kwargs})

    def start(self):
        value = self.call("start", confirmed=True)
        self.assertTrue(value["ok"], value)
        self.url = urlsplit(value["url"])
        self.prefix = self.url.path.removesuffix("web/index.html")
        return value

    def request(self, suffix="web/index.html", headers=None, method="GET", body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.url.port, timeout=3)
        try:
            connection.request(method, self.prefix + suffix, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_status_and_confirmation_never_create_state(self):
        self.assertFalse(self.call("status")["running"])
        for action in ("start", "stop"):
            self.assertEqual(self.call(action)["error"]["code"], "confirmation_required")
        for value in (1, "true", None):
            self.assertEqual(self.call("start", confirmed=value)["error"]["code"], "invalid_input")
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_lifecycle_reuse_restart_and_private_record(self):
        first = self.start()
        self.assertFalse(first["reused"])
        second = self.call("start", confirmed=True)
        self.assertEqual(second["url"], first["url"])
        self.assertTrue(second["reused"])
        directory = self.workspace / runtime.RUNTIME_NAME
        state = runtime.read_state(directory)
        self.assertEqual(state["plugin"], "offline-satellite-orbit-workbench")
        self.assertNotIn("pid", state)
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual((directory / "server.json").stat().st_mode & 0o777, 0o600)
        stopped = self.call("stop", confirmed=True)
        self.assertTrue(stopped["ok"], stopped)
        self.assertFalse(stopped["running"])
        self.assertFalse(runtime.contact(state))
        self.assertFalse(self.call("status")["running"])
        self.assertTrue((directory / "server.json").exists())
        restarted = self.call("start", confirmed=True)
        self.assertTrue(restarted["ok"], restarted)
        self.assertNotEqual(restarted["url"], first["url"])

    def test_missing_entry_page_refuses_to_publish_url(self):
        (self.payload / "web/index.html").unlink()
        result = self.call("start", confirmed=True)
        self.assertEqual(result["error"]["code"], "server_failed")
        self.assertNotIn("url", result)
        self.assertFalse((self.workspace / runtime.RUNTIME_NAME / "server.json").exists())

    def test_packaged_resources_mime_and_closed_paths(self):
        self.start()
        for path, mime in (("web/app.js", "text/javascript"), ("web/worker.js", "text/javascript"),
                           ("web/vendor/engine.js", "text/javascript"), ("web/vendor/_engine.mjs", "text/javascript"), ("web/style.css", "text/css"),
                           ("web/example.tle", "text/plain")):
            status, headers, body = self.request(path)
            self.assertEqual(status, 200, path)
            self.assertIn(mime, headers["Content-Type"])
            self.assertEqual(body, (self.payload / path).read_bytes())
            self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
            self.assertNotIn("unsafe-eval", headers["Content-Security-Policy"])
            self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        for path in ("", "../web/index.html", "%2e%2e/web/index.html", "web/../tools/server.py",
                     "tools/server.py", "examples/private.tle", "web/app.js?x=1", "web/app.js#fragment", "web//app.js", "web/", "__stop"):
            self.assertEqual(self.request(path)[0], 404, path)
        self.assertEqual(self.request(headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request(headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.request("api/orbit", method="POST", body=b"{}")[0], 405)
        self.assertEqual(self.request(method="GET", body=b"orbit-data")[0], 405)
        self.assertEqual(self.request(headers={"X-Filler": "a" * 9000})[0], 431)

    def test_only_user_activated_cross_site_entry_navigation_allowed(self):
        self.start()
        for site in ("same-site", "cross-site"):
            navigation = {"Sec-Fetch-Site": site, "Sec-Fetch-Mode": "navigate",
                          "Sec-Fetch-Dest": "document", "Sec-Fetch-User": "?1"}
            self.assertEqual(self.request(headers=navigation)[0], 200)
            for change in ({"Sec-Fetch-Mode": "cors"}, {"Sec-Fetch-Dest": "iframe"},
                           {"Sec-Fetch-User": "?0"}, {"Origin": "http://127.0.0.1:6392"}):
                self.assertEqual(self.request(headers={**navigation, **change})[0], 403)
            for path in ("web/app.js", "web/worker.js", "web/example.tle", "__health", "__stop"):
                self.assertEqual(self.request(path, headers=navigation)[0], 403, path)
            for method in ("HEAD", "POST"):
                self.assertEqual(self.request(headers=navigation, method=method)[0], 403)
        self.assertEqual(self.request("__stop", method="POST")[0], 403)
        self.assertEqual(self.request("__stop", headers={"X-Workbench-Instance": "0" * 32}, method="POST")[0], 403)
        self.assertTrue(self.call("status")["running"])

    def test_health_and_control_require_instance(self):
        self.start()
        self.assertEqual(self.request("__health")[0], 403)
        state = runtime.read_state(self.workspace / runtime.RUNTIME_NAME)
        headers = {"X-Workbench-Instance": state["instance"]}
        self.assertEqual(self.request("__health", headers=headers)[0], 200)
        self.assertEqual(self.request("__health", headers={**headers, "Origin": "http://127.0.0.1:6395"})[0], 403)
        self.assertTrue(self.call("status")["running"])

    def test_symlinks_special_files_and_hardlinked_records_rejected(self):
        link = self.root / "linked-workspace"
        link.symlink_to(self.workspace, target_is_directory=True)
        self.assertEqual(runtime.workbench({"action": "status", "workspace": str(link)})["error"]["code"], "invalid_workspace")
        self.start()
        external = self.root / "private.txt"
        external.write_text("private content")
        (self.payload / "web/leak.txt").symlink_to(external)
        os.link(external, self.payload / "web/hardlink.txt")
        (self.payload / "web/linked").symlink_to(self.root, target_is_directory=True)
        os.mkfifo(self.payload / "web/pipe.txt")
        for path in ("web/leak.txt", "web/hardlink.txt", "web/linked/private.txt", "web/pipe.txt"):
            self.assertEqual(self.request(path)[0], 404)
        self.call("stop", confirmed=True)
        directory = self.workspace / runtime.RUNTIME_NAME
        record = directory / "server.json"
        before = record.read_bytes()
        os.link(record, self.root / "record-link.json")
        value = self.call("start", confirmed=True)
        self.assertFalse(value["ok"])
        self.assertEqual(record.read_bytes(), before)

    def test_foreign_and_corrupt_records_preserved_without_contact_or_spawn(self):
        directory = self.workspace / runtime.RUNTIME_NAME
        directory.mkdir(mode=0o700)
        record = directory / "server.json"
        state = {"plugin": runtime.PLUGIN, "version": runtime.VERSION, "port": 1234,
                 "token": "0" * 64, "instance": "1" * 32, "root": str(self.root / "other-installation")}
        for raw in (json.dumps(state).encode(), b'{"port":1,"port":2}', b'invalid'):
            record.write_bytes(raw)
            record.chmod(0o600)
            inode = record.stat().st_ino
            for action in ("status", "start", "stop"):
                with patch.object(runtime, "contact") as contact, patch.object(runtime.subprocess, "Popen") as spawn:
                    value = self.call(action, confirmed=True)
                    self.assertEqual(value["error"]["code"], "invalid_runtime")
                    contact.assert_not_called()
                    spawn.assert_not_called()
                self.assertEqual(record.read_bytes(), raw)
                self.assertEqual(record.stat().st_ino, inode)
                self.assertEqual([p.name for p in directory.iterdir()], ["server.json"])

    def test_foreign_listener_is_never_stopped(self):
        requests = []
        class ForeignHandler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                requests.append("GET")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"instance":"foreign"}')
            def do_POST(self):
                requests.append("POST")
                self.send_response(200)
                self.end_headers()
        with HTTPServer(("127.0.0.1", 0), ForeignHandler) as foreign:
            thread = threading.Thread(target=foreign.serve_forever, daemon=True)
            thread.start()
            try:
                directory = self.workspace / runtime.RUNTIME_NAME
                directory.mkdir(mode=0o700)
                record = directory / "server.json"
                record.write_text(json.dumps({"plugin": runtime.PLUGIN, "version": runtime.VERSION,
                    "port": foreign.server_port, "token": "0" * 64, "instance": "1" * 32, "root": str(self.payload)}))
                record.chmod(0o600)
                self.assertFalse(self.call("stop", confirmed=True)["running"])
                self.assertEqual(requests, ["GET"])
                self.start()
                self.assertNotEqual(self.url.port, foreign.server_port)
                self.assertNotIn("POST", requests)
                self.assertTrue(thread.is_alive())
            finally:
                foreign.shutdown()
                thread.join(3)

    def test_concurrent_launch_serializes_and_reuses(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.call("start", confirmed=True), range(2)))
        self.assertTrue(any(value.get("running") for value in results), results)
        for value in results:
            if not value["ok"]:
                self.assertEqual(value["error"]["code"], "busy")
        final = self.call("start", confirmed=True)
        self.assertTrue(final["reused"])
        self.assertTrue(all(value.get("url", final["url"]) == final["url"] for value in results))

    def test_idle_timeout_ends_actual_server_process(self):
        launcher = "import importlib.util; s=importlib.util.spec_from_file_location('server',__import__('sys').argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.IDLE_SECONDS=.05; m.main()"
        process = subprocess.run([sys.executable, "-B", "-c", launcher, str(self.payload / "tools/server.py")],
            input=json.dumps({"token": "1" * 64, "instance": "2" * 32}).encode(), capture_output=True, timeout=4)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertGreater(json.loads(process.stdout)["port"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
