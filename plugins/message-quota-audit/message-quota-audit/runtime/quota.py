"""消息配额与用量审计：显式本地账本，不发送或拦截消息。

Ported from dsh-whale-post packages/gate@0.6.1,
commit d78a82699722f0da6ae3d2b4cbdbaa411f2f67af.
Copyright (c) 2026 The Tank — original MIT text in licenses/whale-post-gate/LICENSE.
Modified: Python/SQLite transactions, bounded validation, idempotency, explicit timezone,
read-only previews, Chinese host tools. Original source header is retained in notices.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
import unicodedata
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VERSION = "1.0.1"
STATE = ".message-quota-audit"
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
ACK = re.compile(r"(?:已读|收到|好的|好|行|ok|同意|赞成|谢谢|多谢|不客气|辛苦了|辛苦|明白|了解|知道了|没问题|嗯|赞|thx|thanks|thankyou|manythanks|ack|roger|copy|noted|understood|sure|np|gotit|willdo|allclear|noworries)+\Z", re.I)
DEFAULT = {"timezone": "Asia/Shanghai", "day_boundary_hour": 0,
           "buckets": {"direct": {"limit": 120, "per_send": False},
                       "offline": {"limit": 80, "per_send": True}},
           "pair_window_seconds": 1200, "pair_max": 3, "hop_max": 3, "ack_max_bytes": 40}
MAX_EVENTS = 10000


class Failure(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


def fail(code, message):
    raise Failure(code, message)


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(packed(value).encode("utf-8")).hexdigest()


def strict_json(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 512 * 1024:
        fail("invalid_json", "JSON 必须是最多 512 KiB 的 UTF-8 文本。")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail("duplicate_json_key", "JSON 含有重复字段。")
            result[key] = value
        return result
    def constant(_):
        fail("invalid_json", "JSON 不接受非有限数字。")
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        packed(value).encode("utf-8")
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):
        fail("invalid_json", "JSON 格式、文本编码或嵌套深度无效。")


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def identifier(value):
    return isinstance(value, str) and IDENT.fullmatch(value) is not None


def policy_value(value):
    if not isinstance(value, dict) or set(value) != set(DEFAULT):
        fail("invalid_policy", "策略必须且只能包含示例中的全部字段。")
    zone = value["timezone"]
    if not isinstance(zone, str) or len(zone) > 64:
        fail("invalid_policy", "timezone 必须是有效的 IANA 时区名称。")
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        fail("timezone_unavailable", "系统找不到该时区；请使用已安装的 IANA 时区资料。")
    bounds = {"day_boundary_hour": (0, 23), "pair_window_seconds": (1, 86400),
              "pair_max": (1, 1000), "hop_max": (1, 100), "ack_max_bytes": (0, 1024)}
    for key, (low, high) in bounds.items():
        if not integer(value[key], low, high):
            fail("invalid_policy", "策略整数超出允许范围或类型不正确。")
    buckets = value["buckets"]
    if not isinstance(buckets, dict) or not 1 <= len(buckets) <= 32:
        fail("invalid_policy", "buckets 必须包含 1～32 个配额桶。")
    for name, setting in buckets.items():
        if not identifier(name) or not isinstance(setting, dict) or set(setting) != {"limit", "per_send"}:
            fail("invalid_policy", "配额桶标识或字段无效。")
        if not integer(setting["limit"], 0, 1000000) or type(setting["per_send"]) is not bool:
            fail("invalid_policy", "limit 必须是 0～1000000 的整数，per_send 必须是布尔值。")
    return value


def message_value(value):
    required = {"id", "as", "targets", "type", "mode", "body", "hop"}
    if not isinstance(value, dict) or not required <= set(value) or set(value) - required - {"sentAtMs"}:
        fail("invalid_message", "消息字段缺失或存在未知字段；只接受文档中的受限配额输入。")
    if not all(identifier(value[k]) for k in ("id", "as", "type")):
        fail("invalid_message", "id、as、type 必须是 1～64 位安全标识。")
    targets = value["targets"]
    if not isinstance(targets, list) or not 1 <= len(targets) <= 128 or not all(identifier(x) for x in targets):
        fail("invalid_message", "targets 必须是 1～128 个收件人标识。")
    if len(set(targets)) != len(targets):
        fail("duplicate_target", "收件人标识不可重复，以免重复计数。")
    if value["mode"] not in ("online", "offline") or not isinstance(value["body"], str):
        fail("invalid_message", "mode 只接受 online/offline，body 必须为文本。")
    if len(value["body"].encode("utf-8")) > 65536 or not integer(value["hop"], 0, 1000):
        fail("invalid_message", "正文最多 64 KiB；hop 必须是 0～1000 的整数。")
    if "sentAtMs" in value and not integer(value["sentAtMs"], 0, 9007199254740991):
        fail("invalid_message", "sentAtMs 必须是非负安全整数毫秒。")
    return {**value, "targets": sorted(targets)}


def day_of(now_ms, policy):
    local = datetime.fromtimestamp(now_ms / 1000, timezone.utc).astimezone(ZoneInfo(policy["timezone"]))
    return (local.date() - timedelta(days=local.hour < policy["day_boundary_hour"])).isoformat()


def private_path(workspace, initialize=False):
    if os.name != "posix":
        fail("unsupported_platform", "此版本仅支持经过目录权限检查的 Linux/macOS 环境。")
    if not isinstance(workspace, str) or not Path(workspace).is_absolute():
        fail("invalid_workspace", "请明确提供已存在工作目录的绝对路径。")
    path = Path(workspace)
    created = False
    try:
        if path.resolve(strict=True) != path or not path.is_dir():
            fail("unsafe_path", "工作目录必须存在且不得经过符号链接或非规范路径。")
        directory = path / STATE
        if initialize:
            try:
                directory.mkdir(mode=0o700)
            except FileExistsError:
                pass
        st = directory.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            fail("unsafe_state", "账本目录必须由当前用户拥有、权限为私有且不是链接。")
        db = directory / "ledger.sqlite3"
        if initialize and not db.exists():
            fd = os.open(db, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            created = True
        st = db.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid() or st.st_mode & 0o077:
            fail("unsafe_state", "账本文件必须是当前用户拥有的私有普通文件，不得为链接。")
        if st.st_size > 64 * 1024 * 1024:
            fail("state_limit", "账本超过 64 MiB；请保留原账本并改用新的工作目录。")
        if not created and st.st_size == 0:
            fail("corrupt_state", "已有账本为空；拒绝把缺失历史当成新账本覆盖。")
        for suffix in ("-journal", "-wal", "-shm"):
            side = Path(str(db) + suffix)
            if side.exists() or side.is_symlink():
                ss = side.lstat()
                if not stat.S_ISREG(ss.st_mode) or ss.st_nlink != 1 or ss.st_uid != os.getuid() or ss.st_mode & 0o077:
                    fail("unsafe_state", "SQLite 辅助文件不是安全的私有普通文件。")
        return db, created
    except FileNotFoundError:
        fail("not_initialized", "尚未初始化，或账本缺失；请先执行 init，不会自动覆盖坏账本。")
    except FileExistsError:
        fail("state_busy", "初始化发生并发冲突；请读取状态后重试。")


@contextlib.contextmanager
def connection(workspace, write=False, initialize=False):
    db, created = private_path(workspace, initialize)
    con = sqlite3.connect(db.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True, timeout=2)
    try:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA trusted_schema=OFF")
        con.execute("PRAGMA busy_timeout=2000")
        if not write:
            con.execute("PRAGMA query_only=ON")
        con.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        if created:
            con.execute("CREATE TABLE settings(version INTEGER NOT NULL, revision INTEGER NOT NULL, policy TEXT NOT NULL)")
            con.execute("INSERT INTO settings VALUES(1,0,?)", (packed(DEFAULT),))
            con.execute("CREATE TABLE events(sender TEXT NOT NULL,id TEXT NOT NULL,fingerprint TEXT NOT NULL,day TEXT NOT NULL,bucket TEXT NOT NULL,units INTEGER NOT NULL CHECK(units>0),body_bytes INTEGER NOT NULL CHECK(body_bytes>=0),targets TEXT NOT NULL,mode TEXT NOT NULL,recorded_ms INTEGER NOT NULL,revision INTEGER NOT NULL,PRIMARY KEY(sender,id))")
        yield con
        if write:
            con.commit()
    finally:
        con.close()


def read_policy(con):
    expected = {"settings": ["version", "revision", "policy"],
                "events": ["sender", "id", "fingerprint", "day", "bucket", "units", "body_bytes", "targets", "mode", "recorded_ms", "revision"]}
    for table, names in expected.items():
        actual = [r["name"] for r in con.execute("PRAGMA table_info(" + table + ")")]
        if actual != names:
            fail("corrupt_state", "账本表结构与支持格式不符；拒绝读取或覆盖历史。")
    if con.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        fail("corrupt_state", "账本完整性检查失败；不会忽略损坏数据或从零重建。")
    rows = con.execute("SELECT version, revision, policy FROM settings").fetchall()
    if len(rows) != 1 or rows[0]["version"] != 1 or not integer(rows[0]["revision"], 0, 1000000000):
        fail("corrupt_state", "账本版本或策略记录无效。")
    p = policy_value(strict_json(rows[0]["policy"]))
    count = con.execute("SELECT count(*) FROM events").fetchone()[0]
    if count > MAX_EVENTS:
        fail("corrupt_state", "账本记录数超过支持上限。")
    for event in con.execute("SELECT * FROM events"):
        try:
            targets = strict_json(event["targets"])
            valid = (all(identifier(event[k]) for k in ("sender", "id", "bucket"))
                     and isinstance(event["fingerprint"], str)
                     and re.fullmatch(r"[0-9a-f]{64}", event["fingerprint"])
                     and isinstance(event["day"], str)
                     and re.fullmatch(r"\d{4}-\d{2}-\d{2}", event["day"])
                     and integer(event["units"], 1, 128)
                     and integer(event["body_bytes"], 0, 65536)
                     and integer(event["recorded_ms"], 0, 4102444800000)
                     and integer(event["revision"], 0, rows[0]["revision"])
                     and event["mode"] in ("online", "offline")
                     and isinstance(targets, list) and 1 <= len(targets) <= 128
                     and all(identifier(t) for t in targets)
                     and len(set(targets)) == len(targets))
            if not valid:
                fail("corrupt_state", "账本记录字段无效；不会忽略损坏记录。")
            datetime.fromisoformat(event["day"])
        except (Failure, ValueError, TypeError):
            fail("corrupt_state", "账本记录字段无效；不会忽略损坏记录。")
    return p, rows[0]["revision"]


def result(**fields):
    return {"ok": True, "version": VERSION, **fields}


def manage(req):
    action = req.get("action")
    if action not in ("init", "status", "configure"):
        fail("invalid_action", "action 只接受 init、status 或 configure。")
    write = action != "status"
    with connection(req.get("workspace"), write, action == "init") as con:
        p, revision = read_policy(con)
        count = con.execute("SELECT count(*) FROM events").fetchone()[0]
        if action == "configure":
            if not integer(req.get("expected_revision"), 0, 1000000000):
                fail("invalid_revision", "configure 必须提供最新的 expected_revision。")
            if req["expected_revision"] != revision:
                fail("revision_conflict", "策略修订号已变化；请重新读取 status，不会覆盖并发修改。")
            proposed = policy_value(strict_json(req.get("policy_json")))
            if count and any(p[k] != proposed[k] for k in ("timezone", "day_boundary_hour")):
                fail("time_policy_locked", "已有用量后不能更换时区或日界；请保留账本，改用新的工作目录。")
            if proposed != p:
                revision += 1
                con.execute("UPDATE settings SET revision=?,policy=?", (revision, packed(proposed)))
            p = proposed
        return result(action=action, revision=revision, policy=p, event_count=count,
                      message="策略已保存。" if write else "只读状态；未修改策略或账本。")


def evaluate(con, p, revision, m, now):
    last = con.execute("SELECT max(recorded_ms) FROM events").fetchone()[0]
    if last is not None and now < last:
        fail("clock_rollback", "系统时间早于已记录事件；请校正时间后重试。")
    if "sentAtMs" in m and not 0 <= now - m["sentAtMs"] <= 300000:
        fail("invalid_event_time", "sentAtMs 必须在当前时间前五分钟以内，不接受未来或回填事件。")
    bucket = "offline" if m["mode"] == "offline" else m["type"]
    if bucket not in p["buckets"]:
        fail("unknown_bucket", "策略未定义该配额桶；不会使用无限额默认值。")
    day = day_of(now, p)
    setting = p["buckets"][bucket]
    units = 1 if m["mode"] == "offline" or setting["per_send"] else len(m["targets"])
    used = con.execute("SELECT coalesce(sum(units),0) FROM events WHERE sender=? AND day=? AND bucket=?", (m["as"], day, bucket)).fetchone()[0]
    reason, text = "allowed", "当前声明满足本地策略；此预览不保留额度，也不证明消息已发送。"
    if m["mode"] == "online":
        flat = "".join(c for c in m["body"] if not c.isspace() and unicodedata.category(c)[0] not in "PS")
        if len(m["body"].encode()) <= p["ack_max_bytes"] and flat and ACK.fullmatch(flat):
            reason, text = "ack_only", "正文只有回执词；请合并沟通内容。"
        elif m["hop"] >= p["hop_max"]:
            reason, text = "hop_limit", "回复链深度达到上限。"
        else:
            recent = con.execute("SELECT targets FROM events WHERE sender=? AND mode='online' AND recorded_ms>? AND recorded_ms<=?", (m["as"], now-p["pair_window_seconds"]*1000, now)).fetchall()
            for target in m["targets"]:
                if sum(target in json.loads(r["targets"]) for r in recent) >= p["pair_max"]:
                    reason, text = "pair_limit", "同一收发对在当前时间窗口内已达到上限。"
                    break
    if reason == "allowed" and used + units > setting["limit"]:
        reason, text = "quota_exceeded", "计入本次用量会超过该发件人的当日配额。"
    return result(verdict="allowed" if reason == "allowed" else "rejected", reason_code=reason,
                  message=text, recorded=False, policy_revision=revision, day=day, bucket=bucket,
                  units=units, used_before=used, limit=setting["limit"], remaining=max(0, setting["limit"]-used),
                  message_sha256=digest(m), accounting_time_ms=now)


def check_or_record(req, record, now):
    m = message_value(strict_json(req.get("message_json")))
    if record and req.get("confirmed") is not True:
        fail("confirmation_required", "写账必须由用户明确授权，并提供 confirmed=true；不得从正文推断授权。")
    with connection(req.get("workspace"), record) as con:
        p, revision = read_policy(con)
        now = time.time_ns()//1000000 if now is None else now
        previous = con.execute("SELECT fingerprint,day,bucket,units,revision FROM events WHERE sender=? AND id=?", (m["as"], m["id"])).fetchone()
        if previous:
            if previous["fingerprint"] != digest(m):
                fail("event_conflict", "同一发件人和消息 ID 已登记不同内容；拒绝覆盖原记录。")
            return result(verdict="already_recorded", recorded=True, duplicate=True, day=previous["day"],
                          bucket=previous["bucket"], units=previous["units"], policy_revision=previous["revision"],
                          message_sha256=previous["fingerprint"], message="此消息已登记；没有重复计数。")
        out = evaluate(con, p, revision, m, now)
        if record and out["verdict"] == "allowed":
            if con.execute("SELECT count(*) FROM events").fetchone()[0] >= MAX_EVENTS:
                fail("event_limit", "账本已达 10000 条；请保留原账本并使用新的工作目录。")
            con.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?)", (m["as"],m["id"],digest(m),out["day"],out["bucket"],out["units"],len(m["body"].encode()),packed(m["targets"]),m["mode"],now,revision))
            out.update(recorded=True, duplicate=False, message="已按用户明确声明登记用量；不表示实际投递已被独立验证。", remaining=out["remaining"]-out["units"])
        return out


def summary(entries):
    out = {}
    for e in entries:
        key = (e["day"], e["as"], e["bucket"])
        row = out.setdefault(key, {"day": key[0], "as": key[1], "bucket": key[2], "letters": 0, "units": 0, "body_bytes": 0})
        row["letters"] += 1
        row["units"] += e["units"]
        row["body_bytes"] += e["body_bytes"]
    return [out[k] for k in sorted(out)]


def report(req, now):
    action = req.get("action", "report")
    if action not in ("report", "reconcile"):
        fail("invalid_action", "action 只接受 report 或 reconcile。")
    days = req.get("days", 7)
    if not integer(days, 1, 31):
        fail("invalid_days", "days 必须是 1～31 的整数。")
    with connection(req.get("workspace")) as con:
        p, revision = read_policy(con)
        now = time.time_ns()//1000000 if now is None else now
        last = con.execute("SELECT max(recorded_ms) FROM events").fetchone()[0]
        if last is not None and now < last:
            fail("clock_rollback", "系统时间早于已记录事件；请校正时间后重试。")
        today = day_of(now, p)
        earliest = (datetime.fromisoformat(today).date()-timedelta(days=days-1)).isoformat()
        rows = con.execute("SELECT * FROM events WHERE day>=? AND day<=? ORDER BY recorded_ms,sender,id", (earliest, today)).fetchall()
        if len(rows) > 500:
            fail("report_limit", "此范围超过 500 条；请缩小 days。原账本未修改。")
        entries = [{"id": r["id"], "as": r["sender"], "day": r["day"], "bucket": r["bucket"], "units": r["units"], "body_bytes": r["body_bytes"]} for r in rows]
        out = result(action=action, policy_revision=revision, start_day=earliest, end_day=today,
                     event_count=len(entries), totals=summary(entries), entries=entries,
                     message="只读汇总；正文不写入账本，记录不证明实际投递。")
        if action == "reconcile":
            supplied = strict_json(req.get("entries_json"))
            if not isinstance(supplied, list) or len(supplied)>500:
                fail("invalid_entries", "重算输入必须是最多 500 条的记录数组。")
            seen = set()
            for e in supplied:
                if not isinstance(e, dict) or set(e)!={"id","as","day","bucket","units","body_bytes"}:
                    fail("invalid_entries", "重算记录字段必须与 report.entries 完全一致。")
                if not all(identifier(e[k]) for k in ("id","as","bucket")) or not integer(e["units"],1,128) or not integer(e["body_bytes"],0,65536):
                    fail("invalid_entries", "重算记录的标识、单位或字节数无效。")
                if not isinstance(e["day"],str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",e["day"]) or not earliest<=e["day"]<=today:
                    fail("invalid_entries", "重算日期必须位于本次完整汇总范围内。")
                datetime.fromisoformat(e["day"])
                key=(e["as"],e["id"])
                if key in seen:
                    fail("duplicate_entry", "重算输入包含重复消息 ID。")
                seen.add(key)
            # Compare individual identities/values as well as independent aggregate totals;
            # matching totals alone would conceal substituted messages.
            order=lambda e:(e["as"],e["id"])
            matched=sorted(entries,key=order)==sorted(supplied,key=order)
            out.update(matched=matched, supplied_totals=summary(supplied), supplied_event_count=len(supplied),
                       reason_code="matched" if matched else "reconciliation_mismatch",
                       message="输入记录与账本一致；未写入或修复账本。" if matched else "输入记录与账本不同；未写入或修复账本。")
        return out


def dispatch(operation, req, *, now_ms=None):
    try:
        if not isinstance(req, dict):
            fail("invalid_request", "工具输入必须是对象。")
        allowed = {"policy":{"workspace","action","expected_revision","policy_json"},
                   "check":{"workspace","message_json"}, "record":{"workspace","message_json","confirmed"},
                   "report":{"workspace","action","days","entries_json"}}
        if operation not in allowed or set(req)-allowed[operation]:
            fail("invalid_request", "请求含有未知操作或参数。")
        now = time.time_ns()//1000000 if now_ms is None else now_ms
        if not integer(now,0,4102444800000):
            fail("invalid_clock", "系统时间超出支持范围。")
        if operation == "policy":
            return manage(req)
        if operation in ("check","record"):
            return check_or_record(req,operation=="record",now_ms)
        return report(req,now_ms)
    except Failure as exc:
        return {"ok":False,"version":VERSION,"error":{"code":exc.code,"message":exc.message}}
    except sqlite3.Error as exc:
        code="state_busy" if "locked" in str(exc).lower() else "corrupt_state"
        return {"ok":False,"version":VERSION,"error":{"code":code,"message":"账本被占用或数据库无效；操作未完成，不会忽略数据重建。"}}
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        return {"ok":False,"version":VERSION,"error":{"code":"operation_failed","message":"本地路径、权限、编码或状态无效；操作未完成。"}}
