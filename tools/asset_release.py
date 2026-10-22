#!/usr/bin/env python3
"""Local packaging checks; never executes downloaded skills or plugin modules."""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

import yaml

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"\d+\.\d+\.\d+\Z")
KINDS = {"skill", "swarmskill", "agent-plugin"}
CATEGORIES = {"软件开发", "办公与生产力", "内容创作", "多模态与媒体", "数据与科学研究", "合规与法律", "生活与健康", "金融与财富管理"}
MAX_BYTES = 95 * 1024 * 1024
FORBIDDEN = {"persona", "agent_card", "model", "subagents", "memories", "rubrics"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"{path}: expected an object")
    return data


def relative_file(root: Path, raw: str, *, directory: bool = False) -> Path:
    require(isinstance(raw, str) and bool(raw.strip()), "empty/non-string declared path")
    raw = raw.removeprefix("./")
    p = PurePosixPath(raw)
    require(not p.is_absolute() and ".." not in p.parts and "\\" not in raw and ":" not in raw, f"unsafe path: {raw}")
    require(str(p) not in {".", ""}, "empty relative path")
    target = root / p
    cursor = root
    for part in p.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), f"symlink forbidden: {raw}")
    require(target.resolve().is_relative_to(root.resolve()), f"path escapes payload: {raw}")
    require(target.is_dir() if directory else target.is_file(), f"declared path missing: {raw}")
    return target


def skill_frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    require(bool(lines) and lines[0] == "---", f"{path}: missing YAML frontmatter")
    close = next((i for i in range(1, len(lines)) if lines[i] == "---"), None)
    require(close is not None, f"{path}: unclosed YAML frontmatter")
    fm = yaml.safe_load("\n".join(lines[1:close]))
    require(isinstance(fm, dict), f"{path}: frontmatter must be an object")
    name, desc = fm.get("name"), fm.get("description")
    require(isinstance(name, str) and len(name) <= 64 and bool(SLUG.fullmatch(name)), f"{path}: invalid skill name")
    require(name == path.parent.name, f"{path}: name must match directory")
    require(isinstance(desc, str) and 0 < len(desc.strip()) <= 4096, f"{path}: invalid description")
    if fm.get("kind"):
        require(fm["kind"] == "swarm-skill", "repository supports kind: swarm-skill only")
        roles = fm.get("roles")
        require(isinstance(roles, list) and len(roles) >= 2, "swarm-skill needs at least 2 roles")
        ids = [r.get("id") if isinstance(r, dict) else None for r in roles]
        require(all(isinstance(i, str) and i.strip() for i in ids), "role IDs must be nonempty")
        require(len(set(ids)) == len(ids), "duplicate swarm role IDs")
    return fm


def check_provenance(asset: Path, payload: Path) -> dict:
    p = read_json(asset / "provenance.json")
    relative_file(asset, p.get("audit_file", ""))
    require(p.get("mode") in {"native", "ported"}, "provenance mode must be native/ported")
    require(isinstance(p.get("sources"), list), "sources must be a list")
    require(isinstance(p.get("reused_paths"), list), "reused_paths must be a list")
    for name in p["reused_paths"]:
        relative_file(payload, name)
    if p["mode"] == "native":
        require(p.get("permission_status") == "original" and not p["reused_paths"], "native mode cannot contain copied implementation")
        relative_file(asset, p.get("independent_spec", ""))
    else:
        require(p.get("permission_status") == "verified", "unknown permission cannot be packaged as ported")
        require(bool(p["sources"]), "ported assets need fixed upstream source evidence")
        require(bool(p["reused_paths"]), "ported assets must list actually reused paths")
        for source in p["sources"]:
            require(isinstance(source, dict), "invalid upstream source")
            for field in ("url", "revision", "license_expression"):
                require(isinstance(source.get(field), str) and bool(source[field].strip()), f"missing source {field}")
            evidence = source.get("license_evidence")
            require(isinstance(evidence, list) and bool(evidence), "ported source needs in-payload license evidence")
            for item in evidence:
                require(isinstance(item, dict), "invalid license evidence")
                f = relative_file(payload, item.get("path", ""))
                require(sha(f.read_bytes()) == item.get("sha256"), f"license evidence hash mismatch: {f.name}")
    return p


