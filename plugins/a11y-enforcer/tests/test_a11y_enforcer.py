"""Unit tests for the a11y-enforcer payload (tools/a11y_enforcer.py).

Run with a Python that has the openjiuwen SDK, from a scratch directory (the SDK writes a logs/ folder to the cwd):
    python -B -X utf8 -m unittest discover -s <abs path to plugins/a11y-enforcer/tests>
"""
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
ASSET = Path(__file__).resolve().parents[1]
PAYLOAD = ASSET / 'a11y-enforcer'
spec = importlib.util.spec_from_file_location('a11y_enforcer_under_test', PAYLOAD / 'tools' / 'a11y_enforcer.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

UPSTREAM_TAG_RE = re.compile(r"<([A-Za-z][\w.-]*)((?:\s+(?:\{[^}]*\}|[^\s>=/]+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\}|[^\s>]+))?))*)\s*(/?)>", re.S)
UPSTREAM_LABEL_FOR = re.compile(r"<label\b[^>]*\b(?:for|htmlFor)\s*=\s*[\"'{]\s*[\"']?([\w:-]+)")


def call(name, arguments):
    return asyncio.run(M.call_tool(name, arguments))


class TempCase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix='a11y-test-'))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def write(self, name, text, encoding='utf-8', newline=None):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode(encoding)
        path.write_bytes(data)
        return str(path)

    def rules(self, name, text):
        path = self.write(name, text)
        return [(i['rule'], i['line']) for i in M.scan_file(path)]

    def rule_names(self, name, text):
        return [r for r, _ in self.rules(name, text)]


