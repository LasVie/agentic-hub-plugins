"""网页无障碍检查：两个只读原生工具 a11y_scan（静态扫描）和 a11y_contrast（WCAG 对比度）。

本文件中“移植自上游”一段（扫描规则和对比度算法）来自 a11y-enforcer：
  https://github.com/petrovicistefan/claude-code-plugins/tree/0b19c0dd919c2b5e0b992fb1610ef2ca427a357f/a11y-enforcer
  skills/a11y-enforcer/scripts/a11y_scan.py 与 contrast.py
  MIT License, Copyright (c) 2026 Stefan Petrovici
完整许可文本见 licenses/a11y-enforcer/LICENSE，来源与修改摘要见 THIRD_PARTY_NOTICES.md。
本团队的修改：中文输出和中文识别、有界匹配与时间上限（防止畸形输入拖死）、去掉命令行入口和写文件选项、
输入范围检查；文件末尾的两个原生工具、输入校验和错误处理为本团队编写。

只读：只读取用户指定的网页界面代码文件，不改文件、不联网、不保存内容。
"""
from __future__ import annotations

import os
import re
import time

MAX_FILE_BYTES = 1024 * 1024        # 单个文件上限 1 MiB，超过的跳过并说明
MAX_TAG_CHARS = 8000                # 一个标签（含属性）最长匹配 8000 字符，防止未闭合标签造成二次方回溯
MAX_INNER_CHARS = 20000             # 查找按钮/链接结束标签时最多向后看 20000 字符
MAX_LABEL_CHARS = 2000              # 一个 <label> 标签最长匹配 2000 字符
SCAN_BUDGET_SECONDS = 60.0          # 一次调用的总时间预算
FILE_BUDGET_SECONDS = 10.0          # 单个文件的时间预算


class ScanTimeout(Exception):
    """扫描一个文件超过了时间预算。"""


class FileTooLarge(Exception):
    """文件超过大小上限。"""


