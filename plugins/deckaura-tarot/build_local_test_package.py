#!/usr/bin/env python3
"""Repackage the canonical Hub inner payload for the current local WorkSwarm importer."""
import hashlib
import io
import json
from pathlib import Path
import zipfile


def main():
    asset_dir = Path(__file__).resolve().parent
    repo = asset_dir.parents[1]
    asset = json.loads((asset_dir / "asset.json").read_text())
    name, version = asset["name"], asset["version"]
    canonical = repo / "releases/agent-plugin" / name / version / f"{name}-{version}.zip"
    prefix = f"{name}/{name}/"
    output = io.BytesIO()
    hashes = {}
    with zipfile.ZipFile(canonical) as source, zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as target:
        for path in sorted(source.namelist()):
            if not path.startswith(prefix):
                continue
            relative = path[len(prefix):]
            content = source.read(path)
            item = zipfile.ZipInfo(f"{name}/{relative}", date_time=(2020, 1, 1, 0, 0, 0))
            item.external_attr = 0o100644 << 16
            target.writestr(item, content)
            hashes[relative] = hashlib.sha256(content).hexdigest()
    body = output.getvalue()
    with zipfile.ZipFile(io.BytesIO(body)) as native:
        manifest = json.loads(native.read(f"{name}/manifest.json"))
        assert manifest["id"] == name and manifest["version"] == version
        assert hashes == {p[len(name) + 1:]: hashlib.sha256(native.read(p)).hexdigest() for p in native.namelist()}
    destination = asset_dir / "local-testing" / version
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{name}-{version}-workswarm.zip"
    if path.exists() and path.read_bytes() != body:
        raise SystemExit("Existing local-test version differs; bump the package version.")
    path.write_bytes(body)
    record = {
        "hub_zip": canonical.relative_to(repo).as_posix(),
        "hub_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
        "native_zip": path.name,
        "native_sha256": hashlib.sha256(body).hexdigest(),
        "payload_file_count": len(hashes), "payload_sha256": hashes,
        "payloads_identical": True,
        "purpose": "Local WorkSwarm import only; canonical Hub ZIP remains the repository release artifact.",
    }
    (destination / "artifact.json").write_text(json.dumps(record, indent=2) + "\n")
    print(path)
    print(record["native_sha256"])


if __name__ == "__main__":
    main()
