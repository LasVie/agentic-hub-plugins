"""离线书架阅读器：有界导入、私有书架和仅回环阅读服务。

Ported local-book/chapter/shelf workflows from xrn1997/dsh-novel 0.8.1,
f9a19f5fbd2d76ef5e970c2333a67f9dcb66b31c, Copyright 2026 xrn1997.
Licensed under Apache-2.0; full text: ../licenses/dsh-novel/LICENSE.
Changed 2026-10-27 by Cai Zhenze: Python standard-library text-only adapter,
explicit encodings, strict bounds, integrity checks, transactional private state,
native tools and independent loopback UI; no DSH hooks or online source engine.
"""
import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import unquote, urlsplit
from urllib.request import ProxyHandler, Request, build_opener
import xml.etree.ElementTree as ET
import zipfile

VERSION = "1.0.0"
SLUG = "offline-ebook-reader"
NAME = "离线书架阅读器"
MAX_INPUT = 8 * 1024 * 1024
MAX_TEXT = 2_000_000
MAX_CHAPTERS = 500
MAX_BOOKS = 40
MAX_STORE = 128 * 1024 * 1024
DEFAULT_PREFS = {"font_size": 20, "line_height": 1.8, "width": 760, "theme": "paper"}
ID_RE = re.compile(r"[a-f0-9]{64}\Z")
CHAPTER_RE = re.compile(r"^\s*(?:第[0-9零一二三四五六七八九十百千万亿两壹贰叁肆伍陆柒捌玖拾佰仟萬億]+[章卷回节集部篇]|[章卷回节集部篇][0-9零一二三四五六七八九十百千万亿两]+|序章|楔子|番外|尾声|后记|Chapter\s*\d+)\s*[:：.、\s]*(.*)$", re.I)


