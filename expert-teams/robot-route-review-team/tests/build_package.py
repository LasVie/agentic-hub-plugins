"""Build and inspect this team's native and Agentic Hub archives locally.

The official CLI is a reviewed, separately downloaded build prerequisite. This
script neither downloads tooling nor invokes publishing, registration or models.
"""

from __future__ import annotations

import argparse
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


TEAM_DIR = Path(__file__).resolve().parents[1]
SLUG = "robot-route-review-team"
PAYLOAD = TEAM_DIR / SLUG
OUTPUT_ROOT = TEAM_DIR
CLI_REF = "c8ee4ef44be0453470114aa5a19f4e1017462907"
DEFAULT_PYTHON = Path(
    "/Users/IDLE_And_R/Downloads/Huawei/jiuwenswarm/"
    "local-only/connector-import/venv/bin/python"
)
ZIP_TIME = (2026, 1, 1, 0, 0, 0)
ZIP_EPOCH = 1767225600
MAX_ZIP = 95 * 1024 * 1024
MAX_UNPACKED = 512 * 1024 * 1024
MAX_ENTRIES = 1000
MAX_RATIO = 50
FORBIDDEN_PARTS = {"__pycache__", ".git", "node_modules", ".DS_Store"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_regular(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular, non-symlink file: {path}")
    return path.read_bytes()


def payload_files() -> dict[str, bytes]:
    if PAYLOAD.is_symlink() or not PAYLOAD.is_dir():
        raise ValueError("Native payload directory is missing or is a symlink")
    result: dict[str, bytes] = {}
    aliases: set[str] = set()
    for path in sorted(PAYLOAD.rglob("*")):
        rel = path.relative_to(PAYLOAD).as_posix()
        if path.is_symlink():
            raise ValueError(f"Symlink is not distributable: {rel}")
        # Finder metadata is unrelated to runtime content. Leave the user's
        # file in place while excluding it from the reviewed package payload.
        if path.name == ".DS_Store" and path.is_file():
            continue
        if any(part in FORBIDDEN_PARTS for part in path.relative_to(PAYLOAD).parts):
            raise ValueError(f"Development/cache path in payload: {rel}")
        if path.is_dir():
            continue
        if not path.is_file() or path.suffix in {".pyc", ".pyo"}:
            raise ValueError(f"Invalid payload file: {rel}")
        alias = unicodedata.normalize("NFC", rel).casefold()
        if alias in aliases:
            raise ValueError(f"Aliased payload path: {rel}")
        aliases.add(alias)
        result[rel] = read_regular(path)
    if not result or len(result) > MAX_ENTRIES - 1:
        raise ValueError("Empty payload or too many payload files")
    if sum(map(len, result.values())) > MAX_UNPACKED:
        raise ValueError("Payload exceeds platform extracted-size limit")
    return result


def yaml_text(asset: dict) -> bytes:
    # JSON scalar quoting is also valid YAML and preserves all Chinese text.
    quoted = lambda value: json.dumps(value, ensure_ascii=False)
    return (
        f"name: {quoted(SLUG)}\n"
        f"version: {quoted(asset['version'])}\n"
        f"display_name: {quoted(asset['display_name'])}\n"
        f"description: {quoted(asset['description'])}\n"
        "runtime:\n  type: agent-group\n"
        f"metadata:\n  author: {quoted(asset['publisher'])}\n"
        f"  tags: {quoted(asset['tags'])}\n"
    ).encode("utf-8")


def archive_contents(path: Path) -> dict[str, bytes]:
    if path.is_symlink() or path.stat().st_size > MAX_ZIP:
        raise ValueError(f"Unsafe or oversized ZIP: {path}")
    contents: dict[str, bytes] = {}
    aliases: set[str] = set()
    expanded = 0
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        if not infos or len(infos) > MAX_ENTRIES:
            raise ValueError("ZIP is empty or exceeds the entry limit")
        for info in infos:
            name = info.filename
            pure = PurePosixPath(name)
            if (
                not name
                or info.orig_filename != name
                or "\x00" in name
                or name.startswith("/")
                or "\\" in name
                or ":" in name
                or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
                or str(pure) != name.rstrip("/")
            ):
                raise ValueError(f"Unsafe ZIP path: {name}")
            alias = unicodedata.normalize("NFC", name.rstrip("/")).casefold()
            if alias in aliases:
                raise ValueError(f"Duplicate or aliased ZIP path: {name}")
            aliases.add(alias)
            if any(part in FORBIDDEN_PARTS for part in pure.parts):
                raise ValueError(f"Development/cache path in ZIP: {name}")
            mode_type = stat.S_IFMT(info.external_attr >> 16)
            if mode_type not in {0, stat.S_IFDIR, stat.S_IFREG} or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f"Unsupported ZIP member type: {name}")
            if info.flag_bits & 1:
                raise ValueError(f"Encrypted ZIP member is not supported: {name}")
            if info.is_dir():
                if mode_type == stat.S_IFREG:
                    raise ValueError(f"File metadata on directory: {name}")
                continue
            if mode_type == stat.S_IFDIR:
                raise ValueError(f"Directory metadata on file: {name}")
            expanded += info.file_size
            if expanded > MAX_UNPACKED:
                raise ValueError("ZIP exceeds extracted-size limit")
            if info.file_size and (
                not info.compress_size or info.file_size / info.compress_size > MAX_RATIO
            ):
                raise ValueError(f"ZIP member compression ratio exceeds limit: {name}")
            contents[name] = zf.read(info)
    return contents


def write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except FileExistsError:
        if read_regular(path) != data:
            raise ValueError(
                f"Existing artifact differs; preserve it and choose a new version: {path}"
            ) from None


def run_cli(python: Path, cli_source: Path, stage: Path, args: list[str]) -> dict:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(cli_source),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
    }
    cmd = [str(python), "-B", "-m", "openjiuwen_agentichub.main", *args]
    completed = subprocess.run(
        cmd, cwd=stage, env=env, text=True, capture_output=True, timeout=120
    )
    record = {"command": cmd, "returncode": completed.returncode,
              "stdout": completed.stdout, "stderr": completed.stderr}
    if completed.returncode:
        raise ValueError(json.dumps(record, ensure_ascii=False))
    return record


