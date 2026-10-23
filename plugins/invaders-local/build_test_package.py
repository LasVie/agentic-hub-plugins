"""从规范 ZIP 提取相同载荷，为旧 WorkSwarm 生成确定性原生 ZIP。"""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SLUG = 'invaders-local'
VERSION = '1.0.2'


def main():
    canonical = ROOT / f'releases/agent-plugin/{SLUG}/{VERSION}/{SLUG}-{VERSION}.zip'
    target = ROOT / f'dist/{SLUG}/{VERSION}/{SLUG}-{VERSION}-workswarm.zip'
    prefix = f'{SLUG}/{SLUG}/'
    with zipfile.ZipFile(canonical) as source:
        entries = {n[len(prefix):]: source.read(n) for n in source.namelist() if n.startswith(prefix) and not n.endswith('/')}
    assert 'manifest.json' in entries
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 23, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    data = buffer.getvalue()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != data:
        raise SystemExit('目标版本已存在且内容不同；请创建新版本，不得覆盖。')
    target.write_bytes(data)
    result = {'canonical_path': str(canonical), 'canonical_sha256': hashlib.sha256(canonical.read_bytes()).hexdigest(),
              'workswarm_path': str(target), 'workswarm_sha256': hashlib.sha256(data).hexdigest(),
              'payload_files': {n: hashlib.sha256(b).hexdigest() for n,b in sorted(entries.items())},
              'payload_byte_identical': True, 'version': VERSION}
    (target.parent/'artifact.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
