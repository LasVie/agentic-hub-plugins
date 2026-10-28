#!/usr/bin/env python3
"""Word 引用脚注转换：离线检查、精确计划与经确认的新 DOCX。

Ported note-part / separator / reference construction from Cite2FN 0.1.0,
https://github.com/anitasrinivasan/cite2fn at
00cc8c12c67633371a41db2a93516b9f3aff92f4, cite2fn/footnotes.py.
Copyright (c) 2026 Anita Srinivasan. MIT; full text: licenses/cite2fn/LICENSE.
Modified 2026-10-27: Chinese bounded ZIP/XML inspection, exact Unicode spans,
source-and-output-bound confirmation, preserved package parts, no inferred
short forms or bibliography deletion, and exclusive atomic new-file publication.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import io
import json
import os
import posixpath
import re
import stat
import sys
from urllib.parse import unquote, urlsplit
import uuid
import zipfile
import zlib

VERSION = "1.0.0"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
MAIN_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
MAX_DOCX, MAX_TOTAL, MAX_PART = 8 * 1024**2, 32 * 1024**2, 4 * 1024**2
MAX_JSON, MAX_ENTRIES, MAX_NOTES, MAX_PARAGRAPHS = 512 * 1024, 256, 100, 200
SHA = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[a-z][a-z0-9_-]{0,47}\Z")
BOUNDARY = "只转换明确支持的正文段落和用户确认的精确文字；不推断文献真实性、Bluebook正确性或法律资格，不抓取网络，不自动删除参考文献。"


class Failure(Exception):
    def __init__(self, code, message, **details):
        self.code, self.message, self.details = code, message, details


def require(condition, code, message, **details):
    if not condition:
        raise Failure(code, message, **details)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def qn(local):
    return f"{{{W}}}{local}"


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def closed(obj, allowed, required, code="invalid_input"):
    require(isinstance(obj, dict), code, "参数必须是JSON对象。")
    require(set(obj) <= set(allowed) and set(required) <= set(obj), code, "字段缺失或含不支持的字段；不会静默忽略。")


def json_object(raw):
    def pairs(values):
        obj = {}
        for key, value in values:
            require(key not in obj, "duplicate_json_key", "JSON含重复键；拒绝静默覆盖。", key=key)
            obj[key] = value
        return obj
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except Failure:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise Failure("invalid_plan", "计划必须是有界、有效的UTF-8 JSON，不接受非有限数值。")


def absolute(value):
    require(isinstance(value, str) and 1 <= len(value) <= 4096, "invalid_path", "请提供完整绝对路径。")
    require(value.startswith("/") and not any(ord(c) < 32 for c in value), "invalid_path", "路径须为POSIX绝对路径且不含控制字符。")
    bits = value.split("/")[1:]
    require(bool(bits) and len(bits) <= 64 and all(b not in ("", ".", "..") for b in bits),
            "invalid_path", "路径不能含空段、.、.. 或过多层级。")
    return bits


class Workspace:
    def __init__(self, value):
        self.root = value
        self.parts = absolute(value)
        self.fd = None

    def __enter__(self):
        require(os.name == "posix" and hasattr(os, "O_NOFOLLOW"), "unsupported_platform", "本版仅支持具有O_NOFOLLOW的macOS/Linux。")
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in self.parts:
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = nxt
        except OSError:
            os.close(fd)
            raise Failure("unsafe_path", "工作目录不存在、含链接或不能安全打开。")
        self.fd = fd
        return self

    def __exit__(self, *args):
        if self.fd is not None:
            os.close(self.fd)

    @contextmanager
    def parent(self, value):
        parts = absolute(value)
        require(parts[:len(self.parts)] == self.parts and len(parts) > len(self.parts),
                "path_outside_workspace", "文件必须位于用户指定工作目录内。")
        relative = parts[len(self.parts):]
        require(len(relative) <= 16, "invalid_path", "工作目录内的路径层级过多。")
        fd = os.dup(self.fd)
        try:
            for part in relative[:-1]:
                try:
                    nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                except OSError:
                    raise Failure("unsafe_path", "父目录不存在、含链接或不能安全打开。")
                os.close(fd)
                fd = nxt
            yield fd, relative[-1]
        finally:
            os.close(fd)

    def read(self, value, limit):
        with self.parent(value) as (fd, name):
            try:
                handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            except FileNotFoundError:
                raise Failure("input_missing", "指定输入文件不存在。")
            except OSError:
                raise Failure("unsafe_path", "输入文件含链接或不能安全打开。")
            try:
                before = os.fstat(handle)
                require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                        "unsafe_path", "只接受普通文件，不接受软链接、硬链接或设备。")
                require(before.st_size <= limit, "input_too_large", "输入文件超过本版大小上限。", limit_bytes=limit)
                pieces, count = [], 0
                while True:
                    b = os.read(handle, min(65536, limit + 1 - count))
                    if not b:
                        break
                    pieces.append(b)
                    count += len(b)
                    require(count <= limit, "input_too_large", "输入读取时超过大小上限。", limit_bytes=limit)
                after = os.fstat(handle)
                signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
                require(signature(before) == signature(after), "source_changed", "读取期间输入发生变化；请重新检查。")
                return b"".join(pieces)
            finally:
                os.close(handle)

    def check_output(self, value):
        require(isinstance(value, str) and value.lower().endswith(".docx"), "invalid_path", "输出须为新的.docx完整路径。")
        with self.parent(value) as (fd, name):
            try:
                os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return
            raise Failure("output_exists", "输出路径已存在；不能覆盖文件、目录或链接。")

    def publish(self, value, raw):
        """Write owned temporary bytes, then atomically link without overwriting."""
        with self.parent(value) as (fd, name):
            temp = ".word-notes-" + uuid.uuid4().hex + ".tmp"
            handle, published = None, False
            try:
                handle = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
                view = memoryview(raw)
                while view:
                    written = os.write(handle, view)
                    require(written > 0, "io_error", "写入未取得进展；未宣称生成成功。")
                    view = view[written:]
                os.fsync(handle)
                try:
                    os.link(temp, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
                except FileExistsError:
                    raise Failure("output_exists", "输出路径已被创建；拒绝覆盖。")
                published = True
                os.fsync(fd)
            except Failure:
                raise
            except OSError:
                if published:
                    raise Failure("partial_output", "新输出已出现，但持久写入确认失败；保留文件供人工检查，不宣称成功。", output=value)
                raise Failure("io_error", "写入失败；没有发布新输出，原件未修改。")
            finally:
                if handle is not None:
                    identity = os.fstat(handle)
                    os.close(handle)
                    try:
                        current = os.stat(temp, dir_fd=fd, follow_symlinks=False)
                        if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                            os.unlink(temp, dir_fd=fd)
                    except FileNotFoundError:
                        pass


def xml(raw, part):
    from lxml import etree
    require(not re.search(br"<!\s*(DOCTYPE|ENTITY)\b", raw, re.I), "invalid_xml", "XML含DTD或实体声明；拒绝解析。", part=part)
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                                 huge_tree=False, remove_blank_text=False)
        node = etree.fromstring(raw, parser)
        require(not node.getroottree().docinfo.doctype, "invalid_xml", "不接受XML文档类型声明。", part=part)
        return node
    except Failure:
        raise
    except (etree.XMLSyntaxError, ValueError, RecursionError):
        raise Failure("invalid_xml", "XML格式无效或超过安全解析限制。", part=part)


def serial(node):
    from lxml import etree
    return etree.tostring(node, encoding="UTF-8", xml_declaration=True, standalone=True)


def text_hash(text):
    return sha256(text.encode("utf-8"))


def read_package(raw):
    from lxml import etree
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile, OSError):
        raise Failure("invalid_archive", "输入不是有效的DOCX ZIP包。")
    parts, infos = {}, {}
    with archive:
        entries = archive.infolist()
        require(1 <= len(entries) <= MAX_ENTRIES, "archive_limit", "ZIP条目数超过上限。", max_entries=MAX_ENTRIES)
        total = 0
        for info in entries:
            name = info.filename
            require(name and info.orig_filename == name and not name.startswith("/") and "\\" not in name and not any(ord(c) < 32 for c in name),
                    "invalid_archive", "ZIP成员路径无效。")
            bits = name.rstrip("/").split("/")
            require(all(b not in ("", ".", "..") for b in bits) and len(bits) <= 16,
                    "invalid_archive", "ZIP含重复分隔、点路径或过多层级。")
            require(name not in parts and name not in infos, "invalid_archive", "ZIP含重复成员。", part=name)
            mode = (info.external_attr >> 16) & 0o170000
            require(mode in (0, stat.S_IFREG, stat.S_IFDIR), "invalid_archive", "ZIP含链接或特殊成员。")
            require(not (info.flag_bits & 1), "invalid_archive", "不接受加密DOCX ZIP成员。")
            total += info.file_size
            require(info.file_size <= MAX_PART and total <= MAX_TOTAL and
                    info.file_size <= max(info.compress_size, 1) * 100,
                    "archive_limit", "ZIP解压大小或压缩比超过上限。", part=name)
            infos[name] = info
            if info.is_dir():
                continue
            try:
                data = archive.read(info)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, zlib.error, EOFError):
                raise Failure("invalid_archive", "ZIP成员读取或校验失败。", part=name)
            require(len(data) == info.file_size, "invalid_archive", "ZIP成员实际大小不符。", part=name)
            parts[name] = data
    for required in ("[Content_Types].xml", "_rels/.rels", "word/document.xml"):
        require(required in parts, "invalid_archive", "缺少必要的DOCX部件。", part=required)
    parsed = {}
    for name, data in parts.items():
        require(not name.lower().startswith("_xmlsignatures/") and not name.lower().endswith(("vbaproject.bin", ".exe")),
                "unsupported_document", "不处理签名、宏或可执行部件。", part=name)
        if name.endswith((".xml", ".rels")):
            parsed[name] = xml(data, name)
        if re.match(r"word/(?:footnotes|endnotes|comments|header\d*|footer\d*)\.xml$", name, re.I):
            raise Failure("unsupported_document", "本版不处理已有脚注、尾注、批注、页眉或页脚部件。", part=name)
    ctypes = parsed["[Content_Types].xml"]
    require(ctypes.tag == f"{{{CT}}}Types", "invalid_archive", "Content Types根元素不正确。")
    overrides, defaults = {}, set()
    for child in ctypes:
        content_type = child.get("ContentType", "")
        require(child.tag in (f"{{{CT}}}Override", f"{{{CT}}}Default") and content_type,
                "invalid_archive", "部件内容类型声明不完整或含未知元素。")
        require(not any(v in content_type.lower() for v in ("macroenabled", "vba", "footnotes", "endnotes", "digital-signature")),
                "unsupported_document", "不接受宏、已有注释或数字签名内容类型。")
        if child.tag == f"{{{CT}}}Override":
            pn = child.get("PartName")
            require(pn and pn.startswith("/") and pn[1:] in parts and pn not in overrides,
                    "invalid_archive", "部件内容类型重复、缺失或目标不存在。")
            overrides[pn] = content_type
        else:
            extension = child.get("Extension")
            require(extension and extension not in defaults, "invalid_archive", "默认内容类型缺失或重复。")
            defaults.add(extension)
    require(overrides.get("/word/document.xml") == MAIN_CT, "unsupported_document", "仅接受标准过渡版.docx正文文档。")
    root_office = 0
    for name, tree in parsed.items():
        if not name.endswith(".rels"):
            continue
        require(tree.tag == f"{{{PKG}}}Relationships", "invalid_archive", "关系部件根元素无效。", part=name)
        base = "" if name == "_rels/.rels" else posixpath.dirname(posixpath.dirname(name))
        ids = set()
        for rel in tree:
            rid, target, reltype = rel.get("Id"), rel.get("Target"), rel.get("Type", "")
            require(rel.tag == f"{{{PKG}}}Relationship" and rid and rid not in ids and target,
                    "invalid_archive", "关系ID、类型或目标缺失/重复。", part=name)
            ids.add(rid)
            require(rel.get("TargetMode", "Internal") in ("Internal", "External"), "invalid_archive", "关系目标模式不支持。")
            if rel.get("TargetMode") == "External":
                require(reltype == R + "/hyperlink" and urlsplit(target).scheme in ("http", "https", "mailto"),
                        "unsupported_document", "仅允许普通超链接外部关系；不加载外部模板、图片或数据。", part=name)
                continue
            require(not urlsplit(target).scheme and not target.startswith("/") and "\\" not in target,
                    "invalid_archive", "内部关系目标无效。")
            resolved = posixpath.normpath(posixpath.join(base, unquote(target)))
            require(not resolved.startswith("../") and resolved in parts, "invalid_archive", "内部关系指向缺失或越界部件。", part=name)
            if name == "_rels/.rels" and reltype == R + "/officeDocument":
                require(resolved == "word/document.xml", "unsupported_document", "不支持非标准正文位置。")
                root_office += 1
    require(root_office == 1, "invalid_archive", "包须含唯一标准正文关系。")
    for tree in parsed.values():
        require(not tree.xpath(".//w:footnotePr|.//w:endnotePr", namespaces={"w": W}),
                "unsupported_document", "已有脚注/尾注编号设置不受支持；不会自动改写。")
    document = parsed["word/document.xml"]
    require(document.tag == qn("document"), "unsupported_document", "仅支持标准WordprocessingML命名空间。")
    require(all(t.getparent() is not None and t.getparent().tag == qn("r") and not len(t)
                for t in document.iter(qn("t"))), "unsupported_document", "文字须为普通文字行中的直接文本节点。")
    bodies = document.findall(qn("body"))
    require(len(bodies) == 1, "invalid_archive", "文档须含唯一正文。")
    body = bodies[0]
    require(all(e.tag in (qn("p"), qn("sectPr")) for e in body), "unsupported_document", "本版只处理顶层正文段落；表格、文本框及其他正文容器不受支持。")
    sections = body.findall(qn("sectPr"))
    require(len(sections) <= 1 and (not sections or body[-1] is sections[0]),
            "unsupported_document", "只支持位于正文末尾的单一节设置。")
    require(not document.xpath(".//w:pPr/w:sectPr", namespaces={"w": W}), "unsupported_document", "不支持段落内分节设置。")
    paragraphs = []
    rels = parsed.get("word/_rels/document.xml.rels")
    docrels = {r.get("Id"): r for r in rels} if rels is not None else {}
    elements = body.findall(qn("p"))
    require(len(elements) <= MAX_PARAGRAPHS, "archive_limit", "正文段落数超过上限。", max_paragraphs=MAX_PARAGRAPHS)
    for number, paragraph in enumerate(elements, 1):
        require(all(c.tag in (qn("pPr"), qn("r"), qn("hyperlink")) for c in paragraph),
                "unsupported_document", "段落含书签、修订、字段或其他未支持节点。", paragraph_id=f"p{number:04d}")
        require(len(paragraph.findall(qn("pPr"))) <= 1, "invalid_archive", "段落属性节点重复。")
        for child in paragraph:
            if child.tag == qn("pPr"):
                require(not child.xpath(".//w:pPrChange|.//w:sectPr", namespaces={"w": W}), "unsupported_document", "不支持修订或分节属性。")
                continue
            if child.tag == qn("hyperlink"):
                require(all(c.tag == qn("r") for c in child), "unsupported_document", "仅支持含普通文字行的超链接。")
                rid = child.get(f"{{{R}}}id")
                require((rid in docrels and docrels[rid].get("Type") == R + "/hyperlink") or
                        (rid is None and bool(child.get(qn("anchor")))), "invalid_archive", "超链接缺少有效关系或锚点。")
                runs = list(child)
            else:
                runs = [child]
            for run in runs:
                require(all(n.tag in (qn("rPr"), qn("t")) for n in run) and len(run.findall(qn("rPr"))) <= 1,
                        "unsupported_document", "文字行含字段、图像、制表符、换行或其他未支持节点。", paragraph_id=f"p{number:04d}")
                require(not run.xpath(".//w:rPrChange|.//w:ins|.//w:del", namespaces={"w": W}), "unsupported_document", "不支持文字修订。")
        text = "".join(paragraph.xpath(".//w:t/text()", namespaces={"w": W}))
        require(len(text) <= 20000, "archive_limit", "单段文字过长。")
        paragraphs.append({"id": f"p{number:04d}", "text": text, "sha256": text_hash(text)})
    require(sum(len(p["text"]) for p in paragraphs) <= 200000, "archive_limit", "正文文字总量超过上限。")
    return {"parts": parts, "infos": infos, "parsed": parsed, "document": document,
            "paragraphs": paragraphs, "elements": elements, "body": body}


def plan_actions(plan, package, source_sha):
    closed(plan, ("schema_version", "source_sha256", "notes_kind", "notes"),
           ("schema_version", "source_sha256", "notes_kind", "notes"), "invalid_plan")
    require(type(plan["schema_version"]) is int and plan["schema_version"] == 1, "invalid_plan", "只支持schema_version=1。")
    require(isinstance(plan["source_sha256"], str) and SHA.fullmatch(plan["source_sha256"]), "invalid_plan", "source_sha256须为完整小写SHA-256。")
    require(plan["source_sha256"] == source_sha, "source_changed", "源DOCX与计划确认的摘要不同；请重新检查并取得确认。")
    require(plan["notes_kind"] in ("footnote", "endnote"), "invalid_plan", "notes_kind须为footnote或endnote。")
    notes = plan["notes"]
    require(isinstance(notes, list) and 1 <= len(notes) <= MAX_NOTES, "invalid_plan", "计划须含1至100条明确注释。")
    by_id = {p["id"]: (i, p) for i, p in enumerate(package["paragraphs"])}
    seen, actions = set(), []
    fields = ("id", "paragraph_id", "start", "end", "quote", "note_text", "body_action")
    for n in notes:
        closed(n, fields, fields, "invalid_plan")
        require(isinstance(n["id"], str) and ID.fullmatch(n["id"]) and n["id"] not in seen, "invalid_plan", "注释ID须唯一且符合格式。")
        seen.add(n["id"])
        require(isinstance(n["paragraph_id"], str) and n["paragraph_id"] in by_id, "invalid_plan", "paragraph_id不是实际检查返回的段落ID。")
        index, paragraph = by_id[n["paragraph_id"]]
        a, b = n["start"], n["end"]
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(paragraph["text"]), "invalid_plan", "跨度须为段落内非空Unicode字符范围，end不包含在内。")
        require(isinstance(n["quote"], str) and n["quote"] == paragraph["text"][a:b], "span_mismatch", "quote与实际精确跨度不符；不会按年份或子串猜测位置。", id=n["id"])
        require(n["body_action"] in ("replace", "append"), "invalid_plan", "body_action须明确为replace或append。")
        text = n["note_text"]
        require(isinstance(text, str) and 1 <= len(text) <= 4000 and bool(text.strip()) and
                all((ord(c) >= 32 and not 0xD800 <= ord(c) <= 0xDFFF and ord(c) not in (0xFFFE, 0xFFFF)) for c in text),
                "invalid_plan", "note_text须为1至4000个有效单行文字字符，不解释Markdown或格式标记。")
        actions.append({**n, "paragraph_index": index})
    actions.sort(key=lambda x: (x["paragraph_index"], x["start"], x["end"], x["id"]))
    for first, second in zip(actions, actions[1:]):
        require(first["paragraph_index"] != second["paragraph_index"] or first["end"] <= second["start"],
                "overlapping_spans", "同一段落的注释范围重叠；请明确不相交的范围。")
    for index, action in enumerate(actions, 1):
        action["note_id"] = index
    return actions


def make_reference(note_id, kind, internal=False):
    from lxml import etree
    run = etree.Element(qn("r"))
    rpr = etree.SubElement(run, qn("rPr"))
    etree.SubElement(rpr, qn("vertAlign")).set(qn("val"), "superscript")
    reference = etree.SubElement(run, qn(kind + ("Ref" if internal else "Reference")))
    if not internal:
        reference.set(qn("id"), str(note_id))
    return run


def make_notes(actions, kind):
    """Adapted Cite2FN separator / note / reference element construction."""
    from lxml import etree
    root = etree.Element(qn(kind + "s"), nsmap={"w": W})
    for note_id, separator in ((-1, "separator"), (0, "continuationSeparator")):
        note = etree.SubElement(root, qn(kind))
        note.set(qn("id"), str(note_id))
        note.set(qn("type"), separator)
        p = etree.SubElement(note, qn("p"))
        r = etree.SubElement(p, qn("r"))
        etree.SubElement(r, qn(separator))
    for action in actions:
        note = etree.SubElement(root, qn(kind))
        note.set(qn("id"), str(action["note_id"]))
        p = etree.SubElement(note, qn("p"))
        p.append(make_reference(action["note_id"], kind, True))
        run = etree.SubElement(p, qn("r"))
        rpr = etree.SubElement(run, qn("rPr"))
        etree.SubElement(rpr, qn("sz")).set(qn("val"), "20")
        text = etree.SubElement(run, qn("t"))
        text.set(XML_SPACE, "preserve")
        text.text = " " + action["note_text"]
    return serial(root)


def rewrite_paragraph(paragraph, actions, kind):
    """Keep original run properties, splitting only at approved codepoint edges."""
    from lxml import etree
    segments, empty, offset = [], [], 0
    for node in paragraph:
        if node.tag == qn("pPr"):
            continue
        runs = list(node) if node.tag == qn("hyperlink") else [node]
        for run in runs:
            text = "".join(t.text or "" for t in run.findall(qn("t")))
            wrapper = node if node.tag == qn("hyperlink") else None
            if text:
                segments.append((offset, offset + len(text), run, wrapper, text))
            else:
                empty.append((offset, run, wrapper))
            offset += len(text)
    removed = [(a["start"], a["end"]) for a in actions if a["body_action"] == "replace"]
    insertions = {}
    for action in actions:
        pos = action["start"] if action["body_action"] == "replace" else action["end"]
        insertions.setdefault(pos, []).append(action)
    boundaries = {0, offset}
    for start, end, *_ in segments:
        boundaries.update((start, end))
    for action in actions:
        boundaries.update((action["start"], action["end"]))
    for pos, *_ in empty:
        boundaries.add(pos)
    boundaries = sorted(boundaries)
    for child in list(paragraph):
        if child.tag != qn("pPr"):
            paragraph.remove(child)

    def append_run(run, wrapper):
        if wrapper is None:
            paragraph.append(run)
        else:
            link = etree.Element(wrapper.tag, attrib=dict(wrapper.attrib), nsmap=wrapper.nsmap)
            link.append(run)
            paragraph.append(link)

    for index, position in enumerate(boundaries):
        for pos, run, wrapper in empty:
            if pos == position:
                append_run(deepcopy(run), wrapper)
        for action in insertions.get(position, []):
            paragraph.append(make_reference(action["note_id"], kind))
        if index + 1 == len(boundaries):
            continue
        end = boundaries[index + 1]
        if any(start <= position and end <= stop for start, stop in removed):
            continue
        for start, stop, source_run, wrapper, text in segments:
            if start <= position and end <= stop:
                run = deepcopy(source_run)
                for child in list(run):
                    if child.tag != qn("rPr"):
                        run.remove(child)
                node = etree.SubElement(run, qn("t"))
                node.set(XML_SPACE, "preserve")
                node.text = text[position-start:end-start]
                append_run(run, wrapper)
                break


def assemble(package, actions, kind):
    from lxml import etree
    grouped = {}
    for action in actions:
        grouped.setdefault(action["paragraph_index"], []).append(action)
    for index, group in grouped.items():
        rewrite_paragraph(package["elements"][index], group, kind)
    section = package["body"].find(qn("sectPr"))
    if section is None:
        section = etree.SubElement(package["body"], qn("sectPr"))
    note_pr = etree.Element(qn(kind + "Pr"))
    etree.SubElement(note_pr, qn("numFmt")).set(qn("val"), "decimal")
    etree.SubElement(note_pr, qn("numStart")).set(qn("val"), "1")
    etree.SubElement(note_pr, qn("numRestart")).set(qn("val"), "continuous")
    # sectPr sequence puts note properties before page size/margins/type.
    at = 0
    while at < len(section) and section[at].tag in (qn("headerReference"), qn("footerReference")):
        at += 1
    section.insert(at, note_pr)
    relations = package["parsed"].get("word/_rels/document.xml.rels")
    if relations is None:
        relations = etree.Element(f"{{{PKG}}}Relationships", nsmap={None: PKG})
    existing = {r.get("Id") for r in relations}
    number = 1
    while f"rIdWordNotes{number}" in existing:
        number += 1
    relationship = etree.SubElement(relations, f"{{{PKG}}}Relationship")
    relationship.set("Id", f"rIdWordNotes{number}")
    relationship.set("Type", R + "/" + kind + "s")
    relationship.set("Target", kind + "s.xml")
    types = package["parsed"]["[Content_Types].xml"]
    override = etree.SubElement(types, f"{{{CT}}}Override")
    override.set("PartName", "/word/" + kind + "s.xml")
    override.set("ContentType", "application/vnd.openxmlformats-officedocument.wordprocessingml." + kind + "s+xml")
    changed = {"word/document.xml": serial(package["document"]),
               "word/_rels/document.xml.rels": serial(relations),
               "[Content_Types].xml": serial(types),
               "word/" + kind + "s.xml": make_notes(actions, kind)}
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, info in package["infos"].items():
            if info.is_dir():
                archive.writestr(deepcopy(info), b"")
            else:
                archive.writestr(deepcopy(info), changed.get(name, package["parts"][name]))
        for name in sorted(set(changed) - set(package["parts"])):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system, info.external_attr = 3, 0o100644 << 16
            archive.writestr(info, changed[name])
    return output.getvalue(), sorted(changed)


def prepare(workspace, inputs):
    path = inputs["path"]
    require(isinstance(path, str) and path.lower().endswith(".docx"), "invalid_path", "输入须为.docx完整路径。")
    raw = workspace.read(path, MAX_DOCX)
    package = read_package(raw)
    source_sha = sha256(raw)
    if "plan_path" not in inputs:
        return raw, package, {"source_sha256": source_sha, "source_bytes": len(raw),
            "paragraph_count": len(package["paragraphs"]), "paragraphs": package["paragraphs"],
            "notes_supported": ["footnote", "endnote"], "writes_performed": False,
            "supported": True, "boundary": BOUNDARY}
    plan_raw = workspace.read(inputs["plan_path"], MAX_JSON)
    plan = json_object(plan_raw)
    actions = plan_actions(plan, package, source_sha)
    workspace.check_output(inputs["output"])
    plan_sha = sha256(plan_raw)
    review = {"source_sha256": source_sha, "source_bytes": len(raw), "plan_sha256": plan_sha,
              "notes_kind": plan["notes_kind"], "note_count": len(actions),
              "actions": actions, "output": inputs["output"], "boundary": BOUNDARY}
    binding = {"schema_version": 1, "workspace": workspace.root, "path": path,
               "plan_path": inputs["plan_path"], "plan": plan, **review}
    review["preview_sha256"] = sha256(canonical(binding))
    review["writes_performed"] = False
    return raw, package, review


def dispatch(operation, inputs):
    try:
        require(operation in ("inspect", "preview", "apply"), "invalid_input", "操作须为inspect、preview或apply。")
        allowed = {"workspace", "path"}
        needed = set(allowed)
        if operation != "inspect":
            allowed |= {"plan_path", "output"}
            needed = set(allowed)
        if operation == "apply":
            allowed |= {"confirmed", "expected_preview_sha256"}
        closed(inputs, allowed, needed)
        if operation == "apply":
            require(inputs.get("confirmed") is True, "confirmation_required", "须先展示完整预览并取得用户明确确认，再执行转换。")
            require(isinstance(inputs.get("expected_preview_sha256"), str) and SHA.fullmatch(inputs["expected_preview_sha256"]),
                    "invalid_input", "请提供实际返回且用户已确认的完整preview_sha256。")
        with Workspace(inputs["workspace"]) as workspace:
            raw, package, result = prepare(workspace, inputs)
            if operation == "apply":
                require(inputs["expected_preview_sha256"] == result["preview_sha256"], "preview_changed", "计划、源文件或输出与已确认预览不同；请重新预览并取得确认。")
                output, changed = assemble(package, result["actions"], result["notes_kind"])
                # A changed source or plan is not automatically adopted after XML construction.
                require(sha256(workspace.read(inputs["path"], MAX_DOCX)) == result["source_sha256"] and
                        sha256(workspace.read(inputs["plan_path"], MAX_JSON)) == result["plan_sha256"],
                        "source_changed", "生成期间源文件或计划发生变化；未发布输出。")
                workspace.publish(inputs["output"], output)
                result.update({"writes_performed": True, "output_sha256": sha256(output), "output_bytes": len(output),
                    "report": {"message": "已按确认计划创建新的Word注释文档；原文件与未选部件保留。",
                        "notes_kind": result["notes_kind"], "note_count": result["note_count"],
                        "numbering": "按正文位置从1开始连续十进制编号，保留引用文字由body_action明确决定。",
                        "changed_parts": changed, "unchanged_part_count": len(set(package["parts"]) - set(changed)),
                        "bibliography_removed": False, "short_forms_inferred": False,
                        "publication": "完成暂存后排他原子发布；不覆盖已有路径。",
                        "visual_review_required": True, "boundary": BOUNDARY}})
            return {"ok": True, "version": VERSION, **result}
    except Failure as error:
        return {"ok": False, "version": VERSION, "error": {"code": error.code, "message": error.message, **error.details}}
    except ImportError:
        return {"ok": False, "version": VERSION, "error": {"code": "dependency_missing", "message": "缺少外部lxml依赖；请按中文安装说明配置，不伪称执行成功。"}}
    except OSError:
        return {"ok": False, "version": VERSION, "error": {"code": "io_error", "message": "文件操作失败；请检查路径和权限，不宣称生成成功。"}}
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return {"ok": False, "version": VERSION, "error": {"code": "invalid_input", "message": "输入、路径或文档结构无效，未宣称转换成功。"}}


class ChineseParser(argparse.ArgumentParser):
    def format_help(self):
        return super().format_help().replace("usage:", "用法：", 1)

    def error(self, message):
        result = {"ok": False, "version": VERSION,
                  "error": {"code": "invalid_input", "message": "命令行参数缺失或不支持；请使用--help查看中文用法。"}}
        self.exit(2, json.dumps(result, ensure_ascii=False) + "\n")


def main():
    parser = ChineseParser(description="Word引用脚注转换：先只读检查和预览，明确确认后创建新DOCX。",
                           usage="%(prog)s {inspect,preview,apply} --input-json JSON", add_help=False)
    parser._positionals.title, parser._optionals.title = "位置参数", "选项"
    parser.add_argument("-h", "--help", action="help", help="显示中文用法并退出")
    parser.add_argument("operation", choices=("inspect", "preview", "apply"), help="inspect检查；preview预览；apply经确认转换")
    parser.add_argument("--input-json", required=True, help="完整JSON参数文本，文件参数均使用工作目录内绝对路径")
    try:
        options = parser.parse_args()
        require(len(options.input_json.encode("utf-8")) <= MAX_JSON, "input_too_large", "参数JSON超过上限。")
        values = json_object(options.input_json.encode("utf-8"))
        result = dispatch(options.operation, values)
    except Failure as error:
        result = {"ok": False, "version": VERSION, "error": {"code": error.code, "message": error.message}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