def check_asset(asset: Path) -> tuple[dict, Path, dict]:
    c = read_json(asset / "asset.json")
    require(c.get("type") in KINDS, "supported types: skill, swarmskill, agent-plugin")
    name = c.get("name", "")
    require(isinstance(name, str) and len(name) <= 64 and bool(SLUG.fullmatch(name)), "invalid asset slug")
    require(bool(VERSION.fullmatch(str(c.get("version", "")))), "version must be x.y.z")
    for field, limit in (("display_name", 128), ("description", 4096), ("publisher", 128)):
        v = c.get(field)
        require(isinstance(v, str) and 0 < len(v.strip()) <= limit, f"invalid {field}")
        require(v != "YOUR_HUB_LOGIN" and not v.startswith("请替换"), f"replace placeholder {field}")
    require(c.get("category") in CATEGORIES, "use one of the 8 official category labels")
    tags = c.get("tags")
    require(isinstance(tags, list) and len(tags) <= 32, "invalid tags list")
    require(all(isinstance(t, str) and 0 < len(t.strip()) <= 64 and "," not in t for t in tags), "invalid tag")
    payload = asset / name
    require(payload.is_dir() and not payload.is_symlink(), "missing same-name payload directory")
    files = list(payload.rglob("*"))
    require(not any(f.is_symlink() for f in files), "payload contains a symlink")
    require(not any(any(part.startswith(".") or part in {"__pycache__", "node_modules", "venv", "__MACOSX"} for part in f.relative_to(payload).parts) for f in files), "payload contains cache/hidden/development files")
    require(not any(f.name == "plugin.yaml" for f in files), "market plugin.yaml belongs outside the payload")
    require(not any(f.suffix in {".pyc", ".pyo"} for f in files), "compiled cache files forbidden")
    if c["type"] in {"skill", "swarmskill"}:
        fm = skill_frontmatter(payload / "SKILL.md")
        require(fm.get("version", c["version"]) == c["version"], "skill and release versions differ")
        require((fm.get("kind") == "swarm-skill") == (c["type"] == "swarmskill"), "skill type/kind mismatch")
    else:
        m = read_json(payload / "manifest.json")
        require(m.get("package_type") == "plugin", "manifest.package_type must be plugin")
        require(m.get("id") == name and m.get("version") == c["version"], "manifest identity/version mismatch")
        require(not (FORBIDDEN & m.keys()), "plugin contains expert-only manifest fields")
        if "tags" in m:
            require(isinstance(m["tags"], list), "manifest.tags must be an array")
            require(all(isinstance(tag, dict) and all(isinstance(tag.get(language), str) and bool(tag[language].strip())
                                                     for language in ("zh", "en")) for tag in m["tags"]),
                    "manifest.tags must contain localized objects with nonempty zh/en strings")
        require(any(m.get(k) for k in ("skills", "tools", "rails", "mcps")), "tested plugin must provide at least one capability")
        for field in ("skills", "tools", "rails", "mcps"):
            entries = m.get(field, [])
            require(isinstance(entries, list), f"manifest.{field} must be an array")
            for entry in entries:
                require(isinstance(entry, dict), f"invalid {field} entry")
                if field == "skills":
                    d = relative_file(payload, entry.get("dir", ""), directory=True)
                    skill_frontmatter(d / "SKILL.md")
                elif entry.get("file"):
                    f = relative_file(payload, entry["file"])
                    if field == "tools" and entry.get("class"):
                        tree = ast.parse(f.read_text(encoding="utf-8"))
                        require(any(isinstance(n, ast.ClassDef) and n.name == entry["class"] for n in tree.body), "declared tool class not found statically")
                elif field == "mcps" and entry.get("dir"):
                    relative_file(payload, entry["dir"], directory=True)
                else:
                    require(field == "mcps" and bool(entry.get("connector")), f"missing declared {field} file")
        if m.get("avatar"):
            f = relative_file(payload, m["avatar"])
            b = f.read_bytes()
            require(f.suffix.lower() == ".png" and b.startswith(b"\x89PNG\r\n\x1a\n") and len(b) <= 5 * 1024 * 1024, "avatar must be PNG <= 5 MiB")
    p = check_provenance(asset, payload)
    return c, payload, p


