"""I/O, integrity and process-boundary tests for the approved preview scope."""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PAYLOAD = Path(os.environ.get('SOURCE_PREVIEW_PAYLOAD', Path(__file__).resolve().parents[1] / 'plugins/source-preview-recovery/source-preview-recovery'))
CORE = PAYLOAD / 'runtime/recovery.py'
spec = importlib.util.spec_from_file_location('preview_recovery_test_core', CORE)
q = importlib.util.module_from_spec(spec)
old = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(q)
finally:
    sys.dont_write_bytecode = old


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='source-preview-test-')
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / '中文日志.txt'
        self.raw = ('标题🙂\r\n\r\n' + '重复记录\r\n'*30 + '错误：需要确认\r\n' + ''.join(f'记录{i}：中文内容\r\n' for i in range(200)) + '结束\r\n').encode()
        self.source.write_bytes(self.raw)

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, op, **kwargs):
        return q.dispatch(op, {'workspace': str(self.root), **kwargs})

    def preview(self, **kwargs):
        return self.call('preview', path=str(self.source), confirmed=True, **kwargs)

    def snap(self):
        r = self.preview()
        self.assertTrue(r['ok'], r)
        return r['snapshot_id']

    def error(self, r, code=None):
        self.assertFalse(r['ok'], r)
        self.assertEqual(r['version'], '1.0.1')
        self.assertRegex(r['error']['message'], '[\u4e00-\u9fff]')
        if code:
            self.assertEqual(r['error']['code'], code)

    def test_original_bytes_hash_and_source_unchanged(self):
        before = self.source.stat().st_mtime_ns
        r = self.preview()
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(r['original_bytes'], len(self.raw))
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertEqual(self.source.stat().st_mtime_ns, before)
        self.assertTrue(r['integrity_verified'])

    def test_accurate_blank_repeat_coordinates(self):
        r = self.preview(style='lines')
        self.assertIn('L33: 错误：需要确认', r['preview'])
        self.assertIn(33, r['shown_source_lines'])
        self.assertIn('省略', r['preview'])

    def test_range_preserves_crlf_and_unicode(self):
        sid = self.snap()
        r = self.call('read', snapshot_id=sid, action='range', start_line=2, end_line=5)
        self.assertEqual(r['text'].encode(), b'\r\n' + '重复记录\r\n'.encode()*3)

    def test_restart_process_durable_id(self):
        sid = self.snap()
        p = subprocess.run([sys.executable, '-B', str(CORE), 'read', '--input-json', json.dumps({'workspace': str(self.root), 'snapshot_id': sid, 'action': 'range', 'start_line': 33, 'end_line': 33})], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['text'], '错误：需要确认\r\n')

    def test_original_changed_does_not_change_snapshot(self):
        sid = self.snap()
        self.source.write_text('新内容')
        r = self.call('read', snapshot_id=sid, action='range', start_line=1, end_line=1)
        self.assertEqual(r['text'], '标题🙂\r\n')

    def test_original_removed_still_recovers(self):
        sid = self.snap(); self.source.unlink()
        self.assertTrue(self.call('read', snapshot_id=sid)['ok'])

    def test_export_exact_and_refuse_overwrite(self):
        sid = self.snap(); out = self.root/'导出.txt'
        r = self.call('export', snapshot_id=sid, output=str(out), confirmed=True)
        self.assertTrue(r['ok'], r); self.assertEqual(out.read_bytes(), self.raw)
        self.error(self.call('export', snapshot_id=sid, output=str(out), confirmed=True), 'output_exists')
        self.assertEqual(out.read_bytes(), self.raw)

    def test_confirmation_before_snapshot_write(self):
        self.error(self.call('preview', path=str(self.source), confirmed=False), 'confirmation_required')
        self.assertFalse((self.root/q.STATE).exists())

    def test_export_requires_confirmation(self):
        sid = self.snap(); out = self.root/'no.txt'
        self.error(self.call('export', snapshot_id=sid, output=str(out), confirmed=False), 'confirmation_required')
        self.assertFalse(out.exists())

    def test_repeated_snapshot_reuses_identical_full_bytes(self):
        sid = self.snap(); r = self.preview()
        self.assertTrue(r['reused']); self.assertEqual(sid, r['snapshot_id'])
        self.assertEqual(len(list((self.root/q.STATE).glob('*.snapshot'))), 1)

    def test_tampered_snapshot_is_rejected(self):
        sid = self.snap(); p = self.root/q.STATE/(sid+'.snapshot')
        p.chmod(0o600); p.write_bytes(q.MAGIC+b'tampered')
        self.error(self.call('read', snapshot_id=sid), 'integrity_mismatch')
        self.error(self.preview(), 'integrity_mismatch')

    def test_missing_snapshot_not_replaced_with_source(self):
        sid = self.snap(); (self.root/q.STATE/(sid+'.snapshot')).unlink()
        self.error(self.call('read', snapshot_id=sid), 'snapshot_missing')

    def test_read_does_not_initialize_store(self):
        self.error(self.call('read', snapshot_id='sha256-'+'a'*64), 'snapshot_missing')
        self.assertFalse((self.root/q.STATE).exists())

    def test_source_symlink_rejected(self):
        link = self.root/'link'; link.symlink_to(self.source)
        self.error(self.call('preview', path=str(link), confirmed=True))
        self.assertFalse((self.root/q.STATE).exists())

    def test_parent_symlink_rejected(self):
        link = self.root/'alias'; link.symlink_to(self.root, target_is_directory=True)
        self.error(self.call('preview', path=str(link/self.source.name), confirmed=True))

    def test_workspace_symlink_rejected(self):
        link = self.root/'alias'; link.symlink_to(self.root, target_is_directory=True)
        self.error(q.dispatch('preview', {'workspace': str(link), 'path': str(link/self.source.name), 'confirmed': True}))

    def test_hardlink_source_rejected(self):
        os.link(self.source, self.root/'hard')
        self.error(self.preview(), 'unsafe_file')

    def test_export_symlink_refuses_without_touching_target(self):
        sid = self.snap(); dest = self.root/'link'; dest.symlink_to(self.source)
        self.error(self.call('export', snapshot_id=sid, output=str(dest), confirmed=True), 'output_exists')
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_store_symlink_rejected(self):
        (self.root/q.STATE).symlink_to(self.root, target_is_directory=True)
        self.error(self.preview())

    def test_snapshot_symlink_rejected(self):
        sid = self.snap(); p = self.root/q.STATE/(sid+'.snapshot'); p.unlink(); p.symlink_to(self.source)
        self.error(self.call('read', snapshot_id=sid))

    def test_outside_workspace_and_dotdot_rejected(self):
        self.error(self.call('preview', path=str(self.root.parent/'outside.txt'), confirmed=True), 'outside_workspace')
        self.error(self.call('preview', path=str(self.root)+'/../x.txt', confirmed=True), 'unsafe_path')

    def test_internal_snapshot_not_a_source(self):
        sid = self.snap()
        self.error(self.call('preview', path=str(self.root/q.STATE/(sid+'.snapshot')), confirmed=True), 'unsafe_path')

    def test_json_types_large_integers_and_decimal_preserved_in_view(self):
        self.source.write_text('['+','.join('{"n":900719925474099312345,"d":1.234567890123456789,"s":"null","v":null,"b":true,"t":"true"}' for _ in range(20))+']')
        r = self.preview()
        self.assertEqual(r['strategy'], 'json-record-preview')
        self.assertIn('900719925474099312345', r['preview'])
        self.assertIn('1.234567890123456789', r['preview'])
        self.assertIn('"null", null, true, "true"', r['preview'])
        self.assertIn('不是源文件行号', r['preview'])

    def test_duplicate_json_keys_fall_back_without_losing_original(self):
        raw = ('['+','.join('{"a":1,"a":2}' for _ in range(10))+']').encode(); self.source.write_bytes(raw)
        r = self.preview(); self.assertEqual(r['strategy'], 'source-line-preview')
        out = self.root/'duplicate.json'; self.call('export', snapshot_id=r['snapshot_id'], output=str(out), confirmed=True)
        self.assertEqual(out.read_bytes(), raw)

    def test_jsonl_falls_back_to_correct_source_coordinates(self):
        self.source.write_text('\n'.join('{"x":'+str(i)+'}' for i in range(100)))
        r = self.preview(); self.assertEqual(r['strategy'], 'source-line-preview')
        self.assertEqual(self.call('read', snapshot_id=r['snapshot_id'], action='range', start_line=42, end_line=42)['text'], '{"x":41}\n')

    def test_bom_mixed_newline_export_exact(self):
        raw = b'\xef\xbb\xbf'+'中文\r第二行\n第三行\r\n尾'.encode(); self.source.write_bytes(raw)
        sid = self.snap(); info = self.call('read', snapshot_id=sid)
        self.assertTrue(info['utf8_bom']); self.assertEqual(info['line_count'], 4)
        out = self.root/'bom.txt'; self.call('export', snapshot_id=sid, output=str(out), confirmed=True)
        self.assertEqual(out.read_bytes(), raw)

    def test_unicode_line_separator_is_data(self):
        self.source.write_text('甲\u2028乙\n丙')
        self.assertEqual(self.preview()['line_count'], 2)

    def test_empty_file(self):
        self.source.write_bytes(b''); sid = self.snap()
        self.assertEqual(self.call('read', snapshot_id=sid)['line_count'], 0)
        self.error(self.call('read', snapshot_id=sid, action='range'), 'invalid_range')

    def test_invalid_utf8_or_nul_no_snapshot(self):
        for raw in [b'\xff', b'a\x00b']:
            self.source.write_bytes(raw); self.error(self.preview(), 'invalid_utf8')
        self.assertFalse((self.root/q.STATE).exists())

    def test_excessive_line_count_fails_before_storage(self):
        self.source.write_bytes(b'\n' * 200001)
        self.error(self.preview(), 'line_limit')
        self.assertFalse((self.root/q.STATE).exists())

    def test_json_escaped_surrogate_falls_back_to_safe_source(self):
        self.source.write_text('['+','.join('{"a":"\\ud800"}' for _ in range(10))+']')
        r = self.preview()
        self.assertTrue(r['ok'], r); self.assertEqual(r['strategy'], 'source-line-preview')

    def test_large_json_header_respects_preview_budget(self):
        self.source.write_text(json.dumps([{'k'*10000:i} for i in range(10)]))
        r = self.preview(max_preview_chars=1000)
        self.assertTrue(r['ok'], r); self.assertLessEqual(len(r['preview']), 1000)

    def test_oversized_source_rejected_not_truncated(self):
        self.source.write_bytes(b'a'*(q.MAX_BYTES+1)); self.error(self.preview(), 'size_limit')
        self.assertFalse((self.root/q.STATE).exists())

    def test_large_full_export_exceeds_old_cache_limit(self):
        raw = ('中文🙂\n'*100000).encode(); self.source.write_bytes(raw)
        r = self.preview(); out = self.root/'large.txt'
        self.assertTrue(self.call('export', snapshot_id=r['snapshot_id'], output=str(out), confirmed=True)['ok'])
        self.assertEqual(out.read_bytes(), raw)

    def test_range_limits_never_truncate(self):
        self.source.write_text('a\n'*1500); sid = self.snap()
        self.error(self.call('read', snapshot_id=sid, action='range', start_line=1, end_line=1001), 'range_too_large')
        self.source.write_text('中'*30000); sid = self.snap()
        self.error(self.call('read', snapshot_id=sid, action='range', start_line=1, end_line=1), 'range_too_large')

    def test_arguments_and_unknown_keys(self):
        self.error(self.preview(head_lines=True), 'invalid_argument')
        self.error(self.preview(style='x'), 'invalid_argument')
        self.error(self.call('read', snapshot_id='../secret'), 'invalid_snapshot_id')
        self.error(self.call('preview', path=str(self.source), confirmed=True, command='x'), 'invalid_argument')

    def test_store_quota_does_not_delete_existing(self):
        sid = self.snap(); self.source.write_text('不同内容')
        with patch.object(q, 'MAX_FILES', 1):
            self.error(self.preview(), 'store_limit')
        self.assertTrue(self.call('read', snapshot_id=sid)['ok'])

    def test_unknown_store_file_fails_without_cleanup(self):
        self.snap(); p = self.root/q.STATE/'unexpected'; p.write_text('keep')
        self.source.write_text('new'); self.error(self.preview(), 'invalid_store'); self.assertEqual(p.read_text(), 'keep')

    def test_write_failure_does_not_claim_success(self):
        with patch.object(q, 'write_all', side_effect=OSError('simulated full disk')):
            self.error(self.preview(), 'filesystem_error')
        self.assertEqual(list((self.root/q.STATE).glob('*.snapshot')), [])

    def test_source_changed_during_read(self):
        original = q.os.read; changed = False
        def read(fd, n):
            nonlocal changed
            data = original(fd, n)
            if not changed:
                changed = True; self.source.write_bytes(b'changed')
            return data
        with patch.object(q.os, 'read', read):
            self.error(self.preview(), 'source_changed')

    def test_concurrent_process_creation_reuses_or_reports_busy(self):
        args = json.dumps({'workspace': str(self.root), 'path': str(self.source), 'confirmed': True})
        def run(_):
            p = subprocess.run([sys.executable, '-B', str(CORE), 'preview', '--input-json', args], capture_output=True, text=True)
            return json.loads(p.stdout)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(run, range(8)))
        self.assertTrue(any(r['ok'] for r in results))
        self.assertTrue(all(r['ok'] or r['error']['code']=='store_busy' for r in results), results)
        self.assertEqual(len(list((self.root/q.STATE).glob('*.snapshot'))), 1)
        self.assertTrue(self.preview()['reused'])

    def test_preview_bounded_with_chinese_not_claimed_billing(self):
        self.source.write_text('中文🙂'*10000)
        r = self.preview(max_preview_chars=1000)
        self.assertLessEqual(len(r['preview']), 1000)
        self.assertIn('精简预览', r['message']); self.assertNotIn('tokens', r)

    def test_manifest_and_license_identity(self):
        m = json.loads((PAYLOAD/'manifest.json').read_text())
        self.assertEqual(m['version'], '1.0.1'); self.assertEqual(m['id'], 'source-preview-recovery')
        self.assertEqual(len(m['tools']), 3)
        self.assertEqual(hashlib.sha256((PAYLOAD/'licenses/save-token/LICENSE').read_bytes()).hexdigest(), 'd9f4d0687b6934f18e9bab4e75f26c04b83a5f5d7898f464a921abd1ee8ef85e')


if __name__ == '__main__':
    unittest.main()
