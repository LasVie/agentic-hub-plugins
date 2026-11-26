import argparse
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def connector(slug):
    root = ROOT / slug / slug
    sys.path.insert(0, str(root))
    try:
        spec = importlib.util.spec_from_file_location(f"test_{slug}", root / "connector.py")
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value
    finally:
        sys.path.pop(0)


class ConnectorTests(unittest.TestCase):
    def test_confluence(self):
        m = connector("confluence-cloud")
        args = argparse.Namespace(command="create", container="SPACE", title="测试", body="正文")
        cmd = m.select_command(args)
        self.assertEqual(cmd[:3], ["confluence","content","create"])
        self.assertEqual(cmd[cmd.index("--space-id")+1], "SPACE")
        self.assertIn("--yes", cmd)
        with patch.object(m, "run", return_value=subprocess.CompletedProcess([],0,'{"data":{"auth":{"resolved":{"tokenPresent":true}}}}')):
            self.assertTrue(m.status())
        with patch.object(m, "run", return_value=subprocess.CompletedProcess([],0,'{"data":{"auth":{"resolved":{"tokenPresent":false}}}}')):
            self.assertFalse(m.status())
