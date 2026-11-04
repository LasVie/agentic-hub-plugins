import os
from pathlib import Path
import shutil
import subprocess
import unittest


class ChangeVerificationTests(unittest.TestCase):
    def test_real_git_runtime_regression_suite(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node 20+ is required for this asset')
        version = subprocess.check_output([node, '--version'], text=True).strip()
        if int(version.lstrip('v').split('.')[0]) < 20:
            self.skipTest('Node 20+ is required for this asset')
        if not shutil.which('git'):
            self.skipTest('Git is required for this asset')
        root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env.pop('CHANGE_VERIFICATION_PAYLOAD', None)
        result = subprocess.run([node, '--test', '--test-reporter=tap', str(root / 'plugins/change-verification/tests/runtime.test.mjs')],
                                cwd=root, env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('# pass 17', result.stdout)
        self.assertIn('# fail 0', result.stdout)
