"""Real export behavior, filesystem boundaries and Chinese offline payload."""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest

PAYLOAD = Path(os.environ.get('INVADERS_PAYLOAD', Path(__file__).resolve().parents[1] / 'plugins/invaders-local/invaders-local'))
spec = importlib.util.spec_from_file_location('invaders_export', PAYLOAD / 'runtime/export_game.py')
export = importlib.util.module_from_spec(spec)
# CI runs without -B. Keep imported runtime bytecode out of the immutable payload.
previous_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(export)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def test_chinese_html_export_hash_version_license(self):
        p = self.base / '我的游戏.html'
        r = export.execute({'output_path': str(p), 'seed': 77})
        self.assertEqual(r['version'], '1.0.2')
        self.assertEqual(r['sha256'], hashlib.sha256(p.read_bytes()).hexdigest())
        html = p.read_text()
        for value in ('星际防线', '重新开始', '保存进度', '游戏结束', 'const INITIAL_SEED = 77;', 'Copyright (c) 2026 Nigel Hudson', 'THE SOFTWARE IS PROVIDED "AS IS"'):
            self.assertIn(value, html)
        self.assertNotIn('@@', html)
        self.assertIn("connect-src 'none'", html)
        for forbidden in ('fetch(', 'XMLHttpRequest', 'WebSocket(', '<script src=', '<link ', 'from \'node:'):
            self.assertNotIn(forbidden, html)

    def test_repeated_render_is_byte_identical(self):
        self.assertEqual(export.render_game(0), export.render_game(0))
        self.assertNotEqual(export.render_game(0), export.render_game(1))

    def test_existing_file_not_overwritten(self):
        p = self.base / 'existing.html'
        p.write_text('original')
        with self.assertRaisesRegex(export.InputError, '未覆盖'):
            export.execute({'output_path': str(p)})
        self.assertEqual(p.read_text(), 'original')

    def test_invalid_seed_shapes(self):
        for seed in (True, -1, 2147483648, 1.5, '123', None):
            with self.subTest(seed=seed), self.assertRaises(export.InputError):
                export.execute({'output_path': str(self.base / 'x.html'), 'seed': seed})
        self.assertFalse((self.base / 'x.html').exists())

    def test_bad_paths_and_unknown_inputs(self):
        for value in ('relative.html', str(self.base/'x.txt'), str(self.base/'missing/x.html'), str(self.base/'../x.html'), '', 5, None, '\x00'):
            with self.subTest(path=value), self.assertRaises(export.InputError):
                export.execute({'output_path': value})
        for value in ([], None, {'output_path': str(self.base/'x.html'), 'extra':1}):
            with self.assertRaises(export.InputError): export.execute(value)

    def test_symlink_target_and_parent_refused(self):
        target = self.base/'target.html'
        target.write_text('preserve')
        link = self.base/'link.html'
        link.symlink_to(target)
        with self.assertRaises(export.InputError): export.execute({'output_path':str(link)})
        directory = self.base/'real'; directory.mkdir()
        linked_dir = self.base/'linked'; linked_dir.symlink_to(directory, target_is_directory=True)
        with self.assertRaises(export.InputError): export.execute({'output_path':str(linked_dir/'x.html')})
        self.assertEqual(target.read_text(),'preserve')
        self.assertFalse((directory/'x.html').exists())

    def test_concurrent_exports_exclusive_create(self):
        path = str(self.base/'race.html')
        def attempt(seed):
            try: return export.execute({'output_path':path,'seed':seed})
            except export.InputError: return None
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            results = list(pool.map(attempt, range(8)))
        wins = [r for r in results if r]
        self.assertEqual(len(wins),1)
        self.assertEqual(wins[0]['sha256'],hashlib.sha256(Path(path).read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main()
