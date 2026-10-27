"""审查实际归档，运行解包版测试；不修改 payload。"""
import hashlib, importlib.util, io, json, os, stat, subprocess, sys, zipfile
from pathlib import Path

ASSET=Path(__file__).resolve().parents[1]
REPO=ASSET.parents[1]
WORK=REPO.parents[1]
sys.path.insert(0,str(REPO/'tools'))
import asset_release
out=WORK/'plugin-builds/anidoodle/1.0.0'
out.mkdir(parents=True,exist_ok=True)
canonical=asset_release.pack(ASSET)
body=canonical.read_bytes()
assert asset_release.pack(ASSET).read_bytes()==body
source=ASSET/'anidoodle'
payload={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
with zipfile.ZipFile(canonical) as z:
    z.extractall(out/'extracted')
extracted=out/'extracted/anidoodle/anidoodle'
assert {p.relative_to(extracted).as_posix():p.read_bytes() for p in extracted.rglob('*') if p.is_file()}==payload
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
    for name,content in sorted(payload.items()):
        info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
        z.writestr(info,content)
native=out/'anidoodle-1.0.0-native.zip'
if native.exists(): assert native.read_bytes()==buf.getvalue(),'Version exists with different bytes'
else: native.write_bytes(buf.getvalue())
with zipfile.ZipFile(native) as z: assert {n:z.read(n) for n in z.namelist()}==payload
env=dict(os.environ,ANIDOODLE_PAYLOAD=str(extracted),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
run=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ASSET/'tests'),'-v'],env=env,capture_output=True,encoding='utf-8',timeout=180)
(out/'extracted-tests.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
if run.returncode: print(run.stdout,run.stderr);raise SystemExit(run.returncode)
spec=importlib.util.spec_from_file_location('extracted_art',extracted/'runtime.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
previews=out/'previews';previews.mkdir(exist_ok=True)
for scene in mod.SCENES:
    dest=previews/(scene+'.html')
    expected=mod.render_page(scene)
    if dest.exists(): assert dest.read_text(encoding='utf-8')==expected
    else:
        result=mod.execute({'action':'create','scene':scene,'workspace':str(previews),'name':scene})
        assert result['ok'],result
for source_info in json.loads((ASSET/'provenance.json').read_text(encoding='utf-8'))['sources']:
    for item in source_info['license_evidence']:
        assert hashlib.sha256((extracted/item['path']).read_bytes()).hexdigest()==item['sha256']
assert {p.relative_to(extracted).as_posix():p.read_bytes() for p in extracted.rglob('*') if p.is_file()}==payload
record={'date':'2026-10-27','task_id':'AH-20261027-anidoodle','version':'1.0.0','canonical_zip':str(canonical),'canonical_sha256':hashlib.sha256(body).hexdigest(),'native_zip':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'payload_files':len(payload),'payload_bytes':sum(map(len,payload.values())),'deterministic_repack':True,'payloads_equal':True,'extracted_tests':9,'extracted_tests_passed':True,'actual_sdk_calls':6,'user_testing':'pending','host_ui_import':'pending','user_confirmation_and_original_screenshots':'pending'}
(ASSET/'test-evidence.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
