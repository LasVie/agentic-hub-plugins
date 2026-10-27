#!/usr/bin/env python3
"""家庭文档台账：显式元数据、有效期检查和经确认的材料副本。

Ported bounded metadata/lifecycle workflow from Document Vault 0.5.3,
Copyright (c) 2026 Ilya, MIT; see licenses/document-vault/LICENSE.
Modified 2026-10-26: Chinese WorkSwarm tools, closed JSON schemas, precise
calendar/uncertainty semantics, revisioned history, preview fingerprints,
POSIX descriptor-relative paths and exclusive copy-only output. No OCR,
content extraction, automatic filing/deletion, legal rules or encryption.
"""
import argparse
import calendar
from contextlib import contextmanager
from datetime import date
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

VERSION = "1.0.0"
STATE = ".family-document-registry"
MAX_JSON = 512 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_PEOPLE, MAX_DOCS, MAX_ITEMS, MAX_HISTORY = 32, 128, 32, 64
ID = re.compile(r"[a-z][a-z0-9_-]{0,47}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
BOUNDARY = "仅依据用户确认的元数据和自定义条件；文件只按字节读取以核对摘要，不提取或认证正文，不判断法律或办事资格，不提供加密或自动脱敏。"


class Failure(Exception):
    def __init__(self, code, message, **details):
        self.code, self.message, self.details = code, message, details


def check(ok, code, message, **details):
    if not ok:
        raise Failure(code, message, **details)


def dump(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(v, lo=0, hi=120):
    check(type(v) is int and lo <= v <= hi, "invalid_argument", f"整数必须在 {lo}～{hi} 内，不能使用布尔值。")
    return v


def fields(v, required, optional=()):
    check(type(v) is dict, "invalid_schema", "必须提供 JSON 对象。")
    check(set(required) <= v.keys() and v.keys() <= set(required) | set(optional), "invalid_schema", "字段缺失或存在未知字段；不会忽略未支持字段。")


def text(v, limit=120, nullable=False):
    if nullable and v is None:
        return v
    check(type(v) is str and 0 < len(v) <= limit and v == v.strip()
          and not any(ord(c) < 32 or ord(c) == 127 for c in v), "invalid_schema", "文本必须非空、无首尾空白或控制字符，并符合长度限制。")
    return v


def ident(v):
    check(type(v) is str and ID.fullmatch(v), "invalid_schema", "标识符须以小写字母开头，仅含小写字母、数字、下划线或连字符，最长48字符。")
    return v


def pairs(items):
    out = {}
    for key, value in items:
        check(key not in out, "duplicate_json_key", "JSON 包含重复键；拒绝静默覆盖。")
        out[key] = value
    return out


def decode(raw):
    check(len(raw) <= MAX_JSON, "size_limit", "JSON 最多512KiB；不会截断。")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Failure("invalid_json", "JSON 不接受非有限数值。")))
    except (UnicodeError, ValueError, RecursionError):
        raise Failure("invalid_json", "必须提供有效、非超深嵌套的 UTF-8 JSON。")


def parsed_date(value, exact=False):
    if value is None and not exact:
        return None
    check(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}" if exact else r"\d{4}-\d{2}(?:-\d{2})?", value),
          "invalid_date", "日期须为 YYYY-MM-DD；登记日期可为 YYYY-MM 或 null，不接受模糊日期。")
    try:
        return date.fromisoformat(value if len(value) == 10 else value + "-01")
    except ValueError:
        raise Failure("invalid_date", "日期不存在或超出支持范围。")


def add_months(d, n):
    # Preserve the day when possible; clamp only to the real last day of target month.
    q, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + q, m + 1
    check(1 <= y <= 9999, "invalid_date", "月份计算超出支持的日期范围。")
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def absolute(raw):
    check(type(raw) is str and raw.startswith("/") and raw != "/" and len(raw) <= 4096
          and all(p not in ("", ".", "..") for p in raw.split("/")[1:])
          and not any(ord(c) < 32 or ord(c) == 127 for c in raw),
          "unsafe_path", "使用无空段、.、.. 或控制字符的真实绝对路径；不能选择根目录。")
    return Path(raw)


def relative(raw):
    text(raw, 512)
    parts = raw.split("/")
    check(len(parts) <= 12 and all(p not in ("", ".", "..") for p in parts)
          and not raw.startswith("/") and not any(c in raw for c in "\\:") and parts[0] != STATE,
          "unsafe_path", "登记路径须为工作目录内的普通相对路径，不能穿越目录、使用内部台账或包含链接。")
    return parts