def read_source(path):
    """读取一个文件并按上游的文本模式规整换行（\\r\\n、\\r 都当作 \\n）。"""
    size = os.path.getsize(path)
    if size > MAX_FILE_BYTES:
        raise FileTooLarge(size)
    with open(path, "rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise FileTooLarge(len(data))
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def _check_deadline(deadline):
    if deadline is not None and time.monotonic() > deadline:
        raise ScanTimeout()


def iter_tags(src, deadline=None):
    """与 TAG_RE.finditer(src) 结果相同（标签不超过 MAX_TAG_CHARS 时），但每次匹配都限定在一个窗口内，
    并定期检查时间预算；上游的整段匹配遇到大量未闭合的标签时耗时随长度二次方增长。"""
    pos = 0
    size = len(src)
    attempts = 0
    while True:
        start_match = _TAG_START.search(src, pos)
        if start_match is None:
            return
        start = start_match.start()
        attempts += 1
        if attempts % 64 == 0:
            _check_deadline(deadline)
        match = TAG_RE.match(src, start, min(size, start + MAX_TAG_CHARS))
        if match:
            yield match
            pos = match.end()
        else:
            pos = start + 1


def collect_label_for(src, deadline=None):
    """与上游 re.findall(<label ... for=...>) 得到的集合相同，但每个 <label 的匹配限定在窗口内。"""
    found = set()
    size = len(src)
    attempts = 0
    for start_match in _LABEL_START.finditer(src):
        attempts += 1
        if attempts % 64 == 0:
            _check_deadline(deadline)
        match = _LABEL_FOR.match(src, start_match.start(), min(size, start_match.start() + MAX_LABEL_CHARS))
        if match:
            found.add(match.group(1))
    return found


_TAG_START = re.compile(r"<[A-Za-z]")
_LABEL_START = re.compile(r"<label\b")
_LABEL_FOR = re.compile(r"<label\b[^>]*\b(?:for|htmlFor)\s*=\s*[\"'{]\s*[\"']?([\w:-]+)")


# ==== 以下为移植自上游的规则代码（a11y_scan.py 和 contrast.py，改动见 THIRD_PARTY_NOTICES.md） ====

EXTS = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", ".svelte-kit", "vendor"}

TAG_RE = re.compile(r"<([A-Za-z][\w.-]*)((?:\s+(?:\{[^}]*\}|[^\s>=/]+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\}|[^\s>]+))?))*)\s*(/?)>", re.S)
ATTR_RE = re.compile(r"([^\s=/{}]+)(?:\s*=\s*(\"[^\"]*\"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\}|[^\s>]+))?")


def attrs_of(raw):
    out = {}
    for m in ATTR_RE.finditer(raw or ""):
        name = m.group(1)
        val = m.group(2)
        if val and val[0] in "\"'":
            val = val[1:-1]
        out[name.lower()] = val if val is not None else True
    return out


def has_any(a, *names):
    return any(n in a for n in names)


def has_spread(raw):
    return "{..." in (raw or "")


def inner_text(src, start, tag):
    """Text between an opening tag ending at start and its closing tag (same name, no nesting check beyond depth)."""
    close = re.compile(r"<(/?)%s\b[^>]*?(/?)>" % re.escape(tag), re.I)
    depth = 1
    for m in close.finditer(src, start, min(len(src), start + MAX_INNER_CHARS)):
        if m.group(1):
            depth -= 1
            if depth == 0:
                return src[start:m.start()]
        elif not m.group(2):
            depth += 1
    return src[start:start + 400]


def visible_text(fragment):
    if re.search(r"<(img|svg)\b[^>]*\b(alt|aria-label|title)\s*=\s*[\"'{][^\"'}]", fragment, re.I):
        return True
    if re.search(r"<title>\s*\S", fragment, re.I):
        return True
    if re.search(r"\baria-label(ledby)?\s*=", fragment, re.I):
        return True
    text = re.sub(r"<[^>]*>", " ", fragment)
    text = re.sub(r"\{\s*/\*.*?\*/\s*\}", " ", text, flags=re.S)
    return bool(re.search(r"[\w{]", text))


def line_of(src, pos):
    return src.count("\n", 0, pos) + 1


def scan_file(path, deadline=None):
    src = read_source(path)
    is_html = path.lower().endswith((".html", ".htm"))
    issues = []

    def add(pos, rule, wcag, msg, level="error"):
        issues.append({"file": path, "line": line_of(src, pos), "rule": rule, "wcag": wcag, "level": level, "message": msg})

    label_for = collect_label_for(src, deadline)
    headings = []

    for m in iter_tags(src, deadline):
        tag, raw, selfclose = m.group(1), m.group(2), m.group(3)
        t = tag.lower()
        a = attrs_of(raw)
        pos = m.start()
        spread = has_spread(raw)
        hidden = a.get("aria-hidden") in ("true", "{true}", True) or "hidden" in a
        named = has_any(a, "aria-label", "aria-labelledby", "title")

        if t == "html" and is_html and "lang" not in a:
            add(pos, "html-lang", "3.1.1", "<html> 没有 lang 属性")

        elif t in ("img", "image") and tag[0].islower() or tag in ("Image", "NextImage"):
            if "alt" not in a and not spread and not hidden and a.get("role") not in ("presentation", "none"):
                add(pos, "img-alt", "1.1.1", f"<{tag}> 没有 alt 文本（装饰性图片请写 alt=\"\"）")

        elif t == "input" and tag[0].islower():
            typ = str(a.get("type", "text")).lower()
            if typ == "hidden":
                continue
            if typ == "image" and "alt" not in a:
                add(pos, "input-image-alt", "1.1.1", "<input type=image> 没有 alt")
            if typ in ("submit", "button", "reset", "image"):
                continue
            if not named and not spread and str(a.get("id", "")) not in label_for and not _wrapped_in_label(src, pos):
                add(pos, "form-label", "1.3.1 / 4.1.2", f"<input type={typ}> 没有关联的 label，也没有 aria-label 或 aria-labelledby")

        elif t in ("select", "textarea") and tag[0].islower():
            if not named and not spread and str(a.get("id", "")) not in label_for and not _wrapped_in_label(src, pos):
                add(pos, "form-label", "1.3.1 / 4.1.2", f"<{t}> 没有关联的 label，也没有 aria-label 或 aria-labelledby")

        elif t == "button" and tag[0].islower():
            if not named and not spread and not selfclose and not visible_text(inner_text(src, m.end(), tag)):
                add(pos, "button-name", "4.1.2", "<button> 没有文字也没有 aria-label（是不是只有图标的按钮？）")
            if selfclose and not named and not spread:
                add(pos, "button-name", "4.1.2", "<button/> 没有文字也没有 aria-label")

        elif t == "a" and tag[0].islower():
            if not named and not spread and not selfclose:
                body = inner_text(src, m.end(), tag)
                if not visible_text(body):
                    add(pos, "link-name", "2.4.4 / 4.1.2", "<a> 没有文字也没有 aria-label")
                elif re.fullmatch(r"\s*(click here|here|read more|more|link|点击这里|点这里|这里|了解更多|查看更多|更多|详情|点击查看|链接)\s*", re.sub(r"<[^>]*>", "", body), re.I):
                    add(pos, "link-purpose", "2.4.4", "链接文字没有说明要去哪里或做什么", "warning")
            if "href" not in a and has_any(a, "onclick", "@click", "v-on:click", "on:click") and "role" not in a:
                add(pos, "anchor-is-button", "4.1.2", "没有 href 的 <a> 被当成按钮用，请改用 <button>")

        elif t in ("div", "span", "li", "td", "p", "section", "img") and tag[0].islower():
            if has_any(a, "onclick", "@click", "v-on:click", "on:click", "(click)"):
                if "role" not in a:
                    add(pos, "click-no-role", "4.1.2", f"可点击的 <{t}> 没有 role；请改用 <button>，或补上 role 和 tabindex")
                if "tabindex" not in a:
                    add(pos, "click-no-focus", "2.1.1", f"可点击的 <{t}> 用键盘到不了（没有 tabindex）")
                if not has_any(a, "onkeydown", "onkeyup", "onkeypress", "@keydown", "@keyup", "v-on:keydown", "on:keydown", "(keydown)"):
                    add(pos, "click-no-key", "2.1.1", f"可点击的 <{t}> 没有键盘事件处理")

        elif t in ("video", "audio") and tag[0].islower():
            if "autoplay" in a and "muted" not in a:
                add(pos, "media-autoplay", "1.4.2", f"<{t}> 自动播放且带声音")
            if t == "video" and not selfclose and "<track" not in inner_text(src, m.end(), tag):
                add(pos, "video-captions", "1.2.2", "<video> 没有提供字幕的 <track>", "warning")

        elif t == "iframe" and "title" not in a and not spread:
            add(pos, "iframe-title", "4.1.2", "<iframe> 没有 title")

        elif re.fullmatch(r"h[1-6]", t):
            headings.append((pos, int(t[1])))

        if t == "meta" and str(a.get("name", "")).lower() == "viewport":
            content = str(a.get("content", "")).replace(" ", "").lower()
            if "user-scalable=no" in content or "user-scalable=0" in content or re.search(r"maximum-scale=1(\.0)?(,|$)", content):
                add(pos, "viewport-zoom", "1.4.4", "viewport 设置禁止了缩放")

        ti = a.get("tabindex")
        if isinstance(ti, str):
            num = re.sub(r"[^\d-]", "", ti)
            if num.lstrip("-").isdigit() and int(num) > 0:
                add(pos, "tabindex-positive", "2.4.3", f"tabindex={num} 会打乱默认的焦点顺序")

        if "accesskey" in a:
            add(pos, "accesskey", "2.1.4", "accesskey 可能和读屏软件的快捷键冲突", "warning")

        if a.get("role") in ("button", "link", "checkbox", "tab", "menuitem", "switch") and t not in ("button", "a", "input") and "tabindex" not in a:
            add(pos, "role-no-focus", "2.1.1", f"<{t}> 上有 role={a.get('role')} 但没有 tabindex")

        if "outline" in str(a.get("style", "")).replace(" ", "") and re.search(r"outline:(none|0)", str(a.get("style", "")).replace(" ", "")):
            add(pos, "focus-outline", "2.4.7", "行内样式去掉了焦点轮廓", "warning")

    prev = 0
    for pos, level in headings:
        if prev and level > prev + 1:
            add(pos, "heading-order", "1.3.1", f"标题从 h{prev} 直接跳到 h{level}", "warning")
        prev = level

    for m in re.finditer(r"outline\s*:\s*(none|0)\b", src) if path.lower().endswith((".vue", ".svelte", ".astro", ".html", ".htm")) else []:
        if not re.search(r":focus-visible|:focus", src):
            add(m.start(), "focus-outline", "2.4.7", "CSS 去掉了焦点轮廓，而且没有找到 :focus 样式", "warning")
            break

    issues.sort(key=lambda i: i["line"])
    return issues


def _wrapped_in_label(src, pos):
    before = src[max(0, pos - 600):pos]
    return before.rfind("<label") > before.rfind("</label>")


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for dirpath, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for n in sorted(names):
                if n.lower().endswith(EXTS) and not os.path.islink(os.path.join(dirpath, n)):
                    yield os.path.join(dirpath, n)


NAMES = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
    "gray": "#808080", "grey": "#808080", "silver": "#c0c0c0", "yellow": "#ffff00", "orange": "#ffa500",
    "purple": "#800080", "navy": "#000080", "teal": "#008080", "maroon": "#800000", "olive": "#808000",
    "lime": "#00ff00", "aqua": "#00ffff", "fuchsia": "#ff00ff", "lightgray": "#d3d3d3", "darkgray": "#a9a9a9",
}


