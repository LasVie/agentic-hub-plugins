"""Functional tests of actual runtime, archive failures and real loopback reader HTTP."""
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import stat
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request
import zipfile

REPO = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get('EBOOK_TEST_PAYLOAD', str(REPO/'plugins/offline-ebook-reader/offline-ebook-reader')))


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    old=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True;spec.loader.exec_module(m)
    finally:sys.dont_write_bytecode=old
    return m


core=module('ebook_functional_core',PAYLOAD/'runtime/ebook.py')
fixtures=module('ebook_fixture_data',REPO/'plugins/offline-ebook-reader/prepare_manual_testing.py')


class EbookTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='offline-ebook-test-')
        self.root=Path(self.tmp.name).resolve();self.work=self.root/'工作目录';self.work.mkdir()
        self.source=self.root/'中文示例.txt';self.source.write_text('前言文字\n第一章 清晨\n真实正文🙂\n第二章 傍晚\n最后一章正文',encoding='utf-8')
    def tearDown(self):self.tmp.cleanup()
    def call(self,action,**kw):return core.dispatch('library',{'workspace':str(self.work),'action':action,**kw})
    def imported(self,data=None,name='book.epub'):
        p=self.source
        if data is not None:p=self.root/name;p.write_bytes(data)
        r=self.call('import',path=str(p),confirmed=True);self.assertTrue(r['ok'],r);return r
    def rejected(self,code,**kw):
        p=self.root/'拒绝.epub';p.write_bytes(fixtures.epub_bytes(**kw));r=self.call('import',path=str(p),confirmed=True)
        self.assertFalse(r['ok'],r);self.assertEqual(r['error']['code'],code,r)
    def replace_zip(self,changes):
        with zipfile.ZipFile(io.BytesIO(fixtures.epub_bytes())) as z:parts={n:z.read(n) for n in z.namelist()}
        parts.update(changes);b=io.BytesIO()
        with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n,d in parts.items():z.writestr(n,d)
        return b.getvalue()
    def test_empty_list_no_write(self):
        self.assertEqual(self.call('list')['books'],[]);self.assertFalse((self.work/'.offline-ebook-reader').exists())
    def test_confirmation_before_write(self):
        r=self.call('import',path=str(self.source));self.assertEqual(r['error']['code'],'confirmation_required');self.assertFalse((self.work/'.offline-ebook-reader').exists())
    def test_txt_chapters_exact_body_and_source_preserved(self):
        before=self.source.read_bytes();r=self.imported();bid=r['book']['book_id']
        toc=self.call('toc',book_id=bid);self.assertEqual([c['title'] for c in toc['chapters']],['正文','第一章 清晨','第二章 傍晚'])
        read=core.dispatch('read',{'workspace':str(self.work),'book_id':bid,'chapter_index':1});self.assertEqual(read['text'],'真实正文🙂');self.assertEqual(self.source.read_bytes(),before)
    def test_duplicate_preserves_position(self):
        a=self.imported();bid=a['book']['book_id'];s=self.call('progress',book_id=bid,chapter_index=2,offset_ratio=.4,expected_revision=a['revision'],confirmed=True);self.assertTrue(s['ok'])
        b=self.imported();self.assertTrue(b['reused']);self.assertEqual(b['book']['progress']['offset_ratio'],.4);self.assertEqual(b['revision'],s['revision'])
    def test_gb18030_explicit(self):
        self.source.write_bytes('第一章 中文\n旧编码正文'.encode('gb18030'));bad=self.call('import',path=str(self.source),confirmed=True);self.assertEqual(bad['error']['code'],'invalid_encoding')
        good=self.call('import',path=str(self.source),encoding='gb18030',confirmed=True);self.assertTrue(good['ok'],good)
    def test_utf16_bom_and_utf8_bom(self):
        for encoding,raw in [('utf-16','第一章\n有BOM'.encode('utf-16')),('utf-8','第一章\n有BOM'.encode('utf-8-sig'))]:
            self.source.write_bytes(raw);self.assertTrue(self.call('import',path=str(self.source),encoding=encoding,confirmed=True)['ok'])
    def test_nul_rejected(self):
        self.source.write_bytes(b'abc\x00def');r=self.call('import',path=str(self.source),confirmed=True);self.assertEqual(r['error']['code'],'invalid_text')
    def test_txt_without_headings(self):
        self.source.write_text('没有标题的完整正文',encoding='utf-8');r=self.imported();self.assertEqual(r['book']['chapter_count'],1)
    def test_epub_order_nav_labels_and_omissions(self):
        r=self.imported(fixtures.epub_bytes());bid=r['book']['book_id'];toc=self.call('toc',book_id=bid)
        self.assertEqual([c['title'] for c in toc['chapters']],['第一章 出发','第二章 归来']);self.assertGreater(len(r['book']['warnings']),1)
        d=core.dispatch('read',{'workspace':str(self.work),'book_id':bid,'chapter_index':0});self.assertIn('春天',d['text']);self.assertIn('[图片：远方的小屋]',d['text']);self.assertNotIn('shouldNeverRun',d['text'])
    def test_epub2(self):self.assertEqual(self.imported(fixtures.epub_bytes(version='2.0'))['book']['format'],'epub')
    def test_drm_rejected(self):self.rejected('encrypted_epub',encrypted=True)
    def test_fixed_rejected(self):self.rejected('fixed_layout',fixed=True)
    def test_image_only_rejected(self):self.rejected('image_only',image=True)
    def test_missing_chapter_rejected(self):self.rejected('missing_entry',missing=True)
    def test_traversal_rejected(self):self.rejected('unsafe_archive',unsafe=True)
    def test_xml_entities_rejected(self):
        r=self.call_data(self.replace_zip({'META-INF/container.xml':b'<!DOCTYPE x [<!ENTITY e "bad">]><container>&e;</container>'}));self.assertEqual(r['error']['code'],'unsafe_xml')
    def call_data(self,data):
        p=self.root/'bad.epub';p.write_bytes(data);return self.call('import',path=str(p),confirmed=True)
    def test_malformed_xml(self):self.assertEqual(self.call_data(self.replace_zip({'META-INF/container.xml':b'<unclosed>'}))['error']['code'],'invalid_xml')
    def test_remote_spine_rejected(self):
        with zipfile.ZipFile(io.BytesIO(fixtures.epub_bytes())) as z:opf=z.read('OEBPS/book.opf').replace(b'first.xhtml',b'https://example.invalid/first.xhtml')
        r=self.call_data(self.replace_zip({'OEBPS/book.opf':opf}));self.assertEqual(r['error']['code'],'unsafe_archive')
    def test_missing_nav_reference_rejected(self):
        data=self.replace_zip({'OEBPS/nav.xhtml':b'<html><body><a href="missing.xhtml">missing</a></body></html>'});self.assertEqual(self.call_data(data)['error']['code'],'missing_entry')
    def test_duplicate_zip_entry_rejected(self):
        b=io.BytesIO(fixtures.epub_bytes())
        with zipfile.ZipFile(b,'a') as z:
            with self.assertWarns(UserWarning):z.writestr('mimetype','application/epub+zip')
        self.assertEqual(self.call_data(b.getvalue())['error']['code'],'unsafe_archive')
    def test_symlink_zip_entry_rejected(self):
        b=io.BytesIO(fixtures.epub_bytes())
        with zipfile.ZipFile(b,'a') as z:
            info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'target')
        self.assertEqual(self.call_data(b.getvalue())['error']['code'],'unsafe_archive')
    def test_corrupt_zip_no_text_fallback(self):self.assertEqual(self.call_data(b'PK-bad')['error']['code'],'invalid_epub')
    def test_expansion_limit(self):
        b=io.BytesIO(fixtures.epub_bytes())
        with zipfile.ZipFile(b,'a',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('large.txt',b'a'*(4*1024*1024+1))
        self.assertEqual(self.call_data(b.getvalue())['error']['code'],'unsafe_archive')
    def test_input_limit(self):
        self.source.write_bytes(b'a'*(core.MAX_INPUT+1));self.assertEqual(self.call('import',path=str(self.source),confirmed=True)['error']['code'],'size_limit')
    def test_source_symlink_refused(self):
        p=self.root/'link.txt';p.symlink_to(self.source);self.assertEqual(self.call('import',path=str(p),confirmed=True)['error']['code'],'unsafe_path')
    def test_state_symlink_refused(self):
        (self.work/'.offline-ebook-reader').symlink_to(self.root,target_is_directory=True);self.assertEqual(self.call('import',path=str(self.source),confirmed=True)['error']['code'],'unsafe_state')
    def test_tampered_copy_refused(self):
        r=self.imported();bid=r['book']['book_id'];(self.work/'.offline-ebook-reader/books'/bid/'original').write_bytes(b'bad');self.assertEqual(self.call('toc',book_id=bid)['error']['code'],'integrity_mismatch')
    def test_state_corruption_preserved(self):
        self.imported();p=self.work/'.offline-ebook-reader/shelf.json';p.write_bytes(b'bad');self.assertFalse(self.call('list')['ok']);self.assertEqual(p.read_bytes(),b'bad')
    def test_invalid_progress_and_stale_revision(self):
        r=self.imported();bid=r['book']['book_id']
        for index,ratio in [(False,.1),(900,.1),(1,float('nan')),(1,1.1)]:
            x=self.call('progress',book_id=bid,chapter_index=index,offset_ratio=ratio,expected_revision=r['revision'],confirmed=True);self.assertEqual(x['error']['code'],'invalid_progress')
        x=self.call('progress',book_id=bid,chapter_index=1,offset_ratio=.75,expected_revision=r['revision'],confirmed=True);self.assertTrue(x['ok'])
        y=self.call('progress',book_id=bid,chapter_index=0,offset_ratio=0,expected_revision=r['revision'],confirmed=True);self.assertEqual(y['error']['code'],'revision_conflict');self.assertEqual(self.call('list')['books'][0]['progress']['offset_ratio'],.75)
    def test_preferences_persist_across_module_reopen(self):
        r=self.imported();prefs={'font_size':24,'line_height':2.2,'width':560,'theme':'dark'}
        s=self.call('preferences',preferences=prefs,expected_revision=r['revision'],confirmed=True);self.assertTrue(s['ok'],s)
        other=module('ebook_reopened',PAYLOAD/'runtime/ebook.py');self.assertEqual(other.dispatch('library',{'workspace':str(self.work),'action':'list'})['preferences'],prefs)
    def test_invalid_preferences(self):
        r=self.imported();x=self.call('preferences',preferences={**core.DEFAULT_PREFS,'font_size':500},expected_revision=r['revision'],confirmed=True);self.assertEqual(x['error']['code'],'invalid_preferences')
    def test_character_range_discloses_truncation(self):
        r=self.imported();bid=r['book']['book_id'];a=core.dispatch('read',{'workspace':str(self.work),'book_id':bid,'chapter_index':1,'max_chars':2});self.assertTrue(a['truncated']);self.assertEqual(a['next_char'],2)
        b=core.dispatch('read',{'workspace':str(self.work),'book_id':bid,'chapter_index':1,'start_char':2});self.assertEqual(a['text']+b['text'],'真实正文🙂')
    def test_unknown_book_and_invalid_argument(self):
        self.imported();self.assertEqual(self.call('toc',book_id='../x')['error']['code'],'book_missing');self.assertFalse(core.dispatch('library',[] )['ok']);self.assertFalse(self.call('list',unknown=True)['ok'])
    def test_ui_uses_text_nodes_no_external_media(self):
        app=(PAYLOAD/'assets/app.js').read_text();self.assertIn('text.textContent=chapter.text',app);self.assertNotIn('innerHTML',app);self.assertNotIn('https://',app)
    def test_live_reader_health_book_and_cross_site_refusal(self):
        r=self.imported(fixtures.epub_bytes());bid=r['book']['book_id']
        start=core.dispatch('reader',{'workspace':str(self.work),'action':'start','confirmed':True});self.assertTrue(start['ok'],start)
        opener=build_opener(ProxyHandler({}));url=start['url']
        def request(name,body=None,headers=None):
            return opener.open(Request(url+name,data=None if body is None else json.dumps(body).encode(),headers=headers or {'Content-Type':'application/json'}),timeout=5)
        try:
            with request('') as response:self.assertIn('离线书架阅读器',response.read().decode());self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])
            with request('api/book',{'book_id':bid}) as response:self.assertEqual(len(json.load(response)['chapters']),2)
            with self.assertRaises(HTTPError) as cm:request('api/save',{'action':'progress'}, {'Content-Type':'application/json','Origin':'https://example.invalid'})
            self.assertEqual(cm.exception.code,403)
            current=core.dispatch('reader',{'workspace':str(self.work),'action':'status'});self.assertEqual(current['session_id'],start['session_id'])
            self.assertEqual(core.dispatch('reader',{'workspace':str(self.work),'action':'start','confirmed':True})['session_id'],start['session_id'])
        finally:self.assertTrue(core.dispatch('reader',{'workspace':str(self.work),'action':'stop','confirmed':True})['ok'])
        self.assertFalse(core.dispatch('reader',{'workspace':str(self.work),'action':'status'})['running'])


if __name__=='__main__':unittest.main()
