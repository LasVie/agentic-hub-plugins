"""Create the connector's exact native and official agent-mcp wrapped ZIPs.

Run only after SOURCE_REVIEW.md and TEST_REPORT.md are ready. No credentials,
OAuth, provider requests, host modifications or publishing occur here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import unicodedata
import zipfile

REPOSITORY = Path(__file__).resolve().parents[1]
CLI_SOURCE = "https://github.com/openJiuwen-ai/skillhub"
CLI_COMMIT = "c8ee4ef44be0453470114aa5a19f4e1017462907"
MAX_ZIP = 95 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024
MAX_ENTRIES = 1000
MAX_RATIO = 50


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(name: str) -> str:
    if not name or "\\" in name or "\x00" in name or name.startswith("/"):
        raise ValueError(f"Unsafe package path: {name!r}")
    parts = name.rstrip("/").split("/")
    for part in parts:
        if not part or part in {".", ".."} or ":" in part or part[-1:] in {".", " "}:
            raise ValueError(f"Unsafe package path: {name!r}")
        if re.fullmatch(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part, flags=re.IGNORECASE):
            raise ValueError(f"Platform-aliased package path: {name!r}")
    return unicodedata.normalize("NFC", "/".join(parts)).casefold()


def payload_files(root: Path) -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Payload root must be a real directory")
    files = {}
    aliases = set()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.relative_to(root).parts or path.suffix in {".pyc", ".pyo"}:
            continue
        alias = safe_path(relative)
        if alias in aliases:
            raise ValueError(f"Aliased payload path: {relative}")
        aliases.add(alias)
        if path.is_symlink():
            raise ValueError(f"Payload symlink: {relative}")
        if path.is_dir():
            continue
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"Non-regular payload entry: {relative}")
        if path.name in {".DS_Store", ".env", "token.json", "oauth-client.json", "client.json", "credentials.json"} or path.name.endswith((".token.json", ".login.json")):
            raise ValueError(f"Runtime/private file in payload: {relative}")
        files[relative] = path.read_bytes()
    if not files or len(files) + 1 > MAX_ENTRIES or sum(map(len, files.values())) > MAX_EXPANDED:
        raise ValueError("Payload size or entry limit exceeded")
    return files


def inspect_zip(path: Path) -> dict[str, bytes]:
    if path.stat().st_size > MAX_ZIP:
        raise ValueError("ZIP exceeds repository 95 MiB limit")
    members = {}
    aliases = set()
    expanded = 0
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_ENTRIES:
            raise ValueError("ZIP entry limit exceeded")
        for member in entries:
            name = member.filename
            alias = safe_path(name)
            if alias in aliases:
                raise ValueError(f"Duplicate/aliased ZIP path: {name}")
            aliases.add(alias)
            kind = stat.S_IFMT(member.external_attr >> 16)
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError(f"Symlink/special ZIP entry: {name}")
            if member.flag_bits & 1:
                raise ValueError("Encrypted ZIP is unsupported")
            if member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                raise ValueError("Unexpected ZIP compression method")
            expanded += member.file_size
            if expanded > MAX_EXPANDED or member.file_size / max(member.compress_size, 1) > MAX_RATIO:
                raise ValueError("ZIP expansion size or compression-ratio limit exceeded")
            if "__pycache__" in PurePosixPath(name).parts or name.endswith((".pyc", ".pyo")):
                raise ValueError("Compiled Python/cache entry in ZIP")
            if not member.is_dir():
                members[name] = archive.read(member)
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC verification failed")
    return members


def run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command!r}\n{result.stdout}\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def build(asset_dir: Path, cli: Path, cli_python: Path) -> dict:
    import yaml

    asset = json.loads((asset_dir / "asset.json").read_text(encoding="utf-8"))
    name, version = asset["name"], asset["version"]
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise ValueError("Invalid connector slug")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or asset["type"] != "agent-mcp":
        raise ValueError("Invalid connector type/version")
    payload = asset_dir / name
    files = payload_files(payload)
    manifest = json.loads(files["manifest.json"])
    if (manifest["id"], manifest["version"], manifest["package_type"]) != (name, version, "mcp"):
        raise ValueError("Native/asset identity mismatch")
    if manifest["display_name"]["zh"] != asset["display_name"]:
        raise ValueError("Chinese display name mismatch")
    reviews = {filename: sha256((asset_dir / filename).read_bytes()) for filename in ("SOURCE_REVIEW.md", "TEST_REPORT.md", "provenance.json")}
    cli_version = run([str(cli_python), "-c", "from importlib.metadata import version; print(version('openjiuwen-agentichub'))"])
    if cli_version != "0.0.1":
        raise ValueError(f"CLI changed from reviewed version0.0.1: {cli_version}")
    wrapper = {
        "name": name, "version": version, "display_name": asset["display_name"],
        "description": manifest["description"], "runtime": {"type": "agent-mcp"},
        "metadata": {"author": asset["owner"], "tags": ["办公协作", "Google Workspace", "浏览器授权"]},
    }
    native_target = asset_dir / "test-packages" / f"{name}-{version}-native.zip"
    wrapped_target = asset_dir / "release" / version / f"{name}-{version}-agent-mcp.zip"
    artifact_target = wrapped_target.parent / "artifact.json"
    if any(path.exists() for path in (native_target, wrapped_target, artifact_target)):
        raise FileExistsError("Final artifacts already exist; preserve their bytes. Review explicitly before rebuilding a version.")
    commands = []
    checks = []
    with tempfile.TemporaryDirectory(prefix="google-connector-pack-") as temporary:
        temporary = Path(temporary)
        init = [str(cli), "init", name, "--type", "agent-mcp"]
        commands.append(init)
        checks.append({"step": "official_init", "output": run(init, cwd=temporary)})
        stage = temporary / name
        # Remove only placeholders created by the preceding init inside owned scratch.
        shutil.rmtree(stage / name)
        for relative, contents in files.items():
            target = stage / name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
        (stage / "plugin.yaml").write_text(yaml.safe_dump(wrapper, allow_unicode=True, sort_keys=False), encoding="utf-8")
        (stage / "README.md").write_text(
            f"# {asset['display_name']}\n\n实际说明位于原生目录中的 README.md。\n",
            encoding="utf-8",
        )
        validate = [str(cli), "validate", str(stage)]
        commands.append(validate)
        checks.append({"step": "official_validate", "output": run(validate)})
        pack = [str(cli), "pack", str(stage), "--output", str(temporary / "out")]
        commands.append(pack)
        checks.append({"step": "official_pack", "output": run(pack)})
        wrapped = temporary / "out" / f"{name}-{version}.zip"
        native = temporary / "native.zip"
        with zipfile.ZipFile(native, "w", compression=zipfile.ZIP_STORED) as archive:
            for relative, contents in files.items():
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, contents)
        native_members = inspect_zip(native)
        wrapped_members = inspect_zip(wrapped)
        metadata_paths = [path for path in wrapped_members if PurePosixPath(path).name == "plugin.yaml"]
        if len(metadata_paths) != 1:
            raise ValueError("Wrapped ZIP must have exactly one plugin.yaml")
        outer = PurePosixPath(metadata_paths[0]).parent.as_posix()
        prefix = f"{outer}/{name}/"
        expected_outer = {metadata_paths[0], *(prefix + relative for relative in files)}
        if set(wrapped_members) != expected_outer:
            raise ValueError("Unexpected wrapper entries")
        wrapped_payload = {path[len(prefix):]: contents for path, contents in wrapped_members.items() if path.startswith(prefix)}
        if files != native_members or files != wrapped_payload:
            raise ValueError("Source/native/wrapped payloads differ")
        if yaml.safe_load(wrapped_members[metadata_paths[0]]) != wrapper:
            raise ValueError("Wrapped metadata identity mismatch")
        # Inspect the actual extracted native and wrapped runtime files as well.
        for path, suffix in ((native, "native"), (wrapped, "wrapped")):
            extraction = temporary / f"extract-{suffix}"
            extraction.mkdir()
            with zipfile.ZipFile(path) as archive:
                archive.extractall(extraction)  # inspected safe members above
            extracted_payload = extraction if suffix == "native" else extraction / outer / name
            if payload_files(extracted_payload) != files:
                raise ValueError("Extracted payload differs")
        preflight = REPOSITORY / "tools" / "asset_release.py"
        for target, label in ((payload, "native_source"), (native, "native_zip"), (wrapped, "wrapped_zip")):
            command = [str(cli_python), str(preflight), "preflight", str(target)]
            commands.append(command)
            checks.append({"step": "javascript_preflight_" + label, "output": run(command)})
        records = []
        for form, source, target in (("native", native, native_target), ("agent-mcp_wrapped", wrapped, wrapped_target)):
            records.append({"form": form, "path": target.relative_to(REPOSITORY).as_posix(), "filename": target.name, "sha256": sha256(source.read_bytes()), "size_bytes": source.stat().st_size})
        artifact = {
            "schema_version": 1, "asset_type": "agent-mcp", "name": name,
            "display_name": asset["display_name"], "version": version,
            "task_id": asset["task_id"], "internal_asset_id": asset["internal_asset_id"],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "artifacts": records,
            "payload_sha256": {relative: sha256(contents) for relative, contents in files.items()},
            "review_files_sha256": reviews,
            "official_cli": {"distribution": "openjiuwen-agentichub", "version": cli_version, "source": CLI_SOURCE, "source_commit": CLI_COMMIT, "commands": commands},
            "checks": checks,
            "verification_limits": "Packaging/JavaScript preflight and byte-equivalence only; not authenticated provider access or user manual-test acceptance.",
        }
        created = []
        try:
            for source, target in ((native, native_target), (wrapped, wrapped_target)):
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as output:
                    created.append(target)
                    output.write(source.read_bytes())
            with artifact_target.open("x", encoding="utf-8") as output:
                created.append(artifact_target)
                json.dump(artifact, output, ensure_ascii=False, indent=2)
                output.write("\n")
        except Exception:
            for target in created:
                target.unlink(missing_ok=True)
            raise
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Package a reviewed Google Workspace connector using the official CLI.")
    parser.add_argument("asset", type=Path, help="Connector source directory")
    parser.add_argument("--cli", type=Path, required=True, help="Reviewed official agentichub CLI path")
    parser.add_argument("--cli-python", type=Path, help="Python belonging to that CLI installation (default: sibling python)")
    args = parser.parse_args()
    # Keep the venv interpreter path: resolving its ordinary symlink to the
    # base interpreter would discard this CLI's installed dependencies.
    artifact = build(args.asset.resolve(), args.cli.absolute(), (args.cli_python or args.cli.parent / "python").absolute())
    print(json.dumps({"name": artifact["name"], "version": artifact["version"], "artifacts": artifact["artifacts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