def inspect_packages(asset: dict, files: dict[str, bytes], wrapper: bytes) -> dict:
    version = asset["version"]
    native = OUTPUT_ROOT / "test-packages" / f"{SLUG}-{version}-native.zip"
    canonical = OUTPUT_ROOT / "release" / version / f"{SLUG}-{version}.zip"
    actual_native = archive_contents(native)
    actual_wrapped = archive_contents(canonical)
    prefix = f"{SLUG}-{version}/"
    expected_wrapped = {prefix + "plugin.yaml": wrapper}
    expected_wrapped.update({prefix + SLUG + "/" + path: body for path, body in files.items()})
    if actual_native != files:
        raise ValueError("Native ZIP paths/content differ from reviewed source payload")
    if actual_wrapped != expected_wrapped:
        raise ValueError("Wrapped ZIP paths/content differ from the exact native payload and wrapper")
    if "manifest.json" not in actual_native:
        raise ValueError("Native manifest.json must be at ZIP root")
    manifest = json.loads(actual_native["manifest.json"])
    if manifest.get("name") != SLUG or manifest.get("version") != version:
        raise ValueError("Native identity/version does not match asset metadata")
    if manifest.get("package_type") != "agent_group" or asset.get("type") != "agent-group":
        raise ValueError("Native/wrapper asset type mismatch")
    return {
        "schema_version": 1,
        "asset_id": f"repo:agent-group:{SLUG}",
        "task_id": asset["task_id"],
        "candidate_id": "Not Applicable",
        "type": "agent-group",
        "name": SLUG,
        "display_name": asset["display_name"],
        "version": version,
        "zip": canonical.name,
        "sha256": digest(read_regular(canonical)),
        "zip_bytes": canonical.stat().st_size,
        "native_test_zip": f"../../test-packages/{native.name}",
        "native_test_zip_sha256": digest(read_regular(native)),
        "native_test_zip_bytes": native.stat().st_size,
        "plugin_yaml_sha256": digest(wrapper),
        "payload_file_count": len(files),
        "payload_sha256": {path: digest(body) for path, body in files.items()},
        "package_verification": {
            "paths_types_sizes_ratios": "passed",
            "native_wrapped_source_payload_equality": "passed",
            "native_compression": "ZIP_STORED",
            "canonical_compression": "official CLI ZIP_DEFLATED",
            "reproducible_archive_timestamp": "2026-01-01T00:00:00",
        },
    }