class RuleTests(TempCase):
    def test_html_lang(self):
        self.assertIn('html-lang', self.rule_names('a.html', '<html><body></body></html>'))
        self.assertNotIn('html-lang', self.rule_names('b.html', '<html lang="zh-CN"><body></body></html>'))
        self.assertNotIn('html-lang', self.rule_names('c.vue', '<template><html></html></template>'))

    def test_img_alt(self):
        self.assertEqual(self.rule_names('a.html', '<img src="a.png">'), ['img-alt'])
        for ok in ('<img src="a.png" alt="">', '<img src="a.png" alt="公司标志">', '<img src="a.png" role="presentation">',
                   '<img src="a.png" aria-hidden="true">', '<img {...props}>'):
            self.assertEqual(self.rule_names('ok.html', ok), [], ok)
        self.assertEqual(self.rule_names('a.jsx', '<Image src="a.png" />'), ['img-alt'])
        self.assertEqual(self.rule_names('b.tsx', '<NextImage src={x} />'), ['img-alt'])
        self.assertEqual(self.rule_names('c.jsx', '<Avatar src="a.png" />'), [])

    def test_input_labels(self):
        self.assertEqual(self.rule_names('a.html', '<input type="text" id="q">'), ['form-label'])
        self.assertEqual(self.rule_names('b.html', '<input placeholder="搜索">'), ['form-label'])
        for ok in ('<label for="q">搜索</label><input id="q">', '<label>搜索 <input></label>', '<input aria-label="搜索">',
                   '<input aria-labelledby="x">', '<input title="搜索">', '<input type="hidden">', '<input type="submit">',
                   '<input type="button" value="发送">', '<input {...rest}>'):
            self.assertEqual(self.rule_names('ok.html', ok), [], ok)
        self.assertEqual(self.rule_names('c.jsx', '<label htmlFor="n">姓名</label><input id="n" />'), [])
        self.assertEqual(self.rule_names('d.html', '<input type="image" src="x.png">'), ['input-image-alt'])
        self.assertEqual(self.rule_names('e.html', '<select><option>1</option></select>'), ['form-label'])
        self.assertEqual(self.rule_names('f.html', '<textarea></textarea>'), ['form-label'])
        self.assertEqual(self.rule_names('g.html', '<label for="t">备注</label><textarea id="t"></textarea>'), [])

    def test_button_and_link_names(self):
        self.assertEqual(self.rule_names('a.html', '<button><svg></svg></button>'), ['button-name'])
        self.assertEqual(self.rule_names('b.html', '<button></button>'), ['button-name'])
        self.assertEqual(self.rule_names('c.jsx', '<button />'), ['button-name'])
        for ok in ('<button>提交</button>', '<button aria-label="关闭"><svg></svg></button>', '<button><svg><title>关闭</title></svg></button>',
                   '<button><img src="x.png" alt="关闭"></button>', '<button>{label}</button>', '<button {...props}></button>'):
            self.assertEqual(self.rule_names('ok.html', ok), [], ok)
        self.assertEqual(self.rule_names('d.html', '<a href="/x"></a>'), ['link-name'])
        self.assertEqual(self.rule_names('e.html', '<a href="/x"><svg></svg></a>'), ['link-name'])
        self.assertEqual(self.rule_names('f.html', '<a href="/x">首页</a>'), [])

    def test_link_purpose_english_and_chinese(self):
        for text in ('click here', 'Read more', 'here', '点击这里', '更多', '了解更多', '详情', '点击查看', '链接'):
            names = self.rule_names('a.html', '<a href="/x">%s</a>' % text)
            self.assertEqual(names, ['link-purpose'], text)
        self.assertEqual(self.rule_names('b.html', '<a href="/x">查看本月销售报表</a>'), [])
        issue = M.scan_file(self.write('c.html', '<a href="/x">更多</a>'))[0]
        self.assertEqual(issue['level'], 'warning')

    def test_anchor_as_button(self):
        self.assertEqual(self.rule_names('a.html', '<a onclick="go()">去</a>'), ['anchor-is-button'])
        self.assertEqual(self.rule_names('b.vue', '<a @click="go">去</a>'), ['anchor-is-button'])
        self.assertEqual(self.rule_names('c.html', '<a href="/x" onclick="go()">去</a>'), [])

    def test_clickable_non_interactive(self):
        names = self.rule_names('a.html', '<div onclick="go()">去</div>')
        self.assertEqual(names, ['click-no-role', 'click-no-focus', 'click-no-key'])
        self.assertEqual(self.rule_names('b.html', '<div onclick="go()" role="button" tabindex="0" onkeydown="k()">去</div>'), [])
        self.assertEqual(self.rule_names('c.vue', '<span @click="go">去</span>'), ['click-no-role', 'click-no-focus', 'click-no-key'])
        self.assertEqual(self.rule_names('d.html', '<li (click)="go()">去</li>'), ['click-no-role', 'click-no-focus', 'click-no-key'])
        self.assertEqual(self.rule_names('e.svelte', '<div on:click={go}>去</div>'), ['click-no-role', 'click-no-focus', 'click-no-key'])
        self.assertEqual(self.rule_names('f.jsx', '<div onClick={go}>去</div>'), ['click-no-role', 'click-no-focus', 'click-no-key'])  # attribute names are lowercased

    def test_media(self):
        self.assertEqual(self.rule_names('a.html', '<video autoplay src="a.mp4"></video>'), ['media-autoplay', 'video-captions'])
        self.assertEqual(self.rule_names('b.html', '<video autoplay muted><track kind="captions"></video>'), [])
        self.assertEqual(self.rule_names('c.html', '<audio autoplay src="a.mp3"></audio>'), ['media-autoplay'])
        self.assertEqual(self.rule_names('d.html', '<audio controls src="a.mp3"></audio>'), [])

    def test_iframe_headings_viewport_tabindex_accesskey_role(self):
        self.assertEqual(self.rule_names('a.html', '<iframe src="x"></iframe>'), ['iframe-title'])
        self.assertEqual(self.rule_names('b.html', '<iframe src="x" title="地图"></iframe>'), [])
        self.assertEqual(self.rule_names('c.html', '<h1>a</h1><h3>b</h3><h2>c</h2><h4>d</h4>'), ['heading-order', 'heading-order'])
        self.assertEqual(self.rule_names('d.html', '<h1>a</h1><h2>b</h2><h2>c</h2><h3>d</h3>'), [])
        self.assertEqual(self.rule_names('e.html', '<meta name="viewport" content="width=device-width, user-scalable=no">'), ['viewport-zoom'])
        self.assertEqual(self.rule_names('f.html', '<meta name="viewport" content="width=device-width, maximum-scale=1.0">'), ['viewport-zoom'])
        self.assertEqual(self.rule_names('g.html', '<meta name="viewport" content="width=device-width, initial-scale=1">'), [])
        self.assertEqual(self.rule_names('h.html', '<div tabindex="3">x</div>'), ['tabindex-positive'])
        self.assertEqual(self.rule_names('i.jsx', '<div tabIndex={2}>x</div>'), ['tabindex-positive'])  # attribute names are lowercased
        self.assertEqual(self.rule_names('j.html', '<div tabindex="0">x</div><div tabindex="-1">y</div>'), [])
        self.assertEqual(self.rule_names('k.html', '<button accesskey="s">保存</button>'), ['accesskey'])
        self.assertEqual(self.rule_names('l.html', '<div role="tab">x</div>'), ['role-no-focus'])
        self.assertEqual(self.rule_names('m.html', '<div role="tab" tabindex="0">x</div>'), [])
        self.assertEqual(self.rule_names('n.html', '<button role="tab">x</button>'), [])

    def test_focus_outline(self):
        # upstream quirk kept: in .html/.vue/.svelte/.astro an inline outline:none is reported by both the inline-style and the CSS-text check
        self.assertEqual(self.rule_names('a.html', '<button style="outline: none">x</button>'), ['focus-outline', 'focus-outline'])
        self.assertEqual(self.rule_names('a2.jsx', '<button style="outline: none">x</button>'), ['focus-outline'])
        self.assertEqual(self.rule_names('b.html', '<style>a{outline:none}</style><a href="#">x</a>'), ['focus-outline'])
        self.assertIn('focus-outline', self.rule_names('c.vue', '<style>a{outline:none}</style>'))
        self.assertNotIn('focus-outline', self.rule_names('d.vue', '<style>a{outline:none} a:focus-visible{outline:2px solid}</style>'))
        self.assertNotIn('focus-outline', self.rule_names('e.jsx', 'const css = "a{outline:none}"'))

    def test_messages_are_chinese_and_ids_are_upstream(self):
        issues = M.scan_file(self.write('a.html', '<html><img src="a.png"><button></button></html>'))
        self.assertEqual({i['rule'] for i in issues}, {'html-lang', 'img-alt', 'button-name'})
        for issue in issues:
            self.assertTrue(any('一' <= ch <= '鿿' for ch in issue['message']), issue)
            self.assertIn(issue['level'], ('error', 'warning'))
            self.assertRegex(issue['wcag'], r'^\d\.\d\.\d')

    def test_line_numbers_across_newline_styles(self):
        for newline in ('\n', '\r\n', '\r'):
            text = newline.join(['<html lang="zh-CN">', '<body>', '', '<img src="a.png">', '</body>', '</html>'])
            self.assertEqual(self.rules('n%d.html' % len(newline), text), [('img-alt', 4)], repr(newline))
        path = self.write('mixed.html', '<p>一</p>\r\n<p>二</p>\r<img src="a.png">\n')
        self.assertEqual([i['line'] for i in M.scan_file(path)], [3])

    def test_framework_files(self):
        jsx = 'export const A = () => (<div><img src={x} /><input type="text" /><button onClick={go}></button></div>);'
        self.assertEqual(self.rule_names('a.jsx', jsx), ['img-alt', 'form-label', 'button-name'])
        self.assertEqual(self.rule_names('a.tsx', jsx), ['img-alt', 'form-label', 'button-name'])
        self.assertEqual(self.rule_names('a.vue', '<template><img :src="u"><input v-model="v"></template>'), ['img-alt', 'form-label'])
        self.assertEqual(self.rule_names('a.svelte', '<img src={u}><input bind:value={v}>'), ['img-alt', 'form-label'])
        self.assertEqual(self.rule_names('a.astro', '---\nconst a = 1;\n---\n<img src={u}>'), ['img-alt'])

    def test_chinese_content_and_bom_and_gbk(self):
        text = '<html lang="zh-CN"><body><button>提交订单</button><label for="n">收货人姓名</label><input id="n"><img src="a.png" alt="首页轮播图：双十一促销"></body></html>'
        self.assertEqual(self.rules('cn.html', text), [])
        bom = self.write('bom.html', '﻿' + '<html lang="zh-CN"><img src="a.png"></html>')
        self.assertEqual([i['rule'] for i in M.scan_file(bom)], ['img-alt'])
        gbk = self.write('gbk.html', '<html lang="zh-CN"><img src="a.png" alt="首页"><button>提交</button></html>', encoding='gbk')
        self.assertEqual([i['rule'] for i in M.scan_file(gbk)], [])
        gbk_bad = self.write('gbk2.html', '<html lang="zh-CN"><img src="a.png"><button>提交</button></html>', encoding='gbk')
        self.assertEqual([i['rule'] for i in M.scan_file(gbk_bad)], ['img-alt'])

    def test_clean_page_has_no_findings(self):
        page = ('<!doctype html><html lang="zh-CN"><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>登录</title></head>'
                '<body><h1>登录</h1><form><label for="u">账号</label><input id="u" type="text"><label for="p">密码</label><input id="p" type="password">'
                '<button type="submit">登录</button></form><a href="/help">查看登录帮助</a><img src="logo.png" alt="公司标志"></body></html>')
        self.assertEqual(self.rules('clean.html', page), [])