class ReaderError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def fail(code, message):
    raise ReaderError(code, message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def result(**kw):
    return {"ok": True, "version": VERSION, **kw}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n").encode()


def absolute(value, directory=False):
    if not isinstance(value, str) or not value or "\x00" in value:
        fail("invalid_path", "请提供真实绝对路径。")
    p = Path(value)
    if not p.is_absolute() or ".." in p.parts:
        fail("invalid_path", "路径必须为不含上级跳转的绝对路径。")
    for part in [p, *p.parents]:
        if part.is_symlink():
            fail("unsafe_path", "不接受符号链接路径。")
    if directory and not p.is_dir():
        fail("invalid_directory", "指定工作目录必须已存在。")
    return p


def read_bytes(p, limit):
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as f:
        before = os.fstat(f.fileno())
        if not stat.S_ISREG(before.st_mode):
            fail("unsafe_file", "只接受普通文件。")
        if before.st_size > limit:
            fail("size_limit", "文件超过本次操作的大小上限。")
        data = f.read(limit + 1)
        after = os.fstat(f.fileno())
        if len(data) > limit or len(data) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            fail("file_changed", "文件读取期间发生变化或超过上限；请停止写入后重试。")
        return data


def read_json(p, limit=16 * 1024 * 1024):
    return json.loads(read_bytes(p, limit))


def atomic_json(p, value):
    if p.is_symlink():
        fail("unsafe_state", "状态文件不能为链接。")
    fd, temp = tempfile.mkstemp(prefix=".new-", dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(encode(value)); f.flush(); os.fsync(f.fileno())
        os.replace(temp, p)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def private_dir(p):
    try:
        p.mkdir(mode=0o700)
    except FileExistsError:
        pass
    st = p.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        fail("unsafe_state", "书架状态目录须为当前用户私有的普通目录（权限700）。")


def state_dir(workspace, create=False):
    base = absolute(workspace, directory=True)
    if base == Path("/") or base == Path.home():
        fail("invalid_workspace", "请选择专用工作目录，不使用根目录或整个主目录。")
    root = base / ".offline-ebook-reader"
    if create:
        private_dir(root)
        private_dir(root / "books")
    elif root.exists() or root.is_symlink():
        for p in (root, root / "books"):
            st = p.lstat()
            if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
                fail("unsafe_state", "书架状态目录不安全或损坏。")
    return root


@contextlib.contextmanager
def locked(root, name="state.lock"):
    fd = os.open(root / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            fail("unsafe_state", "锁文件不安全。")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def initial_state():
    return {"schema": 1, "revision": 0, "books": {}, "current_book": None, "preferences": dict(DEFAULT_PREFS)}


def load_state(root):
    p = root / "shelf.json"
    s = read_json(p) if p.exists() or p.is_symlink() else initial_state()
    if not isinstance(s, dict) or s.get("schema") != 1 or type(s.get("revision")) is not int or not isinstance(s.get("books"), dict) or len(s["books"]) > MAX_BOOKS:
        fail("state_corrupt", "书架记录损坏；未重置或覆盖。")
    if any(not ID_RE.fullmatch(k) for k in s["books"]):
        fail("state_corrupt", "书籍标识无效。")
    return s


def save_state(root, s):
    s["revision"] += 1
    atomic_json(root / "shelf.json", s)


def checked_revision(s, value):
    if type(value) is not int or value != s["revision"]:
        fail("revision_conflict", "书架已变更；请重新读取状态，不覆盖较新的记录。")


def validate_text(text):
    if not text.strip() or "\x00" in text or any(ord(c) < 32 and c not in "\t\r\n" for c in text):
        fail("invalid_text", "书籍为空或含不支持的控制字符。")
    if len(text) > MAX_TEXT:
        fail("text_limit", "正文超过200万字符上限。")


def parse_txt(data, encoding):
    options = {"utf-8": "utf-8-sig", "gb18030": "gb18030", "utf-16": "utf-16"}
    if encoding not in options:
        fail("unsupported_encoding", "TXT编码仅支持utf-8、gb18030或带BOM的utf-16；不会猜测编码。")
    try:
        text = data.decode(options[encoding], errors="strict").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError:
        fail("invalid_encoding", "TXT无法按指定编码严格解码；请选择正确编码，不输出乱码替代文字。")
    validate_text(text)
    chapters, lines, title = [], [], "正文"
    for line in text.split("\n"):
        if len(line) < 180 and CHAPTER_RE.match(line):
            if lines and "\n".join(lines).strip():
                chapters.append({"title": title, "text": "\n".join(lines).strip()})
            title, lines = line.strip(), []
        else:
            lines.append(line)
    if lines or not chapters:
        chapters.append({"title": title, "text": "\n".join(lines).strip()})
    if len(chapters) > MAX_CHAPTERS:
        fail("chapter_limit", "章节超过500章上限。")
    return {"format": "txt", "encoding": encoding, "chapters": chapters, "warnings": [], "author": ""}


def local_name(tag):
    return tag.split("}")[-1].lower()


def xml(data, label):
    if len(data) > 4 * 1024 * 1024:
        fail("xml_limit", "XML文档超过4MiB上限。")
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeError:
        fail("unsupported_encoding", "本版EPUB XML仅支持UTF-8。")
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", text, re.I):
        fail("unsafe_xml", "本版拒绝含DTD或实体声明的EPUB XML。")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        fail("invalid_xml", f"EPUB XML解析失败：{label}。")
    stack, count = [(root, 0)], 0
    while stack:
        node, depth = stack.pop(); count += 1
        if depth > 50 or count > 100_000:
            fail("xml_limit", "XML层级或节点数量超限。")
        stack.extend((child, depth + 1) for child in node)
    return root


def archive_path(value, base=""):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        fail("unsafe_archive", "EPUB内路径不安全。")
    u = urlsplit(value)
    raw = unquote(u.path)
    if u.scheme or u.netloc or u.query or raw.startswith("/") or ".." in PurePosixPath(raw).parts or ":" in raw:
        fail("unsafe_archive", "拒绝远程或越界的EPUB路径。")
    p = str(PurePosixPath(base) / raw)
    if p in ("", "."):
        fail("unsafe_archive", "EPUB内路径为空。")
    return p


def parse_epub(data):
    warnings = {"本版为纯文本阅读：不保留出版方CSS、字体、图片或复杂版式，不执行脚本或联网。"}
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        fail("invalid_epub", "EPUB不是完整有效的ZIP归档。")
    with archive:
        infos = archive.infolist()
        if len(infos) > 400 or sum(i.file_size for i in infos) > 24 * 1024 * 1024:
            fail("archive_limit", "EPUB最多400项、累计解压24MiB。")
        names = set()
        for i in infos:
            n = archive_path(i.filename.rstrip("/"))
            mode = i.external_attr >> 16
            if n in names or i.flag_bits & 1 or i.file_size > 4 * 1024 * 1024 or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                fail("unsafe_archive", "EPUB含重复项、加密项、链接、特殊文件或过大条目。")
            if i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                fail("unsafe_archive", "EPUB压缩方式不受支持。")
            names.add(n)
        def entry(name):
            if name not in names:
                fail("missing_entry", f"EPUB引用的文档不存在：{name}。")
            try:
                return archive.read(name)
            except (zipfile.BadZipFile, RuntimeError, ValueError):
                fail("invalid_epub", "EPUB条目校验失败。")
        if entry("mimetype") != b"application/epub+zip":
            fail("invalid_epub", "EPUB缺少正确的mimetype声明。")
        if "META-INF/encryption.xml" in names or "META-INF/rights.xml" in names:
            fail("encrypted_epub", "本版不处理加密、DRM或字体混淆EPUB。")
        container = xml(entry("META-INF/container.xml"), "container.xml")
        roots = [n for n in container.iter() if local_name(n.tag) == "rootfile"]
        if len(roots) != 1:
            fail("unsupported_epub", "本版要求EPUB只包含一个包文档。")
        package_path = archive_path(roots[0].get("full-path", ""))
        package = xml(entry(package_path), package_path)
        if any(local_name(n.tag) == "meta" and (n.get("property") == "rendition:layout" and (n.text or "").strip() == "pre-paginated" or n.get("name") == "fixed-layout" and n.get("content") == "true") for n in package.iter()):
            fail("fixed_layout", "本版仅支持流式文本EPUB，不支持固定版式。")
        manifest, spine, label_map = {}, [], {}
        for n in package.iter():
            if local_name(n.tag) == "item":
                key = n.get("id")
                if not key or key in manifest:
                    fail("invalid_epub", "EPUB清单标识缺失或重复。")
                manifest[key] = n
            if local_name(n.tag) == "itemref" and n.get("linear", "yes") != "no":
                spine.append(n.get("idref"))
        if not spine or len(spine) > MAX_CHAPTERS:
            fail("invalid_spine", "EPUB主阅读序列为空或超过500章。")
        base = str(PurePosixPath(package_path).parent)
        # Optional nav/NCX labels; chapter order always comes from the spine.
        for n in manifest.values():
            if "nav" in n.get("properties", "").split() or n.get("media-type") == "application/x-dtbncx+xml":
                navpath = archive_path(n.get("href", ""), base)
                nav = xml(entry(navpath), navpath)
                for a in nav.iter():
                    if local_name(a.tag) == "a" and a.get("href"):
                        target = archive_path(a.get("href"), str(PurePosixPath(navpath).parent))
                        if target not in names:
                            fail("missing_entry", "EPUB目录引用的文档不存在。")
                        label_map.setdefault(target, " ".join("".join(a.itertext()).split())[:200])
                    if local_name(a.tag) == "navpoint":
                        label = next((" ".join("".join(x.itertext()).split()) for x in a.iter() if local_name(x.tag) == "navlabel"), "")
                        content = next((x.get("src") for x in a.iter() if local_name(x.tag) == "content"), None)
                        if content:
                            target = archive_path(content, str(PurePosixPath(navpath).parent))
                            if target not in names:
                                fail("missing_entry", "EPUB目录引用的文档不存在。")
                            label_map.setdefault(target, label[:200])
        chapters = []
        for key in spine:
            if key not in manifest:
                fail("invalid_spine", "EPUB主序列引用了不存在的清单项。")
            item = manifest[key]
            if item.get("media-type") not in ("application/xhtml+xml", "text/html"):
                fail("unsupported_epub", "本版主序列只支持XHTML文本章节。")
            path = archive_path(item.get("href", ""), base)
            doc = xml(entry(path), path)
            body = next((n for n in doc.iter() if local_name(n.tag) == "body"), None)
            if body is None:
                fail("invalid_epub", "EPUB章节缺少body正文。")
            chunks = []
            def visit(n):
                tag = local_name(n.tag)
                if tag in ("script", "style", "iframe", "object", "embed", "svg", "math", "audio", "video"):
                    warnings.add("已略去脚本、样式或复杂媒体/数学内容；请使用原书核对。")
                    return
                if tag == "img":
                    chunks.append("[图片：" + (n.get("alt") or "无替代文字") + "]")
                    warnings.add("正文图片仅显示替代文字，不加载本地或远程图片。")
                    return
                if tag in ("p", "div", "section", "article", "h1", "h2", "h3", "li", "br", "tr", "blockquote", "pre"):
                    chunks.append("\n")
                if n.text:
                    chunks.append(n.text)
                for child in n:
                    visit(child)
                    if child.tail:
                        chunks.append(child.tail)
                if tag in ("p", "div", "section", "article", "li", "h1", "h2", "h3", "tr", "blockquote", "pre"):
                    chunks.append("\n")
            visit(body)
            text = "\n".join(line.strip() for line in "".join(chunks).splitlines() if line.strip())
            # Image placeholders alone are not a text-bearing book.
            if not re.sub(r"\[图片：[^\]]*\]", "", text).strip():
                fail("image_only", "章节没有可阅读文本；不把图片占位符当作正文。")
            validate_text(text)
            headings = [n for n in body.iter() if local_name(n.tag) in ("h1", "h2")]
            title = label_map.get(path) or (" ".join("".join(headings[0].itertext()).split()) if headings else f"第{len(chapters) + 1}章")
            chapters.append({"title": title[:200], "text": text})
        if sum(len(c["text"]) for c in chapters) > MAX_TEXT:
            fail("text_limit", "EPUB正文超过200万字符上限。")
        title = next((n.text for n in package.iter() if local_name(n.tag) == "title" and n.text), "")
        author = next((n.text for n in package.iter() if local_name(n.tag) == "creator" and n.text), "")
        return {"format": "epub", "title": title[:200], "author": author[:200], "encoding": "utf-8", "chapters": chapters, "warnings": sorted(warnings)}


def book_data(root, s, bid):
    if not isinstance(bid, str) or not ID_RE.fullmatch(bid) or bid not in s["books"]:
        fail("book_missing", "书籍不存在；请从当前书架选择真实book_id。")
    entry = s["books"][bid]
    folder = root / "books" / bid
    if folder.is_symlink() or not folder.is_dir():
        fail("unsafe_state", "书籍副本目录损坏。")
    raw = read_bytes(folder / "book.json", 16 * 1024 * 1024)
    if sha(raw) != entry.get("parsed_sha256") or sha(read_bytes(folder / "original", MAX_INPUT)) != bid:
        fail("integrity_mismatch", "书籍副本完整性校验失败；未继续阅读。")
    book = json.loads(raw)
    if not isinstance(book.get("chapters"), list) or not 1 <= len(book["chapters"]) <= MAX_CHAPTERS:
        fail("state_corrupt", "书籍章节记录损坏。")
    return book


def shelf_view(s):
    return result(revision=s["revision"], books=sorted(s["books"].values(), key=lambda x: (-x["progress"]["updated_at"], x["book_id"])), preferences=s["preferences"], current_book=s["current_book"], message="书架状态已读取。")


def library(inputs):
    allowed = {"action", "workspace", "path", "encoding", "confirmed", "book_id", "chapter_index", "offset_ratio", "expected_revision", "preferences"}
    if set(inputs) - allowed:
        fail("invalid_input", "存在不支持的参数。")
    action = inputs.get("action", "list")
    if action not in ("import", "list", "toc", "progress", "preferences"):
        fail("invalid_action", "操作仅支持import、list、toc、progress、preferences。")
    write = action in ("import", "progress", "preferences")
    if write and inputs.get("confirmed") is not True:
        fail("confirmation_required", "保存书籍副本、阅读位置或设置需要明确授权并提供confirmed=true。")
    root = state_dir(inputs.get("workspace"), create=action == "import")
    if not root.exists():
        if action == "list":
            return shelf_view(initial_state())
        fail("library_missing", "书架尚未创建，请先导入书籍。")
    with locked(root):
        s = load_state(root)
        if action == "list":
            return shelf_view(s)
        if action == "import":
            source = absolute(inputs.get("path"))
            if source == root or root in source.parents:
                fail("state_as_source", "不要把书架自身的状态文件再次导入。")
            data = read_bytes(source, MAX_INPUT)
            bid = sha(data)
            if bid in s["books"]:
                book_data(root, s, bid)
                return result(reused=True, book=s["books"][bid], revision=s["revision"], message="相同原始字节已在书架中，保留已有阅读位置。")
            if len(s["books"]) >= MAX_BOOKS:
                fail("library_limit", "本版书架最多40本书；请使用另一个专用工作目录。")
            if not data:
                fail("invalid_text", "输入文件为空。")
            if data.startswith(b"PK"):
                book = parse_epub(data)
            elif source.suffix.lower() == ".txt":
                book = parse_txt(data, inputs.get("encoding", "utf-8"))
            else:
                fail("unsupported_format", "仅接受TXT文本或有正确EPUB内容的ZIP书籍。")
            title = book.get("title") or source.stem[:200]
            raw = encode(book)
            used = sum(p.lstat().st_size for p in (root / "books").rglob("*") if p.is_file() and not p.is_symlink())
            if used + len(data) + len(raw) > MAX_STORE:
                fail("store_limit", "书架副本总量超过128MiB上限。")
            target = root / "books" / bid
            if target.exists() or target.is_symlink():
                fail("orphan_copy", "存在未登记的同名书籍副本；未覆盖，请检查状态。")
            stage = Path(tempfile.mkdtemp(prefix=".import-", dir=root / "books"))
            published = False
            try:
                for name, content in (("original", data), ("book.json", raw)):
                    fd = os.open(stage / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                    with os.fdopen(fd, "wb") as f:
                        f.write(content); f.flush(); os.fsync(f.fileno())
                os.rename(stage, target); published = True
                entry = {"book_id": bid, "source_sha256": bid, "parsed_sha256": sha(raw), "title": title, "original_name": source.name, "author": book["author"], "format": book["format"], "encoding": book["encoding"], "chapter_count": len(book["chapters"]), "warnings": book["warnings"], "progress": {"chapter_index": 0, "offset_ratio": 0, "updated_at": time.time()}}
                s["books"][bid] = entry
                save_state(root, s)
            except BaseException:
                if published:
                    shutil.rmtree(target)
                raise
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
            return result(reused=False, book=entry, revision=s["revision"], message="已导入私有副本，原文件未修改；请查看导入说明。")
        if action == "preferences":
            checked_revision(s, inputs.get("expected_revision"))
            prefs = inputs.get("preferences")
            if not isinstance(prefs, dict) or set(prefs) != set(DEFAULT_PREFS):
                fail("invalid_preferences", "设置须包含font_size、line_height、width、theme。")
            if type(prefs["font_size"]) is not int or not 16 <= prefs["font_size"] <= 32 or type(prefs["width"]) is not int or not 480 <= prefs["width"] <= 1100 or type(prefs["line_height"]) not in (int, float) or not 1.3 <= prefs["line_height"] <= 2.5 or prefs["theme"] not in ("paper", "light", "dark"):
                fail("invalid_preferences", "字号16～32，行距1.3～2.5，宽度480～1100，主题paper/light/dark。")
            s["preferences"] = prefs; save_state(root, s)
            return shelf_view(s)
        bid = inputs.get("book_id"); book = book_data(root, s, bid)
        if action == "toc":
            return result(book=s["books"][bid], revision=s["revision"], chapters=[{"chapter_index": i, "title": c["title"], "characters": len(c["text"])} for i, c in enumerate(book["chapters"])], message="目录按TXT切章或EPUB主序列顺序返回。")
        checked_revision(s, inputs.get("expected_revision"))
        index, ratio = inputs.get("chapter_index"), inputs.get("offset_ratio")
        if type(index) is not int or not 0 <= index < len(book["chapters"]) or type(ratio) not in (int, float) or not math.isfinite(ratio) or not 0 <= ratio <= 1:
            fail("invalid_progress", "章节下标或章内比例无效；比例须在0～1之间。")
        s["books"][bid]["progress"] = {"chapter_index": index, "offset_ratio": ratio, "updated_at": time.time()}
        s["current_book"] = bid; save_state(root, s)
        return shelf_view(s)


def read_chapter(inputs):
    if set(inputs) - {"workspace", "book_id", "chapter_index", "start_char", "max_chars"}:
        fail("invalid_input", "存在不支持的阅读参数。")
    root = state_dir(inputs.get("workspace"))
    if not root.exists():
        fail("library_missing", "书架尚未创建。")
    with locked(root):
        s = load_state(root); book = book_data(root, s, inputs.get("book_id"))
        index, start, count = inputs.get("chapter_index"), inputs.get("start_char", 0), inputs.get("max_chars", 20000)
        if type(index) is not int or not 0 <= index < len(book["chapters"]):
            fail("chapter_missing", "章节下标不存在。")
        chapter = book["chapters"][index]
        if type(start) is not int or not 0 <= start <= len(chapter["text"]) or type(count) is not int or not 1 <= count <= 40000:
            fail("invalid_range", "字符起点须在正文内，max_chars须为1～40000。")
        end = min(start + count, len(chapter["text"]))
        return result(book_id=inputs["book_id"], source_sha256=inputs["book_id"], chapter_index=index, title=chapter["title"], text=chapter["text"][start:end], start_char=start, end_char=end, total_characters=len(chapter["text"]), truncated=end < len(chapter["text"]), next_char=end if end < len(chapter["text"]) else None, warnings=book["warnings"], message="返回实际纯文本片段，不是摘要或改写。")


def dispatch(operation, inputs):
    try:
        if not isinstance(inputs, dict):
            fail("invalid_input", "参数须为JSON对象。")
        if operation == "library": return library(inputs)
        if operation == "read": return read_chapter(inputs)
        if operation == "reader": return control(inputs)
        fail("invalid_action", "未知工具操作。")
    except ReaderError as e:
        return {"ok": False, "version": VERSION, "error": {"code": e.code, "message": str(e)}}
    except BlockingIOError:
        return {"ok": False, "version": VERSION, "error": {"code": "busy", "message": "书架正在处理另一项操作，请稍后重试。"}}
    except (OSError, ValueError, KeyError, TypeError, RecursionError, NotImplementedError) as e:
        return {"ok": False, "version": VERSION, "error": {"code": "operation_failed", "message": "文件、格式、权限或状态无效；未确认操作成功。", "exception_type": type(e).__name__}}


def local_request(info, endpoint, body=None):
    url = info.get("url", "")
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}/[A-Za-z0-9_-]{43}/", url):
        fail("invalid_session", "本地阅读器地址损坏，未连接。")
    req = Request(url + "api/" + endpoint, data=None if body is None else encode(body), headers={"Content-Type": "application/json"})
    with build_opener(ProxyHandler({})).open(req, timeout=3) as response:
        return json.loads(response.read(16 * 1024 * 1024))


def control(inputs):
    if set(inputs) - {"workspace", "action", "confirmed"} or inputs.get("action") not in ("start", "status", "stop"):
        fail("invalid_action", "阅读器操作仅支持start、status、stop和workspace、confirmed参数。")
    action = inputs["action"]
    if action != "status" and inputs.get("confirmed") is not True:
        fail("confirmation_required", "启动或关闭本机阅读器需要明确授权。")
    root = state_dir(inputs.get("workspace"), create=action == "start")
    if not root.exists():
        return result(running=False, message="此工作目录没有运行的阅读器。")
    with locked(root, "control.lock"):
        p = root / "session.json"
        info = read_json(p) if p.exists() or p.is_symlink() else None
        alive = False
        if info:
            try:
                h = local_request(info, "health")
                alive = h.get("plugin") == SLUG and h.get("version") == VERSION and h.get("session_id") == info.get("session_id") and h.get("workspace_key") == sha(str(root).encode())
            except Exception:
                pass
        if action == "stop":
            if alive:
                local_request(info, "stop", {})
                for _ in range(40):
                    if read_json(p).get("status") == "stopped": break
                    time.sleep(.05)
                else: fail("stop_pending", "已请求关闭，但尚未确认完成，请稍后查询。")
            return result(running=False, message="此工作目录的阅读器已关闭或未运行；书籍与阅读位置保留。")
        if action == "start" and not alive:
            sid = secrets.token_hex(12)
            logfd = os.open(root / ("start-" + sid + ".log"), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(logfd, "wb") as log:
                proc = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--serve"], stdin=subprocess.PIPE, stdout=log, stderr=log, start_new_session=True, cwd=str(root), env={"PATH": "/usr/bin:/bin", "LANG": "zh_CN.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"})
            proc.stdin.write(encode({"workspace": inputs["workspace"], "session_id": sid})); proc.stdin.close()
            for _ in range(80):
                if proc.poll() is not None:
                    fail("start_failed", "阅读器启动失败，请检查本书架的私有启动日志；未终止其他进程。")
                try:
                    candidate = read_json(p)
                    if candidate.get("session_id") == sid and local_request(candidate, "health").get("session_id") == sid:
                        info, alive = candidate, True; break
                except Exception:
                    pass
                time.sleep(.05)
            if not alive:
                proc.terminate()
                with contextlib.suppress(subprocess.TimeoutExpired): proc.wait(timeout=2)
                fail("start_timeout", "本次创建的阅读器启动超时。")
            threading.Thread(target=proc.wait, daemon=True).start()
        if not alive:
            return result(running=False, message="没有可验证的运行会话，未终止任何进程。")
        return result(running=True, display_name=NAME, url=info["url"], session_id=info["session_id"], message="在独立浏览器标签页打开完整地址。地址含本机访问凭据，请勿分享；仅本机监听，30分钟空闲后关闭。启动成功不等于人工阅读测试通过。")


def serve(config):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    root = state_dir(config["workspace"])
    lifetime = os.open(root / "server.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lifetime, fcntl.LOCK_EX | fcntl.LOCK_NB)
    token = secrets.token_urlsafe(32); prefix = "/" + token + "/"
    assets = Path(__file__).resolve().parents[1] / "assets"
    static = {"": ("page.html", "text/html"), "app.js": ("app.js", "text/javascript"), "style.css": ("style.css", "text/css")}
    last = [time.monotonic()]; birth = last[0]
    sid = config["session_id"]; workspace_key = sha(str(root).encode())
    class Handler(BaseHTTPRequestHandler):
        server_version = "OfflineReader"; sys_version = ""
        def log_message(self, *args): pass
        def send_error(self, code, *args): self.output({"ok": False, "message": "HTTP请求格式或方法不支持。"}, code)
        def output(self, value, status=200, mime="application/json"):
            data = value if isinstance(value, bytes) else encode(value)
            self.send_response(status)
            for key, val in {"Content-Type": mime + "; charset=utf-8", "Content-Length": str(len(data)), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Cross-Origin-Resource-Policy": "same-origin", "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"}.items(): self.send_header(key, val)
            self.end_headers(); self.wfile.write(data)
        def do_GET(self): self.route_safe()
        def do_POST(self): self.route_safe()
        def route_safe(self):
            self.connection.settimeout(10)
            try: self.route()
            except (BrokenPipeError, ConnectionResetError, TimeoutError): pass
            except Exception: self.output({"ok": False, "message": "请求失败，未确认成功。"}, 400)
        def route(self):
            host = "127.0.0.1:" + str(self.server.server_port)
            if self.headers.get("Host") != host or self.headers.get("Origin") not in (None, "http://" + host) or self.headers.get("Sec-Fetch-Site") == "cross-site" and not (self.command == "GET" and self.path == prefix and self.headers.get("Sec-Fetch-Mode") == "navigate"):
                self.output({"ok": False, "message": "拒绝跨站或非本机主机请求。"}, 403); return
            if not self.path.startswith(prefix) or "?" in self.path or "#" in self.path:
                self.output({"ok": False, "message": "会话地址无效。"}, 404); return
            endpoint = self.path[len(prefix):]; last[0] = time.monotonic()
            if self.command == "GET":
                if endpoint in static:
                    name, mime = static[endpoint]; self.output((assets / name).read_bytes(), mime=mime); return
                if endpoint == "api/health": self.output(result(plugin=SLUG, session_id=sid, workspace_key=workspace_key)); return
                if endpoint == "api/library": self.output(dispatch("library", {"workspace": config["workspace"], "action": "list"})); return
            if self.command != "POST" or not self.headers.get("Content-Type", "").startswith("application/json") or self.headers.get("Transfer-Encoding"):
                self.output({"ok": False, "message": "仅接受本机JSON操作。"}, 415); return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 <= length <= 8192: raise ValueError()
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict): raise ValueError()
            except ValueError:
                self.output({"ok": False, "message": "JSON长度或内容无效。"}, 400); return
            if endpoint == "api/stop":
                self.output(result(message="阅读器正在关闭，书架状态保留。")); threading.Thread(target=self.server.shutdown, daemon=True).start(); return
            if endpoint == "api/book" and set(body) == {"book_id"}:
                with locked(root):
                    s = load_state(root); book = book_data(root, s, body["book_id"])
                    self.output(result(book=s["books"][body["book_id"]], chapters=book["chapters"], revision=s["revision"], preferences=s["preferences"]))
                return
            if endpoint == "api/save" and body.get("action") in ("progress", "preferences") and "workspace" not in body and "confirmed" not in body:
                self.output(dispatch("library", {**body, "workspace": config["workspace"], "confirmed": True})); return
            self.output({"ok": False, "message": "不支持此阅读器操作；导入须通过原生工具明确选择路径。"}, 404)
    class Server(ThreadingHTTPServer):
        daemon_threads = True; block_on_close = False; request_queue_size = 8
    server = Server(("127.0.0.1", 0), Handler)
    info = {"status": "running", "version": VERSION, "session_id": sid, "url": f"http://127.0.0.1:{server.server_port}{prefix}"}
    atomic_json(root / "session.json", info)
    def timer():
        while time.monotonic() - last[0] < 1800 and time.monotonic() - birth < 14400:
            time.sleep(2)
        server.shutdown()
    threading.Thread(target=timer, daemon=True).start()
    try: server.serve_forever(poll_interval=.1)
    finally:
        server.server_close(); info["status"] = "stopped"; atomic_json(root / "session.json", info); os.close(lifetime)


if __name__ == "__main__":
    if sys.argv[1:] == ["--serve"]:
        serve(json.loads(sys.stdin.readline(8192)))
    else:
        parser = argparse.ArgumentParser(description="离线书架阅读器：导入副本、目录、正文、阅读位置和本机界面。")
        parser.add_argument("operation", choices=["library", "read", "reader"], help="原生工具类别")
        parser.add_argument("--input-json", required=True, help="JSON对象；路径使用真实绝对路径")
        args = parser.parse_args(); out = dispatch(args.operation, json.loads(args.input_json))
        print(json.dumps(out, ensure_ascii=False, indent=2)); sys.exit(0 if out["ok"] else 2)
