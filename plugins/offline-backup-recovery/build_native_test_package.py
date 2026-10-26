"""Build deterministic native WorkSwarm test ZIP with the exact canonical payload."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ASSET = Path(__file__).resolve().parent
REPO = ASSET.parents[1]
META = json.loads((ASSET/'asset.json').read_text())
SLUG, VERSION = META['name'], META['version']
PAYLOAD = ASSET/SLUG
TARGET = ASSET/'test-packages'/f'{SLUG}-{VERSION}-workswarm.zip'
TARGET.parent.mkdir(exist_ok=True)
import io
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as z:
    for p in sorted(PAYLOAD.rglob('*')):
        if p.is_file():
            assert not p.is_symlink() and '__pycache__' not in p.parts
            info=zipfile.ZipInfo(p.relative_to(PAYLOAD).as_posix(),(1980,1,1,0,0,0))
            info.create_system=3;info.external_attr=0o100644<<16
            z.writestr(info,p.read_bytes())
body=buffer.getvalue()
if TARGET.exists() and TARGET.read_bytes()!=body:raise SystemExit('Existing version differs; bump version')
TARGET.write_bytes(body)
dest=REPO/'dist'/SLUG/VERSION;dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(TARGET,dest/TARGET.name)
canonical=REPO/'releases/agent-plugin'/SLUG/VERSION/f'{SLUG}-{VERSION}.zip'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'version':VERSION,'workswarm_zip':str(dest/TARGET.name),'workswarm_sha256':sha(TARGET),'canonical_zip':str(canonical),'canonical_sha256':sha(canonical),'payload_files':{p.relative_to(PAYLOAD).as_posix():sha(p) for p in sorted(PAYLOAD.rglob('*')) if p.is_file()}}
(dest/'companion-artifact.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='payload_files'},ensure_ascii=False,indent=2))
