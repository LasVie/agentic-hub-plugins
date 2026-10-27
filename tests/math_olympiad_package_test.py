"""Package, localization and script checks for the math-olympiad plugin ZIP.

Usage: python tests/math_olympiad_package_test.py <math-olympiad-x.y.z.zip>
Never runs model calls; scripts are exercised with a PATH that hides LaTeX.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

SLUG = "math-olympiad"
EXPECTED = {
    "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md", "manifest.json",
    "licenses/claude-plugins-official/LICENSE",
    "skills/math-olympiad/SKILL.md",
    "skills/math-olympiad/scripts/check_latex.sh",
    "skills/math-olympiad/scripts/compile_pdf.sh",
    *(f"skills/math-olympiad/references/{n}.md" for n in (
        "adversarial_prompts", "attempt_agent", "known_constructions",
        "presentation_prompts", "solver_heuristics", "verifier_patterns")),
}
ADAPTED = [p for p in EXPECTED if p.startswith("skills/")]
LICENSE_SHA = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
CJK = re.compile(r"[一-鿿]")


def check(ok: bool, msg: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL: {msg}")
    print(f"PASS: {msg}")


def main() -> None:
    zpath = Path(sys.argv[1]).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="math-olympiad-test-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(zpath) as z:
            check(z.testzip() is None, "ZIP integrity")
            names = z.namelist()
            check(all(n.startswith(f"{SLUG}/") for n in names), "single outer directory")
            z.extractall(root)
        outer = root / SLUG
        check(sorted(p.name for p in outer.iterdir()) == ["math-olympiad", "plugin.yaml"],
              "outer directory holds only plugin.yaml and inner payload")
        wrapper = yaml.safe_load((outer / "plugin.yaml").read_text(encoding="utf-8"))
        check(wrapper["name"] == SLUG and wrapper["runtime"]["type"] == "agent-plugin", "wrapper identity/runtime")

        payload = outer / SLUG
        files = {p.relative_to(payload).as_posix() for p in payload.rglob("*") if p.is_file()}
        check(files == EXPECTED, f"payload inventory is exactly {len(EXPECTED)} expected files")

        manifest = json.loads((payload / "manifest.json").read_text(encoding="utf-8"))
        check(manifest["id"] == SLUG and manifest["package_type"] == "plugin"
              and manifest["version"] == wrapper["version"], "manifest identity/version")
        check(not ({"persona", "agent_card", "model", "subagents", "memories", "rubrics"} & manifest.keys()),
              "manifest has no forbidden root keys")
        check(manifest["name"] == "奥数竞赛证明与对抗验证" == manifest["display_name"]["zh"], "Chinese display name")
        for entry in manifest["skills"]:
            check((payload / entry["dir"] / "SKILL.md").is_file(), f"declared skill exists: {entry['dir']}")

        for rel in (payload / "LICENSE", payload / "licenses/claude-plugins-official/LICENSE"):
            check(hashlib.sha256(rel.read_bytes()).hexdigest() == LICENSE_SHA, f"unchanged Apache-2.0 text: {rel.name}")

        for rel in sorted(EXPECTED - {"LICENSE", "licenses/claude-plugins-official/LICENSE"}):
            data = (payload / rel).read_bytes()
            text = data.decode("utf-8")
            check(not data.startswith(b"\xef\xbb\xbf"), f"UTF-8 without BOM: {rel}")
            if rel != "THIRD_PARTY_NOTICES.md":
                check(len(CJK.findall(text)) > 50, f"Chinese content present: {rel}")
        for rel in ADAPTED:
            head = (payload / rel).read_text(encoding="utf-8")[:1200]
            check("改编自 Anthropic" in head and "修改说明" in head and "d4226d0629" in head,
                  f"Apache change notice at top: {rel}")

        skill = (payload / "skills/math-olympiad/SKILL.md").read_text(encoding="utf-8")
        fm = yaml.safe_load(skill.split("---")[1])
        check(fm["name"] == SLUG and fm["version"] == manifest["version"] and CJK.search(fm["description"]),
              "skill frontmatter name/version/Chinese description")
        for ref in re.findall(r"`(references/[\w_]+\.md|scripts/[\w_]+\.sh)`", skill):
            check((payload / "skills/math-olympiad" / ref).is_file(), f"SKILL.md reference resolves: {ref}")
        for phrase in ("默认用简体中文", "没有可信的解答", "由同一智能体分阶段验证", "禁止联网", "4 轮 HOLDS 才确认", "相对于**本 SKILL.md 所在目录**", "plugin_packages/<来源>/math-olympiad/skills/math-olympiad/"):
            check(phrase in skill, f"SKILL.md key instruction: {phrase}")
        check(not re.search(r"\b(subagent|Agent tool|WebFetch|opts\.label)\b", skill), "no Claude-only tool references in SKILL.md")

        scripts = payload / "skills/math-olympiad/scripts"
        for s in scripts.iterdir():
            check(subprocess.run(["bash", "-n", str(s)]).returncode == 0, f"bash syntax: {s.name}")
        bare = {**os.environ, "PATH": "/usr/bin:/bin"}
        if not any(Path(d, "xelatex").exists() for d in ("/usr/bin", "/bin")):
            r = subprocess.run(["bash", str(scripts / "check_latex.sh")], env=bare)
            check(r.returncode == 1, "check_latex.sh reports missing xelatex with exit 1")
            body = root / "正文.tex"
            body.write_text("\\begin{theorem}对任意正整数 $n$，$n^2\\ge n$。\\end{theorem}\n", encoding="utf-8")
            out = root / "out"
            r = subprocess.run(["bash", str(scripts / "compile_pdf.sh"), str(body), str(out)],
                               env=bare, capture_output=True, text=True)
            check(r.returncode == 1 and "未找到 xelatex" in r.stderr, "compile_pdf.sh gives Chinese error without xelatex")
            full = (out / "正文_full.tex").read_text(encoding="utf-8")
            check("{ctexart}" in full and "{定理}" in full and "n^2" in full and full.rstrip().endswith("\\end{document}"),
                  "compile_pdf.sh writes a complete ctexart document with the Chinese body")
        r = subprocess.run(["bash", str(scripts / "compile_pdf.sh")], capture_output=True, text=True)
        check(r.returncode == 2 and "用法" in r.stderr, "compile_pdf.sh usage error in Chinese")
    print("ALL PASS")


if __name__ == "__main__":
    main()
