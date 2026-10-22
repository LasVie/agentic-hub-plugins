"""Import/install/uninstall the native test ZIP in an isolated JiuwenSwarm home."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="JiuwenSwarm source checkout")
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-version", default="1.0.1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve()))
    with tempfile.TemporaryDirectory(prefix="learning-output-host-") as tmp:
        os.environ["JIUWENSWARM_DATA_DIR"] = tmp
        os.chdir(tmp)
        from jiuwenswarm.common import utils
        assert utils.get_user_workspace_dir().resolve() == Path(tmp).resolve()
        from jiuwenswarm.server.runtime import extension_package_manager as manager
        from openjiuwen.harness.resources.extension_loader import load_plugin_package

        imported = manager.import_plugin_package({"path": str(args.archive.resolve())})
        assert imported["id"] == "learning-output-style"
        manager.install_plugin_package(imported)
        assert manager.is_plugin_allowed(imported["id"])
        installed = manager.resolve_plugin_dir(imported["id"])
        assert installed.resolve().is_relative_to(Path(tmp).resolve())
        assert json.loads((installed / "manifest.json").read_text())["version"] == args.expected_version
        spec = load_plugin_package(installed / "manifest.json")
        assert len(spec.prompt_sections) == 1 and len(spec.skills) == 1
        manager.uninstall_plugin_package(imported)
        assert not installed.exists()
        assert not manager.is_plugin_allowed(imported["id"])
        result = {"passed": True, "checks": [
            "Real JiuwenSwarm import of native test ZIP",
            "Real install and installed-state lookup in isolated data directory",
            f"Installed version {args.expected_version} loads native prompt section and Skill",
            "Real uninstall removes package and installed state"
        ], "scope": "Temporary data directory only; no active user installation modified"}
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
