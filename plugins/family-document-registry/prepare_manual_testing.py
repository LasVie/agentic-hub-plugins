"""准备公开虚构的中文手测输入，保留已有不同内容，不初始化用户台账。"""
import hashlib
import json
from pathlib import Path

ASSET = Path(__file__).resolve().parent
REPO = ASSET.parents[1]
META = json.loads((ASSET / "asset.json").read_text())
DEST = REPO / "dist" / META["name"] / META["version"] / "manual-workspace"
DEST.mkdir(parents=True, exist_ok=True)
hashes = {}
for source in sorted((ASSET / META["name"] / "examples").rglob("*")):
    if not source.is_file():
        continue
    name = source.relative_to(ASSET / META["name"] / "examples")
    target, raw = DEST / name, source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != raw:
        raise SystemExit(f"已有不同测试文件，保留原内容：{target}")
    if not target.exists():
        with target.open("xb") as f:
            f.write(raw)
    hashes[name.as_posix()] = hashlib.sha256(raw).hexdigest()
(DEST.parent / "manual-input-hashes.json").write_text(json.dumps(hashes, ensure_ascii=False, indent=2)+"\n")
print(json.dumps({"workspace": str(DEST), "input_files": len(hashes), "registry_initialized_by_preparation": False}, ensure_ascii=False, indent=2))
