"""Actual Node CLI + actual openJiuwen loader/ToolCard checks (no fake SDK)."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get('MWG_TEST_PAYLOAD', ASSET / 'modern-web-guidance')).resolve()
NODE = shutil.which('node')


def cli(value):
    result = subprocess.run([NODE, str(PAYLOAD/'runtime/cli.mjs')], input=json.dumps(value, ensure_ascii=False),
                            encoding='utf-8', capture_output=True, timeout=15)
    return result.returncode, json.loads(result.stdout)


class GuidanceTests(unittest.TestCase):
    def test_help_and_complete_catalog(self):
        code, value = cli({'action':'help'})
        self.assertEqual(code, 0)
        self.assertEqual(value['version'], '1.0.0')
        self.assertEqual(value['guide_count'], 12)
        listed = cli({'action':'list'})[1]['guides']
        self.assertEqual(len({g['id'] for g in listed}), 12)
        for guide in listed:
            with self.subTest(id=guide['id']):
                code, read = cli({'action':'retrieve','ids':[guide['id']]})
                self.assertEqual(code, 0)
                self.assertIn('修改声明', read['guides'][0]['content'])
                self.assertIn('固定上游快照', read['guides'][0]['content'])
                self.assertIn(guide['source'], read['guides'][0]['content'])

    def test_twelve_real_chinese_queries(self):
        cases = {
            '容器查询卡片布局':'size-aware-styling',
            '父元素 has 状态样式':'style-parent-with-has',
            'Safari 弹窗点击遮罩关闭':'light-dismiss-a-dialog',
            '自然高度折叠展开动画':'animate-to-intrinsic-sizes',
            '单页视图切换过渡':'same-document-transitions',
            '首屏 LCP 图片优先级':'optimize-image-priority',
            '长任务卡顿 scheduler yield':'break-up-long-tasks',
            '首屏外渲染 content-visibility':'defer-rendering-heavy-content',
            '交互后表单校验 user-invalid':'validate-input-after-interaction',
            '中文输入法回车误提交':'ime-safe-enter-submit',
            '响应式表格固定表头':'responsive-table',
            '系统暗色主题 dark mode':'dark-mode',
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                code, value = cli({'action':'search','query':query,'limit':3})
                self.assertEqual(code, 0)
                self.assertEqual(value['results'][0]['id'], expected)

    def test_negative_inputs(self):
        for value in [None, [], {}, {'action':'execute'}, {'action':'search','query':''},
                      {'action':'search','query':' '}, {'action':'search','query':42},
                      {'action':'search','query':'x'*301}, {'action':'search','query':'LCP','limit':0},
                      {'action':'search','query':'LCP','limit':1.5},
                      {'action':'search','query':'LCP','limit':13},
                      {'action':'retrieve','ids':['../../README']},
                      {'action':'retrieve','ids':['missing']}, {'action':'retrieve','ids':[]},
                      {'action':'retrieve','ids':['dark-mode']*4},
                      {'action':'list','file':'C:/private.txt'}]:
            with self.subTest(value=value):
                code, result = cli(value)
                self.assertEqual(code, 2)
                self.assertFalse(result['ok'])
                self.assertRegex(result['message'], '[\u4e00-\u9fff]')

    def test_malformed_and_oversized_stdin(self):
        for raw in ['{', 'x'*20000]:
            result = subprocess.run([NODE,str(PAYLOAD/'runtime/cli.mjs')],input=raw,
                                    encoding='utf-8',capture_output=True,timeout=15)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)['ok'])

    def test_uncovered_and_shell_text_are_data(self):
        for query in ['PostgreSQL 数据库索引', 'zzzznotacapability', '$(whoami); `touch pwned`']:
            result = cli({'action':'search','query':query})[1]
            self.assertTrue(result['ok'])
            self.assertEqual(result['results'], [])

    def test_retrieve_deduplicates(self):
        result = cli({'action':'retrieve','ids':['dark-mode','dark-mode']})[1]
        self.assertEqual(len(result['guides']),1)

    def test_no_payload_writes(self):
        def snapshot():
            return {str(p.relative_to(PAYLOAD)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in PAYLOAD.rglob('*') if p.is_file()}
        before=snapshot()
        for action in [{'action':'list'},{'action':'search','query':'弹窗'},
                       {'action':'retrieve','ids':['light-dismiss-a-dialog']}]:
            self.assertEqual(cli(action)[0],0)
        self.assertEqual(before,snapshot())

    def test_license_and_localization_coverage(self):
        p=json.loads((ASSET/'provenance.json').read_text(encoding='utf-8'))
        for source in p['sources']:
            for item in source['license_evidence']:
                self.assertEqual(hashlib.sha256((PAYLOAD/item['path']).read_bytes()).hexdigest(),item['sha256'])
        for item in p['source_mapping']:
            self.assertEqual(hashlib.sha256((PAYLOAD/item['target']).read_bytes()).hexdigest(),item['target_sha256'])
        for f in PAYLOAD.rglob('*.md'):
            text=f.read_text(encoding='utf-8')
            self.assertNotIn('\ufffd',text)
            self.assertRegex(text, '[\u4e00-\u9fff]')
        self.assertFalse(list(PAYLOAD.rglob('node_modules')))
        self.assertFalse(list(PAYLOAD.rglob('*.bin')))

    def test_native_loader_and_actual_tool(self):
        from openjiuwen.harness.resources import load_plugin_package
        from openjiuwen.harness.schema.extension_spec import validate_plugin_paths
        spec=load_plugin_package(PAYLOAD/'manifest.json')
        validate_plugin_paths(spec)
        self.assertEqual(spec.id,'modern-web-guidance')
        self.assertEqual(len(spec.skills),1)
        self.assertEqual(len(spec.tools),1)
        tool=spec.tools[0].build(language='cn')
        async def run():
            found=await tool.invoke({'action':'search','query':'中文输入法回车误提交','limit':1})
            self.assertEqual(found['results'][0]['id'],'ime-safe-enter-submit')
            read=await tool.invoke({'action':'retrieve','ids':['ime-safe-enter-submit']})
            self.assertIn('先排除组合输入',read['guides'][0]['content'])
            stream=[x async for x in tool.stream({'action':'help'})]
            self.assertEqual(stream[0]['guide_count'],12)
            self.assertFalse((await tool.invoke([]))['ok'])
            self.assertFalse((await tool.invoke({'action':'search','query':float('nan')}))['ok'])
            old=os.environ.get('PATH','')
            try:
                os.environ['PATH']=''
                missing=await tool.invoke({'action':'help'})
                self.assertFalse(missing['ok'])
                self.assertIn('未找到 Node.js',missing['message'])
            finally:
                os.environ['PATH']=old
        asyncio.run(run())

    def test_relocated_chinese_space_directory(self):
        with tempfile.TemporaryDirectory(prefix='mwg-') as tmp:
            relocated=Path(tmp)/'中文 插件'/ 'modern-web-guidance'
            shutil.copytree(PAYLOAD,relocated)
            result=subprocess.run([NODE,str(relocated/'runtime/cli.mjs')],input='{"action":"list"}',
                                  encoding='utf-8',capture_output=True,timeout=15,cwd=tmp)
            self.assertEqual(result.returncode,0)
            self.assertEqual(len(json.loads(result.stdout)['guides']),12)

    def test_corrupt_package_has_chinese_error(self):
        with tempfile.TemporaryDirectory(prefix='mwg-broken-') as tmp:
            broken=Path(tmp)/'plugin'
            shutil.copytree(PAYLOAD,broken)
            (broken/'data/catalog.json').write_text('{}',encoding='utf-8')
            result=subprocess.run([NODE,str(broken/'runtime/cli.mjs')],input='{"action":"list"}',
                                  encoding='utf-8',capture_output=True,timeout=15)
            self.assertEqual(result.returncode,2)
            self.assertIn('目录损坏',json.loads(result.stdout)['message'])


if __name__=='__main__':
    unittest.main(verbosity=2)
