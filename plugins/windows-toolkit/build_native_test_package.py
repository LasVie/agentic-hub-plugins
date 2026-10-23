"""Build the flat importer ZIP from the checked canonical release payload."""
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile


def main():
    asset = Path(__file__).resolve().parent
    root = asset.parents[1]
    meta = json.loads((asset / "asset.json").read_text(encoding="utf-8"))
    name, version = meta["name"], meta["version"]
    payload = asset / name
    release = root / "releases" / "agent-plugin" / name / version
    record = json.loads((release / "artifact.json").read_text(encoding="utf-8"))
    canonical = release / record["zip"]
    assert hashlib.sha256(canonical.read_bytes()).hexdigest() == record["sha256"]
    prefix = f"{name}/{name}/"
    buffer = io.BytesIO()
    with zipfile.ZipFile(canonical) as source, zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as target:
        assert source.testzip() is None
        for relative, expected in sorted(record["payload_sha256"].items()):
            body = source.read(prefix + relative)
            assert body == (payload / relative).read_bytes(), relative
            assert hashlib.sha256(body).hexdigest() == expected, relative
            assert b"\r\n" not in body, f"Build from an LF checkout: {relative}"
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            target.writestr(info, body)
    destination = asset / "test-packages" / f"{name}-{version}-native.zip"
    body = buffer.getvalue()
    if destination.exists() and destination.read_bytes() != body:
        raise ValueError("Existing native ZIP differs; use a new package version")
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(body)
    print(json.dumps({"version": version, "native_zip": str(destination.relative_to(root)), "native_sha256": hashlib.sha256(body).hexdigest(), "canonical_sha256": record["sha256"], "payload_files": len(record["payload_sha256"])}))


if __name__ == "__main__":
    main()