class EquivalenceTests(TempCase):
    SAMPLES = [
        '<html lang="zh-CN"><body><img src="a.png"><input type="text" id="q"><button>提交</button></body></html>',
        '<div a={b} c="d" e=\'f\' g=h {...rest}><span x={{y: {z: 1}}}>t</span></div>',
        '<label for="a">A</label> <label htmlFor="b">B</label> <label for=\'c\'>C</label> <label class="x">X</label>',
        'a < b and c > d <3 <a href="x">y</a> <1 not a tag <p/>',
        '<Foo.Bar baz="1" /><my-element data-x="1"></my-element><svg:rect/>',
    ]

    def test_iter_tags_matches_upstream_regex(self):
        for sample in self.SAMPLES:
            ours = [(m.start(), m.end(), m.group(1), m.group(2), m.group(3)) for m in M.iter_tags(sample)]
            theirs = [(m.start(), m.end(), m.group(1), m.group(2), m.group(3)) for m in UPSTREAM_TAG_RE.finditer(sample)]
            self.assertEqual(ours, theirs, sample)

    def test_label_for_matches_upstream_findall(self):
        for sample in self.SAMPLES:
            self.assertEqual(M.collect_label_for(sample), set(UPSTREAM_LABEL_FOR.findall(sample)), sample)

    def test_fixture_files_scan_same_with_upstream_tag_regex(self):
        for path in sorted((ASSET / 'tests' / 'fixtures' / 'manual').glob('*')):
            if path.suffix.lower() in M.EXTS:
                src = M.read_source(str(path))
                ours = [(m.start(), m.end()) for m in M.iter_tags(src)]
                theirs = [(m.start(), m.end()) for m in UPSTREAM_TAG_RE.finditer(src)]
                self.assertEqual(ours, theirs, path.name)


