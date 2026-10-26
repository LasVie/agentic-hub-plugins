#!/usr/bin/env python3
"""原文快照与精简预览；Python 3.11+，仅 POSIX 本地文件。

Ported workflow/preview algorithms from dsh-plugin-save-token 2.4.1,
Copyright (c) 2026 PlayWithAI, MIT. See licenses/save-token/LICENSE and
UPSTREAM_HEADER.txt. Modified 2026-10-23: Python implementation, immutable
verified bytes, durable IDs, accurate coordinates, typed preview cells,
exclusive exports, Chinese results; no host hooks/shell/pruning/metering.
"""
import argparse
from contextlib import contextmanager
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

VERSION = "1.0.1"
STATE = ".source-preview-recovery"
MAGIC = b"SPR1\x00"
MAX_BYTES = 8 * 1024 * 1024
MAX_STORE = 64 * 1024 * 1024
MAX_FILES = 128
MAX_RANGE_BYTES = 65536
MAX_LINES = 200000
ID_RE = re.compile(r"sha256-([0-9a-f]{64})\Z")
ERROR_RE = re.compile(r"fatal|panic|traceback|exception|\berror\b|fail(?:ed|ure)?|denied|timeout|错误|失败|异常|超时", re.I)


class Failure(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


def require(ok, code, message):
    if not ok:
        raise Failure(code, message)


def integer(value, default, lo, hi):
    if value is None:
        return default
    require(type(value) is int and lo <= value <= hi, "invalid_argument", f"整数参数必须在 {lo}～{hi} 范围内，不能使用布尔值。")
    return value


def absolute(value):
    require(isinstance(value, str) and value.startswith("/") and ".." not in value.split("/") and "\x00" not in value,
            "unsafe_path", "必须使用不含 .. 的真实绝对路径；不支持符号链接。")
    return Path(value)


def directory(p):
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def workspace(value):
    p = absolute(value)
    require(p != Path("/"), "unsafe_path", "不能把文件系统根目录作为工作目录。")
    return p


def child_parts(root, value):
    p = absolute(value)
    try:
        parts = p.relative_to(root).parts
    except ValueError:
        raise Failure("outside_workspace", "输入或输出必须位于明确指定的工作目录内。")
    require(parts and parts[0] != STATE, "unsafe_path", "不能选择工作目录本身或插件内部快照目录。")
    return parts


@contextmanager
def parent_fd(root, value):
    parts = child_parts(root, value)
    fd = directory(root)
    try:
        for part in parts[:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        yield fd, parts[-1]
    finally:
        os.close(fd)


def regular(fd):
    s = os.fstat(fd)
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe_file", "只接受普通且没有硬链接的文件。")
    return s


def read_fd(fd, limit):
    chunks, count = [], 0
    while True:
        b = os.read(fd, min(65536, limit + 1 - count))
        if not b:
            return b"".join(chunks)
        chunks.append(b)
        count += len(b)
        require(count <= limit, "size_limit", "文件超过大小上限；不会只保存截断前缀。")


def decode(raw):
    require(b"\x00" not in raw, "invalid_utf8", "输入包含 NUL 字节，不作为 UTF-8 文本处理。")
    count = raw.count(b"\r") + raw.count(b"\n") - raw.count(b"\r\n") + int(bool(raw) and not raw.endswith((b"\r", b"\n")))
    require(count <= MAX_LINES, "line_limit", "单文件最多 200000 个物理源行；不会截断后保存。")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise Failure("invalid_utf8", "输入不是有效 UTF-8；请先显式转换编码，原文件未修改。")


def lines_of(text):
    # Only CR, LF, CRLF are physical source lines. Unicode separators are data.
    parts = re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", text)
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def source_bytes(root, path):
    with parent_fd(root, path) as (parent, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = regular(fd)
            require(before.st_size <= MAX_BYTES, "size_limit", "单文件最多 8 MiB；不会截断后伪称完整快照。")
            raw = read_fd(fd, MAX_BYTES)
            after = os.fstat(fd)
            require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                    and len(raw) == before.st_size, "source_changed", "读取期间源文件发生变化，请在文件稳定后重试。")
            decode(raw)
            return raw
        finally:
            os.close(fd)


@contextmanager
def store(root, create=False):
    require(os.name == "posix", "unsupported_platform", "此版本仅支持 macOS/Linux。")
    import fcntl
    wfd, sfd, lock = directory(root), None, None
    try:
        if create:
            try:
                os.mkdir(STATE, 0o700, dir_fd=wfd)
            except FileExistsError:
                pass
        try:
            sfd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=wfd)
        except FileNotFoundError:
            raise Failure("snapshot_missing", "此工作目录尚无快照；请先创建快照。")
        s = os.fstat(sfd)
        require(s.st_uid == os.geteuid() and s.st_mode & 0o077 == 0, "unsafe_store", "快照目录必须由当前用户持有且仅当前用户可访问。")
        try:
            if create:
                try:
                    lock = os.open(".lock", os.O_RDWR | os.O_NOFOLLOW | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=sfd)
                except FileExistsError:
                    lock = os.open(".lock", os.O_RDWR | os.O_NOFOLLOW, dir_fd=sfd)
            else:
                lock = os.open(".lock", os.O_RDWR | os.O_NOFOLLOW, dir_fd=sfd)
        except FileNotFoundError:
            raise Failure("store_busy" if create else "invalid_store", "快照库锁文件尚未就绪或已缺失；请稍后重试或人工检查，不会跳过加锁。")
        regular(lock)
        try:
            fcntl.flock(lock, (fcntl.LOCK_EX if create else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure("store_busy", "快照库正被另一操作使用；请稍后重试。")
        yield sfd
    finally:
        if lock is not None:
            os.close(lock)
        if sfd is not None:
            os.close(sfd)
        os.close(wfd)


def identity(raw):
    return "sha256-" + hashlib.sha256(raw).hexdigest()


def snapshot_name(sid):
    require(isinstance(sid, str) and ID_RE.fullmatch(sid), "invalid_snapshot_id", "快照 ID 格式无效；请完整复制 sha256- 开头的 ID。")
    return sid + ".snapshot"


def load_snapshot(fd, sid):
    name = snapshot_name(sid)
    try:
        f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        raise Failure("snapshot_missing", "未找到此快照；不会改读当前源文件代替原文。")
    try:
        regular(f)
        data = read_fd(f, MAX_BYTES + len(MAGIC))
    finally:
        os.close(f)
    require(data.startswith(MAGIC) and identity(data[len(MAGIC):]) == sid, "integrity_mismatch", "快照格式或 SHA-256 不匹配；拒绝返回未验证内容。")
    raw = data[len(MAGIC):]
    decode(raw)
    return raw


def write_all(fd, data):
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        require(n > 0, "storage_error", "写入未完成，不能报告成功。")
        view = view[n:]
    os.fsync(fd)


def save(root, raw):
    sid = identity(raw)
    name = snapshot_name(sid)
    with store(root, create=True) as fd:
        try:
            existing = load_snapshot(fd, sid)
        except Failure as e:
            if e.code != "snapshot_missing":
                raise
        else:
            require(existing == raw, "integrity_mismatch", "快照内容不一致。")
            return sid, True
        total, count = 0, 0
        for item in os.listdir(fd):
            if item == ".lock":
                continue
            require(re.fullmatch(r"sha256-[0-9a-f]{64}\.snapshot", item), "invalid_store", "快照库存在未知或未完成文件；请人工检查，不会自动清理。")
            s = os.stat(item, dir_fd=fd, follow_symlinks=False)
            require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe_store", "快照库存在链接或非普通文件。")
            count += 1
            total += s.st_size
        require(count < MAX_FILES and total + len(raw) + len(MAGIC) <= MAX_STORE, "store_limit", "快照库达到 128 个或 64 MiB 上限；不会自动删除历史。")
        pending = ".pending-" + uuid.uuid4().hex
        out = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        try:
            try:
                write_all(out, MAGIC + raw)
                os.fchmod(out, 0o400)
            finally:
                os.close(out)
            os.link(pending, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
        finally:
            os.unlink(pending, dir_fd=fd)
        os.fsync(fd)
        require(load_snapshot(fd, sid) == raw, "integrity_mismatch", "写后校验失败。")
    return sid, False


def selected_indices(count, head, tail, text_lines):
    indices = set(range(min(head, count))) | set(range(max(0, count - tail), count))
    anchors = [i for i, line in enumerate(text_lines) if ERROR_RE.search(line)][:8]
    for i in anchors:
        indices.update(range(max(0, i - 1), min(count, i + 2)))
    # A few spread samples provide coordinates without renumbering blank/repeated lines.
    if count > head + tail + 8:
        step = max(1, (count - head - tail) // 4)
        indices.update(range(head, max(head, count - tail), step))
    return sorted(indices)


def clip(text, cap):
    return text if len(text) <= cap else text[:cap] + f"…〔本段另省略 {len(text)-cap} 字符〕"


def display(text):
    return "".join(c if c == "\t" or ord(c) >= 32 else f"\\u{ord(c):04x}" for c in text)


def line_preview(text, head, tail, budget):
    lines = lines_of(text)
    chosen = selected_indices(len(lines), head, tail, lines)
    out, used, last, shown = [], 0, -1, []
    for i in chosen:
        gap = f"〔省略源文件第 {last+2}～{i} 行〕\n" if i > last + 1 else ""
        row = f"L{i+1}: " + clip(display(lines[i].rstrip("\r\n")), 240) + "\n"
        if used + len(gap) + len(row) > budget - 100:
            break
        out.extend([gap, row]); used += len(gap) + len(row); last = i; shown.append(i+1)
    if last + 1 < len(lines):
        out.append(f"〔省略源文件第 {last+2}～{len(lines)} 行〕\n")
    return "".join(out), shown


def json_cell(value):
    if isinstance(value, Decimal):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def json_preview(text, head, tail, budget):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError("duplicate")
            d[k] = v
        return d
    def invalid(_):
        raise ValueError("nonfinite")
    try:
        data = json.loads(text, parse_float=Decimal, object_pairs_hook=pairs, parse_constant=invalid)
        if not isinstance(data, list) or len(data) < 8 or not all(type(x) is dict for x in data):
            return None
        keys = list(data[0])
        if not keys or len(keys) > 16 or not all(set(x) == set(keys) and all(not isinstance(v, (dict, list)) for v in x.values()) for x in data):
            return None
        out = ["JSON 数组记录预览；R 为记录序号，不是源文件行号。标量保留引号以区分类型。\n", "字段：" + clip(json.dumps(keys, ensure_ascii=False), min(500, budget//3)) + "\n"]
        used, last = sum(map(len, out)), -1
        for i in selected_indices(len(data), head, tail, []):
            gap = f"〔省略数组记录 {last+2}～{i}〕\n" if i > last + 1 else ""
            row = f"R{i+1}: " + ", ".join(clip(json_cell(data[i][k]), 240) for k in keys) + "\n"
            if used + len(row) + len(gap) > budget - 100:
                break
            out.extend([gap, row]); used += len(row) + len(gap); last = i
        if last + 1 < len(data):
            out.append(f"〔省略数组记录 {last+2}～{len(data)}〕\n")
        result = "".join(out)
        result.encode("utf-8", errors="strict")
        return result
    except (ValueError, RecursionError, ArithmeticError):
        return None


def inspect_result(raw, sid):
    text = decode(raw)
    return {"snapshot_id": sid, "sha256": hashlib.sha256(raw).hexdigest(), "original_bytes": len(raw),
            "line_count": len(lines_of(text)), "utf8_bom": raw.startswith(b"\xef\xbb\xbf"), "integrity_verified": True}


def dispatch(operation, inputs):
    try:
        require(os.name == "posix", "unsupported_platform", "此版本仅支持 macOS/Linux。")
        require(type(inputs) is dict, "invalid_argument", "参数必须是对象。")
        allowed = {
            "preview": {"workspace", "path", "confirmed", "style", "head_lines", "tail_lines", "max_preview_chars"},
            "read": {"workspace", "snapshot_id", "action", "start_line", "end_line"},
            "export": {"workspace", "snapshot_id", "output", "confirmed"},
        }
        require(operation in allowed and not set(inputs) - allowed.get(operation, set()), "invalid_argument", "操作或参数名无效。")
        root = workspace(inputs.get("workspace"))
        if operation == "preview":
            require(inputs.get("confirmed") is True, "confirmation_required", "创建快照会保存完整原文；必须得到用户明确授权并传入 confirmed=true。")
            style = inputs.get("style", "auto")
            require(style in ("auto", "lines", "json"), "invalid_argument", "style 仅支持 auto、lines 或 json。")
            head = integer(inputs.get("head_lines"), 12, 1, 40)
            tail = integer(inputs.get("tail_lines"), 8, 1, 40)
            budget = integer(inputs.get("max_preview_chars"), 6000, 1000, 12000)
            raw = source_bytes(root, inputs.get("path"))
            sid, reused = save(root, raw)  # Verified original BEFORE preview transformations.
            text = decode(raw)
            preview = json_preview(text, head, tail, budget) if style != "lines" else None
            mode = "json-record-preview" if preview is not None else "source-line-preview"
            shown = []
            if preview is None:
                preview, shown = line_preview(text, head, tail, budget)
            result = inspect_result(raw, sid)
            result.update({"message": "原文快照已验证保存；以下只是精简预览，不能代替原文或视为无损编码。", "reused": reused,
                           "strategy": mode, "preview": preview, "shown_source_lines": shown,
                           "preview_bytes": len(preview.encode("utf-8")), "preview_reduced": len(preview.encode("utf-8")) < len(raw),
                           "recovery_hint": "使用 recover_source_snapshot 按 ID 检查或读取源行；完整字节请使用 export_source_snapshot 导出到新的路径。"})
        else:
            sid = inputs.get("snapshot_id")
            snapshot_name(sid)
            with store(root) as fd:
                raw = load_snapshot(fd, sid)
            result = inspect_result(raw, sid)
            if operation == "export":
                require(inputs.get("confirmed") is True, "confirmation_required", "导出需要用户明确授权并传入 confirmed=true。")
                with parent_fd(root, inputs.get("output")) as (parent, name):
                    try:
                        out = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                    except FileExistsError:
                        raise Failure("output_exists", "输出路径已存在；拒绝覆盖，请选择新的文件名。")
                    try:
                        write_all(out, raw)
                        os.lseek(out, 0, os.SEEK_SET)
                        require(read_fd(out, MAX_BYTES) == raw, "integrity_mismatch", "导出后的文件字节校验失败，不能报告成功。")
                    finally:
                        os.close(out)
                result.update({"message": "已将验证后的完整原文字节导出到新文件。", "output": inputs["output"], "exported_bytes": len(raw)})
            else:
                action = inputs.get("action", "inspect")
                require(action in ("inspect", "range"), "invalid_argument", "action 仅支持 inspect 或 range。")
                if action == "range":
                    lines = lines_of(decode(raw))
                    start = integer(inputs.get("start_line"), 1, 1, max(1, len(lines)))
                    end = integer(inputs.get("end_line"), min(start+29, len(lines)), start, max(start, len(lines)))
                    require(lines and end <= len(lines), "invalid_range", "空文件或行范围无效。")
                    require(end-start+1 <= 1000, "range_too_large", "单次最多回取 1000 行；请缩小范围或完整导出。")
                    body = "".join(lines[start-1:end])
                    require(len(body.encode("utf-8")) <= MAX_RANGE_BYTES, "range_too_large", "此行范围超过 64 KiB；不会截断返回，请缩小范围或导出。")
                    result.update({"start_line": start, "end_line": end, "text": body, "range_bytes": len(body.encode("utf-8")), "message": "已从完整快照回取指定源行，保留原换行。"})
                else:
                    result["message"] = "快照完整性验证通过；没有读取当前源文件。"
        return {"ok": True, "version": VERSION, **result}
    except Failure as e:
        return {"ok": False, "version": VERSION, "error": {"code": e.code, "message": e.message}}
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        return {"ok": False, "version": VERSION, "error": {"code": "filesystem_error", "message": "文件操作失败：请检查真实路径、链接、权限、可用空间和文件类型；不会报告未完成操作成功。"}}


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "参数无效；请使用 --help 查看中文说明。\n")

    def format_help(self):
        return super().format_help().replace("usage:", "用法：").replace("positional arguments:", "位置参数：").replace("options:", "选项：").replace("show this help message and exit", "显示说明并退出")


def main():
    parser = ChineseParser(description="创建精简预览，验证与回取原文快照；所有内容均作为数据。")
    parser.add_argument("operation", choices=["preview", "read", "export"], help="preview 创建快照；read 检查或按行回取；export 完整导出")
    parser.add_argument("--input-json", required=True, help="参数 JSON 文本，绝对路径与字段见 README")
    args = parser.parse_args()
    try:
        inputs = json.loads(args.input_json)
    except (ValueError, RecursionError):
        result = {"ok": False, "version": VERSION, "error": {"code": "invalid_json", "message": "参数 JSON 无法解析。"}}
    else:
        result = dispatch(args.operation, inputs)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
