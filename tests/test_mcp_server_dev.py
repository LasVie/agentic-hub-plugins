import importlib.util
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/mcp-server-dev/mcp-server-dev/scripts/devkit.py"
spec = importlib.util.spec_from_file_location("mcp_devkit", SCRIPT)
devkit = importlib.util.module_from_spec(spec)
previous_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True  # Functional tests must not mutate the release payload.
    spec.loader.exec_module(devkit)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting


class MCPServerDevTests(unittest.TestCase):
    def test_native_host_display_metadata(self):
        manifest = json.loads((SCRIPT.parents[1] / "manifest.json").read_text(encoding="utf-8"))
        # Native list/detail cards read these fields, not name/description.
        # The frontend accesses value.zh/value.en without string normalization.
        for field in ("display_name", "display_description"):
            self.assertIsInstance(manifest.get(field), dict, field)
            for language in ("zh", "en"):
                with self.subTest(field=field, language=language):
                    value = manifest[field].get(language)
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())
        self.assertEqual(manifest["version"], devkit.VERSION)

    def test_routes_reuse_builder_and_choose_specialists(self):
        for local, ui, prototype in itertools.product((False, True), repeat=3):
            with self.subTest(local=local, ui=ui, prototype=prototype):
                result = devkit.plan(dict(local_access=local, interactive_ui=ui, prototype=prototype))
                self.assertEqual(result["base_development_asset"]["id"], devkit.BUILDER_ID)
                self.assertEqual("build-mcp-app" in result["skills"], ui)
                self.assertEqual("build-mcpb" in result["skills"], local and not prototype)
                self.assertEqual(result["transport"], "stdio" if local or prototype else "streamable-http")

    def test_bad_specs_fail(self):
        for data in ([], {}, {"local_access": "false", "interactive_ui": False, "prototype": False},
                     {"local_access": 1, "interactive_ui": False, "prototype": False}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                devkit.plan(data)

    def test_generation_preserves_existing_files_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            existing = root / "existing"
            existing.mkdir()
            (existing / "valuable.txt").write_text("keep")
            with self.assertRaises(ValueError):
                devkit.scaffold("app", existing, "demo", "Tester")
            self.assertEqual((existing / "valuable.txt").read_text(), "keep")
            (root / "link").symlink_to(existing)
            with self.assertRaises(ValueError):
                devkit.scaffold("mcpb", root / "link", "demo", "Tester")

    def test_name_validation_and_generated_launch_config(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("../escape", "Bad Name", "bad;command", "a" * 65):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    devkit.scaffold("mcpb", Path(d) / "project", name, "Tester")
            target = Path(d) / "safe"
            devkit.scaffold("mcpb", target, "safe-demo", 'Tester "quoted"')
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertEqual(manifest["author"]["name"], 'Tester "quoted"')
            self.assertEqual(manifest["server"]["mcp_config"]["args"], ["${__dirname}/server.mjs"])
            self.assertTrue((target / "licenses/claude-plugins-official/LICENSE").is_file())

    def test_cli_invalid_json_and_size(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "spec.json"
            for text in ("{bad", " " * 16385):
                path.write_text(text)
                r = subprocess.run([sys.executable, str(SCRIPT), "plan", str(path)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 2)
                self.assertIn("ERROR:", r.stderr)
                self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
