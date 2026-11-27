"""Build and verify local native and official Hub-format archives."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_STORED

import yaml

ASSET = Path(__file__).resolve().parent
CLI_REF = 'c8ee4ef44be0453470114aa5a19f4e1017462907'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_zip(blob, expected):
    with ZipFile(blob) as z:
        records = z.infolist()
        names = [r.filename for r in records]
        if len(set(names)) != len(names) or set(names) != expected.keys() or z.testzip() is not None:
            raise ValueError('Unexpected ZIP members or corrupt bytes')
        if blob.stat().st_size > 95 * 1024**2 or len(names) > 1000 or sum(r.file_size for r in records) > 512 * 1024**2:
            raise ValueError('ZIP exceeds size or count limits')
        for r in records:
            if stat.S_ISLNK(r.external_attr >> 16) or r.file_size > 50 * max(r.compress_size, 1):
                raise ValueError(f'Unsafe ZIP member: {r.filename}')
            if z.read(r) != expected[r.filename]:
                raise ValueError(f'ZIP bytes differ: {r.filename}')


def save_zip(source, dest, expected):
    check_zip(source, expected)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream:
            stream.write(source.read_bytes())
    check_zip(dest, expected)
    return {'path': dest.relative_to(ASSET).as_posix(), 'sha256': digest(dest.read_bytes())}


def main():
    meta = json.loads((ASSET / 'asset.json').read_bytes())
    slug, version = meta['name'], meta['version']
    native = ASSET / slug
    payload = {}
    for file in sorted(native.rglob('*')):
        rel = file.relative_to(native)
        if file.is_symlink() or '__pycache__' in rel.parts or file.suffix == '.pyc':
            raise ValueError(f'Unsafe native entry: {rel}')
        if file.is_file():
            payload[rel.as_posix()] = file.read_bytes()
    manifest = json.loads(payload['manifest.json'])
    if (manifest['name'], manifest['version'], manifest['package_type']) != (slug, version, 'agent_group'):
        raise ValueError('Manifest identity mismatch')
    wrapper = yaml.safe_dump({k: meta[k] for k in ('name', 'version', 'display_name', 'description')} | {
        'runtime': {'type': 'agent-group'}, 'metadata': {'author': meta['publisher'], 'tags': meta['tags']}
    }, allow_unicode=True, sort_keys=False).encode('utf-8')
    prefix = f'{slug}-{version}'
    release = ASSET / 'release' / version
    expected = {f'{prefix}/{slug}/{name}': val for name, val in payload.items()}
    expected[f'{prefix}/plugin.yaml'] = wrapper
    with tempfile.TemporaryDirectory(prefix='survey-pack-', dir=Path(sys.argv[1])) as scratch:
        build = Path(scratch)
        stage = build / 'stage'
        for rel, data in {'plugin.yaml': wrapper, **{f'{slug}/{k}': v for k, v in payload.items()}}.items():
            path = stage / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        cli = [sys.executable, '-B', '-m', 'openjiuwen_agentichub.main']
        subprocess.run([*cli, 'validate', str(stage)], check=True)
        subprocess.run([*cli, 'pack', str(stage), '--output', str(build / 'out')], check=True)
        packed, = (build / 'out').glob('*.zip')
        native_tmp = build / 'native.zip'
        with ZipFile(native_tmp, 'w', compression=ZIP_STORED) as z:
            for rel, data in payload.items():
                z.writestr(rel, data)
        artifacts = {'wrapper': save_zip(packed, release / f'{prefix}-agent-group.zip', expected),
                     'native': save_zip(native_tmp, ASSET / 'test-packages' / f'{prefix}-native.zip', payload)}
    artifact = dict(name=slug, version=version, type='agent-group', official_cli_version='0.0.1',
                    official_cli_ref=CLI_REF, archives=artifacts, payload_sha256={k: digest(v) for k, v in payload.items()},
                    source_review_sha256=digest((ASSET / 'SOURCE_REVIEW.md').read_bytes()),
                    test_report_sha256=digest((ASSET / 'TEST_REPORT.md').read_bytes()))
    (release / 'artifact.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(artifacts, indent=2))


if __name__ == '__main__':
    main()
