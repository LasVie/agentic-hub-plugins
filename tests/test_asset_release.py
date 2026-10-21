import importlib.util
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("asset_release", Path(__file__).parents[1] / "tools/asset_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class PackagingContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def fixture(self, kind="skill"):
        asset = self.base / kind
        shutil.copytree(release.ROOT / "templates" / kind, asset)
        c = release.read_json(asset / "asset.json")
        c.update(publisher="fixture-author", display_name="Packaging fixture", description="A synthetic fixture for archive contract tests.")
        (asset / "asset.json").write_text(json.dumps(c))
        (asset / "SOURCE_REVIEW.md").write_text("Synthetic test fixture written for archive validation; no upstream implementation copied.")
        (asset / "NATIVE_DESIGN.md").write_text("Synthetic instruction/manifest fixture; not a real plugin or Hub submission.")
        (asset / "TEST_REPORT.md").write_text("Synthetic contract test fixture. These checks do not assert any production plugin functionality.")
        return asset

    def test_skill_wrapper_has_skill_entry_and_reproducible_bytes(self):
        asset = self.fixture()
        p = release.pack(asset, self.base / "out")
        first = p.read_bytes()
        self.assertEqual(first, release.pack(asset, self.base / "out").read_bytes())
        c, payload = release.inspect_zip(first)
        self.assertEqual(c["runtime"]["type"], "skill")
        self.assertIn("SKILL.md", payload)
        with zipfile.ZipFile(io.BytesIO(first)) as z:
            self.assertIn("example-skill/plugin.yaml", z.namelist())
            self.assertIn("example-skill/example-skill/SKILL.md", z.namelist())

    def test_plugin_uses_manifest_and_matching_version(self):
        asset = self.fixture("plugin")
        p = release.pack(asset, self.base / "out")
        c, payload = release.inspect_zip(p.read_bytes())
        self.assertEqual(c["runtime"]["type"], "agent-plugin")
        self.assertIn("manifest.json", payload)
        m = asset / "example-plugin/manifest.json"
        data = release.read_json(m)
        data["version"] = "9.0.0"
        m.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            release.check_asset(asset)

    def test_declared_missing_skill_rejected(self):
        asset = self.fixture("plugin")
        shutil.rmtree(asset / "example-plugin/skills/example-action")
        with self.assertRaisesRegex(ValueError, "missing"):
            release.check_asset(asset)

    def test_declared_traversal_rejected(self):
        asset = self.fixture("plugin")
        f = asset / "example-plugin/manifest.json"
        m = release.read_json(f)
        m["skills"][0]["dir"] = "../other"
        f.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            release.check_asset(asset)

    def test_unknown_permission_cannot_be_ported(self):
        asset = self.fixture()
        f = asset / "provenance.json"
        p = release.read_json(f)
        p.update(mode="ported", permission_status="unknown")
        f.write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError, "unknown permission"):
            release.check_asset(asset)

    def test_native_cannot_claim_copied_path(self):
        asset = self.fixture()
        f = asset / "provenance.json"
        p = release.read_json(f)
        p["reused_paths"] = ["SKILL.md"]
        f.write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError, "copied implementation"):
            release.check_asset(asset)

    def test_swarm_duplicate_role_ids_rejected(self):
        asset = self.fixture()
        c = release.read_json(asset / "asset.json")
        c["type"] = "swarmskill"
        (asset / "asset.json").write_text(json.dumps(c))
        (asset / "example-skill/SKILL.md").write_text('---\nname: example-skill\ndescription: synthetic\nkind: swarm-skill\nroles:\n  - id: a\n  - id: a\n---\n')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            release.check_asset(asset)

    def test_expert_fields_rejected_in_plugin(self):
        asset = self.fixture("plugin")
        f = asset / "example-plugin/manifest.json"
        m = release.read_json(f)
        m["persona"] = {"dir": "persona"}
        f.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, "expert-only"):
            release.check_asset(asset)

    def test_archive_traversal_rejected_without_extracting(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("../escape", "x")
        with self.assertRaisesRegex(ValueError, "unsafe ZIP"):
            release.inspect_zip(buf.getvalue())

    def test_existing_version_cannot_silently_change(self):
        asset = self.fixture()
        release.pack(asset, self.base / "out")
        f = asset / "example-skill/SKILL.md"
        f.write_text(f.read_text() + "\nA changed instruction.\n")
        with self.assertRaisesRegex(ValueError, "bump version"):
            release.pack(asset, self.base / "out")

    def test_scan_has_no_automatic_permission_grant(self):
        f = self.base / "LICENSE"
        f.write_text("Apache License Version 2.0")
        result = release.audit_upstream(self.base)
        self.assertEqual(result["permission_status"], "unknown")
        self.assertTrue(result["automatic_detection_only"])
        self.assertEqual(len(result["evidence"]), 1)

    def test_ported_permission_record_checks_actual_evidence_bytes(self):
        asset = self.fixture()
        payload = asset / "example-skill"
        evidence = payload / "LICENSE"
        evidence.write_text("Synthetic test-only permission evidence, not a production license.")
        p = release.read_json(asset / "provenance.json")
        p.update(mode="ported", permission_status="verified", reused_paths=["SKILL.md"], sources=[{"url": "https://example.com/test-fixture", "revision": "test-only-fixed-revision", "license_expression": "LicenseRef-TestOnly", "license_evidence": [{"path": "LICENSE", "sha256": "wrong"}]}])
        (asset / "provenance.json").write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            release.check_asset(asset)
        p["sources"][0]["license_evidence"][0]["sha256"] = release.sha(evidence.read_bytes())
        (asset / "provenance.json").write_text(json.dumps(p))
        release.check_asset(asset)

    def test_payload_symlinks_are_rejected(self):
        asset = self.fixture()
        outside = self.base / "outside.txt"
        outside.write_text("not a payload file")
        (asset / "example-skill/linked.txt").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            release.check_asset(asset)

    def test_pack_requires_a_functional_test_report(self):
        asset = self.fixture()
        (asset / "TEST_REPORT.md").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            release.pack(asset, self.base / "out")

    def test_main_source_needs_a_corresponding_release_zip(self):
        asset = self.fixture()
        root = self.base / "repo"
        target = root / "skills/example-skill"
        target.parent.mkdir(parents=True)
        shutil.move(str(asset), target)
        with self.assertRaisesRegex(ValueError, "requires a tested release ZIP"):
            release.check_repo(root)


if __name__ == "__main__":
    unittest.main()
