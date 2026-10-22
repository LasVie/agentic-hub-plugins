"""Exercise the actual openJiuwen Plugin loader on an extracted package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from openjiuwen.harness.resources.extension_loader import load_plugin_package
from openjiuwen.harness.schema.extension_spec import validate_plugin_paths


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(payload: Path) -> list[str]:
    checks = []
    spec = load_plugin_package(payload / "manifest.json")
    validate_plugin_paths(spec)
    assert spec.id == "learning-output-style"
    assert len(spec.prompt_sections) == 1
    assert len(spec.skills) == 1
    assert not spec.tools and not spec.mcps and not spec.rails
    checks.append("Native Plugin loader accepts the real manifest and resolves its Skill path")

    prompt_path = payload / "prompt_sections/learning-output-style.md"
    text = prompt_path.read_text(encoding="utf-8")
    assert spec.prompt_sections[0].content == {"cn": text, "en": text}
    assert spec.prompt_sections[0].priority == 100
    original = text.split("-->\n\n", 1)[1].encode()
    source = json.loads((payload / "SOURCE.json").read_text())
    assert hashlib.sha256(original).hexdigest() == source["prompt_sha256"]
    assert digest(prompt_path) == source["packaged_prompt_sha256"]
    assert "5-10 lines" in text and "★ Insight" in text
    assert "TODO" in text and "Don't request contributions" in text
    checks.append("Active prompt resolves at priority 100 and preserves every original teaching-text byte")

    skill = Path(spec.skills[0].dir)
    assert skill.is_relative_to(payload.resolve())
    assert (skill / "SKILL.md").is_file()
    checks.append("Declared contribution Skill resolves inside the relocated payload")

    assert digest(payload / "LICENSE") == digest(payload / "licenses/claude-plugins-official/LICENSE")
    for path in [prompt_path, skill / "SKILL.md"]:
        assert "2026-10-22" in path.read_text() and "Anthropic" in path.read_text()
    assert not list(payload.rglob("*.sh"))
    checks.append("Complete license and file-level attribution ship without executable upstream hooks")

    for case in ["missing-prompt", "missing-skill", "wrong-type", "escaping-prompt"]:
        with tempfile.TemporaryDirectory(prefix="learning-output-negative-") as tmp:
            broken = Path(tmp) / "plugin"
            shutil.copytree(payload, broken)
            manifest_path = broken / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            if case == "missing-prompt":
                (broken / "prompt_sections/learning-output-style.md").unlink()
            elif case == "missing-skill":
                (broken / "skills/learning-contribution/SKILL.md").unlink()
            elif case == "wrong-type":
                manifest["package_type"] = "agent_template"
            else:
                manifest["prompt_sections"][0]["file"] = "../outside.md"
                (broken.parent / "outside.md").write_text("outside package")
            manifest_path.write_text(json.dumps(manifest))
            try:
                load_plugin_package(manifest_path)
            except (ValueError, FileNotFoundError):
                checks.append("Native loader rejects " + case)
            else:
                raise AssertionError("Native loader accepted " + case)
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = validate(args.payload.resolve())
    record = {"passed": True, "check_count": len(results), "checks": results}
    if args.output:
        args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
