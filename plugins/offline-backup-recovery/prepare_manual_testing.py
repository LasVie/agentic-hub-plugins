"""Prepare synthetic Chinese manual fixtures outside the delivered payload; never overwrite."""
from pathlib import Path
import hashlib
import json

REPO=Path(__file__).resolve().parents[2]
BASE=REPO/'dist/offline-backup-recovery/1.0.0/manual-test'
BASE.mkdir(parents=True,exist_ok=False)
source=BASE/'示例源目录';source.mkdir()
(source/'嵌套目录').mkdir();(source/'空目录').mkdir()
(source/'说明.txt').write_bytes('这是离线备份人工测试。\r\n中文与表情🙂。\n'.encode())
(source/'嵌套目录/数据.json').write_text(json.dumps({'用途':'合成测试','数值':[1,2,3]},ensure_ascii=False)+'\n')
(source/'二进制.bin').write_bytes(bytes(range(256))*16)
files={p.relative_to(source).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in source.rglob('*') if p.is_file()}
(BASE/'expected-source.json').write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n')
# Explicit malformed input, not a fabricated successful backup.
(BASE/'损坏示例.zip').write_bytes(b'not a valid ZIP backup\x00')
print(json.dumps({'source_dir':str(source),'archive_path':str(BASE/'人工测试备份.zip'),'target_dir':str(BASE/'人工测试恢复'),'expected_files':len(files),'expected_directories':2,'expected_bytes':sum(v['bytes'] for v in files.values())},ensure_ascii=False,indent=2))
