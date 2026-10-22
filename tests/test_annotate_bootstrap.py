import concurrent.futures
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location("annotate_launcher", Path(__file__).parents[1] / "plugins/annotate/annotate/scripts/launch.py")
launcher = importlib.util.module_from_spec(SPEC)
_previous_dont_write_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(launcher)
finally:
    sys.dont_write_bytecode = _previous_dont_write_bytecode


class AnnotateBootstrapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.payload = self.base / "annotate"
        self.runtime = self.payload / "runtime"
        self.runtime.mkdir(parents=True)
        self.cache = self.base / "cache"
        self.packages = {
            "node_modules/playwright-core": {"version": "1.63.0"},
            "node_modules/@modelcontextprotocol/sdk": {"version": "1.32.0"},
        }
        (self.runtime / "package.json").write_text('{"version":"1.0.3"}')
        (self.runtime / "package-lock.json").write_text(json.dumps({"packages": self.packages}))
        self.state = self.runtime / "node_modules/.annotate-ready.json"

    def install(self, *arguments, **options):
        for name, metadata in self.packages.items():
            directory = self.runtime / name
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "package.json").write_text(json.dumps(metadata))
        for name in ("node_modules/playwright-core/index.mjs", "node_modules/@modelcontextprotocol/sdk/dist/esm/server/index.js"):
            entry = self.runtime / name
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("")
        return subprocess.CompletedProcess(arguments, 0)

    def prepare(self):
        launcher.ensure_runtime(self.payload, self.cache, "/test/node", "v22.11.0")

    def test_cold_start_installs_with_protocol_safe_output(self):
        with mock.patch.object(launcher.subprocess, "run", side_effect=self.install) as installer, mock.patch("sys.stderr", new_callable=io.StringIO) as diagnostics:
            self.prepare()
            self.assertTrue(self.state.exists())
            self.assertIn("首次使用正在初始化", diagnostics.getvalue())
            self.assertIs(installer.call_args.kwargs["stdout"], diagnostics)
            self.assertEqual(installer.call_args.kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(launcher.read_json(self.cache / "runtime.json"), {"node": "/test/node"})

    def test_warm_start_does_not_reinstall(self):
        with mock.patch.object(launcher.subprocess, "run", side_effect=self.install) as installer:
            self.prepare()
            timestamp = self.state.stat().st_mtime_ns
            self.prepare()
            self.assertEqual(installer.call_count, 1)
            self.assertEqual(self.state.stat().st_mtime_ns, timestamp)

    def test_missing_dependency_triggers_repair(self):
        with mock.patch.object(launcher.subprocess, "run", side_effect=self.install) as installer:
            self.prepare()
            (self.runtime / "node_modules/playwright-core/package.json").unlink()
            self.prepare()
            self.assertEqual(installer.call_count, 2)

    def test_changed_lock_triggers_reinstall(self):
        with mock.patch.object(launcher.subprocess, "run", side_effect=self.install) as installer:
            self.prepare()
            lock = self.runtime / "package-lock.json"
            lock.write_text(lock.read_text() + "\n")
            self.prepare()
            self.assertEqual(installer.call_count, 2)

    def test_failed_install_is_not_ready_and_can_retry(self):
        with mock.patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(RuntimeError, "自动安装依赖失败"):
                self.prepare()
        self.assertFalse(self.state.exists())
        with mock.patch.object(launcher.subprocess, "run", side_effect=self.install):
            self.prepare()
        self.assertTrue(self.state.exists())

    def test_incomplete_install_is_not_ready(self):
        with mock.patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
            with self.assertRaisesRegex(RuntimeError, "依赖安装不完整"):
                self.prepare()
        self.assertFalse(self.state.exists())

    def test_timeout_is_reported_and_not_ready(self):
        with mock.patch.object(launcher.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 150)):
            with self.assertRaisesRegex(RuntimeError, "依赖安装超时"):
                self.prepare()
        self.assertFalse(self.state.exists())

    def test_concurrent_starts_install_only_once(self):
        def delayed_install(*arguments, **options):
            time.sleep(0.15)
            return self.install(*arguments, **options)

        with mock.patch.object(launcher.subprocess, "run", side_effect=delayed_install) as installer:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(self.prepare) for index in range(2)]
                for future in futures:
                    future.result(timeout=5)
            self.assertEqual(installer.call_count, 1)

    def test_invalid_configuration_is_ignored(self):
        configuration = self.base / "runtime.json"
        configuration.write_text("[]")
        self.assertEqual(launcher.read_json(configuration), {})
        configuration.write_text("not json")
        self.assertEqual(launcher.read_json(configuration), {})

    def test_bundled_node_discovery_without_path_or_configuration(self):
        application = Path("/Applications/WorkSwarm.app")
        binary = application / "Contents/Resources/node-runtime/bin/node"
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(launcher.shutil, "which", return_value=None), mock.patch.object(Path, "glob", return_value=[application]), mock.patch.object(Path, "is_file", return_value=True), mock.patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "v22.11.0\n")):
            node, version = launcher.find_node(self.base / "absent.json")
        self.assertEqual(node, str(binary.resolve()))
        self.assertEqual(version, "v22.11.0")

    def test_old_explicit_node_is_rejected(self):
        with mock.patch.dict(os.environ, {"ANNOTATE_NODE": "/test/node"}), mock.patch.object(Path, "is_file", return_value=True), mock.patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "v18.0.0\n")):
            with self.assertRaisesRegex(RuntimeError, "Node.js >=20"):
                launcher.find_node(self.base / "absent.json")


if __name__ == "__main__":
    unittest.main()