def build_bytes(c: dict, payload: Path) -> tuple[bytes, dict]:
    market = {"name": c["name"], "version": c["version"], "display_name": c["display_name"], "description": c["description"], "runtime": {"type": "agent-plugin" if c["type"] == "agent-plugin" else "skill"}, "metadata": {"author": c["publisher"], "tags": c["tags"]}}
    entries = {f"{c['name']}/plugin.yaml": yaml.safe_dump(market, allow_unicode=True, sort_keys=False).encode()}
    hashes = {}
    for f in sorted(payload.rglob("*")):
        if f.is_file():
            rel = f.relative_to(payload).as_posix()
            body = f.read_bytes()
            hashes[rel] = sha(body)
            entries[f"{c['name']}/{c['name']}/{rel}"] = body
    require(len(entries) <= 1000, "Hub permits at most 1000 ZIP entries")
    require(sum(map(len, entries.values())) <= 512 * 1024 * 1024, "expanded size exceeds Hub limit")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        for name, body in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            # Stored members avoid compression-ratio false positives and are deterministic.
            z.writestr(info, body)
    require(len(out.getvalue()) <= MAX_BYTES, "ZIP exceeds repository 95 MiB limit")
    return out.getvalue(), hashes


def inspect_zip(body: bytes) -> tuple[dict, dict]:
    require(len(body) <= MAX_BYTES, "oversized archive")
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        infos = z.infolist()
        require(len(infos) <= 1000 and sum(i.file_size for i in infos) <= 512 * 1024 * 1024, "ZIP expansion limit")
        names = [i.filename for i in infos]
        require(len(names) == len(set(n.casefold() for n in names)), "duplicate/case-colliding ZIP paths")
        for info in infos:
            p = PurePosixPath(info.filename)
            require(not p.is_absolute() and ".." not in p.parts and "\\" not in info.filename and ":" not in info.filename, "unsafe ZIP path")
            require(not stat.S_ISLNK(info.external_attr >> 16), "ZIP symlink forbidden")
        wrappers = [n for n in names if n.endswith("/plugin.yaml")]
        require(len(wrappers) == 1 and len(PurePosixPath(wrappers[0]).parts) == 2, "one outer plugin.yaml required")
        c = yaml.safe_load(z.read(wrappers[0]))
        require(isinstance(c, dict) and isinstance(c.get("name"), str), "invalid wrapper metadata")
        name = c["name"]
        require(wrappers[0] == f"{name}/plugin.yaml", "outer name mismatch")
        prefix = f"{name}/{name}/"
        require(all(n == wrappers[0] or n.startswith(prefix) for n in names), "unexpected market outer entry")
        require(all(len(PurePosixPath(n).parts) >= 3 for n in names if n != wrappers[0]), "missing inner payload")
        payload = {n[len(prefix):]: sha(z.read(n)) for n in names if n.startswith(prefix)}
        runtime = c.get("runtime", {}).get("type")
        require(runtime in {"skill", "agent-plugin"}, "unsupported wrapper runtime")
        if runtime == "skill":
            require("SKILL.md" in payload, "missing skill entry")
        else:
            require("manifest.json" in payload, "missing plugin manifest")
            m = json.loads(z.read(prefix + "manifest.json"))
            require(m.get("id") == name and m.get("package_type") == "plugin" and m.get("version") == c.get("version"), "archived manifest mismatch")
        return c, payload


