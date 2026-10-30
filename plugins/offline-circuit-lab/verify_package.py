"""Inspect both final archives and run analytical checks on extracted source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ASSET = Path(__file__).resolve().parent
SLUG = 'offline-circuit-lab'
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
    assert manifest['display_name']['zh'] == '离线电路实验室'
    for entry in manifest['tools']: assert entry['file'] in native_files
    for entry in manifest['skills']: assert entry['dir']+'/SKILL.md' in native_files
    provenance = json.loads((ASSET/'provenance.json').read_text())
    for source in provenance['sources']:
        for evidence in source['license_evidence']:
            assert digest(native_files[evidence['path']]) == evidence['sha256']
    assert b'GNU GENERAL PUBLIC LICENSE' in native_files['licenses/circuitjs/LICENSE']
    assert 'GPL-2.0-or-later' in native_files['THIRD_PARTY_NOTICES.md'].decode()
    assert 'license.txt' in native_files['web/index.html'].decode()
    with tempfile.TemporaryDirectory() as temporary:
        payload = Path(temporary)
        for name, data in native_files.items():
            file = payload/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        spec = importlib.util.spec_from_file_location('archived_circuit_solver', payload/'runtime/solver.py')
        solver = importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
        def rlc(r=1000):
            return {'components':[{'id':'电源','type':'V','a':'输入','b':'0','value':5},{'id':'电阻','type':'R','a':'输入','b':'输出','value':r},{'id':'电容','type':'C','a':'输出','b':'0','value':1e-6}], 'duration_ms':1,'step_us':10,'probe':'输出'}
        fast, slow = solver.simulate(rlc()), solver.simulate(rlc(2000))
        assert fast['ok'] and slow['ok']
        assert abs(fast['summary']['final_voltage']-3.1606028)<.001
        assert abs(slow['summary']['final_voltage']-1.9673467)<.001
        broken = solver.simulate({'components':[]})
        assert not broken['ok'] and any('\u4e00'<=c<='\u9fff' for c in broken['error']['message'])
    artifact = json.loads(canonical.with_name('artifact.json').read_text())
    assert artifact['sha256'] == digest(canonical.read_bytes())
    report = {'plugin_id':SLUG,'version':VERSION,'canonical_zip':str(canonical.relative_to(ROOT)),
      'canonical_sha256':digest(canonical.read_bytes()),'native_zip':str(native.relative_to(ROOT)),
      'native_sha256':digest(native.read_bytes()),'payload_identical':True,'payload_files':len(native_files),
      'files_sha256':{n:digest(b) for n,b in sorted(native_files.items())},
      'declared_paths_verified':True,'license_hashes_verified':True,'utf8_files_verified':True,
      'extracted_chinese_rc_volts':fast['summary']['final_voltage'],'extracted_chinese_rc_2k_volts':slow['summary']['final_voltage'],
      'extracted_chinese_error':broken['error'],'passed':True,
      'scope':'Archive, extracted numerical functionality and language checks; not user/model conversation or manual testing.'}
    (ASSET/'package-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files_sha256'},ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