def open_directory(path):
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for p in path.parts[1:]:
            next_fd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextmanager
def parent(root, parts):
    fd = open_directory(root)
    try:
        for p in parts[:-1]:
            nfd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nfd
        yield fd, parts[-1]
    finally:
        os.close(fd)


def user_parts(root, value):
    p = absolute(value)
    check(p.is_relative_to(root), "outside_workspace", "输入和输出必须在指定工作目录内。")
    return relative(p.relative_to(root).as_posix())


def read_at(fd, name, limit, private=False):
    f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        a = os.fstat(f)
        check(stat.S_ISREG(a.st_mode) and a.st_nlink == 1, "unsafe_file", "只接受无硬链接的普通文件。")
        if private:
            check(a.st_uid == os.geteuid() and a.st_mode & 0o077 == 0, "invalid_registry", "内部台账文件须仅当前用户可访问。")
        check(a.st_size <= limit, "size_limit", "文件超过此操作的大小上限。")
        out = bytearray()
        while len(out) <= limit:
            part = os.read(f, min(65536, limit + 1 - len(out)))
            if not part:
                break
            out.extend(part)
        b = os.fstat(f)
        check(len(out) <= limit, "size_limit", "文件超过此操作的大小上限。")
        check((a.st_dev, a.st_ino, a.st_size, a.st_mtime_ns, a.st_ctime_ns) ==
              (b.st_dev, b.st_ino, b.st_size, b.st_mtime_ns, b.st_ctime_ns) and len(out) == a.st_size,
              "source_changed", "读取期间文件变化；请停止并发写入后重新预览。")
        return bytes(out)
    finally:
        os.close(f)


def read_user(root, parts, limit=MAX_FILE):
    with parent(root, parts) as (fd, name):
        return read_at(fd, name, limit)


def load_input(root, value):
    raw = read_user(root, user_parts(root, value), MAX_JSON)
    return decode(raw), digest(raw)


def validate_catalog(c):
    fields(c, ("schema_version", "people", "documents"))
    check(type(c["schema_version"]) is int and c["schema_version"] == 1, "invalid_schema", "仅支持 schema_version=1。")
    check(type(c["people"]) is list and 1 <= len(c["people"]) <= MAX_PEOPLE
          and type(c["documents"]) is list and len(c["documents"]) <= MAX_DOCS, "size_limit", "台账最多32人、128份文档，且至少有1人。")
    people = {}
    for p in c["people"]:
        fields(p, ("id", "name"))
        ident(p["id"]); text(p["name"], 80)
        check(p["id"] not in people, "duplicate_id", "人员 ID 重复。")
        people[p["id"]] = p
    docs = {}
    for d in c["documents"]:
        fields(d, ("id", "person_id", "kind", "country", "path", "issued_on", "expires_on", "status", "replaces"))
        ident(d["id"])
        check(d["person_id"] in people, "invalid_reference", "文档引用了不存在的人员。")
        text(d["kind"]); text(d["country"], 80)
        if d["path"] is not None:
            relative(d["path"])
        issued, expires = parsed_date(d["issued_on"]), parsed_date(d["expires_on"])
        if issued and expires and len(d["issued_on"]) == len(d["expires_on"]) == 10:
            check(issued <= expires, "invalid_date", "签发日不能晚于到期日。")
        check(d["status"] in ("active", "renewing", "archived"), "invalid_schema", "状态只接受 active、renewing 或 archived。")
        if d["replaces"] is not None:
            ident(d["replaces"])
        check(d["id"] not in docs, "duplicate_id", "文档 ID 重复。")
        docs[d["id"]] = d
    replacements = set()
    check(all(d["replaces"] is None or d["replaces"] in docs for d in docs.values()),
          "invalid_reference", "替换关系引用了不存在的文档。")
    for d in docs.values():
        prev = d["replaces"]
        if prev is None:
            continue
        check(prev in docs and prev != d["id"], "invalid_reference", "替换关系引用不存在或自身的文档。")
        old = docs[prev]
        check(all(d[k] == old[k] for k in ("person_id", "kind", "country")), "invalid_reference", "替换须属于同一人员、文档类型和国家/地区。")
        check(prev not in replacements, "invalid_reference", "同一文档不能同时被多个新文档替换。")
        replacements.add(prev)
        seen = {d["id"]}
        while prev is not None:
            check(prev not in seen, "invalid_reference", "替换关系不能形成循环。")
            seen.add(prev)
            prev = docs[prev]["replaces"]
    return c