def parse_color(c):
    c = NAMES.get(c.strip().lower(), c.strip())
    m = re.fullmatch(r"#([0-9a-fA-F]{3,8})", c)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h)
        if len(h) not in (6, 8):
            raise ValueError(c)
        rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        alpha = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return rgb, alpha
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)", c)
    if m:
        rgb = [float(m.group(i)) for i in (1, 2, 3)]
        a = m.group(4)
        alpha = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        if any(v > 255 for v in rgb) or not 0 <= alpha <= 1:
            raise ValueError(f"颜色数值超出范围：{c}")
        return rgb, alpha
    raise ValueError(f"无法识别的颜色：{c}")


def luminance(rgb):
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    (frgb, fa), (brgb, _) = parse_color(fg), parse_color(bg)
    blended = [fa * f + (1 - fa) * b for f, b in zip(frgb, brgb)]
    l1, l2 = sorted((luminance(blended), luminance(brgb)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def verdict(r):
    def ok(x):
        return "达标" if r >= x else "未达标"
    return (f"AA 正文 {ok(4.5)}，AA 大字 {ok(3)}，"
            f"AAA 正文 {ok(7)}，AAA 大字 {ok(4.5)}，界面组件 {ok(3)}")


# ==== 以下为本团队编写的原生工具封装 ====
import asyncio
from copy import deepcopy
from typing import Any, AsyncIterator

from openjiuwen.core.foundation.tool import Tool, ToolCard

TOOL_PREFIX = "a11y_"
MAX_PATHS = 10
MAX_PATH_CHARS = 1000
MAX_FILES = 3000                 # 一次调用最多扫描的文件数
MAX_TOTAL_BYTES = 200 * 1024 * 1024
MAX_ISSUES_LIMIT = 500
DEFAULT_MAX_ISSUES = 100
MAX_PAIRS = 50
MAX_COLOR_CHARS = 64
SUPPORTED_EXTS = EXTS            # 上游支持的扩展名

NOTE_ZH = ("请用简体中文向用户汇报。这是静态扫描：只能看到标记里直接写出来的问题，看不到运行时生成的内容、"
           "传给自定义组件的属性和样式表里的 CSS；没有发现问题不等于符合 WCAG，仍需键盘和读屏软件的人工检查。"
           "每条发现都要结合上下文确认后再当作问题；修改代码要尽量小，并说明改了什么。")

CATALOG = {
    "scan": {
        "description": "静态扫描网页界面代码里的无障碍问题（对照 WCAG 2.2 AA）：读取 .html、.htm、.jsx、.tsx、.vue、.svelte、.astro "
                       "文件或文件夹，只读不改，报告缺 alt 的图片、没有名称的按钮和链接、没有标签的表单项、只能点击不能用键盘操作的元素、"
                       "正数 tabindex、缺少 lang、禁止缩放、自动播放、标题层级跳跃、去掉焦点轮廓等，每条带文件、行号、规则名、"
                       "WCAG 成功标准编号和中文说明。这是静态扫描，看不到运行时生成的内容、传给自定义组件的属性和样式表里的 CSS；"
                       "没有发现问题不等于符合 WCAG。文件夹里会跳过 node_modules、dist、build 等目录和符号链接。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["paths"], "properties": {
            "paths": {"type": "array", "minItems": 1, "maxItems": MAX_PATHS, "items": {"type": "string", "minLength": 1, "maxLength": MAX_PATH_CHARS},
                      "description": "要扫描的文件或文件夹路径列表（最多 10 个，建议用完整路径）。文件只支持 .html、.htm、.jsx、.tsx、.vue、.svelte、.astro。"},
            "errors_only": {"type": "boolean", "description": "为 true 时只报告错误，不报告警告，默认 false。"},
            "max_issues": {"type": "integer", "minimum": 1, "maximum": MAX_ISSUES_LIMIT,
                           "description": "最多列出多少条问题，默认 100（统计数字始终覆盖全部问题）。"},
        }},
    },
    "contrast": {
        "description": "计算文字色和背景色的 WCAG 对比度，并判断是否达标：AA 正文 4.5:1、AA 大字 3:1（24px，或加粗 18.66px 以上）、"
                       "界面组件和图标 3:1，AAA 正文 7:1、AAA 大字 4.5:1。颜色可写 #rgb、#rrggbb、#rrggbbaa、rgb()、rgba() 或 20 个基本英文颜色名；"
                       "带透明度的前景色按背景色混合后计算，背景色的透明度被忽略（按不透明处理）。不会读取主题或样式文件，颜色需要先从代码里找出来。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["pairs"], "properties": {
            "pairs": {"type": "array", "minItems": 1, "maxItems": MAX_PAIRS, "items": {
                "type": "object", "additionalProperties": False, "required": ["foreground", "background"], "properties": {
                    "foreground": {"type": "string", "minLength": 1, "maxLength": MAX_COLOR_CHARS, "description": "文字（或图标、边框）的颜色，例如 \"#6b7280\"。"},
                    "background": {"type": "string", "minLength": 1, "maxLength": MAX_COLOR_CHARS, "description": "背景颜色，例如 \"#ffffff\"。"}}},
                "description": "要检查的颜色对列表（最多 50 对）。"},
        }},
    },
}


