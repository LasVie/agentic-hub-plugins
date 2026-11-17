#!/usr/bin/env python3
"""Build this asset with the pinned external official CLI; inspect every payload byte."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

BASE = Path(__file__).resolve().parent
SLUG = 'logic-grid-puzzle-team'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def install_archive(candidate, destination):
    if destination.exists():
        with zipfile.ZipFile(candidate) as a, zipfile.ZipFile(destination) as b:
            if {n: a.read(n) for n in a.namelist()} == {n: b.read(n) for n in b.namelist()}:
                return
        raise ValueError('已有不同包内容；保留旧包，提升版本后重新构建和手测')
    with destination.open('xb') as handle:
        handle.write(candidate.read_bytes())


def main():
    parser = argparse.ArgumentParser(description='构建原生与市场包并逐文件核对')
    parser.add_argument('--python', required=True, help='已配置官方CLI依赖的Python')
    parser.add_argument('--cli-root', required=True, help='固定提交的skillhub/cli目录')
    args = parser.parse_args()
    meta = json.loads((BASE / 'asset.json').read_text())
    version = meta['version']
    payload = BASE / SLUG
    files = {}
    for path in sorted(payload.rglob('*')):
        if path.is_symlink():
            raise ValueError('符号链接不得进入包')
        if path.is_file():
            rel = path.relative_to(payload).as_posix()
            if any(p in ('__pycache__', '.local', '.git') for p in path.parts) or path.suffix == '.pyc':
                raise ValueError('开发缓存不得进入包')
            files[rel] = path.read_bytes()
    stage_parent = BASE / '.local' / 'staging'
    stage_parent.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='build-', dir=stage_parent))
    env = dict(os.environ, PYTHONPATH=str(Path(args.cli_root).resolve()), PYTHONDONTWRITEBYTECODE='1')
    cli = [args.python, '-B', '-m', 'openjiuwen_agentichub.main']
    subprocess.run(cli + ['init', SLUG, '--type', 'agent-group', '--path', str(run)], env=env, check=True)
    stage = run / SLUG
    # Only the scaffold just created in this unique owned directory is replaced.
    shutil.rmtree(stage / SLUG)
    shutil.copytree(payload, stage / SLUG)
    (stage / 'plugin.yaml').write_text(
        f'name: {SLUG}\nversion: {version}\ndisplay_name: 逻辑网格谜题编制与验解专家团\n'
        'description: 原创中文配对谜题，经过完整解数计算与独立题面复核，交付分离题面、答案和审计记录。\n'
        'runtime:\n  type: agent-group\nmetadata:\n  author: Cai Zhenze\n'
        '  tags: [逻辑谜题, 独立验解, 有限约束]\n', encoding='utf-8')
    subprocess.run(cli + ['validate', str(stage)], env=env, check=True)
    out = run / 'out'
    subprocess.run(cli + ['pack', str(stage), '--output', str(out)], env=env, check=True)
    packed, = out.glob('*.zip')
    release = BASE / 'release' / version
    release.mkdir(parents=True, exist_ok=True)
    wrapped = release / f'{SLUG}-{version}-agent-group.zip'
    native = BASE / 'test-packages' / f'{SLUG}-{version}-native.zip'
    native.parent.mkdir(exist_ok=True)
    draft_native = run / 'native.zip'
    with zipfile.ZipFile(draft_native, 'w', compression=zipfile.ZIP_STORED) as z:
        for rel, data in files.items():
            zi = zipfile.ZipInfo(rel, (2026, 11, 17, 0, 0, 0))
            zi.external_attr = 0o100644 << 16
            z.writestr(zi, data)
    install_archive(packed, wrapped)
    install_archive(draft_native, native)
    outer = SLUG + '-' + version
    for archive, prefix in ((native, ''), (wrapped, outer + '/' + SLUG + '/')):
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            assert len(names) == len(set(names)) and len(names) <= 1000
            assert z.testzip() is None
            for info in z.infolist():
                assert not info.filename.startswith('/') and '..' not in Path(info.filename).parts
                assert info.file_size / max(info.compress_size, 1) <= 50
            actual = {n[len(prefix):]: z.read(n) for n in names if n.startswith(prefix) and not n.endswith('/')}
            if prefix:
                actual = {n: b for n, b in actual.items() if n in files}
                allowed = {outer + '/plugin.yaml'} | {prefix + n for n in files}
                assert set(names) == allowed, set(names) ^ allowed
            assert actual == files
        assert archive.stat().st_size <= 95 * 1024 * 1024
    artifact = {'asset': SLUG, 'type': 'agent-group', 'version': version,
                'task_id': meta['task_id'], 'tool': {'name': 'official agentichub', 'version': '0.0.1',
                'commit': 'c8ee4ef44be0453470114aa5a19f4e1017462907'},
                'payload_sha256': {n: sha(b) for n, b in files.items()},
                'artifacts': {kind: {'path': str(path.relative_to(BASE)), 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size}
                              for kind, path in [('native', native), ('wrapped', wrapped)]},
                'source_review_sha256': sha((BASE / 'SOURCE_REVIEW.md').read_bytes()),
                'test_report_sha256': sha((BASE / 'TEST_REPORT.md').read_bytes()),
                'payload_equality': True}
    (release / 'artifact.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(artifact['artifacts'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
