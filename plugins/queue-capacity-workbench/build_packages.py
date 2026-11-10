"""Verify canonical payload equality; derive native ZIP and extraction for tests."""
from pathlib import Path
import hashlib
import io
import json
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ASSET = Path(__file__).resolve().parent
SLUG = 'queue-capacity-workbench'
VERSION = '1.0.1'

def digest(data): return hashlib.sha256(data).hexdigest()

def build():
    release = ROOT / 'releases/agent-plugin' / SLUG / VERSION
    canonical = release / f'{SLUG}-{VERSION}.zip'
    record = json.loads((release/'artifact.json').read_text())
    assert record['sha256'] == digest(canonical.read_bytes())
    source = {p.relative_to(ASSET/SLUG).as_posix():p.read_bytes() for p in (ASSET/SLUG).rglob('*') if p.is_file()}
    assert all(not p.is_symlink() for p in (ASSET/SLUG).rglob('*'))
    assert not any('__pycache__' in n or n.endswith('.pyc') for n in source)
    with zipfile.ZipFile(canonical) as archive:
        prefix=f'{SLUG}/{SLUG}/'
        inner={n[len(prefix):]:archive.read(n) for n in archive.namelist() if n.startswith(prefix) and not n.endswith('/')}
    assert source == inner
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as z:
        for n,data in sorted(inner.items()):
            info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16;z.writestr(info,data)
    dest=ASSET/'test-packages'/f'{SLUG}-{VERSION}-workswarm.zip';dest.parent.mkdir(exist_ok=True)
    if dest.exists(): assert dest.read_bytes()==output.getvalue(), 'Test ZIP exists with different bytes; preserve evidence and review change.'
    else: dest.write_bytes(output.getvalue())
    record={'plugin_id':SLUG,'version':VERSION,'display_name':'离线排队容量实验台','canonical_zip':str(canonical.relative_to(ROOT)),'canonical_sha256':digest(canonical.read_bytes()),'native_zip':str(dest.relative_to(ROOT)),'native_sha256':digest(dest.read_bytes()),'payload_identical':True,'payload_sha256':{n:digest(b) for n,b in sorted(source.items())}}
    (dest.parent/'companion-artifact.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='payload_sha256'},ensure_ascii=False,indent=2))

if __name__=='__main__':build()
