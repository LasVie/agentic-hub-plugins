"""Functional filesystem/HTTP/lifecycle tests; generated WAV only, no model."""
import contextlib
import hashlib
import importlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request
import wave

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get('MUSIC_TEST_PAYLOAD', ROOT / 'plugins/local-music-library/local-music-library'))
pkg = types.ModuleType('_music_under_test'); pkg.__path__ = [str(PAYLOAD)]
sys.modules['_music_under_test'] = pkg
old_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    lib = importlib.import_module('_music_under_test.runtime.library')
    ctl = importlib.import_module('_music_under_test.runtime.control')
finally:
    sys.dont_write_bytecode = old_bytecode


def wav(path):
    import math
    with wave.open(str(path), 'wb') as f:
        f.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        f.writeframes(b''.join(struct.pack('<h', int(7000 * math.sin(i * math.tau * 220 / 8000))) for i in range(64000)))


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='music-functional-')
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / '音乐'; self.root.mkdir()
        self.work = self.base / '工作'; self.work.mkdir()
        wav(self.root / '甲.wav'); wav(self.root / '乙.wav')
        self.store = self.work / '歌单.json'
        self.library = lib.Library(self.root, self.store)

    def tearDown(self):
        self.library.close(); self.temp.cleanup()

    def test_chinese_scan_mime_and_stable_ids(self):
        a = self.library.manifest()
        self.assertEqual(a['version'], '1.0.0')
        self.assertEqual(a['scan']['count'], 2)
        self.assertEqual({t['mime'] for t in a['tracks']}, {'audio/wav'})
        self.assertEqual([t['id'] for t in a['tracks']], [t['id'] for t in self.library.scan()['tracks']])
        self.assertNotIn(str(self.root), json.dumps(a, ensure_ascii=False))

    def test_playlist_persistence_order_and_dedup(self):
        ids = list(self.library.tracks)[::-1]
        self.library.save_playlist('中文歌单', ids + ids)
        b = lib.Library(self.root, self.store)
        try:
            self.assertEqual(b.state['playlists'], [{'name':'中文歌单', 'tracks':ids}])
        finally: b.close()

    def test_invalid_playlist_keeps_existing_bytes(self):
        self.library.save_playlist('保留', list(self.library.tracks))
        before = self.store.read_bytes()
        for name, ids in [('', []), ('名'*81, []), ('无效', ['outside']), ('无效', 'x')]:
            with self.assertRaises(lib.LibraryError): self.library.save_playlist(name, ids)
        self.assertEqual(before, self.store.read_bytes())

    def test_playlist_limit_and_remove(self):
        for i in range(16): self.library.save_playlist(str(i), [])
        with self.assertRaises(lib.LibraryError): self.library.save_playlist('第17个', [])
        self.library.remove_playlist('0')
        self.assertEqual(len(self.library.state['playlists']), 15)
        with self.assertRaises(lib.LibraryError): self.library.remove_playlist('不存在')

    def test_resume_validation_and_roundtrip(self):
        r = {'track':next(iter(self.library.tracks)), 'seconds':1.5, 'volume':.6, 'mode':'repeat'}
        self.library.save_resume(r)
        self.assertEqual(lib.read_json(self.store)['resume'], r)
        for key, value in [('seconds', float('nan')), ('volume', 3), ('mode', 'web')]:
            with self.assertRaises(lib.LibraryError): self.library.save_resume({**r,key:value})

    def test_removed_track_is_reported_missing_and_rejected(self):
        tid = next(iter(self.library.tracks)); self.library.save_playlist('旧曲目', [tid])
        (self.root / self.library.tracks[tid]['name']).unlink()
        self.library.scan()
        self.assertEqual(self.library.state['playlists'][0]['tracks'], [tid])
        with self.assertRaises(lib.LibraryError): self.library.open_track(tid)

    def test_audio_bytes_never_changed(self):
        before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        tid = next(iter(self.library.tracks)); fd, n, _ = self.library.open_track(tid)
        with os.fdopen(fd, 'rb') as f: self.assertEqual(len(f.read()), n)
        self.library.save_playlist('听歌', [tid]); self.library.save_resume({'track':tid,'seconds':0,'volume':1,'mode':'sequence'})
        self.assertEqual(before, {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()})

    def test_symlink_file_directory_and_hardlink_are_excluded(self):
        outside = self.base / '外部.wav'; wav(outside)
        (self.root/'链接.wav').symlink_to(outside)
        (self.root/'目录链接').symlink_to(self.work, target_is_directory=True)
        os.link(outside, self.root/'硬链接.wav')
        result = self.library.scan()
        self.assertEqual(result['scan']['count'], 2)
        for rel in ('../外部.wav', str(outside), '链接.wav', '硬链接.wav'):
            with self.assertRaises((OSError,lib.LibraryError)): self.library.open_relative(rel)

    def test_postscan_symlink_swap_is_rejected(self):
        tid = next(iter(self.library.tracks)); target = self.root/self.library.tracks[tid]['name']
        outside = self.base/'外部.wav'; wav(outside)
        target.unlink(); target.symlink_to(outside)
        with self.assertRaises(lib.LibraryError): self.library.open_track(tid)

    def test_postscan_file_modification_is_rejected(self):
        tid = next(iter(self.library.tracks)); p = self.root/self.library.tracks[tid]['name']
        with p.open('ab') as f: f.write(b'changed')
        with self.assertRaises(lib.LibraryError): self.library.open_track(tid)

    def test_music_only_track_cap(self):
        b = lib.Library(self.root, self.work/'other.json', max_tracks=1)
        try:
            self.assertEqual(b.scan_info['count'], 1); self.assertTrue(b.scan_info['truncated'])
        finally: b.close()

    def test_entry_depth_hidden_empty_and_size_boundaries(self):
        (self.root/'.隐藏.wav').write_bytes(b'a')
        (self.root/'空.wav').touch()
        deep = self.root/'a'/'b'; deep.mkdir(parents=True); wav(deep/'深.wav')
        b = lib.Library(self.root, self.work/'other.json', max_entries=3, max_depth=0)
        try:
            self.assertLessEqual(b.scan_info['entries'],3);self.assertTrue(b.scan_info['truncated'])
        finally:b.close()
        p=self.root/'过大.wav'
        with p.open('wb') as f:f.truncate(lib.MAX_FILE_BYTES+1)
        result=self.library.scan()
        self.assertNotIn('过大.wav',[t['name'] for t in result['tracks']])
        self.assertNotIn('空.wav',[t['name'] for t in result['tracks']])

    def test_corrupt_state_not_silently_reset(self):
        self.store.write_text('{bad')
        with self.assertRaises(ValueError): lib.Library(self.root,self.store)
        self.assertEqual(self.store.read_text(),'{bad')

    def test_symlink_state_rejected(self):
        other=self.work/'other.json';other.write_text('{}');self.store.symlink_to(other)
        with self.assertRaises(OSError):lib.Library(self.root,self.store)
        self.assertEqual(other.read_text(),'{}')

    def test_path_and_confirmation_errors_are_chinese(self):
        for v in ('relative','/',str(self.root/'..')):
            with self.assertRaises(lib.LibraryError):lib.canonical_directory(v)
        r=ctl.safe_execute({'action':'start','library_dir':str(self.root),'workspace':str(self.work)})
        self.assertFalse(r['ok']);self.assertEqual(r['code'],'confirmation_required')
        self.assertIn('明确授权',r['message'])
        self.assertFalse(ctl.safe_execute({'action':'start','library_dir':str(self.root),'workspace':str(self.root),'confirmed':True})['ok'])

    def test_status_does_not_create_state(self):
        r=ctl.safe_execute({'action':'status','library_dir':str(self.root),'workspace':str(self.work)})
        self.assertFalse(r['running']);self.assertFalse((self.work/'.local-music-library').exists())

    def test_ranges(self):
        for value, expected in [(None,(0,99,200)),('bytes=5-9',(5,9,206)),('bytes=5-',(5,99,206)),('bytes=-5',(95,99,206)),('bytes=0-999',(0,99,206))]:
            self.assertEqual(lib.parse_range(value,100),expected)
        for value in ('bytes=-0','bytes=100-','bytes=5-2','bytes=0-1,3-4','x','bytes=-','bytes=999999999999999999999999999-'):
            with self.assertRaises(lib.LibraryError):lib.parse_range(value,100)


class LiveHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='music-http-')
        cls.base=Path(cls.temp.name).resolve();cls.root=cls.base/'音频';cls.root.mkdir();cls.work=cls.base/'工作';cls.work.mkdir()
        wav(cls.root/'中文示例.wav');cls.original=(cls.root/'中文示例.wav').read_bytes()
        cls.args={'action':'start','library_dir':str(cls.root),'workspace':str(cls.work),'confirmed':True}
        cls.info=ctl.safe_execute(cls.args)
        if not cls.info['ok']:raise RuntimeError(cls.info)
        cls.url=cls.info['url'];cls.client=build_opener(ProxyHandler({}))
        cls.manifest=cls.fetch('api/library')[1]
        cls.tid=cls.manifest['tracks'][0]['id']

    @classmethod
    def tearDownClass(cls):
        ctl.safe_execute({**cls.args,'action':'stop'});cls.temp.cleanup()

    @classmethod
    def fetch(cls,path,method='GET',headers=None,body=None):
        req=Request(cls.url+path,data=None if body is None else json.dumps(body).encode(),method=method,headers=headers or {})
        with cls.client.open(req,timeout=5) as r:
            data=r.read();return r.status,json.loads(data) if r.headers.get_content_type()=='application/json' and data else data,dict(r.headers)

    def test_real_audio_get_head_and_range(self):
        status,data,headers=self.fetch('audio/'+self.tid)
        self.assertEqual((status,data),(200,self.original));self.assertEqual(headers['Accept-Ranges'],'bytes')
        for rg,expected in [('bytes=40-80',self.original[40:81]),('bytes=-32',self.original[-32:])]:
            status,data,headers=self.fetch('audio/'+self.tid,headers={'Range':rg});self.assertEqual((status,data),(206,expected))
        status,data,headers=self.fetch('audio/'+self.tid,method='HEAD');self.assertEqual(data,b'');self.assertEqual(int(headers['Content-Length']),len(self.original))

    def test_416_unknown_track_and_bad_token(self):
        with self.assertRaises(HTTPError) as cm:self.fetch('audio/'+self.tid,headers={'Range':'bytes=999999-'})
        self.assertEqual(cm.exception.code,416)
        with self.assertRaises(HTTPError):self.fetch('audio/../../outside')
        with self.assertRaises(HTTPError):self.client.open(self.url.replace(self.url.split('/')[-2],'badtoken'))

    def test_host_origin_contenttype_and_payload_guards(self):
        for headers in ({'Host':'evil.example'},{'Origin':'https://evil.example'},{'Sec-Fetch-Site':'cross-site'}):
            with self.assertRaises(HTTPError) as cm:self.fetch('api/library',headers=headers)
            self.assertEqual(cm.exception.code,403)
        with self.assertRaises(HTTPError) as cm:self.fetch('api/rescan',method='POST',body={})
        self.assertEqual(cm.exception.code,415)
        with self.assertRaises(HTTPError):self.fetch('api/playlist',method='POST',headers={'Content-Type':'application/json'},body={'name':'外部','tracks':['outside']})

    def test_actual_http_playlist_resume_rescan(self):
        headers={'Content-Type':'application/json'}
        self.fetch('api/playlist','POST',headers,{'name':'HTTP歌单','tracks':[self.tid]})
        self.fetch('api/resume','POST',headers,{'track':self.tid,'seconds':1.2,'volume':.5,'mode':'sequence'})
        a=self.fetch('api/library')[1];self.assertEqual(a['resume']['seconds'],1.2)
        self.assertTrue(any(p['name']=='HTTP歌单' for p in a['playlists']))
        self.assertTrue(self.fetch('api/rescan','POST',headers,{})[1]['ok'])

    def test_duplicate_start_status_and_unconfirmed_stop(self):
        r=ctl.safe_execute(self.args);self.assertEqual(r['session_id'],self.info['session_id'])
        self.assertTrue(ctl.safe_execute({**self.args,'action':'status'})['running'])
        self.assertFalse(ctl.safe_execute({**self.args,'action':'stop','confirmed':False})['ok'])

    def test_static_chinese_and_offline_csp(self):
        _,page,headers=self.fetch('')
        self.assertIn('本地音乐库',page.decode());self.assertIn("default-src 'self'",headers['Content-Security-Policy'])
        _,app,_=self.fetch('app.js');self.assertNotIn(b'https://',app)
        _,license_data,_=self.fetch('license');self.assertIn(b'Copyright (c) 2026 kendu76',license_data)

    def test_cross_site_document_navigation_only(self):
        nav={'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'navigate','Sec-Fetch-Dest':'document'}
        self.assertEqual(self.fetch('',headers=nav)[0],200)
        for path in ('api/library','audio/'+self.tid):
            with self.assertRaises(HTTPError) as cm:self.fetch(path,headers=nav)
            self.assertEqual(cm.exception.code,403)


if __name__=='__main__':unittest.main()
