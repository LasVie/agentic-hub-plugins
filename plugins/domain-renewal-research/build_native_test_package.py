"""Build a deterministic flat importer ZIP from the checked canonical release."""
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile


def main():
    asset = Path(__file__).resolve().parent
    root = asset.parents[1]
    meta = json.loads((asset / 'asset.json').read_text(encoding='utf-8'))
    name, version = meta['name'], meta['version']
    release = root / 'releases/agent-plugin' / name / version
    record = json.loads((release / 'artifact.json').read_text(encoding='utf-8'))
    canonical = release / record['zip']
    assert hashlib.sha256(canonical.read_bytes()).hexdigest() == record['sha256']
    buffer = io.BytesIO()
    with zipfile.ZipFile(canonical) as source, zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as target:
        assert source.testzip() is None
        for relative, expected in sorted(record['payload_sha256'].items()):
            data = source.read(f'{name}/{name}/{relative}')
            assert data == (asset / name / relative).read_bytes()
            assert hashlib.sha256(data).hexdigest() == expected
            assert b'\r\n' not in data, relative
            data.decode('utf-8')
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            target.writestr(info, data)
    destination = asset / 'test-packages' / f'{name}-{version}-native.zip'
    data = buffer.getvalue()
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError('Existing native ZIP differs; use a new version')
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(data)
    print(json.dumps({'native_zip': str(destination), 'native_sha256': hashlib.sha256(data).hexdigest(), 'canonical_sha256': record['sha256'], 'payload_files': len(record['payload_sha256'])}))


if __name__ == '__main__':
    main()
