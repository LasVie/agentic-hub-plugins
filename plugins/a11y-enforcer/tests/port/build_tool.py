"""Generate payload tools/a11y_enforcer.py from the pinned upstream blobs plus our own header and wrapper.

Usage: python -B -I build_tool.py --upstream <dir with a11y_scan.py and contrast.py blobs> --out <tools/a11y_enforcer.py>

Every change to the upstream code is an exact-match replacement that must occur exactly once; the script fails on any
mismatch, so the modification summary in SOURCE_REVIEW.md / THIRD_PARTY_NOTICES.md stays checkable.
The upstream blobs are the Git blobs at commit 0b19c0dd919c2b5e0b992fb1610ef2ca427a357f (LF line endings).
"""
import argparse
import difflib
import hashlib
from pathlib import Path

PINNED = {
    'a11y_scan.py': '610e7ac63235bd1577d1f62d7812bea77e25872530fba9ad543cda97e5b4f87f',
    'contrast.py': '4e8a80bef217860874b87ed696b776c82166eea8537bd9fe2e89a280e52b98f0',
}

SCAN = [
    # --- bounded matching and time budget (our change) ---
    (r'''    close = re.compile(r"<(/?)%s\b[^>]*?(/?)>" % re.escape(tag), re.I)
    depth = 1
    for m in close.finditer(src, start):''',
     r'''    close = re.compile(r"<(/?)%s\b[^>]*?(/?)>" % re.escape(tag), re.I)
    depth = 1
    for m in close.finditer(src, start, min(len(src), start + MAX_INNER_CHARS)):'''),
    ('def scan_file(path):\n    src = open(path, encoding="utf-8", errors="replace").read()\n    is_html = path.endswith((".html", ".htm"))',
     'def scan_file(path, deadline=None):\n    src = read_source(path)\n    is_html = path.lower().endswith((".html", ".htm"))'),
    ('    label_for = set(re.findall(r"<label\\b[^>]*\\b(?:for|htmlFor)\\s*=\\s*[\\"\'{]\\s*[\\"\']?([\\w:-]+)", src))\n',
     '    label_for = collect_label_for(src, deadline)\n'),
    ('    for m in TAG_RE.finditer(src):\n', '    for m in iter_tags(src, deadline):\n'),
    ('if path.endswith((".vue", ".svelte", ".astro", ".html", ".htm")) else []:',
     'if path.lower().endswith((".vue", ".svelte", ".astro", ".html", ".htm")) else []:'),
    # --- folder walk: case-insensitive extensions, skip symbolic links (our change) ---
    ('                if n.endswith(EXTS):\n                    yield os.path.join(dirpath, n)',
     '                if n.lower().endswith(EXTS) and not os.path.islink(os.path.join(dirpath, n)):\n                    yield os.path.join(dirpath, n)'),
    # --- Chinese messages (rule ids, WCAG numbers and levels keep the upstream spelling) ---
    ('"<html> has no lang attribute"', '"<html> 没有 lang 属性"'),
    (r'f"<{tag}> has no alt text (use alt=\"\" for decorative images)"', r'f"<{tag}> 没有 alt 文本（装饰性图片请写 alt=\"\"）"'),
    ('"<input type=image> has no alt"', '"<input type=image> 没有 alt"'),
    ('f"<input type={typ}> has no label, aria-label or aria-labelledby"', 'f"<input type={typ}> 没有关联的 label，也没有 aria-label 或 aria-labelledby"'),
    ('f"<{t}> has no label, aria-label or aria-labelledby"', 'f"<{t}> 没有关联的 label，也没有 aria-label 或 aria-labelledby"'),
    ('"<button> has no text or aria-label (icon-only button?)"', '"<button> 没有文字也没有 aria-label（是不是只有图标的按钮？）"'),
    ('"<button/> has no text or aria-label"', '"<button/> 没有文字也没有 aria-label"'),
    ('"<a> has no text or aria-label"', '"<a> 没有文字也没有 aria-label"'),
    ('"link text does not describe the target"', '"链接文字没有说明要去哪里或做什么"'),
    ('"<a> without href used as a button; use <button>"', '"没有 href 的 <a> 被当成按钮用，请改用 <button>"'),
    ('f"clickable <{t}> has no role; use <button> or add role and tabindex"', 'f"可点击的 <{t}> 没有 role；请改用 <button>，或补上 role 和 tabindex"'),
    ('f"clickable <{t}> cannot be reached with the keyboard (no tabindex)"', 'f"可点击的 <{t}> 用键盘到不了（没有 tabindex）"'),
    ('f"clickable <{t}> has no keyboard handler"', 'f"可点击的 <{t}> 没有键盘事件处理"'),
    ('f"<{t}> autoplays with sound"', 'f"<{t}> 自动播放且带声音"'),
    ('"<video> has no <track> for captions"', '"<video> 没有提供字幕的 <track>"'),
    ('"<iframe> has no title"', '"<iframe> 没有 title"'),
    ('"viewport meta blocks zoom"', '"viewport 设置禁止了缩放"'),
    ('f"tabindex={num} changes the natural focus order"', 'f"tabindex={num} 会打乱默认的焦点顺序"'),
    ('"accesskey can clash with screen reader shortcuts"', '"accesskey 可能和读屏软件的快捷键冲突"'),
    ('''f"role={a.get('role')} on <{t}> without tabindex"''', '''f"<{t}> 上有 role={a.get('role')} 但没有 tabindex"'''),
    ('"inline style removes the focus outline"', '"行内样式去掉了焦点轮廓"'),
    ('f"heading jumps from h{prev} to h{level}"', 'f"标题从 h{prev} 直接跳到 h{level}"'),
    ('"CSS removes the focus outline and no :focus style was found"', '"CSS 去掉了焦点轮廓，而且没有找到 :focus 样式"'),
    # --- Chinese vague link texts are also reported (additive) ---
    ('''re.fullmatch(r"\\s*(click here|here|read more|more|link)\\s*", re.sub(r"<[^>]*>", "", body), re.I)''',
     '''re.fullmatch(r"\\s*(click here|here|read more|more|link|点击这里|点这里|这里|了解更多|查看更多|更多|详情|点击查看|链接)\\s*", re.sub(r"<[^>]*>", "", body), re.I)'''),
]