class ContrastTests(unittest.TestCase):
    def pair(self, fg, bg):
        result = call('contrast', {'pairs': [{'foreground': fg, 'background': bg}]})
        self.assertTrue(result['ok'], result)
        return result['pairs'][0], result

    def test_black_on_white(self):
        item, result = self.pair('#000000', '#ffffff')
        self.assertEqual(item['ratio'], 21.0)
        self.assertTrue(all(item[k] for k in ('aa_normal', 'aa_large', 'aaa_normal', 'aaa_large', 'ui_components')))
        self.assertIn('21.00:1', result['report_text'])
        self.assertTrue(result['all_aa_normal'])

    def test_same_color_is_one_to_one(self):
        item, _ = self.pair('#336699', '#336699')
        self.assertEqual(item['ratio'], 1.0)
        self.assertFalse(item['aa_large'])

    def test_known_gray_values(self):
        item, result = self.pair('#777777', '#ffffff')
        self.assertEqual(item['ratio'], 4.48)
        self.assertFalse(item['aa_normal'])
        self.assertTrue(item['aa_large'] and item['ui_components'])
        self.assertFalse(item['aaa_normal'])
        self.assertIn('AA 正文 未达标', result['report_text'])
        self.assertFalse(result['all_aa_normal'])
        ok, _ = self.pair('#767676', '#ffffff')
        self.assertEqual(ok['ratio'], 4.54)
        self.assertTrue(ok['aa_normal'])
        self.assertEqual(self.pair('#6b7280', '#ffffff')[0]['ratio'], 4.83)

    def test_threshold_boundaries(self):
        self.assertTrue(self.pair('#595959', '#ffffff')[0]['aa_normal'])
        self.assertFalse(self.pair('#5a5a5a', '#ffffff')[0]['aaa_normal'])
        self.assertTrue(self.pair('#595959', '#ffffff')[0]['aaa_normal'])  # 7.0:1

    def test_rounding_note_when_display_reaches_threshold_but_exact_does_not(self):
        item, result = self.pair('#667d60', '#ffffff')
        self.assertEqual(item['ratio'], 4.5)
        self.assertLess(item['ratio_exact'], 4.5)
        self.assertFalse(item['aa_normal'])
        self.assertTrue(any('精确值' in note for note in item['notes']))
        self.assertIn('AA 正文 未达标', result['report_text'])

    def test_color_formats(self):
        for fg in ('#000', '#000f', '#000000', '#000000ff', 'rgb(0, 0, 0)', 'rgb(0 0 0)', 'rgba(0,0,0,1)', 'rgba(0, 0, 0, 100%)', 'black', 'BLACK'):
            self.assertEqual(self.pair(fg, 'white')[0]['ratio'], 21.0, fg)

    def test_alpha_blend_and_background_alpha_note(self):
        item, _ = self.pair('rgba(0,0,0,0.5)', '#ffffff')
        self.assertAlmostEqual(item['ratio'], 3.98, places=2)
        self.assertTrue(any('透明度' in n for n in item['notes']))
        item, _ = self.pair('#000000', 'rgba(255,255,255,0.5)')
        self.assertEqual(item['ratio'], 21.0)
        self.assertTrue(any('背景色的透明度被忽略' in n for n in item['notes']))

    def test_invalid_colors(self):
        for bad in ('bogus', '#12', '#12345', '#xyz', 'rgb(0,0)', 'rgb(300,0,0)', 'rgba(0,0,0,1.5)', 'rgba(0,0,0,150%)', 'hsl(0,0%,0%)', 'rgb(1.2.3,0,0)'):
            result = call('contrast', {'pairs': [{'foreground': bad, 'background': '#ffffff'}]})
            self.assertFalse(result['ok'], bad)
            self.assertEqual(result['error']['code'], 'INVALID_COLOR', bad)
            self.assertTrue(any('一' <= ch <= '鿿' for ch in result['error']['message']), bad)

    def test_mixed_valid_and_invalid_pairs_keep_the_valid_result(self):
        result = call('contrast', {'pairs': [{'foreground': '#000', 'background': '#fff'}, {'foreground': 'nope', 'background': '#fff'}]})
        self.assertTrue(result['ok'])
        self.assertEqual(result['pairs'][0]['ratio'], 21.0)
        self.assertIn('无法识别的颜色：nope', result['pairs'][1]['error'])
        self.assertIn('无法识别的颜色：nope', result['report_text'])

    def test_chinese_report_text(self):
        _, result = self.pair('#777777', '#ffffff')
        self.assertIn('#777777 在 #ffffff 上：4.48:1', result['report_text'])
        self.assertIn('界面组件 达标', result['report_text'])


