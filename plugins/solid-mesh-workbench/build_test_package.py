#!/usr/bin/env python3
"""Derive a deterministic native companion from an already packed canonical ZIP."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

sys.dont_write_bytecode = True
from verify_package import canonical_files, checked_source, digest, require


def native_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, data)
    return output.getvalue()


def write_unchanged_or_new(path: Path, body: bytes) -> None:
    require(not path.is_symlink(), f"Output symlink forbidden: {path}")
    if path.exists():
        require(path.is_file() and path.read_bytes() == body, f"Existing artifact differs; use a new version/path: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--record", type=Path, help="Default: companion-artifact.json beside native ZIP")
    args = parser.parse_args()
    try:
        maintained, metadata, payload, _provenance, files = checked_source()
        canonical, files = canonical_files(args.canonical, maintained, metadata, payload, files)
        body = native_bytes(files)
        record_path = args.record or args.native.with_name("companion-artifact.json")
        require(args.native.absolute() != record_path.absolute(), "Native ZIP and companion record must have distinct paths")
        record = {"schema_version": 1, "plugin_id": metadata["name"], "version": metadata["version"], "canonical_zip": str(args.canonical), "canonical_sha256": digest(canonical), "native_zip": str(args.native), "native_sha256": digest(body), "payload_identical": True, "payload_files": {name: digest(data) for name, data in files.items()}}
        record_body = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        # Check both existing destinations before creating either new artifact.
        for path, expected in [(args.native, body), (record_path, record_body)]:
            require(not path.is_symlink() and (not path.exists() or (path.is_file() and path.read_bytes() == expected)), f"Existing artifact differs or is a symlink: {path}")
        write_unchanged_or_new(args.native, body)
        write_unchanged_or_new(record_path, record_body)
        print(json.dumps({key: value for key, value in record.items() if key != "payload_files"}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print(json.dumps({"passed": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
