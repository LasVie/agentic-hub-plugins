"""生成与市场包装具有相同载荷的确定性 WorkSwarm 原生测试 ZIP。"""
import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

ASSET = Path(__file__).resolve().parent
REPO = ASSET.parents[1]
META = json.loads((ASSET / "asset.json").read_text())
SLUG, VERSION = META["name"], META["version"]
PAYLOAD = ASSET / SLUG
TARGET = ASSET / "test-packages" / f"{SLUG}-{VERSION}-workswarm.zip"
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
    for path in sorted(PAYLOAD.rglob("*")):
        assert not path.is_symlink() and "__pycache__" not in path.parts
        if path.is_file():
            info = zipfile.ZipInfo(path.relative_to(PAYLOAD).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
data = buffer.getvalue()
if TARGET.exists() and TARGET.read_bytes() != data:
    raise SystemExit("已有同版本原生 ZIP 内容不同；请先调整版本，不覆盖已确认包。")
TARGET.parent.mkdir(exist_ok=True)
TARGET.write_bytes(data)
destination = REPO / "dist" / SLUG / VERSION
destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(TARGET, destination / TARGET.name)
canonical = REPO / "releases/agent-plugin" / SLUG / VERSION / f"{SLUG}-{VERSION}.zip"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
record = {"version": VERSION, "workswarm_zip": str(destination / TARGET.name),
          "workswarm_sha256": sha(TARGET), "canonical_zip": str(canonical),
          "canonical_sha256": sha(canonical),
          "payload_files": {p.relative_to(PAYLOAD).as_posix(): sha(p)
                            for p in sorted(PAYLOAD.rglob("*")) if p.is_file()}}
(destination / "companion-artifact.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in record.items() if k != "payload_files"}, ensure_ascii=False, indent=2))
