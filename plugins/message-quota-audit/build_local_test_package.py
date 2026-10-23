#!/usr/bin/env python3
"""Derive a native WorkSwarm ZIP from the already packed canonical payload."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def main() -> None:
    asset = Path(__file__).resolve().parent
    root = asset.parents[1]
    meta = json.loads((asset / "asset.json").read_text())
    slug, version = meta["name"], meta["version"]
    release = root / "releases" / "agent-plugin" / slug / version
    canonical = release / f"{slug}-{version}.zip"
    artifact = json.loads((release / "artifact.json").read_text())
    canonical_sha = hashlib.sha256(canonical.read_bytes()).hexdigest()
    if artifact["sha256"] != canonical_sha:
        raise ValueError("Canonical ZIP does not match artifact.json")
    prefix = f"{slug}/{slug}/"
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(canonical) as archive:
        if archive.testzip() is not None:
            raise ValueError("Canonical ZIP CRC check failed")
        for item in archive.infolist():
            if not item.filename.startswith(prefix):
                if item.filename != f"{slug}/plugin.yaml":
                    raise ValueError("Unexpected canonical wrapper entry")
                continue
            name = item.filename[len(prefix):]
            path = PurePosixPath(name)
            if not name or path.is_absolute() or ".." in path.parts or "\\" in name or name in entries:
                raise ValueError("Unsafe or duplicate payload path")
            if not stat.S_ISREG(item.external_attr >> 16):
                raise ValueError("Non-regular payload entry")
            body = archive.read(item)
            if (asset / slug / name).read_bytes() != body:
                raise ValueError("Source changed after canonical packaging")
            entries[name] = body
    if not {"manifest.json", "README.md"} <= entries.keys():
        raise ValueError("Missing native entry files")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, body in sorted(entries.items()):
            item = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(item, body)
    directory = root / "dist" / slug / version
    directory.mkdir(parents=True, exist_ok=True)
    companion = directory / f"{slug}-{version}-workswarm.zip"
    content = out.getvalue()
    if companion.exists() and companion.read_bytes() != content:
        raise ValueError("Refusing to overwrite a different existing test ZIP; archive it first")
    companion.write_bytes(content)
    report = {
        "version": version, "canonical_zip": str(canonical), "canonical_sha256": canonical_sha,
        "workswarm_zip": str(companion), "workswarm_sha256": hashlib.sha256(content).hexdigest(),
        "payload_files": {name: hashlib.sha256(body).hexdigest() for name, body in sorted(entries.items())},
        "payload_equality": "Every native file is byte-identical to the canonical ZIP inner payload.",
    }
    (directory / "companion-artifact.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