def error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


def validate(tool: str, arguments: Any) -> tuple[dict | None, str | None]:
    """返回 (规整后的参数, 错误信息)。"""
    if not isinstance(arguments, dict):
        return None, "参数必须是一个对象。"
    allowed = set(CATALOG[tool]["schema"]["properties"])
    extra = sorted(set(arguments) - allowed)
    if extra:
        return None, "不认识的参数：%s。" % "、".join(extra)
    if tool == "scan":
        paths = arguments.get("paths")
        if not isinstance(paths, list) or not paths:
            return None, "paths 必须是至少含一个路径的列表。"
        if len(paths) > MAX_PATHS:
            return None, "一次最多扫描 %d 个路径。" % MAX_PATHS
        cleaned = []
        for item in paths:
            if not isinstance(item, str) or not item.strip():
                return None, "paths 里的每一项都必须是非空字符串。"
            if len(item) > MAX_PATH_CHARS or "\x00" in item:
                return None, "路径过长或含有非法字符。"
            cleaned.append(item.strip())
        errors_only = arguments.get("errors_only", False)
        if not isinstance(errors_only, bool):
            return None, "errors_only 必须是 true 或 false。"
        max_issues = arguments.get("max_issues", DEFAULT_MAX_ISSUES)
        if isinstance(max_issues, bool) or not isinstance(max_issues, int) or not 1 <= max_issues <= MAX_ISSUES_LIMIT:
            return None, "max_issues 必须是 1 到 %d 之间的整数。" % MAX_ISSUES_LIMIT
        return {"paths": cleaned, "errors_only": errors_only, "max_issues": max_issues}, None
    pairs = arguments.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        return None, "pairs 必须是至少含一对颜色的列表。"
    if len(pairs) > MAX_PAIRS:
        return None, "一次最多检查 %d 对颜色。" % MAX_PAIRS
    cleaned_pairs = []
    for item in pairs:
        if not isinstance(item, dict) or set(item) != {"foreground", "background"}:
            return None, "pairs 里的每一项都必须是只含 foreground 和 background 两个字段的对象。"
        for key in ("foreground", "background"):
            value = item[key]
            if not isinstance(value, str) or not value.strip():
                return None, "%s 必须是非空字符串，例如 \"#6b7280\"。" % key
            if len(value) > MAX_COLOR_CHARS or "\x00" in value:
                return None, "%s 太长或含有非法字符。" % key
        cleaned_pairs.append({"foreground": item["foreground"].strip(), "background": item["background"].strip()})
    return {"pairs": cleaned_pairs}, None