class ToolValidationTests(TempCase):
    def error_code(self, name, arguments):
        result = call(name, arguments)
        self.assertFalse(result['ok'], result)
        return result['error']['code']

    def test_scan_rejects_bad_arguments(self):
        good = self.write('ok.html', '<html lang="zh-CN"></html>')
        for bad in ({}, {'paths': []}, {'paths': 'a.html'}, {'paths': [1]}, {'paths': ['']}, {'paths': ['   ']}, {'paths': ['a\x00b']},
                    {'paths': ['x' * 1001]}, {'paths': ['a.html'] * 11}, {'paths': [good], 'extra': 1}, {'paths': [good], 'errors_only': 'yes'},
                    {'paths': [good], 'max_issues': 0}, {'paths': [good], 'max_issues': 501}, {'paths': [good], 'max_issues': True},
                    {'paths': [good], 'max_issues': 1.5}, None, [], 'x'):
            self.assertEqual(self.error_code('scan', bad), 'INVALID_ARGUMENTS', bad)

    def test_contrast_rejects_bad_arguments(self):
        pair = {'foreground': '#000', 'background': '#fff'}
        for bad in ({}, {'pairs': []}, {'pairs': 'x'}, {'pairs': [pair] * 51}, {'pairs': [{'foreground': '#000'}]},
                    {'pairs': [{'foreground': '#000', 'background': '#fff', 'x': 1}]}, {'pairs': [{'foreground': 1, 'background': '#fff'}]},
                    {'pairs': [{'foreground': '', 'background': '#fff'}]}, {'pairs': [{'foreground': 'a' * 65, 'background': '#fff'}]},
                    {'pairs': [pair], 'extra': True}, {'pairs': ['#000', '#fff']}, None):
            self.assertEqual(self.error_code('contrast', bad), 'INVALID_ARGUMENTS', bad)

    def test_scan_missing_and_unsupported(self):
        missing = str(self.dir / '不存在.html')
        result = call('scan', {'paths': [missing]})
        self.assertEqual(result['error']['code'], 'ALL_PATHS_FAILED')
        self.assertIn('不存在.html', result['error']['message'])
        text = self.write('notes.txt', 'hello')
        result = call('scan', {'paths': [text]})
        self.assertEqual(result['error']['code'], 'NO_FILES')
        self.assertIn('不支持这种文件类型', result['error']['skipped'][0]['reason'])
        good = self.write('ok.html', '<html><img src="a.png"></html>')
        result = call('scan', {'paths': [good, missing, text]})
        self.assertTrue(result['ok'])
        self.assertEqual(result['summary']['files_scanned'], 1)
        self.assertEqual(len(result['skipped']), 2)
        self.assertIn('没有扫描的路径', result['report_text'])
        self.assertTrue(result['scan_complete'])

    def test_empty_folder(self):
        folder = self.dir / 'empty'
        folder.mkdir()
        result = call('scan', {'paths': [str(folder)]})
        self.assertEqual(result['error']['code'], 'NO_FILES')
        self.assertIn('没有找到', result['error']['message'])

    def test_unknown_tool_arguments_do_not_reach_the_filesystem(self):
        marker = self.dir / 'created.txt'
        result = call('scan', {'paths': [str(self.dir)], 'json': str(marker)})
        self.assertEqual(result['error']['code'], 'INVALID_ARGUMENTS')
        self.assertFalse(marker.exists())

    def test_max_issues_and_errors_only(self):
        body = ''.join('<img src="%d.png">\n' % i for i in range(30)) + '<h1>a</h1><h3>b</h3>\n'
        path = self.write('many.html', '<html lang="zh-CN">\n' + body + '</html>')
        result = call('scan', {'paths': [path], 'max_issues': 5})
        self.assertTrue(result['ok'])
        self.assertEqual(len(result['issues']), 5)
        self.assertTrue(result['issues_truncated'])
        self.assertEqual(result['summary']['errors'], 30)
        self.assertEqual(result['summary']['warnings'], 1)
        self.assertEqual(result['summary']['by_rule'], {'img-alt': 30, 'heading-order': 1})
        self.assertIn('只列出前 5 条，共 31 条', result['report_text'])
        only = call('scan', {'paths': [path], 'errors_only': True, 'max_issues': 500})
        self.assertEqual(only['summary'], {'files_scanned': 1, 'errors': 30, 'warnings': 0, 'by_rule': {'img-alt': 30}})
        self.assertFalse(only['issues_truncated'])

    def test_report_text_is_chinese(self):
        path = self.write('a.html', '<html><img src="a.png"></html>')
        result = call('scan', {'paths': [path]})
        self.assertIn('错误 [img-alt] WCAG 1.1.1', result['report_text'])
        self.assertIn('共扫描 1 个文件：2 个错误，0 个警告', result['report_text'])
        self.assertIn('简体中文', result['message'])
        self.assertIn('不等于符合 WCAG', result['message'])

    def test_clean_file_reports_zero(self):
        path = self.write('ok.html', '<html lang="zh-CN"><body><button>确定</button></body></html>')
        result = call('scan', {'paths': [path]})
        self.assertTrue(result['ok'])
        self.assertEqual(result['summary'], {'files_scanned': 1, 'errors': 0, 'warnings': 0, 'by_rule': {}})
        self.assertIn('共扫描 1 个文件：0 个错误，0 个警告', result['report_text'])


