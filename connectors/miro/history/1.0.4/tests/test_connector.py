import argparse
import importlib.util
import sys
import unittest
from pathlib import Path

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
    def test_miro(self):
        m = connector("miro")
        with self.assertRaises(argparse.ArgumentTypeError):
            m.object_argument("[]")
        self.assertEqual(m.object_argument('{"board_id":"x"}'),{"board_id":"x"})
        self.assertIn("canvas_read_as_svg",m.ALLOW)
        self.assertIn("canvas_create_from_svg",m.ALLOW)
        self.assertNotIn("layout_create",m.ALLOW)