CONTRAST = [
    ('def parse(c):', 'def parse_color(c):'),
    ('    (frgb, fa), (brgb, _) = parse(fg), parse(bg)', '    (frgb, fa), (brgb, _) = parse_color(fg), parse_color(bg)'),
    ('''        alpha = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        return rgb, alpha
    raise ValueError(f"Unrecognised color: {c}")''',
     '''        alpha = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        if any(v > 255 for v in rgb) or not 0 <= alpha <= 1:
            raise ValueError(f"颜色数值超出范围：{c}")
        return rgb, alpha
    raise ValueError(f"无法识别的颜色：{c}")'''),
    ('''    def ok(x):
        return "pass" if r >= x else "FAIL"
    return (f"AA normal text {ok(4.5)}, AA large text {ok(3)}, "
            f"AAA normal {ok(7)}, AAA large {ok(4.5)}, UI components {ok(3)}")''',
     '''    def ok(x):
        return "达标" if r >= x else "未达标"
    return (f"AA 正文 {ok(4.5)}，AA 大字 {ok(3)}，"
            f"AAA 正文 {ok(7)}，AAA 大字 {ok(4.5)}，界面组件 {ok(3)}")'''),
]


def apply(text, replacements, label):
    for index, (old, new) in enumerate(replacements, 1):
        count = text.count(old)
        if count != 1:
            raise SystemExit('%s replacement %d matched %d times: %r' % (label, index, count, old[:80]))
        text = text.replace(old, new)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--stats', action='store_true')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    raw = {}
    for name, digest in PINNED.items():
        data = (args.upstream / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit('Upstream blob %s does not match the pinned hash' % name)
        raw[name] = data.decode('utf-8')
    scan = raw['a11y_scan.py']
    scan_body = scan[scan.index('EXTS = '):scan.index('def main():')].rstrip() + '\n'
    contrast = raw['contrast.py']
    contrast_body = contrast[contrast.index('NAMES = {'):contrast.index('def main():')].rstrip() + '\n'
    scan_new = apply(scan_body, SCAN, 'scan')
    contrast_new = apply(contrast_body, CONTRAST, 'contrast')
    header = (here / 'header.py').read_text(encoding='utf-8')
    tail = (here / 'wrapper_tail.py').read_text(encoding='utf-8')
    out = header + '\n' + scan_new + '\n\n' + contrast_new + '\n\n# ==== 以下为本团队编写的原生工具封装 ====\n' + tail
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out, encoding='utf-8', newline='\n')
    if args.stats:
        old_lines = (scan_body + contrast_body).splitlines()
        new_lines = (scan_new + contrast_new).splitlines()
        same = sum(1 for line in old_lines if line in set(new_lines))
        sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
        kept = sum(block.size for block in sm.get_matching_blocks())
        print('upstream lines used: %d, kept verbatim: %d (%.1f%%), line-set overlap: %d' % (len(old_lines), kept, 100.0 * kept / len(old_lines), same))
    print('wrote %s (%d bytes)' % (args.out, len(out.encode('utf-8'))))


if __name__ == '__main__':
    main()
