"""Exercise real host discovery and loading without a model call or installation."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from openjiuwen.harness.resources import load_plugin_package, resolve_plugin_parts
from openjiuwen.harness.schema.build_context import BuildContext
from jiuwenswarm.server.runtime import extension_package_manager as host


def main() -> None:
    native_zip = Path(sys.argv[1]).resolve(strict=True)
    expected_skill_sha = "ed4dc434de1fd7c67cd244213a9d590064f245e4e169a58bf53e6eeb48e407b1"
    with tempfile.TemporaryDirectory(prefix="code-simplifier-load-") as scratch:
        extracted = Path(scratch) / "native"
        with zipfile.ZipFile(native_zip) as archive:
            archive.extractall(extracted)
        root = host._find_package_root(extracted, "plugin")
        host._validate_package_manifest(root, "plugin", "plugin")
        host._require_import_readme(root, "plugin")
        manifest = json.loads((root / "manifest.json").read_text())
        assert manifest["id"] == "code-simplifier" and manifest["version"] == "1.0.1"
        print("PASS: real host local-import discovery, manifest and README checks")

        spec = load_plugin_package(root / "manifest.json")
        assert spec.id == "code-simplifier"
        parts = resolve_plugin_parts(spec, BuildContext(language="en"))
        assert len(parts.skills) == 1 and parts.skills[0].mode == "all"
        skill = Path(parts.skills[0].directory) / "SKILL.md"
        assert hashlib.sha256(skill.read_bytes()).hexdigest() == expected_skill_sha
        assert not any((parts.tools, parts.mcps, parts.rails, parts.subagents))
        print("PASS: real openJiuwen resolver loads one relocated, unchanged skill")

        cards = host._map_skills(root, manifest)
        assert len(cards) == 1 and cards[0]["id"] == "code-simplifier"
        assert cards[0]["displayDescription"]["en"].strip()
        print("PASS: real host skill card discovers name and description")

        broken = Path(scratch) / "broken"
        shutil.copytree(root, broken)
        shutil.rmtree(broken / "skills")
        try:
            broken_spec = load_plugin_package(broken / "manifest.json")
            resolve_plugin_parts(broken_spec, BuildContext(language="en"))
        except (ValueError, FileNotFoundError):
            print("PASS: real loader rejects missing declared skill")
        else:
            raise AssertionError("Missing skill was accepted")

    print("RESULT: 4 host loading/discovery checks passed; no model edit or UI installation performed")


if __name__ == "__main__":
    main()