class FolderWalkTests(TempCase):
    def test_walk_skips_dirs_and_non_ui_files_and_is_case_insensitive(self):
        bad = '<img src="a.png">'
        self.write('src/a.html', bad)
        self.write('src/B.HTML', bad)
        self.write('src/c.TSX', '<img src="a.png" />')
        self.write('src/d.js', bad)
        self.write('src/e.css', bad)
        self.write('node_modules/x/f.html', bad)
        self.write('dist/g.html', bad)
        self.write('build/h.html', bad)
        self.write('.hidden/i.html', bad)
        self.write('src/deep/j.vue', '<template><img src="a.png"></template>')
        result = call('scan', {'paths': [str(self.dir)], 'max_issues': 500})
        files = sorted(Path(i['file']).relative_to(self.dir).as_posix() for i in result['issues'])
        self.assertEqual(files, ['src/B.HTML', 'src/a.html', 'src/c.TSX', 'src/deep/j.vue'])
        self.assertEqual(result['summary']['files_scanned'], 4)

    def test_symlinks_are_skipped(self):
        target = self.write('real/a.html', '<img src="a.png">')
        outside = self.dir / 'folder'
        outside.mkdir()
        link = outside / 'link.html'
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest('symbolic links cannot be created here')
        result = call('scan', {'paths': [str(outside)]})
        self.assertEqual(result['error']['code'], 'NO_FILES')
        direct = call('scan', {'paths': [str(link)]})
        self.assertFalse(direct['ok'])
        self.assertIn('符号链接', direct['error']['skipped'][0]['reason'])

    def test_symlink_logic_with_patched_islink(self):
        real = self.write('src/a.html', '<img src="a.png">')
        other = self.write('src/b.html', '<img src="b.png">')
        original = os.path.islink
        os.path.islink = lambda path: str(path) == other
        try:
            result = call('scan', {'paths': [str(self.dir)], 'max_issues': 500})
            direct = call('scan', {'paths': [other]})
        finally:
            os.path.islink = original
        self.assertEqual([i['file'] for i in result['issues']], [real])
        self.assertFalse(direct['ok'])
        self.assertIn('符号链接', direct['error']['skipped'][0]['reason'])

    def test_scan_is_read_only(self):
        self.write('src/a.html', '<img src="a.png">')
        self.write('src/b.jsx', '<button></button>')
        def snapshot():
            return {p.relative_to(self.dir).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in self.dir.rglob('*') if p.is_file()}
        before = snapshot()
        call('scan', {'paths': [str(self.dir)]})
        call('contrast', {'pairs': [{'foreground': '#000', 'background': '#fff'}]})
        self.assertEqual(snapshot(), before)


