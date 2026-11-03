"""Verify delivered bytes; optionally extract and compare a local host installation."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

REPO = Path(__file__).resolve().parents[2]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def files(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path)
    parser.add_argument('--installed-root', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    records = []
    for item in json.loads((REPO/'tools/dev_five_config.json').read_text()):
        slug, version = item['slug'], item['asset_version']
        outer = REPO/'plugins'/slug
        proof = json.loads((outer/'package-verification.json').read_text())
        canonical = REPO/'releases/agent-plugin'/slug/version/f'{slug}-{version}.zip'
        native = outer/'test-packages'/f'{slug}-{version}-workswarm.zip'
        assert digest(canonical.read_bytes()) == proof['canonical_sha256'], slug
        assert digest(native.read_bytes()) == proof['native_sha256'], slug
        with zipfile.ZipFile(canonical) as archive:
            prefix = f'{slug}/{slug}/'
            inner = {n[len(prefix):]: digest(archive.read(n)) for n in archive.namelist()
                     if n.startswith(prefix) and not n.endswith('/')}
            assert inner == proof['payload_sha256'] == files(outer/slug), slug
            if args.extract:
                for n in archive.namelist():
                    assert not Path(n).is_absolute() and '..' not in Path(n).parts
                archive.extractall(args.extract)
                assert files(args.extract/slug/slug) == inner
        with zipfile.ZipFile(native) as archive:
            assert {n[len(slug)+1:]: digest(archive.read(n)) for n in archive.namelist()
                    if not n.endswith('/')} == inner
        if args.installed_root:
            assert files(args.installed_root/slug) == inner, f'{slug}: installed files differ'
        records.append({'slug': slug, 'version': version, 'files': len(inner),
                        'source_canonical_native_equal': True,
                        'installed_equal': True if args.installed_root else None,
                        'canonical_sha256': proof['canonical_sha256'],
                        'native_sha256': proof['native_sha256']})
    report = json.dumps(records, ensure_ascii=False, indent=2)+'\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report)
    print(report)

if __name__ == '__main__':
    main()