def file_info(root, path):
    if path is None:
        return {"status": "unattached", "sha256": None, "bytes": None}
    try:
        raw = read_user(root, relative(path))
    except FileNotFoundError:
        return {"status": "missing", "sha256": None, "bytes": None}
    return {"status": "present", "sha256": digest(raw), "bytes": len(raw)}


def catalog_preview(root, path):
    catalog, source_sha = load_input(root, path)
    validate_catalog(catalog)
    files = {d["id"]: file_info(root, d["path"]) for d in catalog["documents"]}
    check(sum(x["bytes"] or 0 for x in files.values()) <= MAX_TOTAL, "size_limit", "全部登记文件合计最多64MiB。")
    preview = {"catalog": catalog, "catalog_sha256": source_sha, "files": files}
    return preview, digest(dump(preview))


def write_new(fd, name, raw):
    out = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        offset = 0
        while offset < len(raw):
            n = os.write(out, raw[offset:])
            check(n > 0, "storage_error", "写入未完成。")
            offset += n
        os.fsync(out)
    finally:
        os.close(out)


@contextmanager
def registry_store(root, create=False):
    import fcntl
    rootfd = open_directory(root)
    statefd = lockfd = None
    try:
        if create:
            try:
                os.mkdir(STATE, 0o700, dir_fd=rootfd)
            except FileExistsError:
                pass
        try:
            statefd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=rootfd)
        except FileNotFoundError:
            yield None
            return
        st = os.fstat(statefd)
        check(st.st_uid == os.geteuid() and st.st_mode & 0o077 == 0, "invalid_registry", "台账目录须仅当前用户可访问。")
        if create:
            try:
                write_new(statefd, "lock", b"")
            except FileExistsError:
                pass
        lockfd = os.open("lock", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=statefd)
        st = os.fstat(lockfd)
        check(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid == os.geteuid() and st.st_mode & 0o077 == 0,
              "invalid_registry", "台账锁文件无效。")
        try:
            fcntl.flock(lockfd, (fcntl.LOCK_EX if create else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure("registry_busy", "台账正被其他操作使用；请稍后重试，不会跳过加锁。")
        yield statefd
    finally:
        for fd in (lockfd, statefd, rootfd):
            if fd is not None:
                os.close(fd)


def load_registry(fd):
    if fd is None:
        return None, None
    try:
        head = decode(read_at(fd, "HEAD.json", MAX_JSON, True))
    except FileNotFoundError:
        # Only a newly created, still empty store may lack HEAD.
        check(set(os.listdir(fd)) <= {"lock"}, "invalid_registry", "台账头文件缺失但存在历史；不会冒充新台账重新初始化。")
        return None, None
    fields(head, ("revision", "sha256"))
    integer(head["revision"], 1, MAX_HISTORY)
    check(type(head["sha256"]) is str and SHA.fullmatch(head["sha256"]), "invalid_registry", "台账摘要无效。")
    raw = read_at(fd, f"{head['revision']:03d}-{head['sha256']}.json", MAX_JSON, True)
    check(digest(raw) == head["sha256"], "integrity_mismatch", "台账历史文件与头摘要不一致。")
    state = decode(raw)
    fields(state, ("schema_version", "revision", "previous_sha256", "catalog", "files"))
    validate_catalog(state["catalog"])
    check(state["schema_version"] == 1 and state["revision"] == head["revision"], "invalid_registry", "台账版本或修订号不一致。")
    docs = state["catalog"]["documents"]
    check(type(state["files"]) is dict and set(state["files"]) == {d["id"] for d in docs}, "invalid_registry", "文件摘要索引与文档不一致。")
    for v in state["files"].values():
        fields(v, ("status", "sha256", "bytes"))
        check(v["status"] in ("present", "missing", "unattached"), "invalid_registry", "登记文件状态无效。")
        if v["status"] == "present":
            check(type(v["sha256"]) is str and SHA.fullmatch(v["sha256"]), "invalid_registry", "登记文件摘要无效。")
            integer(v["bytes"], 0, MAX_FILE)
        else:
            check(v["sha256"] is None and v["bytes"] is None, "invalid_registry", "缺失文件不能伪称已验证摘要。")
    return state, head["sha256"]


def manage(root, p):
    action = p.get("action", "status")
    check(action in ("inspect", "status", "init", "update"), "invalid_argument", "action 只接受 inspect、status、init 或 update。")
    if action == "inspect":
        preview, h = catalog_preview(root, p.get("catalog_path"))
        return {"writes_performed": False, "preview_sha256": h, **preview, "message": "请核对完整元数据与实际文件摘要，再明确确认登记。"}
    if action == "status":
        with registry_store(root) as fd:
            state, h = load_registry(fd)
        return {"initialized": state is not None, "revision": state["revision"] if state else 0,
                "registry_sha256": h, "catalog": state["catalog"] if state else None,
                "files": state["files"] if state else {}, "writes_performed": False,
                "message": "已读取完整当前台账。" if state else "工作目录尚未初始化台账。"}
    check(p.get("confirmed") is True, "confirmation_required", "须先展示完整登记预览并取得用户明确确认。")
    expected = integer(p.get("expected_revision"), 0, MAX_HISTORY)
    preview, ph = catalog_preview(root, p.get("catalog_path"))
    check(p.get("expected_preview_sha256") == ph, "preview_changed", "元数据或源文件与确认的预览不符；请重新检查并取得确认。")
    with registry_store(root, True) as fd:
        current, old_sha = load_registry(fd)
        revision = current["revision"] if current else 0
        check(expected == revision, "revision_conflict", "修订号冲突；请读取最新状态，不会覆盖新记录。", actual_revision=revision)
        check((action == "init") == (current is None), "already_initialized" if action == "init" else "registry_missing", "操作与当前初始化状态不符。")
        if current:
            before, after = current["catalog"], preview["catalog"]
            check({x["id"] for x in before["people"]} <= {x["id"] for x in after["people"]}
                  and {x["id"] for x in before["documents"]} <= {x["id"] for x in after["documents"]},
                  "history_required", "不能删除已登记人员或文档；请保留记录并显式标记 archived。")
            new = {d["id"]: d for d in after["documents"]}
            for d in before["documents"]:
                check(all(d[k] == new[d["id"]][k] for k in ("person_id", "kind", "country")),
                      "identity_conflict", "已有文档 ID 的人员、类型和国家/地区身份不能重用；请建立新文档 ID。")
        check(revision < MAX_HISTORY and len(os.listdir(fd)) < 2 * MAX_HISTORY + 4, "history_limit", "台账达到64次修订或历史文件上限；不会自动删除历史。")
        new_state = {"schema_version": 1, "revision": revision + 1, "previous_sha256": old_sha,
                     "catalog": preview["catalog"], "files": preview["files"]}
        raw = dump(new_state); check(len(raw) <= MAX_JSON, "size_limit", "台账序列化超过512KiB。")
        h = digest(raw); history_name = f"{revision + 1:03d}-{h}.json"
        try:
            write_new(fd, history_name, raw)
        except FileExistsError:
            check(read_at(fd, history_name, MAX_JSON, True) == raw, "integrity_mismatch", "已有同名历史内容不一致。")
        pending = "pending-" + uuid.uuid4().hex
        try:
            write_new(fd, pending, dump({"revision": revision + 1, "sha256": h}))
            os.replace(pending, "HEAD.json", src_dir_fd=fd, dst_dir_fd=fd)
            os.fsync(fd)
        finally:
            try:
                os.unlink(pending, dir_fd=fd)
            except FileNotFoundError:
                pass
        state, verified_sha = load_registry(fd)
        check(verified_sha == h, "integrity_mismatch", "写后校验失败，不能报告登记成功。")
    return {"revision": state["revision"], "registry_sha256": h, "previous_registry_sha256": old_sha,
            "preview_sha256": ph, "people_count": len(state["catalog"]["people"]),
            "document_count": len(state["catalog"]["documents"]), "writes_performed": True,
            "message": "已保存新修订并保留历史；原始文档未修改。"}


def registry(root):
    with registry_store(root) as fd:
        current, sha = load_registry(fd)
    check(current is not None, "registry_missing", "请先检查并明确确认初始化台账。")
    return current, sha


def expiry_state(d, ref, horizon):
    value = d["expires_on"]
    if value is None:
        return "unknown", "到期日未知，需要人工确认。"
    expiry = parsed_date(value)
    if len(value) == 7:
        return "month_precision", "仅有到期月份，不能推断具体有效日。"
    if expiry < ref:
        return "expired", "按已登记日期，文档已过期。"
    if expiry == ref:
        return "expires_today", "到期日等于参考日；此处按日期包含当天计算。"
    if expiry <= horizon:
        return "expiring", "到期日在所选提醒范围内。"
    return "beyond_horizon", "到期日晚于提醒范围；这不是法律效力认证。"


def report(root, p):
    ref = parsed_date(p.get("reference_date"), True)
    horizon = add_months(ref, integer(p.get("horizon_months", 6)))
    current, h = registry(root)
    catalog = current["catalog"]
    pid, kind = p.get("person_id"), p.get("kind")
    if pid is not None:
        check(pid in {x["id"] for x in catalog["people"]}, "invalid_reference", "人员 ID 不存在。")
    if kind is not None:
        text(kind)
    out, total = [], 0
    for d in catalog["documents"]:
        if pid is not None and d["person_id"] != pid or kind is not None and d["kind"] != kind:
            continue
        actual = file_info(root, d["path"]); total += actual["bytes"] or 0
        check(total <= MAX_TOTAL, "size_limit", "所选文件合计超过64MiB。")
        original = current["files"][d["id"]]
        file_state = actual["status"]
        if file_state == "present" and actual != original:
            file_state = "changed"
        code, message = expiry_state(d, ref, horizon)
        replacements = [x["id"] for x in catalog["documents"] if x["replaces"] == d["id"]]
        out.append({**d, "expiry_state": code, "expiry_message": message,
                    "future_issue_date": bool(d["issued_on"] and len(d["issued_on"]) == 10 and parsed_date(d["issued_on"]) > ref),
                    "replaced_by": replacements, "file_status": file_state,
                    "registered_sha256": original["sha256"], "actual_sha256": actual["sha256"]})
    return {"revision": current["revision"], "registry_sha256": h, "reference_date": str(ref),
            "horizon_date": str(horizon), "document_count": len(out), "documents": out,
            "writes_performed": False, "message": "已检查登记状态、日期精度和文件摘要；替换关系只表示用户明确登记的关系。"}


def pack_preview(root, p):
    current, sha = registry(root)
    plan, plan_sha = load_input(root, p.get("plan_path"))
    fields(plan, ("schema_version", "reference_date", "requirements"))
    check(type(plan["schema_version"]) is int and plan["schema_version"] == 1, "invalid_schema", "仅支持 schema_version=1。")
    ref = parsed_date(plan["reference_date"], True)
    items = plan["requirements"]
    check(type(items) is list and 1 <= len(items) <= MAX_ITEMS, "size_limit", "材料计划需有1～32项。")
    output_parts = user_parts(root, p.get("output_dir"))
    with parent(root, output_parts) as (parentfd, leaf):
        try:
            os.stat(leaf, dir_fd=parentfd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Failure("output_exists", "输出目录已存在；不能删除或覆盖旧材料包。")
    docs = {d["id"]: d for d in current["catalog"]["documents"]}
    people = {x["id"] for x in current["catalog"]["people"]}
    seen, prepared, buffers, total = set(), [], {}, 0
    for i, item in enumerate(items, 1):
        fields(item, ("id", "person_id", "label", "document_id"), ("min_validity_months", "max_age_months"))
        rid = ident(item["id"]); text(item["label"])
        check(rid not in seen, "duplicate_id", "材料项 ID 重复。")
        seen.add(rid)
        check(item["person_id"] in people, "invalid_reference", "材料项人员不存在。")
        for k in ("min_validity_months", "max_age_months"):
            if k in item:
                integer(item[k])
        result = {**item, "issues": [], "source": None, "sha256": None, "bytes": None, "output_file": None}
        did = item["document_id"]
        if did is None:
            result["issues"].append("missing_document")
        else:
            ident(did)
            check(did in docs and docs[did]["person_id"] == item["person_id"], "invalid_reference", "文档 ID 不存在或不属于指定人员。")
            d = docs[did]
            check(d["path"] is not None, "source_missing", "所选文档未关联文件；请改用缺失项或先确认登记文件。")
            try:
                raw = read_user(root, relative(d["path"]))
            except FileNotFoundError:
                raise Failure("source_missing", "所选文档的源文件缺失。")
            registered = current["files"][did]
            check(registered["status"] == "present" and digest(raw) == registered["sha256"] and len(raw) == registered["bytes"],
                  "source_changed", "源文件与登记摘要不符；请重新检查并确认台账，不会自动采纳新内容。")
            total += len(raw); check(total <= MAX_TOTAL, "size_limit", "材料文件合计最多64MiB。")
            if d["status"] != "active":
                result["issues"].append("status_" + d["status"])
            exp, issue = d["expires_on"], d["issued_on"]
            if exp is None or len(exp) != 10:
                result["issues"].append("expiry_uncertain")
            elif parsed_date(exp) < ref:
                result["issues"].append("expired")
            elif "min_validity_months" in item and parsed_date(exp) < add_months(ref, item["min_validity_months"]):
                result["issues"].append("validity_too_short")
            if issue is not None and len(issue) == 10 and parsed_date(issue) > ref:
                result["issues"].append("future_issue_date")
            if "max_age_months" in item:
                if issue is None or len(issue) != 10:
                    result["issues"].append("issue_date_uncertain")
                elif parsed_date(issue) < add_months(ref, -item["max_age_months"]):
                    result["issues"].append("too_old")
            extension = Path(d["path"]).suffix
            if not re.fullmatch(r"\.[a-zA-Z0-9]{1,12}", extension):
                extension = ".bin"
            dest = f"{i:02d}-{rid}-{did}{extension}"
            result.update(source=d["path"], sha256=digest(raw), bytes=len(raw), output_file=dest)
            buffers[dest] = raw
        result["status"] = "needs_review" if result["issues"] else "meets_declared_conditions"
        prepared.append(result)
    preview = {"revision": current["revision"], "registry_sha256": sha, "plan_sha256": plan_sha,
               "reference_date": str(ref), "output_dir": str(root.joinpath(*output_parts)), "items": prepared,
               "complete": all(not it["issues"] for it in prepared), "copy_count": len(buffers), "total_bytes": total}
    return preview, digest(dump(preview)), buffers, output_parts


ISSUES_ZH = {"missing_document": "未指定文档", "expiry_uncertain": "到期日期不确定", "expired": "已过期",
             "validity_too_short": "有效期不足用户指定月数", "future_issue_date": "签发日晚于参考日",
             "issue_date_uncertain": "签发日期不确定", "too_old": "超过用户指定材料新近程度",
             "status_renewing": "登记状态为续办中", "status_archived": "登记状态为已归档"}


def pack(root, p):
    mode = p.get("mode", "preview")
    check(mode in ("preview", "build"), "invalid_argument", "mode 只接受 preview 或 build。")
    if mode == "build":
        check(p.get("confirmed") is True, "confirmation_required", "请先展示材料计划、待确认项和摘要，并取得用户明确确认。")
    preview, ph, buffers, parts = pack_preview(root, p)
    if mode == "preview":
        return {**preview, "preview_sha256": ph, "writes_performed": False,
                "message": "只读预览；有待确认项的材料包不能称为齐备或具备办理资格。"}
    check(integer(p.get("expected_revision"), 1, MAX_HISTORY) == preview["revision"], "revision_conflict", "台账修订已变化；请重新预览和确认。")
    check(p.get("expected_preview_sha256") == ph, "preview_changed", "计划、台账、输出或源文件与确认的预览不同；请重新预览并取得确认。")
    # Hold a shared lock through copying so a legitimate writer cannot change registry.
    with registry_store(root) as statefd:
        state, sha = load_registry(statefd)
        check(sha == preview["registry_sha256"], "revision_conflict", "台账在预览后变化；未创建材料包。")
        with parent(root, parts) as (parentfd, leaf):
            outfd = None
            created = False
            try:
                os.mkdir(leaf, 0o700, dir_fd=parentfd)
                created = True
                outfd = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parentfd)
                for name, raw in buffers.items():
                    write_new(outfd, name, raw)
                    check(digest(read_at(outfd, name, MAX_FILE, True)) == digest(raw), "integrity_mismatch", "材料副本写后摘要不符。")
                # Do not finalize a pack when any selected file changed during copying.
                for item in preview["items"]:
                    if item["source"]:
                        check(digest(read_user(root, relative(item["source"]))) == item["sha256"], "source_changed", "复制期间源文件变化；未完成的输出须人工检查。")
                lines = ["# 家庭文档材料包", "", "仅为用户确认计划的副本；原文档未修改。", "", BOUNDARY,
                         "", f"参考日：{preview['reference_date']}；台账修订：{preview['revision']}。", "",
                         "| 项目 ID | 人员 ID | 用户要求 | 副本 | 检查结果 |", "|---|---|---|---|---|"]
                esc = lambda v: html.escape(str(v)).replace("|", "\\|")
                for item in preview["items"]:
                    status = "；".join(ISSUES_ZH[c] for c in item["issues"]) or "符合已声明条件"
                    lines.append("| " + " | ".join(map(esc, (item["id"], item["person_id"], item["label"], item["output_file"] or "无", status))) + " |")
                checklist = ("\n".join(lines) + "\n").encode("utf-8")
                write_new(outfd, "checklist.md", checklist)
                manifest = {"schema_version": 1, "version": VERSION, "preview_sha256": ph, **preview,
                            "checklist_sha256": digest(checklist), "boundary": BOUNDARY}
                raw = dump(manifest)
                write_new(outfd, "manifest.json", raw)
                os.fsync(outfd); os.fsync(parentfd)
            except FileExistsError:
                if not created:
                    raise Failure("output_exists", "输出目录已存在；不会覆盖或删除它。")
                raise Failure("partial_output", "本次新输出未完成；保留现场供人工检查，不能称为成功。", output_dir=preview["output_dir"])
            except (Failure, OSError) as e:
                if created:
                    raise Failure("partial_output", "本次新输出未完成；保留现场供人工检查，不能称为成功。",
                                  output_dir=preview["output_dir"], cause_code=e.code if isinstance(e, Failure) else "filesystem_error")
                raise
            finally:
                if outfd is not None:
                    os.close(outfd)
    return {**preview, "preview_sha256": ph, "manifest_sha256": digest(raw), "writes_performed": True,
            "message": "已生成逐字节核验的材料副本和中文清单。" + ("仍有待确认项。" if not preview["complete"] else "仅符合本次已声明条件。")}


def dispatch(operation, inputs):
    try:
        check(os.name == "posix", "unsupported_platform", "此版本仅支持 macOS/Linux 的本地普通文件。")
        allowed = {"manage": {"workspace", "action", "catalog_path", "confirmed", "expected_revision", "expected_preview_sha256"},
                   "report": {"workspace", "reference_date", "horizon_months", "person_id", "kind"},
                   "pack": {"workspace", "plan_path", "output_dir", "mode", "confirmed", "expected_revision", "expected_preview_sha256"}}
        check(operation in allowed and type(inputs) is dict and inputs.keys() <= allowed.get(operation, set()),
              "invalid_argument", "操作未知或包含未支持参数。")
        root = absolute(inputs.get("workspace"))
        fd = open_directory(root); os.close(fd)
        value = {"manage": manage, "report": report, "pack": pack}[operation](root, inputs)
        return {"ok": True, "version": VERSION, "boundary": BOUNDARY, **value}
    except Failure as e:
        return {"ok": False, "version": VERSION, "error": {"code": e.code, "message": e.message, **e.details}}
    except OSError:
        return {"ok": False, "version": VERSION, "error": {"code": "filesystem_error", "message": "文件访问失败；请检查路径、权限、链接、稳定性与磁盘空间。"}}
    except (TypeError, KeyError, ValueError, OverflowError, RecursionError):
        return {"ok": False, "version": VERSION, "error": {"code": "invalid_schema", "message": "参数或台账结构无效；未猜测、执行或静默修补内容。"}}


class ChineseParser(argparse.ArgumentParser):
    def format_help(self):
        return super().format_help().replace("usage:", "用法：", 1)

    def error(self, message):
        self.exit(2, "命令行参数无效；请使用 --help 查看中文格式说明。\n")


def main():
    parser = ChineseParser(description="家庭文档台账：本地元数据、有效期检查和经确认的材料副本；不访问网络或调用模型。", add_help=False)
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示此帮助并退出")
    parser.add_argument("operation", choices=("manage", "report", "pack"), help="manage 管理台账；report 只读检查；pack 预览或创建副本")
    parser.add_argument("--input-json", required=True, help="UTF-8 JSON 参数文本，使用与原生工具相同的字段")
    p = parser.parse_args()
    try:
        result = dispatch(p.operation, decode(p.input_json.encode("utf-8")))
    except Failure as e:
        result = {"ok": False, "version": VERSION, "error": {"code": e.code, "message": e.message}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
