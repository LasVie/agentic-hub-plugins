"""生成自包含中文交互页面；不执行用户代码，不联网，不覆盖已有文件。"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENES = {
    'mascot': ('手绘互动伙伴', '移动鼠标看它的眼睛跟随；悬停按钮、点击欢呼，或按 Tab 和回车操作。'),
    'form': ('手绘表单伙伴', '用虚构信息试填表单：输入演示密码时遮眼，显示密码时偷看，完成时欢呼。'),
    'scroll': ('滚动逐笔绘画', '向下滚动，观察结构、线稿、水彩与细节逐步出现；向上滚动可以回看。'),
}
STYLE = '''
:root{color-scheme:light;--paper:#fbf6ea;--ink:#3d3437;--muted:#75676b;--rose:#c9566b;--line:#e0d3bc}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.8 "Microsoft YaHei",system-ui,sans-serif}nav,main,footer{max-width:1180px;margin:auto;padding:24px 36px}nav{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);font-size:14px}nav strong{letter-spacing:.12em}.hero{display:grid;grid-template-columns:1fr 1fr;gap:42px;align-items:center;min-height:72vh}h1{font-size:clamp(32px,4vw,56px);line-height:1.3;letter-spacing:-.03em;margin:18px 0}h2{font-size:30px;line-height:1.5}.eyebrow{color:var(--rose);font-size:13px;letter-spacing:.18em}.intro{color:var(--muted);white-space:pre-wrap;overflow-wrap:anywhere}button{font:inherit;cursor:pointer;padding:12px 22px;border:2px solid var(--ink);border-radius:30px;background:transparent;color:var(--ink);margin:8px 12px 8px 0}button.primary{background:var(--ink);color:var(--paper);box-shadow:4px 4px 0 #efb6bc}button:focus-visible,input:focus-visible{outline:3px solid #c9566b;outline-offset:4px}button:disabled{opacity:.45;cursor:wait}#art{width:100%;position:relative}#status{font-size:14px;color:var(--muted);min-height:2em}label{display:block;margin:12px 0}input:not([type=checkbox]){display:block;width:100%;max-width:390px;padding:10px 14px;font:inherit;border:1px solid var(--line);border-radius:8px;background:#fffdf6}footer{font-size:12px;color:var(--muted);border-top:1px solid var(--line)}details{margin-top:14px}pre{white-space:pre-wrap;word-break:break-word;font-size:11px}#track{display:grid;grid-template-columns:1fr 1fr;gap:42px}.steps article{min-height:78vh;display:flex;flex-direction:column;justify-content:center}.sticky{position:sticky;top:7vh;height:86vh;display:flex;align-items:center}.scroll-intro{padding:5vh 0 7vh;max-width:760px}.scroll-intro h1{margin-bottom:20px}.bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap}@media(max-width:760px){nav,main,footer{padding:20px}.hero{grid-template-columns:1fr;gap:8px}.hero .stage{order:-1;max-width:400px;margin:auto}#track{grid-template-columns:1fr;gap:0}.sticky{order:-1;top:0;height:auto;background:var(--paper);z-index:2}.sticky #art{max-width:42vh;margin:auto}.steps article{min-height:65vh}h1{font-size:34px}}
'''

def text(value, default, limit):
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'文字必须非空且不超过 {limit} 个字符。')
    return value.strip()

def render_page(scene, title=None, description=None):
    if not isinstance(scene,str) or scene not in SCENES:
        raise ValueError('场景必须为 mascot、form 或 scroll。')
    title = html.escape(text(title, SCENES[scene][0], 80))
    desc = html.escape(text(description, SCENES[scene][1], 600))
    stage = '<div id="art"></div>'
    if scene == 'scroll':
        steps = ''.join(f'<article><span class="eyebrow">0{i+1} / 绘制过程</span><h2>{h}</h2><p class="intro">{p}</p></article>' for i,(h,p) in enumerate([
            ('先找到形状','用简单结构确定头部、身体和姿态，给画面一个起点。'),
            ('让线条生长','铅笔沿着轮廓逐步走过，机器人开始有了表情。'),
            ('水彩慢慢铺开','颜色由浅入深，让纸张与笔触一起留下痕迹。'),
            ('留下最后一笔','线条和颜色汇合成完整插画。向上滚动，还能重新看一遍。')]))
        body = f'<header class="scroll-intro"><span class="eyebrow">一笔一画 · 由你推进</span><h1>{title}</h1><p class="intro">{desc}</p><p>向下滚动 ↓</p></header><section id="track"><div class="steps">{steps}</div><div class="sticky">{stage}</div></section>'
    else:
        controls = '<button class="primary" data-anidoodle="start">一起欢呼</button><button data-anidoodle="tour">向我挥手</button>'
        if scene == 'form':
            controls = '<form novalidate autocomplete="off"><label>演示称呼<input id="name" data-anidoodle="name" maxlength="40" placeholder="例如：小明"></label><label>演示密码<input id="password" type="password" data-anidoodle="password" maxlength="40" autocomplete="new-password" placeholder="请使用虚构内容，至少 4 个字符"></label><label><input id="reveal" type="checkbox" data-anidoodle="reveal"> 显示演示密码</label><button class="primary" type="submit" data-anidoodle="submit">完成演示</button></form>'
        body = f'<section class="hero"><div><span class="eyebrow">铅笔与水彩 · 会回应的插画</span><h1>{title}</h1><p class="intro">{desc}</p>{controls}</div><div class="stage">{stage}</div></section>'
    notices = '\n\n'.join((ROOT/'licenses/anidoodle'/n).read_text(encoding='utf-8') for n in ['LICENSE','NOTICE'])
    js = (ROOT/'engine/art.js').read_text(encoding='utf-8').replace('</script','<\\/script')
    return f'<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data: blob:; connect-src \'none\'; form-action \'none\'; base-uri \'none\'"><title>{title}</title><style>{STYLE}</style></head><body data-scene="{scene}"><nav><strong>手绘交互工坊</strong><span>离线作品 · 1.0.0</span></nav><main>{body}<div class="bar"><button id="save-png" disabled>保存当前画面 PNG</button><span id="status" role="status">正在逐笔绘制，请稍候……</span></div></main><footer>基于 anidoodle · Alex Greenshpun 的绘图引擎；中文适配：Gan Mingrui。<details><summary>开源许可与来源</summary><pre>{html.escape(notices)}</pre></details></footer><script>{js}</script></body></html>'

def execute(inputs):
    try:
        if not isinstance(inputs, dict):
            raise ValueError('输入必须为 JSON 对象。')
        action = inputs.get('action')
        if action == 'list':
            return {'ok': True, 'scenes': [{'id': k,'name': v[0],'description':v[1]} for k,v in SCENES.items()], 'scope': '首版是三个铅笔水彩场景及其可编辑源码，不包含全部上游画风或任意新角色的自动绘制。'}
        if action not in ('create','source'):
            raise ValueError('action 必须为 list、create 或 source。')
        raw = inputs.get('workspace')
        if not isinstance(raw,str) or not Path(raw).is_absolute():
            raise ValueError('workspace 必须为用户工作区的绝对路径。')
        workspace = Path(raw).resolve(strict=True)
        if not workspace.is_dir():
            raise ValueError('工作区必须为已有目录。')
        name = inputs.get('name','hand-drawn-art')
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,49}',name) or name.upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
            raise ValueError('文件名须以小写字母开头，只含小写字母、数字和连字符，最长 50 字符，不能使用系统保留名。')
        target = workspace/(name+'.html' if action=='create' else name+'-source')
        if target.exists() or target.is_symlink():
            raise ValueError('目标已存在，请换一个文件名；工具不会覆盖现有作品。')
        if action == 'create':
            page=render_page(inputs.get('scene','mascot'),inputs.get('title'),inputs.get('description'))
            with target.open('x',encoding='utf-8') as f:
                f.write(page)
            return {'ok':True,'path':str(target),'message':'作品已生成。用 Chrome/Edge 打开 HTML，可离线互动和保存 PNG；宿主对话中能否直接预览取决于宿主。'}
        target.mkdir()
        for n in ['engine','licenses','runtime.py','README.md','THIRD_PARTY_NOTICES.md']:
            p=ROOT/n
            if p.is_dir(): shutil.copytree(p,target/n,ignore=shutil.ignore_patterns('node_modules','__pycache__','*.pyc'))
            else: shutil.copyfile(p,target/n)
        return {'ok':True,'path':str(target),'message':'可编辑源码已导出。修改后按 README 的源码流程编译，再生成 HTML。工程不含 node_modules。'}
    except (ValueError,OSError) as e:
        return {'ok':False,'message':str(e) if isinstance(e,ValueError) else '无法读写目标，请检查目录权限、空间和插件完整性。'}

if __name__ == '__main__':
    try:
        answer=execute(json.load(sys.stdin))
    except (ValueError,UnicodeError):
        answer={'ok':False,'message':'输入不是有效 UTF-8 JSON。'}
    print(json.dumps(answer,ensure_ascii=False))
    sys.exit(0 if answer['ok'] else 2)
