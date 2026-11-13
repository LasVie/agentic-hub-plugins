"""Deterministic native installation ZIP; refuses to overwrite different bytes of an existing version."""
from pathlib import Path
import hashlib
import io
import json
import zipfile

asset = Path(__file__).resolve().parents[1]
payload = asset / 'adds-up'
manifest = json.loads((payload / 'manifest.json').read_text(encoding='utf-8'))
out = io.BytesIO()
hashes = {}
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED) as archive:
    for path in sorted(payload.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(payload).as_posix()
        assert not any(p.startswith('.') or p in ('__pycache__', 'venv', 'node_modules') for p in Path(rel).parts)
        data = path.read_bytes()
        hashes[rel] = hashlib.sha256(data).hexdigest()
        info = zipfile.ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)
body = out.getvalue()
directory = asset / 'test-packages'
directory.mkdir(exist_ok=True)
target = directory / ('adds-up-' + manifest['version'] + '-native.zip')
if target.exists() and target.read_bytes() != body:
    raise SystemExit('Refusing to overwrite an existing different version ZIP')
target.write_bytes(body)
record = {'version': manifest['version'], 'zip': target.name, 'size_bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(), 'payload_sha256': hashes}
(directory / 'native-artifact.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k: record[k] for k in ('zip', 'size_bytes', 'sha256')}, ensure_ascii=False))
