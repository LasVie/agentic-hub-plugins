"""Real filesystem/archive tests; no SDK, model or network required."""
import copy
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

PAYLOAD = Path(os.environ.get('OFFLINE_BACKUP_PAYLOAD', Path(__file__).resolve().parents[1] / 'plugins/offline-backup-recovery/offline-backup-recovery'))
SPEC = importlib.util.spec_from_file_location('backup_under_test', PAYLOAD / 'runtime/backup.py')
core = importlib.util.module_from_spec(SPEC)
_OLD_BYTECODE = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(core)
finally:
    sys.dont_write_bytecode = _OLD_BYTECODE
sha = lambda b: hashlib.sha256(b).hexdigest()


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # /var is a platform symlink on macOS: all test inputs are real paths.
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / '中文资料🙂'
        self.source.mkdir()
        (self.source/'嵌套').mkdir()
        (self.source/'空目录').mkdir()
        (self.source/'嵌套/说明.txt').write_bytes('中文\r\n第二行🙂\n'.encode())
        (self.source/'二进制.bin').write_bytes(bytes(range(256))*8)
        (self.source/'空文件').write_bytes(b'')
        self.archive = self.root/'备份.zip'
        self.target = self.root/'新恢复目录'

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, op, **args):
        r = core.dispatch(op, args)
        self.assertEqual(r['version'], '1.0.0')
        return r

    def create(self):
        r = self.call('create', source_dir=str(self.source), archive_path=str(self.archive), confirmed=True)
        self.assertTrue(r['ok'], r)
        return r

    def error(self, r, code=None):
        self.assertFalse(r['ok'], r)
        if code:
            self.assertEqual(r['error']['code'], code, r)
        self.assertRegex(r['error']['message'], '[\u4e00-\u9fff]')

    def restore(self, **extra):
        return self.call('restore', archive_path=str(self.archive), target_dir=str(self.target), mode='restore', confirmed=True,
                         expected_sha256=sha(self.archive.read_bytes()), **extra)

    @staticmethod
    def inventory(p):
        return {f.relative_to(p).as_posix(): ('dir' if f.is_dir() else sha(f.read_bytes())) for f in p.rglob('*')}

    def custom(self, entries=None, extras=None, compression=zipfile.ZIP_STORED, mutate=None):
        entries = copy.deepcopy(entries if entries is not None else [{'path':'正常.txt','type':'file','size':3,'sha256':sha(b'abc')}])
        m = {'format':core.FORMAT,'plugin_version':'1.0.0','source_name':'测试','created_at':'2026-10-26','entries':entries}
        if mutate:mutate(m)
        with zipfile.ZipFile(self.archive,'w') as z:
            for e in entries:
                i=core.zip_info('data/'+e['path']+('/' if e['type']=='directory' else ''),e['type']=='directory')
                i.compress_type=compression
                z.writestr(i,b'' if e['type']=='directory' else b'abc')
            z.writestr(core.zip_info(core.MANIFEST),json.dumps(m,ensure_ascii=False).encode())
            for info,body in extras or []:z.writestr(info,body)

    def test_chinese_binary_empty_roundtrip_and_original_unchanged(self):
        before=self.inventory(self.source);r=self.create()
        self.assertEqual((r['file_count'],r['directory_count']),(3,2))
        self.assertEqual(r['archive_sha256'],sha(self.archive.read_bytes()))
        check=self.call('inspect',archive_path=str(self.archive),expected_sha256=r['archive_sha256'])
        self.assertTrue(check['ok'],check)
        self.assertEqual(len(check['entries']),5)
        result=self.restore();self.assertTrue(result['ok'],result)
        self.assertEqual(before,self.inventory(self.target));self.assertEqual(before,self.inventory(self.source))
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((self.target/'二进制.bin').stat().st_mode),0o600)

    def test_preview_has_no_writes(self):
        self.create();before=set(self.root.iterdir())
        r=self.call('restore',archive_path=str(self.archive),target_dir=str(self.target))
        self.assertTrue(r['ok'],r);self.assertFalse(r['writes_performed'])
        self.assertEqual(before,set(self.root.iterdir()));self.assertFalse(self.target.exists())

    def test_confirmations_and_required_restore_digest(self):
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=False),'confirmation_required')
        self.assertFalse(self.archive.exists());self.create()
        self.error(self.call('restore',archive_path=str(self.archive),target_dir=str(self.target),mode='restore'),'confirmation_required')
        self.error(self.call('restore',archive_path=str(self.archive),target_dir=str(self.target),mode='restore',confirmed=True),'invalid_argument')
        self.assertFalse(self.target.exists())

    def test_reject_existing_backup_unchanged(self):
        self.archive.write_bytes(b'keep')
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'output_exists')
        self.assertEqual(self.archive.read_bytes(),b'keep')

    def test_reject_existing_even_empty_restore_target(self):
        self.create();self.target.mkdir()
        self.error(self.restore(),'output_exists');self.assertEqual(list(self.target.iterdir()),[])
        (self.target/'保留.txt').write_text('保留')
        self.error(self.restore(),'output_exists');self.assertEqual((self.target/'保留.txt').read_text(),'保留')

    def test_unsafe_absolute_paths_and_output_inside_source(self):
        for source in ('/','relative','/tmp/../x',str(self.source)+'/',str(Path.home())):
            with self.subTest(source=source):self.error(self.call('create',source_dir=source,archive_path=str(self.archive),confirmed=True),'unsafe_path')
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.source/'out.zip'),confirmed=True),'unsafe_path')

    def test_source_symlinks_and_hardlinks_rejected_no_output(self):
        original=self.source/'二进制.bin';other=self.source/'链接'
        for kind in ('symlink','hardlink'):
            with self.subTest(kind=kind):
                os.symlink(original,other) if kind=='symlink' else os.link(original,other)
                self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'unsafe_file')
                self.assertFalse(self.archive.exists());other.unlink()
        self.assertFalse(list(self.root.glob('.offline-backup-*')))

    def test_symlink_parent_and_archive_rejected(self):
        link=self.root/'目录链接';link.symlink_to(self.source,target_is_directory=True)
        self.error(self.call('create',source_dir=str(link),archive_path=str(self.archive),confirmed=True))
        self.create();al=self.root/'归档链接.zip';al.symlink_to(self.archive)
        self.error(self.call('inspect',archive_path=str(al)))
        hl=self.root/'归档硬链接.zip';os.link(self.archive,hl)
        self.error(self.call('inspect',archive_path=str(self.archive)),'unsafe_file')

    def test_fifo_rejected_without_blocking(self):
        os.mkfifo(self.source/'管道')
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'unsafe_file')

    def test_wrong_archive_digest_never_creates_target(self):
        self.create()
        self.error(self.call('restore',archive_path=str(self.archive),target_dir=str(self.target),mode='restore',confirmed=True,expected_sha256='0'*64),'integrity_mismatch')
        self.assertFalse(self.target.exists())

    def test_truncated_archive(self):
        self.create();self.archive.write_bytes(self.archive.read_bytes()[:-30])
        self.error(self.call('inspect',archive_path=str(self.archive)),'invalid_archive')

    def test_manifest_wrong_file_hash(self):
        self.custom(mutate=lambda m:m['entries'][0].update(sha256='0'*64))
        self.error(self.restore(),'integrity_mismatch');self.assertFalse(self.target.exists())

    def test_zip_crc_corruption(self):
        self.custom();raw=self.archive.read_bytes();self.assertIn(b'abc',raw)
        self.archive.write_bytes(raw.replace(b'abc',b'xyz',1))
        self.error(self.call('inspect',archive_path=str(self.archive)),'invalid_archive')

    def test_traversal_and_ambiguous_paths(self):
        for value in ('../escape','/absolute','a/../../escape','a\\escape','a:b','a//b','a/./b','a\nb'):
            with self.subTest(value=value):
                self.custom([{'path':value,'type':'file','size':3,'sha256':sha(b'abc')}])
                self.error(self.restore());self.assertFalse(self.target.exists())
        self.assertFalse((self.root/'escape').exists())

    def test_unlisted_extra_member_rejected(self):
        self.custom(extras=[(core.zip_info('data/extra'),b'abc')])
        self.error(self.call('inspect',archive_path=str(self.archive)),'invalid_archive')

    def test_archive_symlink_member_rejected(self):
        i=core.zip_info('data/link');i.external_attr=(stat.S_IFLNK|0o777)<<16
        self.custom(extras=[(i,b'outside')])
        self.error(self.restore(),'unsafe_file');self.assertFalse(self.target.exists())

    def test_duplicate_manifest_path_and_missing_parent(self):
        e={'path':'same','type':'file','size':3,'sha256':sha(b'abc')}
        with self.assertWarns(UserWarning):self.custom([e,e])
        self.error(self.call('inspect',archive_path=str(self.archive)),'invalid_archive')
        e['path']='missing/file';self.custom([e])
        self.error(self.restore(),'invalid_archive');self.assertFalse(self.target.exists())

    def test_compressed_archives_are_outside_supported_format(self):
        self.custom(compression=zipfile.ZIP_DEFLATED)
        self.error(self.call('inspect',archive_path=str(self.archive)),'invalid_archive')

    def test_wrong_format_version_and_invalid_schema(self):
        for mutate in (lambda m:m.update(format='other'),lambda m:m.update(plugin_version='9.0.0'),lambda m:m['entries'][0].update(size=True)):
            self.custom(mutate=mutate);self.error(self.call('inspect',archive_path=str(self.archive)),'invalid_archive')

    def test_oversize_source_refused_and_temp_cleaned(self):
        with (self.source/'large').open('wb') as f:f.truncate(core.MAX_FILE+1)
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'size_limit')
        self.assertFalse(self.archive.exists());self.assertFalse(list(self.root.glob('.offline-backup-*')))

    def test_entry_and_depth_limits(self):
        with patch.object(core,'MAX_ENTRIES',2):
            self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'size_limit')
        p=self.source
        for _ in range(core.MAX_DEPTH+1):p=p/'层';p.mkdir()
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'size_limit')

    def test_combined_size_and_manifest_limits(self):
        with patch.object(core,'MAX_TOTAL',10):self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'size_limit')
        with patch.object(core,'MAX_MANIFEST',10):self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'size_limit')

    def test_changed_source_file_rejected(self):
        regular=core.regular;changed=False
        def changing(fd,limit):
            nonlocal changed
            r=regular(fd,limit)
            if limit==core.MAX_FILE and not changed:
                changed=True
                for p in self.source.rglob('*'):
                    if p.is_file() and p.stat().st_ino==r.st_ino:p.write_bytes(b'changed source')
            return r
        with patch.object(core,'regular',side_effect=changing):
            self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'source_changed')
        self.assertFalse(self.archive.exists());self.assertFalse(list(self.root.glob('.offline-backup-*')))

    def test_restore_write_failure_cleans_only_its_new_directory(self):
        self.create();keep=self.root/'keep';keep.mkdir();(keep/'a').write_bytes(b'keep')
        with patch.object(core.os,'fsync',side_effect=OSError(errno.ENOSPC,'injected full disk')):
            self.error(self.restore(),'filesystem_error')
        self.assertFalse(self.target.exists());self.assertEqual((keep/'a').read_bytes(),b'keep')
        self.assertTrue(self.archive.exists());self.assertTrue(self.source.exists())

    def test_cleanup_failure_reports_partial_output(self):
        self.create()
        with patch.object(core.os,'fsync',side_effect=OSError(errno.ENOSPC,'injected full disk')),patch.object(core.shutil,'rmtree',side_effect=PermissionError('injected cleanup denial')):
            r=self.restore();self.error(r,'partial_output');self.assertEqual(r['error']['partial_output'],str(self.target))
        self.assertTrue(self.target.exists())

    def test_concurrent_backup_publication_does_not_overwrite(self):
        link=core.os.link
        def race(src,dst,**kwargs):
            self.archive.write_bytes(b'racing existing output')
            return link(src,dst,**kwargs)
        with patch.object(core.os,'link',side_effect=race):self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True),'filesystem_error')
        self.assertEqual(self.archive.read_bytes(),b'racing existing output');self.assertFalse(list(self.root.glob('.offline-backup-*')))

    def test_empty_source_directory_roundtrip(self):
        for p in sorted(self.source.rglob('*'),key=lambda p:len(p.parts),reverse=True):p.rmdir() if p.is_dir() else p.unlink()
        r=self.create();self.assertEqual((r['file_count'],r['directory_count']),(0,0))
        self.assertTrue(self.restore()['ok']);self.assertEqual(list(self.target.iterdir()),[])

    def test_streaming_at_single_file_limit(self):
        p=self.source/'最大文件.bin'
        chunk=bytes(range(256))*256
        with p.open('wb') as f:
            for _ in range(core.MAX_FILE//len(chunk)):f.write(chunk)
        r=self.create();self.assertGreater(r['total_bytes'],core.MAX_FILE)
        self.assertTrue(self.restore()['ok'])
        self.assertEqual(sha(p.read_bytes()),sha((self.target/p.name).read_bytes()))

    def test_cli_fresh_process_inspect_and_chinese_help(self):
        r=self.create()
        p=subprocess.run([sys.executable,'-B',str(PAYLOAD/'runtime/backup.py'),'inspect','--input-json',json.dumps({'archive_path':str(self.archive),'expected_sha256':r['archive_sha256']})],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(p.stdout)['integrity_verified'])
        p=subprocess.run([sys.executable,'-B',str(PAYLOAD/'runtime/backup.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0);self.assertIn('离线备份与恢复',p.stdout)
        self.assertIn('位置参数',p.stdout);self.assertNotIn('usage:',p.stdout)
        p=subprocess.run([sys.executable,'-B',str(PAYLOAD/'runtime/backup.py'),'invalid'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertIn('命令行参数无效',p.stderr)

    def test_unknown_parameters_and_modes(self):
        self.error(self.call('create',source_dir=str(self.source),archive_path=str(self.archive),confirmed=True,overwrite=True),'invalid_argument')
        self.error(self.call('restore',mode='overwrite'),'invalid_argument')


if __name__=='__main__':unittest.main()