class LimitTests(TempCase):
    def test_file_size_cap(self):
        big = self.dir / 'big.html'
        big.write_bytes(b'<html lang="zh-CN">' + b'a' * (M.MAX_FILE_BYTES) + b'</html>')
        small = self.write('small.html', '<img src="a.png">')
        result = call('scan', {'paths': [str(big), small]})
        self.assertTrue(result['ok'])
        self.assertEqual(result['summary']['files_scanned'], 1)
        self.assertIn('超过 1.0 MB 的上限', result['skipped'][0]['reason'])
        alone = call('scan', {'paths': [str(big)]})
        self.assertEqual(alone['error']['code'], 'NO_FILES_SCANNED')
        edge = self.dir / 'edge.html'
        edge.write_bytes(b'<html lang="zh-CN">' + b' ' * (M.MAX_FILE_BYTES - 19 - 7) + b'</html>')
        self.assertEqual(edge.stat().st_size, M.MAX_FILE_BYTES)
        self.assertTrue(call('scan', {'paths': [str(edge)]})['ok'])

    def test_file_count_cap_reports_incomplete(self):
        for i in range(5):
            self.write('f%d.html' % i, '<img src="a.png">')
        old = M.MAX_FILES
        M.MAX_FILES = 3
        try:
            result = call('scan', {'paths': [str(self.dir)]})
        finally:
            M.MAX_FILES = old
        self.assertTrue(result['ok'])
        self.assertFalse(result['scan_complete'])
        self.assertEqual(result['summary']['files_scanned'], 3)
        self.assertIn('扫描没有跑完', result['report_text'])
        self.assertIn('2 个文件', result['report_text'])

    def test_pathological_markup_times_out_per_file_and_other_files_still_scan(self):
        evil = self.write('evil.html', '<div a=b ' * 60000)
        good = self.write('good.html', '<img src="a.png">')
        old = M.FILE_BUDGET_SECONDS
        M.FILE_BUDGET_SECONDS = 1.0
        started = time.monotonic()
        try:
            result = call('scan', {'paths': [evil, good]})
        finally:
            M.FILE_BUDGET_SECONDS = old
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 20)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['summary']['files_scanned'], 1)
        self.assertFalse(result['scan_complete'])
        self.assertTrue(any('时间预算' in s['reason'] and s['path'] == evil for s in result['skipped']))
        self.assertEqual([i['rule'] for i in result['issues']], ['img-alt'])

    def test_normal_large_file_is_fast(self):
        row = '<div class="row"><img src="a.png" alt="图"><label for="i%d">名</label><input id="i%d"><a href="/x">查看详情页面</a></div>\n'
        text = '<html lang="zh-CN"><body>\n' + ''.join(row % (i, i) for i in range(5000)) + '</body></html>'
        path = self.write('large.html', text)
        self.assertLess(os.path.getsize(path), M.MAX_FILE_BYTES)
        started = time.monotonic()
        result = call('scan', {'paths': [path]})
        self.assertTrue(result['ok'])
        self.assertEqual(result['summary']['errors'], 0)
        self.assertLess(time.monotonic() - started, 10)

    def test_unclosed_button_and_link_use_a_bounded_window(self):
        text = '<html lang="zh-CN">' + '<button class="x">' * 4000 + '<a href="/y">' * 4000 + '</html>'
        path = self.write('unclosed.html', text)
        started = time.monotonic()
        result = call('scan', {'paths': [path]})
        self.assertLess(time.monotonic() - started, 30)
        self.assertTrue(result['ok'] or result['error']['code'] == 'NO_FILES_SCANNED')


