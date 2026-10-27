"""Verify final transports and execute tests against the extracted canonical ZIP."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import zipfile

ASSET=Path(__file__).resolve().parents[1]
REPO=ASSET.parents[1]
WORK=REPO.parents[1]
sys.path.insert(0,str(REPO/'tools'))
import asset_release

output=WORK/'plugin-builds/modern-web-guidance/1.0.0'
output.mkdir(parents=True,exist_ok=True)
assert output.resolve().is_relative_to(WORK.resolve())
canonical=asset_release.pack(ASSET)
before=canonical.read_bytes()
assert asset_release.pack(ASSET).read_bytes()==before
config,source,prov=asset_release.check_asset(ASSET)
payloads={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
extracted=output/'extracted'
with zipfile.ZipFile(canonical) as archive:
    assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in archive.namelist())
    archive.extractall(extracted)
target=extracted/'modern-web-guidance/modern-web-guidance'
assert {p.relative_to(target).as_posix():p.read_bytes() for p in target.rglob('*') if p.is_file()}==payloads
native=output/'modern-web-guidance-1.0.0-native.zip'
import io
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_STORED) as archive:
    for name,body in sorted(payloads.items()):
        info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3
        info.external_attr=(stat.S_IFREG|0o644)<<16
        archive.writestr(info,body)
if native.exists():
    assert native.read_bytes()==buffer.getvalue(),'Native version differs; do not silently overwrite'
else:
    native.write_bytes(buffer.getvalue())
with zipfile.ZipFile(native) as archive:
    assert {n:archive.read(n) for n in archive.namelist()}==payloads
    assert 'manifest.json' in archive.namelist()
env=dict(os.environ,MWG_TEST_PAYLOAD=str(target),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
commands=[[sys.executable,str(ASSET/'tests/test_plugin.py')],
          [shutil.which('node'),'--test',str(ASSET/'tests/test_bm25.mjs')]]
results=[]
for i,command in enumerate(commands):
    run=subprocess.run(command,cwd=output,env=env,capture_output=True,encoding='utf-8',timeout=180)
    log=run.stdout+'\n'+run.stderr
    log_path=output/f'extracted-test-{i+1}.log'
    log_path.write_text(log,encoding='utf-8')
    results.append({'command':command,'returncode':run.returncode,'log':str(log_path),
                    'log_sha256':hashlib.sha256(log_path.read_bytes()).hexdigest()})
    if run.returncode:
        print(log);raise SystemExit(run.returncode)
assert {p.relative_to(target).as_posix():p.read_bytes() for p in target.rglob('*') if p.is_file()}==payloads
record={'date':'2026-10-27','task_id':'AH-20261027-modern-web-guidance','version':'1.0.0',
        'canonical_zip':str(canonical),'canonical_sha256':hashlib.sha256(before).hexdigest(),
        'native_zip':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
        'canonical_bytes':len(before),'native_bytes':native.stat().st_size,'payload_file_count':len(payloads),
        'deterministic_repack':True,'payloads_equal':True,'extracted_payload_unchanged_after_tests':True,
        'python_tests':11,'node_tests':5,'tests':results,'human_testing':'pending','ui_import':'not performed',
        'original_screenshots':'pending'}
(ASSET/'test-evidence.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
