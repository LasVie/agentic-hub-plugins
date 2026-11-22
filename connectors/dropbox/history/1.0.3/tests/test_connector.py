import argparse
import importlib.util
import os
import sys
import tempfile
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
    def test_dropbox(self):
        m = connector("dropbox")
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            with patch.object(m,"STATE",d),patch.object(m,"TOKEN",d/"session.json"),patch.dict(os.environ,{"WORKSWARM_DROPBOX_APP_KEY":"example_key"}):
                m.save({"access_token":"test_access","refresh_token":"test_refresh","expires_in":1})
                with patch.object(m,"request",return_value={"access_token":"rotated","expires_in":3600}) as send:
                    self.assertEqual(m.bearer()["Authorization"],"Bearer rotated")
                    self.assertEqual(send.call_args.kwargs["form"]["grant_type"],"refresh_token")
                    self.assertEqual(m.load()["refresh_token"],"test_refresh")
                self.assertEqual(m.execute(argparse.Namespace(command="logout")),{"connected":False})
                self.assertIsNone(m.load())
        with patch.object(m,"bearer",return_value={"Authorization":"Bearer fixture"}),patch.object(m,"api",return_value={}) as send:
            m.execute(argparse.Namespace(command="search",cursor=None,query="测试"))
            self.assertEqual(send.call_args.args[0],"files/search_v2")
            self.assertTrue(send.call_args.args[1]["options"]["filename_only"])
