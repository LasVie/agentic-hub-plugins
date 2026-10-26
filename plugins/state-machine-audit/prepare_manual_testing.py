"""准备本插件的公开虚构模型；不覆盖用户已修改的测试文件。"""
import hashlib
import json
from pathlib import Path

ASSET = Path(__file__).resolve().parent
REPO = ASSET.parents[1]
VERSION = json.loads((ASSET / "asset.json").read_text())["version"]
DEST = REPO / "dist/state-machine-audit" / VERSION / "manual-workspace"
DEST.mkdir(parents=True, exist_ok=True)
hashes = {}
for source in sorted((ASSET / "state-machine-audit/examples").glob("*.json")):
    target = DEST / source.name
    data = source.read_bytes()
    if target.exists() and target.read_bytes() != data:
        raise SystemExit(f"保留已有不同内容，不覆盖：{target}")
    if not target.exists():
        with target.open("xb") as output:
            output.write(data)
    hashes[source.name] = hashlib.sha256(data).hexdigest()
(DEST.parent / "manual-input-hashes.json").write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"workspace": str(DEST), "input_sha256": hashes}, ensure_ascii=False, indent=2))
