#!/usr/bin/env python3
"""Build this asset's deterministic native companion and verify canonical equality."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


ASSET = Path(__file__).resolve().parent
REPO = ASSET.parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    config = json.loads((ASSET / "asset.json").read_text())
    slug, version = config["name"], config["version"]
    payload = ASSET / slug
    for action, target in (("check", ASSET), ("preflight", payload), ("pack", ASSET)):
        subprocess.run([sys.executable, str(REPO / "tools/asset_release.py"), action, str(target)], check=True)
    directory = ASSET / "test-packages"
    directory.mkdir(exist_ok=True)
    native = directory / f"{slug}-{version}-workswarm.zip"
    files = {p.relative_to(payload).as_posix(): p.read_bytes()
             for p in sorted(payload.rglob("*")) if p.is_file()}
    assert all(not p.is_symlink() for p in payload.rglob("*"))
    with zipfile.ZipFile(native, "w", compression=zipfile.ZIP_STORED) as archive:
        for path, data in files.items():
            info = zipfile.ZipInfo(path, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    canonical = REPO / "releases/agent-plugin" / slug / version / f"{slug}-{version}.zip"
    with zipfile.ZipFile(canonical) as archive:
        assert archive.testzip() is None
        prefix = f"{slug}/{slug}/"
        canonical_files = {p[len(prefix):]: archive.read(p) for p in archive.namelist()
                           if p.startswith(prefix) and not p.endswith("/")}
    with zipfile.ZipFile(native) as archive:
        assert archive.testzip() is None
        assert files == {p: archive.read(p) for p in archive.namelist()}
    assert files == canonical_files
    for target in (native, canonical):
        subprocess.run([sys.executable, str(REPO / "tools/asset_release.py"), "preflight", str(target)], check=True)
    record = {
        "schema_version": 1, "asset_id": f"repo:agent-plugin:{slug}", "name": slug,
        "version": version, "native_zip": str(native.relative_to(REPO)),
        "native_sha256": sha(native.read_bytes()),
        "canonical_zip": str(canonical.relative_to(REPO)),
        "canonical_sha256": sha(canonical.read_bytes()),
        "native_canonical_payload_equal": True, "payload_file_count": len(files),
        "payload_sha256": {p: sha(data) for p, data in files.items()},
        "source_review_sha256": sha((ASSET / "SOURCE_REVIEW.md").read_bytes()),
        "functional_test_report_sha256": sha((ASSET / "TEST_REPORT.md").read_bytes()),
    }
    (directory / "artifact.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "payload_sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
