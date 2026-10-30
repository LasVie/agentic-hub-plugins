"""Inspect both final archives and run analytical checks on extracted source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ASSET = Path(__file__).resolve().parent
SLUG = 'offline-optics-lab'
VERSION = '1.0.0'

def digest(data): return hashlib.sha256(data).hexdigest()

def main():
    canonical = ROOT / f'releases/agent-plugin/{SLUG}/{VERSION}/{SLUG}-{VERSION}.zip'
    native = ASSET / f'test-packages/{SLUG}-{VERSION}-workswarm.zip'
    prefix = f'{SLUG}/{SLUG}/'
    with zipfile.ZipFile(canonical) as z:
        assert z.testzip() is None
        canonical_files = {n[len(prefix):]: z.read(n) for n in z.namelist() if n.startswith(prefix)}
        assert set(z.namelist()) == {f'{SLUG}/plugin.yaml', *(prefix+n for n in canonical_files)}
    with zipfile.ZipFile(native) as z:
        assert z.testzip() is None
        native_files = {n:z.read(n) for n in z.namelist()}
    assert canonical_files == native_files
    local_files = {p.relative_to(ASSET/SLUG).as_posix():p.read_bytes() for p in (ASSET/SLUG).rglob('*') if p.is_file()}
    assert local_files == native_files
    assert not any('__pycache__' in n or n.endswith(('.pyc','.pyo','.zip')) for n in native_files)
    for name in native_files:
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        native_files[name].decode('utf-8')
    manifest = json.loads(native_files['manifest.json'])
    assert manifest['id'] == SLUG and manifest['version'] == VERSION
    assert manifest['display_name']['zh'] == '离线光学实验室'
    for entry in manifest['tools']: assert entry['file'] in native_files
    for entry in manifest['skills']: assert entry['dir']+'/SKILL.md' in native_files
    provenance = json.loads((ASSET/'provenance.json').read_text())
    for source in provenance['sources']:
        for evidence in source['license_evidence']:
            assert digest(native_files[evidence['path']]) == evidence['sha256']
    assert b'Apache License' in native_files['licenses/ray-optics/LICENSE']
    assert 'Apache-2.0' in native_files['THIRD_PARTY_NOTICES.md'].decode()
    assert 'licenses.txt' in native_files['web/index.html'].decode()
    with tempfile.TemporaryDirectory() as temporary:
        payload = Path(temporary)
        for name, data in native_files.items():
            file = payload/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        spec = importlib.util.spec_from_file_location('archived_optics_lab', payload/'runtime/lab.py')
        lab = importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
        examples=json.loads(native_files['engine/examples.json'])
        results={e['id']:lab.engine_call({'scene':e['scene']}) for e in examples}
        assert all(r['ok'] and r['segments'] and r['detectors'] for r in results.values())
        assert abs(abs(results['lens']['detectors'][0]['power'])-1)<1e-9
        changed=json.loads(json.dumps(next(e['scene'] for e in examples if e['id']=='lens')))
        next(o for o in changed['objects'] if o['type']=='IdealLens')['focalLength']=300
        altered=lab.engine_call({'scene':changed})
        assert altered['ok'] and altered['detectors'][0]['binData']!=results['lens']['detectors'][0]['binData']
        broken=lab.engine_call({'scene':{'schema_version':1,'title':'拒绝示例','objects':[],'backgroundImage':'https://example.invalid'}})
        assert not broken['ok'] and any('\u4e00'<=c<='\u9fff' for c in broken['error']['message'])
    artifact = json.loads(canonical.with_name('artifact.json').read_text())
    assert artifact['sha256'] == digest(canonical.read_bytes())
    report = {'plugin_id':SLUG,'version':VERSION,'canonical_zip':str(canonical.relative_to(ROOT)),
      'canonical_sha256':digest(canonical.read_bytes()),'native_zip':str(native.relative_to(ROOT)),
      'native_sha256':digest(native.read_bytes()),'payload_identical':True,'payload_files':len(native_files),
      'files_sha256':{n:digest(b) for n,b in sorted(native_files.items())},
      'declared_paths_verified':True,'license_hashes_verified':True,'utf8_files_verified':True,
      'extracted_examples':{k:{'segments':len(v['segments']),'detectors':v['detectors'],'stats':v['stats']} for k,v in results.items()},
      'edited_focal_length_changes_bins':True,'extracted_chinese_error':broken['error'],'passed':True,
      'scope':'Archive, extracted numerical functionality and language checks; not user/model conversation or manual testing.'}
    (ASSET/'package-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files_sha256'},ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
