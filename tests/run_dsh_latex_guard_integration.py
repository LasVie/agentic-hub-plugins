#!/usr/bin/env python3
"""Functional tests for the native dsh-latex-guard WorkSwarm port."""
from __future__ import annotations

import asyncio
import importlib.util
import tempfile
from pathlib import Path
from unittest import mock


TOOL_FILE = Path(__file__).parents[1] / "plugins/dsh-latex-guard/dsh-latex-guard/tools/latex_guard.py"
SPEC = importlib.util.spec_from_file_location("latex_guard", TOOL_FILE)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="latex-guard-test-") as raw:
        root = Path(raw)
        bib = root / "main.bib"
        tex = root / "main.tex"
        bib.write_text(
            "@article{known,\n  title={Known paper},\n  doi={10.1234/example}\n}\n\n"
            "@article{known,\n  title={Duplicate}\n}\n\n"
            "@book{unused,\n  title={Unused},\n  publisher={Press},\n  year={2024},\n  editor={Editor}\n}\n",
            encoding="utf-8",
        )
        tex.write_text("\\documentclass{article}\n\\begin{document}\\citep{known,missing}\\end{document}\n", encoding="utf-8")

        audit = await guard.CiteAuditTool().invoke({"bib_path": str(bib), "tex_paths": [str(tex)]})
        assert audit == {"ok": True, "missing_in_bib": ["missing"], "uncited": ["unused"]}, audit

        lint = await guard.BibLintTool().invoke({"bib_path": str(bib), "write": False})
        assert lint["ok"] and not lint["written"]
        assert {item["kind"] for item in lint["issues"]} == {"duplicate-key", "missing-field"}
        assert bib.read_text(encoding="utf-8").count("@article") == 2

        lint_write = await guard.BibLintTool().invoke({"bib_path": str(bib), "write": True})
        assert lint_write["ok"] and lint_write["written"]
        assert bib.read_text(encoding="utf-8").count("@article") == 1

        incomplete = root / "broken.bib"
        incomplete.write_text("@article{broken,\n title={Never closes}\n", encoding="utf-8")
        refused = await guard.BibLintTool().invoke({"bib_path": str(incomplete), "write": True})
        assert not refused["ok"] and refused["error"]["code"] == "INCOMPLETE_PARSE"

        crossref = {
            "message": {
                "title": ["Known paper"],
                "author": [{"family": "Doe", "given": "Jane"}],
                "container-title": ["Journal"],
                "published": {"date-parts": [[2025]]},
                "type": "journal-article",
                "DOI": "10.1234/EXAMPLE",
            }
        }
        with mock.patch.object(guard, "_crossref_json", return_value=crossref):
            fill = await guard.BibFillTool().invoke({"bib_path": str(bib), "write": False})
        assert fill["ok"] and fill["filled"] == ["known"] and not fill["written"], fill
        assert "author = {Doe, Jane}" in fill["fixed"]

        with mock.patch.object(guard.shutil, "which", return_value=None):
            check = await guard.LatexCheckTool().invoke({"project_dir": str(root), "entry": "main.tex", "engine": "auto"})
        assert check["ok"] and check["status"] == "skipped" and check["missing_citations"] == ["missing"], check

        outside = await guard.LatexCheckTool().invoke({"project_dir": str(root), "entry": "../outside.tex"})
        assert not outside["ok"] and outside["error"]["code"] == "NOT_FOUND"

        fake = mock.Mock(return_value=mock.Mock(returncode=1, stdout="! Undefined control sequence.\nl.7 \\bad\n", stderr=""))
        with mock.patch.object(guard.shutil, "which", return_value="/fake/latexmk"), mock.patch.object(guard.subprocess, "run", fake):
            failed = await guard.LatexCheckTool().invoke({"project_dir": str(root), "entry": "main.tex"})
        assert failed["ok"] and failed["status"] == "failed" and failed["errors"][0]["line"] == 7

    print("dsh-latex-guard integration: PASS (4 tools, preview/write guard, skip/failure compile paths)")


if __name__ == "__main__":
    asyncio.run(main())