def main() -> None:
    global OUTPUT_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--cli-source", type=Path,
                        default=TEAM_DIR / ".local/tooling/source/cli")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--record-artifact", action="store_true")
    parser.add_argument("--provisional", action="store_true", help="Keep pre-handoff archives in owned .local/provisional")
    args = parser.parse_args()
    if args.provisional:
        OUTPUT_ROOT = TEAM_DIR / ".local/provisional"
    if args.provisional and args.record_artifact:
        parser.error("Finalize reports before recording canonical release artifacts")
    if args.verify_only and args.record_artifact:
        parser.error("--record-artifact requires a fresh official validate/pack run")
    asset = json.loads(read_regular(TEAM_DIR / "asset.json"))
    version = asset["version"]
    if asset.get("name") != SLUG or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid asset identity or version")
    files = payload_files()
    wrapper = yaml_text(asset)
    commands: list[dict] = []
    if not args.verify_only:
        scratch = TEAM_DIR / ".local/package-runs"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="build-", dir=scratch) as temp:
            temp_dir = Path(temp)
            stage = temp_dir / "staging"
            stage.mkdir()
            (stage / "plugin.yaml").write_bytes(wrapper)
            for name, body in files.items():
                target = stage / SLUG / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
                os.utime(target, (ZIP_EPOCH, ZIP_EPOCH))
            os.utime(stage / "plugin.yaml", (ZIP_EPOCH, ZIP_EPOCH))
            commands.append(run_cli(args.python, args.cli_source, stage,
                                    ["validate", str(stage)]))
            out = temp_dir / "cli-output"
            commands.append(run_cli(args.python, args.cli_source, stage,
                                    ["pack", str(stage), "--output", str(out)]))
            official_zip = out / f"{SLUG}-{version}.zip"
            # Validate the fresh CLI ZIP before copying it into the delivery tree.
            archive_contents(official_zip)
            native_temp = temp_dir / "native.zip"
            with zipfile.ZipFile(native_temp, "w", compression=zipfile.ZIP_STORED) as zf:
                for name, body in files.items():
                    info = zipfile.ZipInfo(name, ZIP_TIME)
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    zf.writestr(info, body)
            native = OUTPUT_ROOT / "test-packages" / f"{SLUG}-{version}-native.zip"
            canonical = OUTPUT_ROOT / "release" / version / official_zip.name
            write_once(native, read_regular(native_temp))
            write_once(canonical, read_regular(official_zip))
    result = inspect_packages(asset, files, wrapper)
    cli_main = args.cli_source / "openjiuwen_agentichub/main.py"
    cli_plugin = args.cli_source / "cli_core/plugin.py"
    result["official_cli"] = {
        "distribution": "openjiuwen-agentichub",
        "version": "0.0.1",
        "source_commit": CLI_REF,
        "main_py_sha256": digest(read_regular(cli_main)),
        "plugin_py_sha256": digest(read_regular(cli_plugin)),
        "commands": commands,
    }
    if args.record_artifact:
        for name, key in [
            ("SOURCE_REVIEW.md", "source_review_sha256"),
            ("TEST_REPORT.md", "functional_test_report_sha256"),
            ("provenance.json", "provenance_sha256"),
        ]:
            result[key] = digest(read_regular(TEAM_DIR / name))
        result["provenance_mode"] = "native"
        # Commands include temporary directories, so keep normalized evidence.
        result["official_cli"]["commands"] = [
            "python -B -m openjiuwen_agentichub.main validate CLEAN_STAGING",
            "python -B -m openjiuwen_agentichub.main pack CLEAN_STAGING --output CLEAN_OUTPUT",
        ]
        body = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        write_once(OUTPUT_ROOT / "release" / version / "artifact.json", body)
    summary = {key: value for key, value in result.items()
               if key not in {"payload_sha256", "official_cli"}}
    summary["official_cli_validation"] = "passed" if commands else "not rerun (verify-only)"
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
