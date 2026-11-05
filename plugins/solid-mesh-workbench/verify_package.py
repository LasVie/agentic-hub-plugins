#!/usr/bin/env python3
"""Verify exact archive contents, provenance and extracted engine behavior."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
ASSET = Path(__file__).resolve().parent
ROOT = ASSET.parents[1]
MAX_ZIP = 95 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024
BLOCKED_PARTS = {"__pycache__", "node_modules", "venv", "__MACOSX"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def asset_tool():
    """Reuse maintained repository validation; do not execute plugin imports."""
    spec = importlib.util.spec_from_file_location("solid_mesh_asset_release", ROOT / "tools/asset_release.py")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as error:
        if error.name == "yaml":
            raise ValueError("Use the existing repository packaging Python environment with PyYAML installed") from error
        raise
    return module


def json_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def safe_name(name: str) -> None:
    path = PurePosixPath(name)
    require(bool(name) and str(path) == name and not path.is_absolute(), f"Invalid archive path: {name}")
    require(".." not in path.parts and "\\" not in name and ":" not in name, f"Unsafe archive path: {name}")
    require(not any(part.startswith(".") or part in BLOCKED_PARTS for part in path.parts), f"Cache/hidden entry: {name}")
    require(path.suffix.lower() not in {".pyc", ".pyo", ".zip", ".tgz"}, f"Development/archive entry: {name}")


def archive_files(body: bytes, *, deterministic: bool = False) -> dict[str, bytes]:
    require(len(body) <= MAX_ZIP, "Archive exceeds repository size limit")
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        infos = archive.infolist()
        require(len(infos) <= 1000 and sum(item.file_size for item in infos) <= MAX_EXPANDED, "Archive expansion limit exceeded")
        names = [item.filename for item in infos]
        require(len(names) == len({name.casefold() for name in names}), "Duplicate/case-colliding archive entries")
        if deterministic:
            require(names == sorted(names) and archive.comment == b"", "Native ZIP order/comment is not deterministic")
        for item in infos:
            safe_name(item.filename)
            mode = item.external_attr >> 16
            require(not item.is_dir() and stat.S_IFMT(mode) in {0, stat.S_IFREG}, f"Non-regular archive entry: {item.filename}")
            require(not item.flag_bits & 1, "Encrypted archive entries are unsupported")
            if deterministic:
                require(item.date_time == (1980, 1, 1, 0, 0, 0) and item.create_system == 3 and mode == (stat.S_IFREG | 0o644) and item.compress_type == zipfile.ZIP_STORED and item.extra == b"" and item.comment == b"", f"Native entry differs from deterministic package convention: {item.filename}")
        require(archive.testzip() is None, "ZIP CRC verification failed")
        return {item.filename: archive.read(item) for item in infos}


def checked_source():
    maintained = asset_tool()
    metadata, payload, provenance = maintained.check_asset(ASSET)
    require(metadata["type"] == "agent-plugin" and metadata["name"] == "solid-mesh-workbench", "Unexpected asset identity")
    files = {}
    for path in sorted(payload.rglob("*")):
        require(not path.is_symlink(), f"Source symlink forbidden: {path}")
        if path.is_file():
            name = path.relative_to(payload).as_posix()
            safe_name(name)
            files[name] = path.read_bytes()
    require("manifest.json" in files and "THIRD_PARTY_NOTICES.md" in files, "Missing native entry or notices")
    return maintained, metadata, payload, provenance, files


def canonical_files(canonical: Path, maintained, metadata, payload, expected: dict[str, bytes]):
    require(canonical.is_file() and not canonical.is_symlink(), "Canonical ZIP must be a regular file")
    body = canonical.read_bytes()
    entries = archive_files(body)
    slug = metadata["name"]
    prefix = f"{slug}/{slug}/"
    require(set(entries) == {f"{slug}/plugin.yaml", *(prefix + name for name in expected)}, "Canonical ZIP has missing or extra entries")
    extracted = {name[len(prefix):]: data for name, data in entries.items() if name.startswith(prefix)}
    require(extracted == expected, "Canonical inner payload differs from maintained source")
    wrapper, hashes = maintained.inspect_zip(body)
    expected_body, expected_hashes = maintained.build_bytes(metadata, payload)
    require(body == expected_body, "Canonical ZIP metadata or deterministic representation differs from the maintained packer")
    require(hashes == expected_hashes, "Canonical payload hash mismatch")
    require(wrapper["display_name"] == metadata["display_name"] and wrapper["runtime"]["type"] == "agent-plugin", "Canonical display/runtime metadata mismatch")
    return body, extracted


def check_artifact(path: Path, canonical: Path, body: bytes, metadata: dict, provenance: dict, files: dict[str, bytes]):
    artifact = json_object(path)
    wanted = {
        "schema_version": 1, "name": metadata["name"], "version": metadata["version"],
        "type": "agent-plugin", "asset_id": f"repo:agent-plugin:{metadata['name']}",
        "zip": canonical.name, "sha256": digest(body), "provenance_mode": provenance["mode"],
        "payload_sha256": {name: digest(data) for name, data in files.items()},
        "source_review_sha256": digest((ASSET / provenance["audit_file"]).read_bytes()),
        "functional_test_report_sha256": digest((ASSET / "TEST_REPORT.md").read_bytes()),
    }
    require(all(artifact.get(key) == value for key, value in wanted.items()), "Canonical artifact.json differs from ZIP, metadata or current evidence")


def check_provenance(metadata: dict, provenance: dict, files: dict[str, bytes]) -> dict:
    require(provenance["mode"] == "ported" and provenance["permission_status"] == "verified", "Source permission is not verified")
    covered = set()
    for source in provenance["sources"]:
        for evidence in source["license_evidence"]:
            name = evidence["path"]
            require(name in files and digest(files[name]) == evidence["sha256"], f"License evidence hash mismatch: {name}")
            covered.add(name)
    require({name for name in files if name.startswith("licenses/")} == covered, "License inventory and provenance coverage differ")
    upstream = provenance["upstream_artifact"]
    require(upstream["version"] == "3.5.4", "Unexpected reviewed Manifold version")
    require({item["path"] for item in upstream["files"]} == set(provenance["reused_paths"]), "Reused artifact hash inventory differs")
    for item in upstream["files"]:
        data = files[item["path"]]
        require(len(data) == item["bytes"] and digest(data) == item["sha256"], f"Vendor artifact mismatch: {item['path']}")
    require(files["vendor/manifold.wasm"].startswith(b"\x00asm\x01\x00\x00\x00"), "Invalid WASM header")
    for name, data in files.items():
        if name != "vendor/manifold.wasm":
            data.decode("utf-8", errors="strict")
    manifest = json.loads(files["manifest.json"])
    require(manifest["id"] == metadata["name"] and manifest["version"] == metadata["version"] and manifest["package_type"] == "plugin", "Native metadata mismatch")
    require(manifest["display_name"]["zh"] == metadata["display_name"], "Chinese package name mismatch")
    for name in ["README.md", "skills/solid-mesh/SKILL.md", "THIRD_PARTY_NOTICES.md", "web/index.html"]:
        require(re.search(r"[\u4e00-\u9fff]", files[name].decode("utf-8")), f"Missing Chinese content: {name}")
    return {"license_files": len(covered), "upstream_version": upstream["version"], "utf8_verified": True}


def node_environment() -> dict[str, str]:
    allowed = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "WINDIR")
    return {key: os.environ[key] for key in allowed if key in os.environ}


def verify_extracted(files: dict[str, bytes], node: Path) -> dict:
    require(node.is_absolute() and node.is_file() and os.access(node, os.X_OK), "--node must be an existing absolute executable path")
    version = subprocess.run([str(node), "--version"], capture_output=True, check=True, timeout=5, env=node_environment()).stdout.decode().strip()
    match = re.fullmatch(r"v(\d+)\.\d+\.\d+", version)
    require(match is not None and int(match[1]) >= 22, "Node.js 22+ is required")
    with tempfile.TemporaryDirectory(prefix="solid-mesh-package-verify-") as temporary:
        payload = Path(temporary)
        for name, data in files.items():
            path = payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        def calculate(project):
            result = subprocess.run(
                [str(node), "--max-old-space-size=256", "--wasm-max-mem-pages=4096", "--disallow-code-generation-from-strings", str(payload / "engine/cli.mjs")],
                input=json.dumps(project, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, cwd=payload, env=node_environment(),
            )
            require(result.returncode == 0 and result.stderr == b"", "Extracted engine failed or emitted stderr")
            require(len(result.stdout) <= 12 * 1024 * 1024 and result.stdout.count(b"\n") == 1, "Extracted engine output framing/size mismatch")
            return json.loads(result.stdout.decode("utf-8"))

        def success(project, volume, area):
            result = calculate(project)
            require(result.get("ok") is True, "Extracted engine rejected a valid fixture")
            require(math.isclose(result["metrics"]["volume_mm3"], volume, rel_tol=1e-7, abs_tol=1e-7), "Extracted volume differs from analytical fixture")
            require(math.isclose(result["metrics"]["area_mm2"], area, rel_tol=1e-7, abs_tol=1e-7), "Extracted area differs from analytical fixture")
            return result

        example = json.loads(files["examples/重叠方块.json"])
        outcomes = {}
        for operation, volume, area, low, high in [
            ("union", 12000, 3200, [0, 0, 0], [30, 20, 20]),
            ("difference", 4000, 1600, [0, 0, 0], [10, 20, 20]),
            ("intersection", 4000, 1600, [10, 0, 0], [20, 20, 20]),
        ]:
            project = {**example, "operation": operation}
            result = success(project, volume, area)
            require(result["metrics"]["bounds"] == {"min": low, "max": high}, "Extracted bounds mismatch")
            outcomes[operation] = result["metrics"]
            if operation == "union":
                union = result
        restored = success(json.loads(json.dumps(union["project"])), 12000, 3200)
        require(restored["metrics"] == union["metrics"] and restored["mesh"] == union["mesh"], "Extracted canonical project reload changed geometry")
        fixture = {"schema": "solid-mesh-workbench/v1", "units": "mm", "operation": "difference", "a": {"kind": "obj", "text": files["examples/闭合方块.obj"].decode("utf-8")}, "b": {"kind": "box", "size": [20, 20, 20], "translate": [100, 0, 0]}}
        closed = success(fixture, 8000, 2400)
        fixture["a"]["text"] = files["examples/错误示例-破洞.obj"].decode("utf-8")
        rejected = calculate(fixture)
        require(rejected.get("ok") is False and "封闭" in rejected.get("error", "") and "mesh" not in rejected, "Extracted open mesh was not rejected with the expected Chinese error")
        fixture["a"]["text"] = union["obj"]
        success(fixture, 12000, 3200)
        return {"node_version": version, "analytical": outcomes, "closed_obj_volume_mm3": closed["metrics"]["volume_mm3"], "invalid_obj_error": rejected["error"], "project_reload_verified": True, "result_obj_reimport_verified": True}


def verify(canonical: Path, native: Path, node: Path, artifact: Path, companion_record: Path) -> dict:
    maintained, metadata, payload, provenance, source_files = checked_source()
    canonical_body, files = canonical_files(canonical, maintained, metadata, payload, source_files)
    require(native.is_file() and not native.is_symlink(), "Native ZIP must be a regular file")
    native_body = native.read_bytes()
    require(archive_files(native_body, deterministic=True) == files, "Native ZIP root files differ from canonical inner payload or source")
    check_artifact(artifact, canonical, canonical_body, metadata, provenance, files)
    companion = json_object(companion_record)
    hashes = {name: digest(data) for name, data in files.items()}
    required_record = {"schema_version": 1, "plugin_id": metadata["name"], "version": metadata["version"], "canonical_sha256": digest(canonical_body), "native_sha256": digest(native_body), "payload_files": hashes, "payload_identical": True}
    require(all(companion.get(key) == value for key, value in required_record.items()), "Companion artifact metadata mismatch")
    licensing = check_provenance(metadata, provenance, files)
    functionality = verify_extracted(files, node)
    return {"passed": True, "plugin_id": metadata["name"], "version": metadata["version"], "display_name": metadata["display_name"], "canonical_zip": str(canonical), "canonical_sha256": digest(canonical_body), "native_zip": str(native), "native_sha256": digest(native_body), "payload_identical": True, "payload_file_count": len(files), "files_sha256": hashes, "provenance": licensing, "extracted_functionality": functionality, "scope": "Automated archive, provenance, UTF-8 and extracted-engine checks; not manual user testing or screenshot confirmation."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, help="Default: artifact.json beside canonical ZIP")
    parser.add_argument("--companion-record", type=Path, help="Default: companion-artifact.json beside native ZIP")
    parser.add_argument("--report", type=Path, help="Optional task-owned JSON verification report")
    args = parser.parse_args()
    try:
        report = verify(args.canonical, args.native, args.node, args.artifact or args.canonical.with_name("artifact.json"), args.companion_record or args.native.with_name("companion-artifact.json"))
        if args.report:
            evidence_paths = [args.canonical, args.native, args.artifact or args.canonical.with_name("artifact.json"), args.companion_record or args.native.with_name("companion-artifact.json")]
            require(args.report.absolute() not in {path.absolute() for path in evidence_paths}, "Report must not overwrite an archive or artifact record")
            require(not args.report.is_symlink(), "Report path is a symlink")
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "files_sha256"}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        print(json.dumps({"passed": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
