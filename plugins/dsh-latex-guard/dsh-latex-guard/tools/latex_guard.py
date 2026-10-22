"""Native WorkSwarm port of dsh-latex-guard 0.1.3.

Modified from the MIT-licensed TypeScript implementation at revision
8046f75141ddcf70a6eae4e61f20525d892e0176. Copyright (c) 2026 Flan246.
See ../licenses/dsh-latex-guard/LICENSE for the full license.
"""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterable

from openjiuwen.core.foundation.tool import Tool, ToolCard

_ENTRY_RE = re.compile(r"@([A-Za-z]+)\s*\{")
_CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|parencite|textcite|autocite|footcite|fullcite|nocite)"
    r"(?:\[[^\]]*\]){0,2}\{([^}]*)\}"
)
_REQUIRED = {
    "article": ("author", "title", "journal", "year"),
    "book": ("title", "publisher", "year"),
    "inproceedings": ("author", "title", "booktitle", "year"),
}
_ENGINES = {"pdflatex": "-pdf", "xelatex": "-xelatex", "lualatex": "-lualatex"}


def _match_brace(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _parse_fields(body: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    index = 0
    while index < len(body):
        match = re.match(r"\s*([A-Za-z]+)\s*=\s*", body[index:])
        if not match:
            break
        name = match.group(1).lower()
        index += match.end()
        if index < len(body) and body[index] == "{":
            close = _match_brace(body, index)
            if close < 0:
                break
            value = body[index + 1:close]
            index = close + 1
        elif index < len(body) and body[index] == '"':
            close = body.find('"', index + 1)
            close = len(body) if close < 0 else close
            value = body[index + 1:close]
            index = min(close + 1, len(body))
        else:
            comma = body.find(",", index)
            end = len(body) if comma < 0 else comma
            value = body[index:end].strip()
            index = end
        fields[name] = value
        comma = body.find(",", index)
        index = len(body) if comma < 0 else comma + 1
    return fields


def parse_bib(text: str) -> list[Dict[str, Any]]:
    entries: list[Dict[str, Any]] = []
    index = 0
    while index < len(text):
        match = _ENTRY_RE.search(text, index)
        if not match:
            break
        opening = match.end() - 1
        closing = _match_brace(text, opening)
        if closing < 0:
            break
        body = text[opening + 1:closing]
        comma = body.find(",")
        key = (body if comma < 0 else body[:comma]).strip()
        entries.append({
            "type": match.group(1).lower(),
            "key": key,
            "fields": _parse_fields("" if comma < 0 else body[comma + 1:]),
        })
        index = closing + 1
    return entries


def _fully_parsed(text: str) -> bool:
    return len(_ENTRY_RE.findall(text)) <= len(parse_bib(text))


def _format_bib(entries: Iterable[Dict[str, Any]]) -> str:
    blocks = []
    for entry in entries:
        fields = ",\n".join(f"  {name} = {{{value}}}" for name, value in entry["fields"].items())
        blocks.append(f"@{entry['type']}{{{entry['key']},\n{fields}\n}}")
    return "\n\n".join(blocks) + "\n"


def lint_bib(text: str) -> Dict[str, Any]:
    issues: list[Dict[str, str]] = []
    seen: set[str] = set()
    kept = []
    for entry in parse_bib(text):
        key = entry["key"]
        if key in seen:
            issues.append({"kind": "duplicate-key", "key": key, "detail": f"duplicate entry key '{key}', later copy dropped"})
            continue
        seen.add(key)
        kept.append(entry)
        required = list(_REQUIRED.get(entry["type"], ("author", "title", "year")))
        missing = [name for name in required if not entry["fields"].get(name, "").strip()]
        if entry["type"] == "book" and not entry["fields"].get("author", "").strip() and not entry["fields"].get("editor", "").strip():
            missing.append("author/editor")
        if missing:
            issues.append({"kind": "missing-field", "key": key, "detail": "missing: " + ", ".join(missing)})
    return {"issues": issues, "fixed": _format_bib(kept)}


def cite_audit(tex_sources: Iterable[str], bib_text: str) -> Dict[str, list[str]]:
    cited: set[str] = set()
    for source in tex_sources:
        for match in _CITE_RE.finditer(source):
            cited.update(key.strip() for key in match.group(1).split(",") if key.strip())
    bib_keys = {entry["key"] for entry in parse_bib(bib_text)}
    return {"missing_in_bib": sorted(cited - bib_keys), "uncited": sorted(bib_keys - cited)}


def _detect_engine(tex: str) -> str:
    magic = re.search(r"^%+\s*!\s*TeX\s+program\s*=\s*(\S+)", tex, re.I | re.M)
    if magic:
        program = magic.group(1).lower()
        if "xetex" in program or "xelatex" in program:
            return "xelatex"
        if "luatex" in program or "lualatex" in program:
            return "lualatex"
    if re.search(r"\\RequireXeTeX|xeCJK|\{ctex", tex):
        return "xelatex"
    if "\\RequireLuaTeX" in tex:
        return "lualatex"
    body = re.sub(r"^\s*%.*$", "", tex, flags=re.M)
    return "xelatex" if re.search(r"[\u4e00-\u9fff]", body) else "pdflatex"


def _parse_log(log: str) -> Dict[str, Any]:
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    missing: set[str] = set()
    lines = log.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("! "):
            line_no = None
            for later in lines[index + 1:]:
                if later.startswith("l."):
                    number = re.match(r"l\.(\d+)", later)
                    line_no = int(number.group(1)) if number else None
                    break
            errors.append({"line": line_no, "message": line[2:].strip(), "file": None})
        elif "LaTeX Warning:" in line:
            warnings.append({"line": None, "message": line.strip(), "file": None})
            citation = re.search(r"Citation ['`]([^'`]+)['`]", line)
            if citation:
                missing.add(citation.group(1))
    return {"errors": errors, "warnings": warnings, "missing_citations": sorted(missing)}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_if_safe(path: Path, original: str, replacement: str, write: bool) -> bool:
    if not write:
        return False
    if not _fully_parsed(original):
        raise ValueError("write refused: BibTeX parser could not account for every entry marker")
    path.write_text(replacement, encoding="utf-8")
    return True


def _crossref_json(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "agentic-hub-dsh-latex-guard/1.0.0", "Accept": "application/json"})
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise LookupError("NOT_FOUND") from exc
            last_error = exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
    raise ConnectionError(str(last_error or "Crossref request failed"))


def _fields_from_work(work: Dict[str, Any]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    if work.get("title"):
        fields["title"] = str(work["title"][0])
    if work.get("author"):
        fields["author"] = " and ".join(", ".join(filter(None, (author.get("family"), author.get("given")))) for author in work["author"])
    venue = (work.get("container-title") or [None])[0]
    if venue:
        fields["journal" if work.get("type") == "journal-article" else "booktitle"] = str(venue)
    date_parts = (work.get("published") or {}).get("date-parts") or []
    if date_parts and date_parts[0]:
        fields["year"] = str(date_parts[0][0])
    for source, target in (("volume", "volume"), ("issue", "number"), ("page", "pages")):
        if work.get(source):
            fields[target] = str(work[source])
    if work.get("DOI"):
        fields["doi"] = str(work["DOI"]).lower()
    return fields


class LatexCheckTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="latex_check", name="latex_check", description="Compile-check a LaTeX entry with latexmk.", input_params={"type": "object", "properties": {"project_dir": {"type": "string"}, "entry": {"type": "string"}, "engine": {"type": "string", "enum": ["auto", "pdflatex", "xelatex", "lualatex"], "default": "auto"}}, "required": ["project_dir", "entry"]}, idempotent=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not inputs.get("project_dir") or not inputs.get("entry"):
            return {"ok": False, "error": {"code": "INVALID_INPUT", "message": "project_dir and entry are required"}}
        project = Path(str(inputs["project_dir"])).expanduser().resolve()
        entry = str(inputs["entry"])
        entry_path = (project / entry).resolve()
        if not entry_path.is_relative_to(project) or not entry_path.is_file():
            return {"ok": False, "error": {"code": "NOT_FOUND", "message": f"entry not found inside project_dir: {entry}"}}
        tex = _read_text(entry_path)
        requested = str(inputs.get("engine", "auto"))
        if requested not in {"auto", *_ENGINES}:
            return {"ok": False, "error": {"code": "INVALID_ENGINE", "message": requested}}
        engine = _detect_engine(tex) if requested == "auto" else requested
        if engine == "pdflatex":
            document_class = re.search(r"\\documentclass(?:\[[^\]]*\])?\{([^}/.]+)\}", tex)
            class_path = project / f"{document_class.group(1)}.cls" if document_class else None
            if class_path and class_path.is_file():
                engine = _detect_engine(_read_text(class_path))
        if not shutil.which("latexmk"):
            missing = []
            bib_path = project / (entry_path.stem + ".bib")
            if bib_path.is_file():
                missing = cite_audit([tex], _read_text(bib_path))["missing_in_bib"]
            return {"ok": True, "status": "skipped", "engine": engine, "errors": [], "warnings": [], "missing_citations": missing, "notice": "latexmk not found on PATH; compile check skipped. Only cite audit was performed.", "log_tail": None}
        try:
            completed = await asyncio.to_thread(subprocess.run, ["latexmk", "-interaction=nonstopmode", _ENGINES[engine], entry], cwd=str(project), capture_output=True, text=True, timeout=120, check=False)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": {"code": "LATEXMK_FAILED", "message": "latexmk timed out"}}
        log = completed.stdout + completed.stderr
        parsed = _parse_log(log)
        status = "passed" if completed.returncode == 0 and not parsed["errors"] else "failed"
        return {"ok": True, "status": status, "engine": engine, **parsed, "notice": None, "log_tail": None if status == "passed" or parsed["errors"] else "\n".join(log.splitlines()[-30:])[-2000:]}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class BibLintTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="bib_lint", name="bib_lint", description="Lint a BibTeX file and optionally write a normalized deduplicated version.", input_params={"type": "object", "properties": {"bib_path": {"type": "string"}, "write": {"type": "boolean", "default": False}}, "required": ["bib_path"]}, parallel_safe=False))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not inputs.get("bib_path"):
            return {"ok": False, "error": {"code": "INVALID_INPUT", "message": "bib_path is required"}}
        path = Path(str(inputs["bib_path"])).expanduser().resolve()
        if not path.is_file():
            return {"ok": False, "error": {"code": "NOT_FOUND", "message": str(path)}}
        original = _read_text(path)
        result = lint_bib(original)
        try:
            result["written"] = _write_if_safe(path, original, result["fixed"], bool(inputs.get("write", False)))
        except ValueError as exc:
            return {"ok": False, "error": {"code": "INCOMPLETE_PARSE", "message": str(exc)}, "issues": result["issues"]}
        return {"ok": True, **result}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class BibFillTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="bib_fill", name="bib_fill", description="Fill missing BibTeX fields using Crossref and optionally write the result.", input_params={"type": "object", "properties": {"bib_path": {"type": "string"}, "write": {"type": "boolean", "default": False}}, "required": ["bib_path"]}, parallel_safe=False))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not inputs.get("bib_path"):
            return {"ok": False, "error": {"code": "INVALID_INPUT", "message": "bib_path is required"}}
        path = Path(str(inputs["bib_path"])).expanduser().resolve()
        if not path.is_file():
            return {"ok": False, "error": {"code": "NOT_FOUND", "message": str(path)}}
        original = _read_text(path)
        entries = parse_bib(original)
        filled: list[str] = []
        missing: list[str] = []
        failed: list[str] = []
        for entry in entries:
            doi = entry["fields"].get("doi")
            title = entry["fields"].get("title")
            if doi:
                url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
            elif title:
                url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": title, "rows": 1})
            else:
                missing.append(entry["key"])
                continue
            try:
                data = await asyncio.to_thread(_crossref_json, url)
                work = data.get("message") if doi else ((data.get("message") or {}).get("items") or [None])[0]
            except LookupError:
                work = None
            except Exception as exc:
                failed.append(f"{entry['key']} ({type(exc).__name__})")
                continue
            if not work:
                missing.append(entry["key"])
                continue
            touched = False
            for name, value in _fields_from_work(work).items():
                if not entry["fields"].get(name, "").strip():
                    entry["fields"][name] = value
                    touched = True
            if touched:
                filled.append(entry["key"])
        fixed = _format_bib(entries)
        try:
            written = _write_if_safe(path, original, fixed, bool(inputs.get("write", False)))
        except ValueError as exc:
            return {"ok": False, "error": {"code": "INCOMPLETE_PARSE", "message": str(exc)}, "filled": filled, "missing": missing, "failed": failed}
        return {"ok": True, "fixed": fixed, "filled": filled, "missing": missing, "failed": failed, "written": written}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class CiteAuditTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="cite_audit", name="cite_audit", description="Audit TeX citation commands against a BibTeX file.", input_params={"type": "object", "properties": {"bib_path": {"type": "string"}, "tex_paths": {"type": "array", "items": {"type": "string"}, "minItems": 1}}, "required": ["bib_path", "tex_paths"]}, idempotent=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not inputs.get("bib_path") or not inputs.get("tex_paths"):
            return {"ok": False, "error": {"code": "INVALID_INPUT", "message": "bib_path and at least one tex_path are required"}}
        bib_path = Path(str(inputs["bib_path"])).expanduser().resolve()
        tex_paths = [Path(str(item)).expanduser().resolve() for item in inputs["tex_paths"]]
        missing_files = [str(path) for path in [bib_path, *tex_paths] if not path.is_file()]
        if missing_files:
            return {"ok": False, "error": {"code": "NOT_FOUND", "message": ", ".join(missing_files)}}
        return {"ok": True, **cite_audit((_read_text(path) for path in tex_paths), _read_text(bib_path))}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)
