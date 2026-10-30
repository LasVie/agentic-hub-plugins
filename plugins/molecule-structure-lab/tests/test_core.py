"""真实离线引擎、原生运行边界与插件独立服务的功能测试。"""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

PAYLOAD = Path(__file__).resolve().parents[1] / "molecule-structure-lab"
SPEC = importlib.util.spec_from_file_location("molecule_test_runtime", PAYLOAD / "tools/runtime.py")
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class EngineTests(unittest.TestCase):
    def test_aspirin_descriptors_match_and_highlight(self):
        r = runtime.analyze({"smiles": "CC(=O)Oc1ccccc1C(=O)O", "smarts": "c1ccccc1"})
        self.assertTrue(r["ok"], r)
        self.assertEqual((r["version"], r["rdkit_version"]), ("1.0.1", "2026.09.1"))
        self.assertEqual(r["canonical_smiles"], "CC(=O)Oc1ccccc1C(=O)O")
        self.assertEqual((r["atom_count"], r["bond_count"]), (13, 13))
        for key, expected in {"amw": 180.159, "exactmw": 180.042258736, "tpsa": 63.6,
                              "NumHBA": 3, "NumHBD": 1, "NumRings": 1, "NumRotatableBonds": 2}.items():
            self.assertAlmostEqual(r["descriptors"][key], expected, places=6)
        self.assertEqual(r["match"]["atoms"], [4, 5, 6, 7, 8, 9])
        self.assertEqual(r["match"]["bonds"], [4, 5, 6, 7, 8, 12])
        self.assertEqual(r["match"]["scope"], "first_match")
        self.assertIn("第一个", r["match"]["message"])
        element = ET.fromstring(r["svg"])
        self.assertEqual(element.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn("atom-4", r["svg"])
        self.assertNotEqual(r["svg"], runtime.analyze({"smiles": r["input"]["smiles"]})["svg"])

    def test_changed_molecule_negative_and_no_query_are_distinct(self):
        r = runtime.analyze({"smiles": " CCO ", "smarts": "c1ccccc1"})
        self.assertTrue(r["ok"], r)
        self.assertAlmostEqual(r["descriptors"]["amw"], 46.069)
        self.assertAlmostEqual(r["descriptors"]["tpsa"], 20.23)
        self.assertTrue(r["match"]["query_supplied"])
        self.assertFalse(r["match"]["matched"])
        self.assertEqual(r["match"]["atoms"], [])
        n = runtime.analyze({"smiles": "CCO"})
        self.assertTrue(n["ok"], n)
        self.assertFalse(n["match"]["query_supplied"])
        self.assertNotEqual(n["match"]["message"], r["match"]["message"])

    def test_first_match_not_exhaustive_count(self):
        r = runtime.analyze({"smiles": "c1ccccc1c2ccccc2", "smarts": "c1ccccc1"})
        self.assertTrue(r["ok"], r)
        self.assertEqual(len(r["match"]["atoms"]), 6)
        self.assertEqual(r["descriptors"]["NumRings"], 2)
        self.assertNotIn("count", r["match"])

    def test_dummy_molecules_rejected_but_wildcard_queries_work(self):
        for smiles in ["C*", "[1*]"]:
            with self.subTest(smiles=smiles):
                result = runtime.analyze({"smiles": smiles})
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "unsupported_atom")
                self.assertIn("虚拟原子", result["error"]["message"])
                self.assertNotIn("descriptors", result)
                self.assertNotIn("svg", result)
        query = runtime.analyze({"smiles": "CCO", "smarts": "*"})
        self.assertTrue(query["ok"], query)
        self.assertTrue(query["match"]["matched"])
        self.assertEqual(query["match"]["atoms"], [0])
        self.assertAlmostEqual(query["descriptors"]["amw"], 46.069)

    def test_hydrogen_normalization_reports_parsed_graph(self):
        result = runtime.analyze({"smiles": "[H]O[H]", "smarts": "[H]"})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["canonical_smiles"], "O")
        self.assertEqual(result["atom_count"], 1)
        self.assertFalse(result["match"]["matched"])
        self.assertAlmostEqual(result["descriptors"]["amw"], 18.015)
        self.assertTrue(any("普通显式氢" in item for item in result["limitations"]))

    def test_unspecified_molecule_bonds_rejected_but_query_bonds_work(self):
        rejected = runtime.analyze({"smiles": "C~C"})
        self.assertFalse(rejected["ok"], rejected)
        self.assertEqual(rejected["error"]["code"], "unsupported_bond")
        self.assertIn("未指定类型的键", rejected["error"]["message"])
        self.assertNotIn("descriptors", rejected)
        self.assertNotIn("svg", rejected)
        for smiles, expected_mass in [("CC", 30.07), ("C=C", 28.054)]:
            with self.subTest(smiles=smiles):
                query = runtime.analyze({"smiles": smiles, "smarts": "C~C"})
                self.assertTrue(query["ok"], query)
                self.assertTrue(query["match"]["matched"])
                self.assertEqual(query["match"]["atoms"], [0, 1])
                self.assertEqual(query["match"]["bonds"], [0])
                self.assertAlmostEqual(query["descriptors"]["amw"], expected_mass)

    def test_invalid_notations_and_chinese_fail_closed(self):
        for inputs, expected in [({"smiles": "C1CC"}, "invalid_smiles"),
                                 ({"smiles": ""}, "empty_smiles"),
                                 ({"smiles": "乙醇"}, "unsupported_notation"),
                                 ({"smiles": "CCO title"}, "unsupported_notation"),
                                 ({"smiles": "CCO\nC"}, "unsupported_notation"),
                                 ({"smiles": "C>>O"}, "unsupported_notation"),
                                 ({"smiles": "CCO", "smarts": "["}, "invalid_smarts"),
                                 ({"smiles": "CCO", "smarts": "中文"}, "unsupported_notation"),
                                 ({"smiles": "C" * 1025}, "input_too_large"),
                                 ({"smiles": "C" * 257}, "molecule_too_large"),
                                 ({"smiles": "CCO", "smarts": "C" * 129}, "query_too_large"),
                                 ({"smiles": "C", "extra": "ignore"}, "invalid_input")]:
            with self.subTest(inputs=str(inputs)[:80]):
                result = runtime.analyze(inputs)
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], expected, result)
                self.assertTrue(any("\u4e00" <= ch <= "\u9fff" for ch in result["error"]["message"]))
                self.assertNotIn("svg", result)

    def test_fixed_bridge_without_fetch_or_remote_import(self):
        node = runtime.node_executable()
        script = """
const fs=require('fs'),path=require('path');
const root=process.argv[1]; let fetches=0;
global.fetch=()=>{fetches++;throw Error('forbidden');};
const init=require(path.join(root,'vendor/rdkit/RDKit_minimal.js'));
init({wasmBinary:fs.readFileSync(path.join(root,'vendor/rdkit/RDKit_minimal.wasm')),
 print:()=>{},printErr:()=>{}}).then(rd=>{
 const result=require(path.join(root,'engine/core.js')).analyze(rd,{smiles:'CCO'});
 console.log(JSON.stringify({ok:result.ok,fetches,version:result.rdkit_version}));
});
"""
        process = subprocess.run([node, "-e", script, str(PAYLOAD)], capture_output=True, timeout=12, check=True)
        self.assertEqual(json.loads(process.stdout), {"ok": True, "fetches": 0, "version": "2026.09.1"})

    def test_missing_node_is_structured_and_browser_independent(self):
        with patch.dict(os.environ, {"MOLECULE_WORKBENCH_NODE": "/does/not/exist"}):
            r = runtime.analyze({"smiles": "CCO"})
            self.assertEqual(r["error"]["code"], "node_unavailable")


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="molecule-core-test-", dir="/private/tmp" if Path("/private/tmp").exists() else None)
        self.workspace = str(Path(self.temp.name).resolve())

    def tearDown(self):
        runtime.workbench({"action": "stop", "workspace": self.workspace, "confirmed": True})
        self.temp.cleanup()

    def test_status_no_write_and_confirmation_gate(self):
        r = runtime.workbench({"action": "status", "workspace": self.workspace})
        self.assertTrue(r["ok"])
        self.assertFalse(r["running"])
        self.assertEqual(list(Path(self.workspace).iterdir()), [])
        for action in ["start", "stop"]:
            r = runtime.workbench({"action": action, "workspace": self.workspace, "confirmed": False})
            self.assertEqual(r["error"]["code"], "confirmation_required")
        self.assertEqual(list(Path(self.workspace).iterdir()), [])

    def test_bad_workspace_and_runtime_symlink(self):
        r = runtime.workbench({"action": "status", "workspace": "relative"})
        self.assertEqual(r["error"]["code"], "invalid_workspace")
        link = Path(self.workspace) / "linked"
        link.symlink_to(self.workspace, target_is_directory=True)
        r = runtime.workbench({"action": "start", "workspace": str(link), "confirmed": True})
        self.assertEqual(r["error"]["code"], "invalid_workspace")
        target = Path(self.workspace) / runtime.RUNTIME_NAME
        target.symlink_to(self.workspace, target_is_directory=True)
        r = runtime.workbench({"action": "start", "workspace": self.workspace, "confirmed": True})
        self.assertEqual(r["error"]["code"], "invalid_runtime")

    def test_lifecycle_routing_and_other_services_protection(self):
        result = runtime.workbench({"action": "start", "workspace": self.workspace, "confirmed": True})
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["running"])
        again = runtime.workbench({"action": "start", "workspace": self.workspace, "confirmed": True})
        self.assertEqual(result["url"], again["url"])
        parsed = urlsplit(result["url"])
        prefix = parsed.path.rsplit("/web/", 1)[0]
        state = runtime.read_state(Path(self.workspace) / runtime.RUNTIME_NAME)
        self.assertEqual(parsed.hostname, "127.0.0.1")
        self.assertNotIn("pid", state)

        def request(path, headers=None, method="GET"):
            connection = http.client.HTTPConnection("127.0.0.1", parsed.port, timeout=3)
            try:
                connection.request(method, path, headers=headers or {})
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                connection.close()

        status, headers, body = request(prefix + "/engine/core.js")
        self.assertEqual(status, 200)
        self.assertIn("text/javascript", headers["Content-Type"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertNotIn("'unsafe-eval'", headers["Content-Security-Policy"])
        self.assertEqual(body, (PAYLOAD / "engine/core.js").read_bytes())
        status, headers, body = request(prefix + "/web/index.html")
        self.assertEqual(status, 200)
        self.assertNotIn("'unsafe-eval'", headers["Content-Security-Policy"])
        status, headers, body = request(prefix + "/web/worker.js")
        self.assertEqual(status, 200)
        self.assertIn("script-src 'self' 'unsafe-eval'", headers["Content-Security-Policy"])
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
        status, headers, body = request(prefix + "/vendor/rdkit/RDKit_minimal.wasm")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/wasm")
        self.assertTrue(body.startswith(b"\x00asm"))
        for route in ["/", "/bad-token/engine/core.js", prefix + "/../settings.json",
                      prefix + "/%2e%2e/settings.json", prefix + "/tools/runtime.py",
                      prefix + "/vendor/", prefix + "/engine/core.js?x=1"]:
            self.assertEqual(request(route)[0], 404, route)
        self.assertEqual(request(prefix + "/__health", {"Host": "evil.example"})[0], 403)
        self.assertEqual(request(prefix + "/__health", {"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(request(prefix + "/__health", {"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(request(prefix + "/__stop")[0], 404)
        self.assertTrue(runtime.contact(state))
        fake = dict(state, token="0" * 64)
        self.assertFalse(runtime.contact(fake, stop=True))
        self.assertTrue(runtime.contact(state))
        stopped = runtime.workbench({"action": "stop", "workspace": self.workspace, "confirmed": True})
        self.assertTrue(stopped["ok"])
        self.assertFalse(stopped["running"])
        for _ in range(20):
            if not runtime.contact(state):
                break
            time.sleep(.05)
        self.assertFalse(runtime.contact(state))

    def test_user_clicked_entry_navigation_only(self):
        started = runtime.workbench({"action": "start", "workspace": self.workspace, "confirmed": True})
        self.assertTrue(started["ok"], started)
        url = urlsplit(started["url"])
        prefix = url.path.removesuffix("web/index.html")

        def request(path=url.path, headers=None, method="GET"):
            connection = http.client.HTTPConnection(url.hostname, url.port, timeout=3)
            try:
                connection.request(method, path, headers=headers or {})
                response = connection.getresponse()
                return response.status, response.read()
            finally:
                connection.close()

        # A real click from WorkSwarm's different port is same-site, not same-origin.
        # A hostname change (localhost -> 127.0.0.1) may instead be cross-site.
        for site in ("same-site", "cross-site"):
            navigation = {"Sec-Fetch-Site": site, "Sec-Fetch-Mode": "navigate",
                          "Sec-Fetch-Dest": "document", "Sec-Fetch-User": "?1"}
            with self.subTest(site=site):
                status, body = request(headers=navigation)
                self.assertEqual(status, 200)
                self.assertIn("离线分子结构工作台".encode(), body)
                # The exception never admits fetches, scripts, frames, automatic
                # navigation, POST/HEAD, service control, or a supplied foreign Origin.
                for changes in ({"Sec-Fetch-Mode": "cors"}, {"Sec-Fetch-Dest": "iframe"},
                                {"Sec-Fetch-Dest": "script"}, {"Sec-Fetch-User": "?0"},
                                {"Origin": "http://127.0.0.1:6392"}, {"Host": "evil.example"}):
                    self.assertEqual(request(headers={**navigation, **changes})[0], 403, changes)
                without_user = {k: v for k, v in navigation.items() if k != "Sec-Fetch-User"}
                self.assertEqual(request(headers=without_user)[0], 403)
                for route in ("__health", "__stop", "web/app.js", "web/worker.js", "vendor/rdkit/RDKit_minimal.wasm"):
                    self.assertEqual(request(prefix + route, navigation)[0], 403, route)
                for method in ("POST", "HEAD"):
                    self.assertEqual(request(headers=navigation, method=method)[0], 403)
                for invalid in ("/wrong-token/web/index.html", url.path + "?x=1", prefix + "../web/index.html"):
                    self.assertNotEqual(request(invalid, navigation)[0], 200, invalid)
        self.assertEqual(request()[0], 200)  # Native clients / address-bar navigation.
        self.assertEqual(request(prefix + "web/app.js", {"Sec-Fetch-Site": "same-origin"})[0], 200)
        self.assertTrue(runtime.workbench({"action": "status", "workspace": self.workspace})["running"])

    def test_foreign_state_is_preserved(self):
        directory = Path(self.workspace) / runtime.RUNTIME_NAME
        directory.mkdir(mode=0o700)
        state_path = directory / "server.json"
        lock_path = directory / "server.lock"
        lock_path.touch(mode=0o600)
        # A valid record from another installation must remain foreign even when
        # the payload/version match. Manual-test workspaces cannot be shared
        # between a standalone installation and WorkSwarm's installed tool root.
        records = {
            "malformed": b'{"pid":42,"port":1234}',
            "other_installation": json.dumps({
                "version": runtime.VERSION, "port": 1234,
                "token": "0" * 64, "instance": "1" * 32,
                "root": str(runtime.ROOT.parent / "other-installation" / runtime.ROOT.name),
            }).encode(),
        }
        for record_kind, original in records.items():
            state_path.write_bytes(original)
            state_path.chmod(0o600)
            before = {p.name: (p.read_bytes(), p.stat().st_ino, p.stat().st_mode)
                      for p in directory.iterdir()}
            for action in ("status", "start", "stop"):
                with self.subTest(record=record_kind, action=action):
                    with patch.object(runtime, "contact") as contact, \
                            patch.object(runtime.subprocess, "Popen") as spawn, \
                            patch.object(runtime, "finish_child") as finish:
                        result = runtime.workbench({"action": action, "workspace": self.workspace,
                                                    "confirmed": True})
                        self.assertFalse(result["ok"])
                        self.assertEqual(result["error"]["code"], "invalid_runtime")
                        contact.assert_not_called()
                        spawn.assert_not_called()
                        finish.assert_not_called()
                    after = {p.name: (p.read_bytes(), p.stat().st_ino, p.stat().st_mode)
                             for p in directory.iterdir()}
                    self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