class PackageConsistencyTests(unittest.TestCase):
    def test_manifest_matches_payload(self):
        manifest = json.loads((PAYLOAD / 'manifest.json').read_text(encoding='utf-8'))
        asset = json.loads((ASSET / 'asset.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['package_type'], 'plugin')
        self.assertEqual(manifest['id'], asset['name'])
        self.assertEqual(manifest['version'], asset['version'])
        self.assertEqual(manifest['name'], asset['display_name'])
        self.assertEqual(manifest['description'], asset['description'])
        self.assertTrue(re.fullmatch(r'[a-z][a-z0-9]*(-[a-z0-9]+)*', manifest['id']))
        for skill in manifest['skills']:
            self.assertTrue((PAYLOAD / skill['dir'] / 'SKILL.md').is_file())
        classes = {(t['file'], t['class']) for t in manifest['tools']}
        self.assertEqual(classes, {('tools/a11y_enforcer.py', 'A11yScanTool'), ('tools/a11y_enforcer.py', 'A11yContrastTool')})
        for file, cls in classes:
            self.assertTrue((PAYLOAD / file).is_file())
            self.assertTrue(hasattr(M, cls))
        for key in ('persona', 'agent_card', 'model', 'subagents', 'memories', 'rubrics'):
            self.assertNotIn(key, manifest)
        for tag in manifest['tags']:
            self.assertTrue(tag['zh'] and tag['en'])

    def test_skill_front_matter_and_chinese(self):
        text = (PAYLOAD / 'skills' / 'web-accessibility-check' / 'SKILL.md').read_text(encoding='utf-8')
        match = re.match(r'---\nname: ([a-z0-9-]+)\ndescription: (.+)\nversion: (\S+)\n---\n', text)
        self.assertTrue(match)
        self.assertEqual(match.group(1), 'web-accessibility-check')
        self.assertIn('a11y_scan', match.group(2))
        self.assertIn('a11y_contrast', match.group(2))
        self.assertIn('references/rules.md', text)
        rules_doc = (PAYLOAD / 'skills' / 'web-accessibility-check' / 'references' / 'rules.md').read_text(encoding='utf-8')
        found = set(re.findall(r'^\| ([a-z][a-z-]+) \|', rules_doc, re.M))
        implemented = set(re.findall(r'add\(pos, "([a-z-]+)"', Path(PAYLOAD / 'tools' / 'a11y_enforcer.py').read_text(encoding='utf-8')))
        self.assertEqual(found, implemented)
        self.assertEqual(len(found), 20)

    def test_license_is_byte_exact_and_recorded(self):
        license_path = PAYLOAD / 'licenses' / 'a11y-enforcer' / 'LICENSE'
        data = license_path.read_bytes()
        self.assertEqual(len(data), 1073)
        self.assertNotIn(b'\r', data)
        digest = hashlib.sha256(data).hexdigest()
        self.assertEqual(digest, '5f434c88921e448707dc3b7983a41364721fdbec7468735c26dba2200f183d04')
        provenance = json.loads((ASSET / 'provenance.json').read_text(encoding='utf-8'))
        evidence = provenance['sources'][0]['license_evidence'][0]
        self.assertEqual(evidence, {'path': 'licenses/a11y-enforcer/LICENSE', 'sha256': digest})
        self.assertIn(b'Copyright (c) 2026 Stefan Petrovici', data)
        notices = (PAYLOAD / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
        for needle in (digest, '0b19c0dd919c2b5e0b992fb1610ef2ca427a357f', 'Stefan Petrovici', 'MIT'):
            self.assertIn(needle, notices)

    def test_no_network_process_or_dynamic_execution_in_payload(self):
        source = (PAYLOAD / 'tools' / 'a11y_enforcer.py').read_text(encoding='utf-8')
        for pattern in (r'\bimport\s+(socket|subprocess|urllib|http|requests|ftplib|smtplib|ctypes|shutil|pickle|marshal)\b', r'\beval\s*\(', r'\bexec\s*\(',
                        r'\bos\.(system|popen|remove|unlink|rename|replace|rmdir|makedirs|mkdir)\b', r'\bopen\([^)]*[\'"][wax+]'):
            self.assertIsNone(re.search(pattern, source), pattern)
        self.assertEqual(re.findall(r'open\(([^)]*)\)', source), ['path, "rb"'])

    def test_no_cache_or_log_files_in_payload(self):
        for path in PAYLOAD.rglob('*'):
            self.assertNotIn('__pycache__', path.parts)
            self.assertNotEqual(path.suffix, '.pyc')
            self.assertNotEqual(path.name, 'logs')


class ToolClassTests(unittest.TestCase):
    def test_tool_cards_and_invoke(self):
        scan, contrast = M.A11yScanTool(), M.A11yContrastTool()
        self.assertEqual((scan.card.id, scan.card.name), ('a11y_scan', 'a11y_scan'))
        self.assertEqual((contrast.card.id, contrast.card.name), ('a11y_contrast', 'a11y_contrast'))
        for tool in (scan, contrast):
            self.assertTrue(any('一' <= ch <= '鿿' for ch in tool.card.description))
        self.assertEqual(scan.card.input_params['required'], ['paths'])
        self.assertEqual(contrast.card.input_params['required'], ['pairs'])
        result = asyncio.run(contrast.invoke({'pairs': [{'foreground': '#000', 'background': '#fff'}]}))
        self.assertTrue(result['ok'])
        rejected = asyncio.run(scan.invoke({}))
        self.assertEqual(rejected['error']['code'], 'INVALID_ARGUMENTS')

        async def streamed():
            return [item async for item in contrast.stream({'pairs': [{'foreground': '#000', 'background': '#fff'}]})]
        self.assertEqual(len(asyncio.run(streamed())), 1)

    def test_concurrent_calls(self):
        async def run():
            tasks = [M.call_tool('contrast', {'pairs': [{'foreground': '#%02x%02x%02x' % (i, i, i), 'background': '#ffffff'}]}) for i in range(0, 200, 10)]
            return await asyncio.gather(*tasks)
        results = asyncio.run(run())
        self.assertTrue(all(r['ok'] for r in results))
        self.assertEqual([r['pairs'][0]['foreground'] for r in results], ['#%02x%02x%02x' % (i, i, i) for i in range(0, 200, 10)])

    def test_internal_error_is_reported_without_a_traceback(self):
        original = M.RUNNERS['contrast']
        def boom(values):
            raise RuntimeError('secret internal detail')
        M.RUNNERS['contrast'] = boom
        try:
            result = call('contrast', {'pairs': [{'foreground': '#000', 'background': '#fff'}]})
        finally:
            M.RUNNERS['contrast'] = original
        self.assertEqual(result['error']['code'], 'INTERNAL_ERROR')
        self.assertNotIn('secret', json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
