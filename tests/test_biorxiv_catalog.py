"""Delivery byte identity and isolated real-SDK business-suite entrypoint."""
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT/'plugins/biorxiv-catalog'
PAYLOAD = ASSET/'biorxiv-catalog'

class BiorxivPackageTests(unittest.TestCase):
    def test_native_and_market_archives_match_source_and_records(self):
        expected = {p.relative_to(PAYLOAD).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PAYLOAD.rglob('*') if p.is_file()}
        native = ASSET/'test-packages/biorxiv-catalog-1.0.0-native.zip'
        release = ROOT/'releases/agent-plugin/biorxiv-catalog/1.0.0/biorxiv-catalog-1.0.0.zip'
        for archive,prefix in ((native,''),(release,'biorxiv-catalog/biorxiv-catalog/')):
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                actual = {name[len(prefix):]:hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist() if name.startswith(prefix) and (not prefix or name!='biorxiv-catalog/plugin.yaml')}
                self.assertEqual(actual,expected)
        record = json.loads((ASSET/'test-packages/native-artifact.json').read_text(encoding='utf-8'))
        self.assertEqual(record['sha256'],hashlib.sha256(native.read_bytes()).hexdigest())
        self.assertEqual(record['payload_sha256'],expected)

    def test_real_sdk_business_suite_in_fresh_process(self):
        if not all(importlib.util.find_spec(name) is not None for name in ('openjiuwen','mcp','jsonschema','httpx')):
            self.skipTest('Host SDK, MCP and jsonschema are not installed in the packaging-only environment')
        scratch = ROOT/'.research/biorxiv-catalog'
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch,prefix='unit-') as working:
            env = dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable,'-B',str(ASSET/'tests/test_adapter.py')],cwd=working,env=env,text=True,encoding='utf-8',capture_output=True,timeout=90)
        (scratch/'business-last.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        self.assertEqual(result.returncode,0,(result.stdout+result.stderr)[-5000:])
        self.assertIn('Ran 12 tests',result.stderr)
        self.assertNotIn('skipped=',result.stderr)

if __name__=='__main__':
    unittest.main(verbosity=2)
