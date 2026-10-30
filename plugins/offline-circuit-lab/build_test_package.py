"""Build a deterministic native ZIP from the canonical, already checked payload."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

ASSET=Path(__file__).resolve().parent
ROOT=ASSET.parents[1]
META=json.loads((ASSET/'asset.json').read_text())
SLUG,VERSION=META['name'],META['version']


def main():
    canonical=ROOT/f'releases/agent-plugin/{SLUG}/{VERSION}/{SLUG}-{VERSION}.zip'
    prefix=f'{SLUG}/{SLUG}/'
    with zipfile.ZipFile(canonical) as z:files={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
    assert 'manifest.json' in files and not any('__pycache__' in n for n in files)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_STORED) as z:
        for n,data in sorted(files.items()):
            info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,data)
    data=buffer.getvalue();native=ASSET/'test-packages'/f'{SLUG}-{VERSION}-workswarm.zip';native.parent.mkdir(exist_ok=True)
    if native.exists() and native.read_bytes()!=data:raise SystemExit('Existing version differs; bump version')
    native.write_bytes(data)
    dist=ROOT/f'dist/{SLUG}/{VERSION}';dist.mkdir(parents=True,exist_ok=True)
    (dist/native.name).write_bytes(data)
    record={'version':VERSION,'canonical_zip':str(canonical),'canonical_sha256':hashlib.sha256(canonical.read_bytes()).hexdigest(),'workswarm_zip':str(dist/native.name),'workswarm_sha256':hashlib.sha256(data).hexdigest(),'payload_identical':True,'payload_files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
    (dist/'companion-artifact.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='payload_files'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
