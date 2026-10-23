"""Build a deterministic flat native test ZIP from the canonical release payload."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

def main():
    asset = Path(__file__).resolve().parent
    repo = asset.parents[1]
    meta = json.loads((asset / "asset.json").read_text(encoding="utf-8"))
    slug, version = meta["name"], meta["version"]
    release = repo / "releases/agent-plugin" / slug / version
    canonical = release / f"{slug}-{version}.zip"
    prefix = f"{slug}/{slug}/"
    buffer = io.BytesIO()
    with zipfile.ZipFile(canonical) as source, zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as target:
        for name in sorted(source.namelist()):
            if name.startswith(prefix) and not name.endswith("/"):
                info = zipfile.ZipInfo(name[len(prefix):], date_time=(2020, 1, 1, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                target.writestr(info, source.read(name))
    destination = repo / ".research/test-packages"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{slug}-{version}-workswarm.zip"
    body = buffer.getvalue()
    path.write_bytes(body)
    record = {"version": version, "path": str(path), "sha256": hashlib.sha256(body).hexdigest(), "purpose": "Local native import test; payload bytes match the canonical marketplace ZIP."}
    path.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))

if __name__ == "__main__":
    main()
