"""Create an AgentGroup wrapper with the official CLI and a native test ZIP."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

BASE = Path(__file__).resolve().parent
CLI_REF = 'c8ee4ef44be0453470114aa5a19f4e1017462907'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(archive, entries):
    with zipfile.ZipFile(archive) as z:
        info = z.infolist()
        if len(info) != len(entries) or set(z.namelist()) != set(entries) or z.testzip() is not None:
            raise ValueError('archive entries or CRC differ')
        if archive.stat().st_size > 95 << 20 or len(info) > 1000 or sum(i.file_size for i in info) > 512 << 20:
            raise ValueError('archive size or entry count exceeds limit')
        for i in info:
            path = PurePosixPath(i.filename)
            if (path.is_absolute() or '..' in path.parts or i.is_dir() or '\\' in i.filename
                    or stat.S_ISLNK(i.external_attr >> 16) or i.file_size > 50 * max(i.compress_size, 1)
                    or z.read(i) != entries[i.filename]):
                raise ValueError(f'invalid archive member: {i.filename}')


def keep(source, dest, entries):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        with dest.open('xb') as out:
            out.write(source.read_bytes())
    verify(dest, entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable, help='Python for the official CLI; its module must be importable')
    parser.add_argument('--scratch', type=Path, required=True, help='parent directory for clean staging')
    args = parser.parse_args()
    meta = json.loads((BASE / 'asset.json').read_text(encoding='utf-8'))
    slug, version = meta['name'], meta['version']
    root = BASE / slug
    payload = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or '__pycache__' in path.relative_to(root).parts or path.suffix == '.pyc':
            raise ValueError(f'unsafe runtime entry: {path}')
        if path.is_file():
            payload[path.relative_to(root).as_posix()] = path.read_bytes()
    manifest = json.loads(payload['manifest.json'])
    if (manifest['name'], manifest['version'], manifest['package_type']) != (slug, version, 'agent_group'):
        raise ValueError('native manifest identity mismatch')
    with tempfile.TemporaryDirectory(prefix='stocktake-pack-', dir=args.scratch) as tmp:
        tmp = Path(tmp)
        stage = tmp / slug
        stage.mkdir()
        shutil.copytree(root, stage / slug)
        wrapper = (f'name: {slug}\nversion: {version}\n'
                   f'display_name: {meta["display_name"]}\ndescription: {meta["description"]}\n'
                   f'runtime:\n  type: agent-group\nmetadata:\n  author: {meta["publisher"]}\n'
                   '  tags: [库存, 盘点, 差异复核]\n').encode('utf-8')
        (stage / 'plugin.yaml').write_bytes(wrapper)
        command = [args.python, '-B', '-m', 'openjiuwen_agentichub.main']
        subprocess.run(command + ['validate', str(stage)], check=True)
        subprocess.run(command + ['pack', str(stage), '--output', str(tmp / 'out')], check=True)
        packed, = (tmp / 'out').glob('*.zip')
        outer = f'{slug}-{version}'
        wrapped_entries = {f'{outer}/{slug}/{name}': val for name, val in payload.items()}
        wrapped_entries[f'{outer}/plugin.yaml'] = wrapper
        verify(packed, wrapped_entries)
        native = tmp / 'native.zip'
        with zipfile.ZipFile(native, 'w', compression=zipfile.ZIP_STORED) as z:
            for name, val in payload.items():
                info = zipfile.ZipInfo(name, (2026, 11, 20, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                z.writestr(info, val)
        verify(native, payload)
        release = BASE / 'release' / version
        target = release / f'{slug}-{version}-agent-group.zip'
        test = BASE / 'test-packages' / f'{slug}-{version}-native.zip'
        keep(packed, target, wrapped_entries)
        keep(native, test, payload)
        artifact = dict(name=slug, version=version, type='agent-group', official_cli_version='0.0.1',
                        official_cli_ref=CLI_REF, payload_sha256={n: sha(v) for n, v in payload.items()},
                        archives={kind: {'path': p.relative_to(BASE).as_posix(), 'sha256': sha(p.read_bytes())}
                                  for kind, p in [('wrapper', target), ('native', test)]},
                        source_review_sha256=sha((BASE / 'SOURCE_REVIEW.md').read_bytes()),
                        test_report_sha256=sha((BASE / 'TEST_REPORT.md').read_bytes()))
        (release / 'artifact.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(artifact['archives'], indent=2))


if __name__ == '__main__':
    main()
