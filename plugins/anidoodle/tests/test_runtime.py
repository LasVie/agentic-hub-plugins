import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import asyncio

PAYLOAD = Path(os.environ.get('ANIDOODLE_PAYLOAD', Path(__file__).resolve().parents[1]/'anidoodle'))
spec=importlib.util.spec_from_file_location('art_runtime',PAYLOAD/'runtime.py')
art=importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def call(self,**kw):
        return art.execute({'action':'create','workspace':str(self.path),'name':'test-art',**kw})
    def test_three_scenes_keep_license_and_chinese(self):
        for scene in art.SCENES:
            r=self.call(scene=scene,name=scene,title='中文手绘作品')
            self.assertTrue(r['ok'],r)
            p=Path(r['path']).read_text(encoding='utf-8')
            for marker in ['lang="zh-CN"','中文手绘作品','Copyright 2026 Alex Greenshpun','Apache License','Third-party material','connect-src \'none\'','保存当前画面 PNG']:
                self.assertIn(marker,p)
    def test_html_injection_escaped(self):
        r=self.call(title='</h1><script>alert(1)</script>',description='<img src=x onerror=alert(2)>')
        self.assertTrue(r['ok'])
        p=Path(r['path']).read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;alert(1)',p)
        self.assertNotIn('<img src=x',p)
    def test_existing_output_preserved(self):
        p=self.path/'test-art.html';p.write_text('original')
        self.assertFalse(self.call()['ok']);self.assertEqual(p.read_text(),'original')
    def test_path_traversal_and_reserved_names_rejected(self):
        for n in ['../escape','a/b','a\\b','con','com1','nul','a.html','x'*51,'a:stream']:
            self.assertFalse(self.call(name=n)['ok'],n)
        self.assertEqual(list(self.path.iterdir()),[])
    def test_invalid_input_and_missing_workspace(self):
        for v in [None,[],{}, {'action':'unknown'}, {'action':'create','workspace':'relative'}]:
            self.assertFalse(art.execute(v)['ok'])
        self.assertFalse(self.call(workspace=str(self.path/'missing'))['ok'])
    def test_limits_and_bad_scene_do_not_write(self):
        for kw in [{'title':'x'*81},{'title':42},{'description':'x'*601},{'scene':'missing'},{'scene':[]}]:
            self.assertFalse(self.call(**kw)['ok'])
        self.assertEqual(list(self.path.iterdir()),[])
    def test_export_source_is_complete_and_not_overwritten(self):
        r=self.call(action='source');self.assertTrue(r['ok'],r)
        p=Path(r['path'])
        for n in ['engine/src/entry.ts','engine/src/canvas-core/core.ts','engine/art.js','engine/build.mjs','runtime.py','README.md','licenses/anidoodle/LICENSE','licenses/anidoodle/NOTICE']:
            self.assertTrue((p/n).is_file(),n)
        self.assertFalse((p/'engine/node_modules').exists())
        self.assertFalse(self.call(action='source')['ok'])
    def test_source_and_html_lists_are_truthful(self):
        r=art.execute({'action':'list'})
        self.assertEqual([x['id'] for x in r['scenes']],['mascot','form','scroll'])
        self.assertIn('不包含',r['scope'])
    def test_actual_host_manifest_and_tool(self):
        from openjiuwen.harness.resources import load_plugin_package
        from openjiuwen.harness.schema.extension_spec import validate_plugin_paths
        spec=load_plugin_package(PAYLOAD/'manifest.json')
        validate_plugin_paths(spec)
        self.assertEqual(spec.id,'anidoodle')
        self.assertEqual(len(spec.skills),1)
        tool=spec.tools[0].build(language='cn')
        async def run():
            self.assertTrue((await tool.invoke({'action':'list'}))['ok'])
            for scene in art.SCENES:
                self.assertTrue((await tool.invoke({'action':'create','scene':scene,'workspace':str(self.path),'name':scene,'title':'中文宿主验收'}))['ok'])
            self.assertTrue((await tool.invoke({'action':'source','workspace':str(self.path),'name':'editable'}))['ok'])
            chunks=[r async for r in tool.stream({'action':'list'})]
            self.assertTrue(chunks[0]['ok'])
        asyncio.run(run())

if __name__=='__main__': unittest.main()