def pack(asset: Path, output: Path | None = None) -> Path:
    c, payload, provenance = check_asset(asset)
    test_report = relative_file(asset, "TEST_REPORT.md")
    require(bool(test_report.read_text(encoding="utf-8").strip()), "functional test report is empty")
    body, hashes = build_bytes(c, payload)
    inspect_zip(body)
    out = output or ROOT / "releases" / c["type"] / c["name"] / c["version"]
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{c['name']}-{c['version']}.zip"
    require(not path.exists() or path.read_bytes() == body, "existing version differs; bump version")
    path.write_bytes(body)
    record = {"schema_version": 1, "asset_id": f"repo:{c['type']}:{c['name']}", "type": c["type"], "name": c["name"], "version": c["version"], "zip": path.name, "sha256": sha(body), "payload_sha256": hashes, "provenance_mode": provenance["mode"], "source_review_sha256": sha((asset / provenance["audit_file"]).read_bytes()), "functional_test_report_sha256": sha(test_report.read_bytes())}
    (out / "artifact.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def audit_upstream(root: Path) -> dict:
    records = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.is_symlink() or ".git" in f.relative_to(root).parts:
            continue
        if not re.match(r"^(licen[cs]e|copying|notice)(\.|$)", f.name, re.I):
            continue
        require(f.stat().st_size <= 2 * 1024 * 1024, "license evidence too large for automatic inspection")
        body = f.read_bytes()
        text = body.decode("utf-8", errors="replace")
        candidates = []
        if "Permission is hereby granted, free of charge" in text and "copyright notice" in text:
            candidates.append("MIT-like text; verify complete license/scope")
        if "Apache License" in text and "Version 2.0" in text:
            candidates.append("Apache-2.0-like text; verify complete license/scope")
        records.append({"path": f.relative_to(root).as_posix(), "sha256": sha(body), "candidate_licenses": candidates})
    return {"automatic_detection_only": True, "permission_status": "unknown", "evidence": records, "next": "AI must inspect the exact upstream revision, scope, file headers, dependencies and intended reuse; do not infer permission from visibility or this scan."}


def check_repo(root: Path = ROOT) -> dict:
    source_count = archive_count = 0
    for area in ("skills", "plugins"):
        for f in sorted((root / area).glob("*/asset.json")):
            c, payload, provenance = check_asset(f.parent)
            require((area == "plugins") == (c["type"] == "agent-plugin"), "source in wrong type directory")
            record_path = root / "releases" / c["type"] / c["name"] / c["version"] / "artifact.json"
            require(record_path.is_file(), f"current source requires a tested release ZIP: {f.parent}")
            a = read_json(record_path)
            expected, _ = build_bytes(c, payload)
            require(a["sha256"] == sha(expected), "current source and release ZIP differ")
            require(a["functional_test_report_sha256"] == sha(relative_file(f.parent, "TEST_REPORT.md").read_bytes()), "test report differs from release record")
            require(a["source_review_sha256"] == sha(relative_file(f.parent, provenance["audit_file"]).read_bytes()), "source review differs from release record")
            source_count += 1
    for f in sorted((root / "releases").glob("*/*/*/artifact.json")):
        a = read_json(f)
        path = relative_file(f.parent, a["zip"])
        body = path.read_bytes()
        require(sha(body) == a["sha256"], f"ZIP checksum mismatch: {path}")
        c, hashes = inspect_zip(body)
        require(c["name"] == a["name"] and c["version"] == a["version"], "release identity mismatch")
        require(hashes == a["payload_sha256"], "archived payload differs from file manifest")
        archive_count += 1
    all_zips = list((root / "releases").rglob("*.zip"))
    require(len(all_zips) == archive_count, "each release ZIP needs exactly one artifact.json")
    return {"source_assets": source_count, "release_zips": archive_count, "note": "Structural checks only; functional tests and human screenshots are separate."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "pack", "audit-upstream"):
        p = sub.add_parser(name)
        p.add_argument("path", type=Path)
        if name == "pack":
            p.add_argument("--output", type=Path)
    sub.add_parser("check-repo")
    a = parser.parse_args()
    if a.command == "check-repo":
        result = check_repo()
    elif a.command == "audit-upstream":
        require(a.path.is_dir(), "upstream must be a local directory")
        result = audit_upstream(a.path)
    elif a.command == "pack":
        result = {"zip": str(pack(a.path, a.output))}
    else:
        c, _, _ = check_asset(a.path)
        result = {"name": c["name"], "type": c["type"], "version": c["version"], "format_ok": True}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, yaml.YAMLError, zipfile.BadZipFile) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
