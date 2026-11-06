"""Delivery byte identity and isolated real-SDK business-suite entrypoint for adhd-study-coach."""
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
ASSET = ROOT / 'plugins/adhd-study-coach'
PAYLOAD = ASSET / 'adhd-study-coach'
EXPECTED_TESTS = 37


class AdhdStudyCoachPackageTests(unittest.TestCase):
    def test_native_and_market_archives_match_source_and_records(self):
        expected = {p.relative_to(PAYLOAD).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in PAYLOAD.rglob('*') if p.is_file()}
        native = ASSET / 'test-packages/adhd-study-coach-1.0.0-native.zip'
        release = ROOT / 'releases/agent-plugin/adhd-study-coach/1.0.0/adhd-study-coach-1.0.0.zip'
        for archive, prefix in ((native, ''), (release, 'adhd-study-coach/adhd-study-coach/')):
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                actual = {name[len(prefix):]: hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist()
                          if name.startswith(prefix) and (not prefix or name != 'adhd-study-coach/plugin.yaml')}
                self.assertEqual(actual, expected)
        record = json.loads((ASSET / 'test-packages/native-artifact.json').read_text(encoding='utf-8'))
        self.assertEqual(record['sha256'], hashlib.sha256(native.read_bytes()).hexdigest())
        self.assertEqual(record['payload_sha256'], expected)

    def test_bundled_license_is_the_pinned_upstream_text(self):
        provenance = json.loads((ASSET / 'provenance.json').read_text(encoding='utf-8'))
        for source in provenance['sources']:
            for item in source['license_evidence']:
                self.assertEqual(hashlib.sha256((PAYLOAD / item['path']).read_bytes()).hexdigest(), item['sha256'])
        self.assertIn('Copyright (c) 2026 Aalaa Fahiem', (PAYLOAD / 'licenses/adhd-study-coach/LICENSE').read_text(encoding='utf-8'))

    def test_real_sdk_business_suite_in_fresh_process(self):
        if importlib.util.find_spec('openjiuwen') is None:
            self.skipTest('Host SDK is not installed in the packaging-only environment')
        with tempfile.TemporaryDirectory(prefix='adhd-unit-') as working:
            env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable, '-B', str(ASSET / 'tests/test_adapter.py')], cwd=working, env=env, text=True,
                                    encoding='utf-8', capture_output=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-5000:])
        self.assertIn(f'Ran {EXPECTED_TESTS} tests', result.stderr)
        self.assertNotIn('skipped=', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