def _size_text(size: int) -> str:
    return "%.1f MB" % (size / 1024 / 1024)


def collect_files(paths: list) -> tuple[list, list]:
    """把用户给的路径展开成文件列表；返回 (文件, 跳过原因)。文件夹按字典序遍历，跳过符号链接。"""
    files, skipped = [], []
    for given in paths:
        if os.path.islink(given):
            skipped.append({"path": given, "reason": "是符号链接，没有读取。"})
        elif os.path.isfile(given):
            if not given.lower().endswith(SUPPORTED_EXTS):
                skipped.append({"path": given, "reason": "不支持这种文件类型（只支持 .html、.htm、.jsx、.tsx、.vue、.svelte、.astro）。"})
            else:
                files.append(given)
        elif os.path.isdir(given):
            found = list(iter_files([given]))
            files.extend(found)
        else:
            skipped.append({"path": given, "reason": "找不到这个文件或文件夹。"})
    return files, skipped


def run_scan(values: dict) -> dict:
    deadline = time.monotonic() + SCAN_BUDGET_SECONDS
    files, skipped = collect_files(values["paths"])
    if not files:
        if skipped and all(item["reason"].startswith("找不到") for item in skipped) and len(skipped) == len(values["paths"]):
            return error("ALL_PATHS_FAILED", "所有路径都找不到：" + "；".join(item["path"] for item in skipped), skipped=skipped)
        return error("NO_FILES", "没有找到 HTML、JSX、TSX、Vue、Svelte 或 Astro 文件。", skipped=skipped)
    issues, scanned, total_bytes, complete = [], 0, 0, True
    not_scanned = 0
    for index, path in enumerate(files):
        if scanned >= MAX_FILES or total_bytes >= MAX_TOTAL_BYTES or time.monotonic() > deadline:
            not_scanned = len(files) - index
            complete = False
            break
        try:
            found = scan_file(path, min(deadline, time.monotonic() + FILE_BUDGET_SECONDS))
        except FileTooLarge as exc:
            size = exc.args[0] if exc.args else 0
            skipped.append({"path": path, "reason": "文件超过 %s 的上限（%s），没有扫描。" % (_size_text(MAX_FILE_BYTES), _size_text(size))})
            continue
        except ScanTimeout:
            skipped.append({"path": path, "reason": "扫描超过时间预算（单个文件 %d 秒），这个文件的结果不完整，已丢弃。" % int(FILE_BUDGET_SECONDS)})
            complete = False
            continue
        except OSError as exc:
            skipped.append({"path": path, "reason": "读不了这个文件（%s）。" % type(exc).__name__})
            continue
        scanned += 1
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        issues.extend(found)
    if not scanned and not issues:
        return error("NO_FILES_SCANNED", "找到了文件，但都没能扫描：" + "；".join("%s：%s" % (s["path"], s["reason"]) for s in skipped[:5]), skipped=skipped)
    if values["errors_only"]:
        issues = [i for i in issues if i["level"] == "error"]
    errors = sum(1 for i in issues if i["level"] == "error")
    warnings = len(issues) - errors
    by_rule: dict = {}
    for item in issues:
        by_rule[item["rule"]] = by_rule.get(item["rule"], 0) + 1
    shown = issues[:values["max_issues"]]
    level_zh = {"error": "错误", "warning": "警告"}
    lines = ["%s:%d: %s [%s] WCAG %s: %s" % (i["file"], i["line"], level_zh[i["level"]], i["rule"], i["wcag"], i["message"]) for i in shown]
    if len(issues) > len(shown):
        lines.append("（只列出前 %d 条，共 %d 条；统计数字覆盖全部。）" % (len(shown), len(issues)))
    lines.append("")
    lines.append("共扫描 %d 个文件：%d 个错误，%d 个警告" % (scanned, errors, warnings))
    for rule, count in sorted(by_rule.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append("  %4d  %s" % (count, rule))
    if skipped:
        lines.append("")
        lines.append("没有扫描的路径：")
        for item in skipped:
            lines.append("  %s：%s" % (item["path"], item["reason"]))
    if not complete:
        lines.append("")
        lines.append("（扫描没有跑完：%s 结果不完整，请缩小范围后重扫。）" % (
            "有 %d 个文件因文件数、总大小或时间上限没有扫描；" % not_scanned if not_scanned else "有文件超时；"))
    return {"ok": True, "tool": TOOL_PREFIX + "scan", "message": NOTE_ZH, "report_text": "\n".join(lines),
            "summary": {"files_scanned": scanned, "errors": errors, "warnings": warnings, "by_rule": by_rule},
            "issues": shown, "issues_truncated": len(issues) > len(shown), "skipped": skipped, "scan_complete": complete}



def run_contrast(values: dict) -> dict:
    results, problems = [], []
    for pair in values["pairs"]:
        fg, bg = pair["foreground"], pair["background"]
        try:
            (_, fg_alpha), (_, bg_alpha) = parse_color(fg), parse_color(bg)
            value = ratio(fg, bg)
        except ValueError as exc:
            problems.append({"foreground": fg, "background": bg, "error": str(exc)})
            results.append({"foreground": fg, "background": bg, "error": str(exc)})
            continue
        shown = "%.2f" % value
        text = "%s 在 %s 上：%s:1  %s" % (fg, bg, shown, verdict(value))
        notes = []
        if fg_alpha < 1:
            notes.append("前景色带透明度，已按背景色混合后计算。")
        if bg_alpha < 1:
            notes.append("背景色的透明度被忽略，按不透明处理；实际背景以叠加后的颜色为准。")
        for threshold in (3, 4.5, 7):
            if value < threshold and float(shown) >= threshold:
                notes.append("四舍五入后显示 %s，但精确值 %.4f 低于 %s:1，按未达标处理。" % (shown, value, ("%g" % threshold)))
        results.append({"foreground": fg, "background": bg, "ratio": float(shown), "ratio_exact": round(value, 4),
                        "aa_normal": value >= 4.5, "aa_large": value >= 3, "aaa_normal": value >= 7, "aaa_large": value >= 4.5,
                        "ui_components": value >= 3, "result_zh": text, "notes": notes})
    if len(problems) == len(results):
        return error("INVALID_COLOR", "所有颜色都无法识别：" + "；".join(p["error"] for p in problems), pairs=results)
    lines = []
    for item in results:
        if "error" in item:
            lines.append("%s 在 %s 上：%s" % (item["foreground"], item["background"], item["error"]))
        else:
            lines.append(item["result_zh"])
            lines.extend("  注：" + n for n in item["notes"])
    return {"ok": True, "tool": TOOL_PREFIX + "contrast", "message": NOTE_ZH, "report_text": "\n".join(lines), "pairs": results,
            "all_aa_normal": all(item.get("aa_normal") for item in results)}


RUNNERS = {"scan": run_scan, "contrast": run_contrast}


async def call_tool(name: str, arguments: Any) -> dict:
    values, message = validate(name, arguments)
    if message:
        return error("INVALID_ARGUMENTS", message, tool=TOOL_PREFIX + name)
    try:
        return await asyncio.to_thread(RUNNERS[name], values)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # 不向用户暴露内部堆栈，也不伪造结果
        return error("INTERNAL_ERROR", "工具内部出错（%s）；本次没有返回结果。" % type(exc).__name__, tool=TOOL_PREFIX + name)


class A11yTool(Tool):
    key = ""

    def __init__(self) -> None:
        entry = CATALOG[self.key]
        super().__init__(ToolCard(id=TOOL_PREFIX + self.key, name=TOOL_PREFIX + self.key,
                                  description=entry["description"], input_params=deepcopy(entry["schema"])))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_tool(self.key, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class A11yScanTool(A11yTool):
    key = "scan"


class A11yContrastTool(A11yTool):
    key = "contrast"
