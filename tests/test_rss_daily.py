import os
from pathlib import Path
import subprocess
import sys
import unittest


class RssDailyIntegrationTests(unittest.TestCase):
    def test_isolated_asset_suite(self):
        root = Path(__file__).resolve().parents[1]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "plugins/rss-daily/tests", "-p", "test_*.py", "-v"],
                                cwd=root, env=environment, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
