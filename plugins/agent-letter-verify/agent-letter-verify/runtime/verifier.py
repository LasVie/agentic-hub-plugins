"""代理信件完整性校验：受限、离线、工作目录隔离的验证核心。

Portions adapted from dsh-whale-post-verify 0.6.1, commit d78a82699722f0da6ae3d2b4cbdbaa411f2f67af.
Copyright (c) 2026 The Tank. MIT; complete original license: ../licenses/whale-post-verify/LICENSE.
Modified 2026-10-23: Python port, strict basic profile, private per-sender keys,
descriptor-relative file access, atomic revision-checked policy, honest verdicts.
Original source header identifies dsh-whale-post-verify / whale.verify apiVersion 1;
its default-disabled/skipped semantics are retained without DSH reminder/bus hooks.

原文件头原文（历史上游接口说明；本次受限适配以随包 README 为准）：
/**
 * dsh-whale-post-verify —— 安全校验（信封验签 ＋ 名单白名单）默认禁用（2026-10-09 定的口径）
 *
 * 接口：`ctx.whale.verify`（apiVersion 1）
 *   verify(letter) → { ok, why?, skipped? }   ← 核心只问这一句
 *   status()       → { enabled, dayIndex, willNag, allowCount, … }
 *   nag()          → string | null            ← 该印提示就返回文案；不该印就返回 null
 *   enable() / disable()
 *
 * 三态设计（依据见 `docs/`；另见同族实现的设计文档）：
 *   ① **默认禁用** —— 未开启时 `verify()` 一律放行，但返回值里带 `skipped: true`
 *      （让上层知道"这封没验过" —— 不许假装验过了）。
 *   ② **禁用中要提示** —— `nag()` 在未开启时返回一条醒目文案：
 *      "安全功能处于禁用中；建议开启，以免未知 agent 对其他 agent 发起欺骗或攻击" ＋ 一句开启方法。
 *   ③ **连提三天就不再提** —— 视为用户执意要在不安全的环境下使用；
 *      但 `status()` **永远**如实显示 `enabled: false`（"不再提示"≠"关掉了安全"）。
 *
 * 它守的两条线（与全仓一致）：
 *   · **只认接口，不认名字** —— 白名单来自 `config.allow`；代码里没有任何成员名。
 *   · **顶层零 I/O** —— 读盘只发生在 `createVerify()` 之后的方法调用里；异常一律自己吞。
 *
 * 验签怎么算：优先用 `config.bus`（或 `ctx.whale.bus`）给的 `digest`／`sign` ——
 *   这样它与核心**同一套算法**、不会各算各的；拿不到就用自己的内置实现（`sha256` ＋ `hmac`）。
 *   签名域与 `whale-bus` 的 `FIELD_ORDER` 一致（`mode` 也在里面）。
 */
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import uuid

VERSION = "1.0.1"
PROTOCOL = "whale-post-basic-v1"
FIELD_ORDER = ("v", "kind", "id", "from", "to", "seq", "subject", "body",
               "sha256", "sentAtMs", "type", "mode", "re", "hop")
STORE = ".agent-letter-verify"
MAX_LETTER = 1024 * 1024
MAX_BODY = 256 * 1024
SAFE_INT = 9007199254740991
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DIRECTORY = getattr(os, "O_DIRECTORY", 0)


class Refusal(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def require(ok, code, message):
    if not ok:
        raise Refusal(code, message)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key", "JSON 含有重复字段，无法确定唯一含义。")
        result[key] = value
    return result


def decode_json(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=object_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except Refusal:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise Refusal("invalid_json", "文件必须是有效且有限值的 UTF-8 JSON。") from None


def valid_id(value):
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def private_mode(info):
    if os.name == "posix":
        require(info.st_uid == os.geteuid() and not info.st_mode & 0o077,
                "unsafe_permissions", "信任目录或文件必须属于当前用户，且不可由组或其他用户访问。")


def read_at(parent, name, maximum, *, private=False):
    flags = os.O_RDONLY | NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent)
    except OSError:
        raise Refusal("file_unavailable", "文件不存在、是链接或无法安全读取。") from None
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                "unsafe_file", "只接受非链接的普通文件。")
        require(info.st_size <= maximum, "file_too_large", "文件超过此操作的大小上限。")
        if private:
            private_mode(info)
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(maximum + 1)
        require(len(data) <= maximum, "file_too_large", "文件读取期间超过大小上限。")
        return data
    finally:
        os.close(fd)


@contextmanager
def directory_at(parent, name, *, create=False, private=False):
    try:
        if create:
            try:
                os.mkdir(name, 0o700, dir_fd=parent)
            except FileExistsError:
                pass
        fd = os.open(name, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=parent)
    except OSError:
        raise Refusal("directory_unavailable", "目录不存在、是链接或不可访问；请检查工作目录和初始化状态。") from None
    try:
        require(stat.S_ISDIR(os.fstat(fd).st_mode), "unsafe_directory", "路径必须是目录。")
        if private:
            private_mode(os.fstat(fd))
        yield fd
    finally:
        os.close(fd)


@contextmanager
def workspace_handle(workspace):
    require(isinstance(workspace, str) and Path(workspace).is_absolute(),
            "invalid_workspace", "workspace 必须是已存在工作目录的绝对路径。")
    try:
        canonical = Path(workspace).resolve(strict=True)
        fd = os.open(canonical, os.O_RDONLY | DIRECTORY | NOFOLLOW)
    except (OSError, ValueError, RuntimeError):
        raise Refusal("invalid_workspace", "无法打开指定工作目录。") from None
    try:
        require(stat.S_ISDIR(os.fstat(fd).st_mode), "invalid_workspace", "workspace 必须是目录。")
        yield fd, canonical
    finally:
        os.close(fd)


def read_letter(root_fd, canonical, original_workspace, path):
    require(isinstance(path, str) and Path(path).is_absolute(),
            "invalid_letter_path", "letter_path 必须是工作目录内 JSON 文件的绝对路径。")
    require(".." not in Path(path).parts, "invalid_letter_path", "信件路径不能包含上级目录跳转。")
    relative = None
    for base in (canonical, Path(os.path.abspath(original_workspace))):
        try:
            relative = Path(path).relative_to(base)
            break
        except ValueError:
            pass
    require(relative is not None and relative.parts and relative.parts[0] != STORE,
            "outside_workspace", "信件必须位于指定工作目录中，且不能从私有信任目录读取。")
    parts = relative.parts
    require(path.endswith(".json"), "invalid_letter_path", "信件文件必须使用 .json 扩展名。")
    handles = []
    parent = root_fd
    try:
        for component in parts[:-1]:
            require(component not in ("", ".", ".."), "invalid_letter_path", "信件路径无效。")
            try:
                parent = os.open(component, os.O_RDONLY | DIRECTORY | NOFOLLOW, dir_fd=parent)
                handles.append(parent)
            except OSError:
                raise Refusal("file_unavailable", "无法安全打开信件目录；不跟随符号链接。") from None
        return read_at(parent, parts[-1], MAX_LETTER)
    finally:
        for handle in reversed(handles):
            os.close(handle)


def load_policy(store):
    policy = decode_json(read_at(store, "policy.json", 65536, private=True))
    require(isinstance(policy, dict) and set(policy) == {"schema_version", "enabled", "allow", "revision"},
            "invalid_policy", "信任策略结构无效；请恢复可信的本地配置。")
    require(type(policy["schema_version"]) is int and policy["schema_version"] == 1
            and type(policy["enabled"]) is bool and type(policy["revision"]) is int
            and 0 <= policy["revision"] <= SAFE_INT, "invalid_policy", "信任策略版本或状态无效。")
    validate_allow(policy["allow"])
    require(not policy["enabled"] or bool(policy["allow"]), "empty_allowlist", "开启校验时白名单不能为空。")
    return policy


def validate_allow(allow):
    require(isinstance(allow, list) and len(allow) <= 128 and all(valid_id(x) for x in allow)
            and len(set(allow)) == len(allow), "invalid_allowlist",
            "白名单最多 128 个唯一发件人；标识须为 1～64 位 ASCII 字母、数字、下划线或短横线，并以字母或数字开头。")


def sender_key(store, sender):
    require(valid_id(sender), "invalid_sender", "发件人标识格式不受支持。")
    with directory_at(store, "keys", private=True) as keys:
        data = read_at(keys, sender + ".key", 128, private=True)
    try:
        text = data.decode("ascii").strip()
    except UnicodeError:
        text = ""
    require(HEX.fullmatch(text.lower()) is not None, "invalid_key", "本地发件人密钥须为 64 位十六进制文本；不回落到共享密钥。")
    return bytes.fromhex(text)


@contextmanager
def policy_lock(store):
    try:
        fd = os.open("policy.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o600, dir_fd=store)
    except FileExistsError:
        raise Refusal("policy_busy", "策略正在更新或遗留锁文件仍存在；请稍后重试，不会自动删除锁。") from None
    try:
        yield
    finally:
        os.close(fd)
        os.unlink("policy.lock", dir_fd=store)


def save_policy(store, policy):
    name = "policy-" + uuid.uuid4().hex + ".tmp"
    fd = None
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o600, dir_fd=store)
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write((json.dumps(policy, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(name, "policy.json", src_dir_fd=store, dst_dir_fd=store)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(name, dir_fd=store)
        except FileNotFoundError:
            pass


def base_result():
    return {"version": VERSION, "protocol": PROTOCOL}


def policy_action(inputs):
    require(isinstance(inputs, dict) and set(inputs) <= {"workspace", "action", "enabled", "allow", "expected_revision"},
            "invalid_request", "策略请求含未知参数或不是对象。")
    action = inputs.get("action", "status")
    require(action in ("init", "status", "configure"), "invalid_action", "action 只能是 init、status 或 configure。")
    extras = set(inputs) - {"workspace", "action"}
    require(action == "configure" or not extras, "invalid_request", "只有 configure 可指定策略更改参数。")
    with workspace_handle(inputs.get("workspace")) as (root, canonical):
        with directory_at(root, STORE, create=action == "init", private=True) as store:
            created = False
            if action == "init":
                with directory_at(store, "keys", create=True, private=True):
                    pass
                with policy_lock(store):
                    try:
                        policy = load_policy(store)
                    except Refusal as err:
                        # Only a missing policy may be initialized. Invalid existing files are preserved.
                        try:
                            os.stat("policy.json", dir_fd=store, follow_symlinks=False)
                        except FileNotFoundError:
                            policy = {"schema_version": 1, "enabled": False, "allow": [], "revision": 0}
                            save_policy(store, policy)
                            created = True
                        else:
                            raise err
            elif action == "configure":
                require(type(inputs.get("expected_revision")) is int, "missing_revision", "更新策略须提供当前 expected_revision。")
                require("enabled" in inputs or "allow" in inputs, "no_change", "请明确指定 enabled 或 allow。")
                with policy_lock(store):
                    policy = load_policy(store)
                    require(inputs["expected_revision"] == policy["revision"], "revision_conflict", "策略已被其他操作修改；请先读取 status。")
                    if "enabled" in inputs:
                        require(type(inputs["enabled"]) is bool, "invalid_enabled", "enabled 必须是布尔值。")
                        policy["enabled"] = inputs["enabled"]
                    if "allow" in inputs:
                        validate_allow(inputs["allow"])
                        policy["allow"] = list(inputs["allow"])
                    require(not policy["enabled"] or policy["allow"], "empty_allowlist", "开启校验前必须设置非空白名单和本地专用密钥。")
                    if policy["enabled"]:
                        for sender in policy["allow"]:
                            sender_key(store, sender)
                    require(policy["revision"] < SAFE_INT, "revision_limit", "策略修订号已达到上限。")
                    policy["revision"] += 1
                    save_policy(store, policy)
            else:
                policy = load_policy(store)
            return {**base_result(), "ok": True, "message": "信任策略已初始化。" if created else "已读取或保存信任策略。",
                    "created": created, "workspace": str(canonical), "policy": policy,
                    "key_directory": str(canonical / STORE / "keys"),
                    "limitations": ["密钥不通过工具参数传入，也不会返回。", "此策略仅用于显式校验，不拦截宿主消息。"]}


def validate_envelope(env):
    require(isinstance(env, dict), "invalid_envelope", "信封必须是 JSON 对象。")
    require(set(env) <= set(FIELD_ORDER) | {"mac"}, "unknown_field", "信封包含未登记字段；该协议版本不接受扩展字段。")
    for key in ("v", "kind", "id", "from", "to", "mac"):
        require(key in env, "missing_field", "信封缺少必填字段。")
    require(type(env["v"]) is int and env["v"] == 1, "unsupported_version", "只支持 v=1 的基础信封。")
    require(env["kind"] in ("msg", "hello", "ack"), "unsupported_kind", "kind 只支持 msg、hello 或 ack。")
    for key in ("id", "from"):
        require(valid_id(env[key]), "invalid_identifier", "id 和 from 必须是受支持的 ASCII 标识。")
    for key in ("to", "subject", "body", "type", "mode", "re"):
        if key in env:
            text = env[key]
            require(isinstance(text, str), "invalid_field_type", "信封文本字段必须是字符串，不能是 null、数组或对象。")
            try:
                size = len(text.encode("utf-8"))
            except UnicodeError:
                raise Refusal("invalid_unicode", "信封文本包含无效 Unicode 字符。") from None
            require(size <= (MAX_BODY if key == "body" else 4096), "field_too_large", "信封文本字段超过上限。")
    require(bool(env["to"]) and len(env["to"]) <= 128, "invalid_recipient", "to 必须是 1～128 字符的收件标识。")
    for key in ("seq", "sentAtMs", "hop"):
        if key in env:
            require(type(env[key]) is int and 0 <= env[key] <= SAFE_INT, "invalid_integer", "数值字段必须是非负 JavaScript 安全整数。")
    if env["kind"] == "msg":
        require(all(k in env for k in ("seq", "body", "sha256")), "missing_field", "msg 信封须包含 seq、body 和 sha256。")
    for key in ("sha256", "mac"):
        if key in env:
            require(isinstance(env[key], str) and HEX.fullmatch(env[key]) is not None,
                    "invalid_digest", "sha256 和 mac 须为 64 位小写十六进制文本。")


def canonical_bytes(env):
    # Adapted from upstream JSON.stringify(FIELD_ORDER.filter(...).map(k => [k, env[k]])).
    return json.dumps([[key, env[key]] for key in FIELD_ORDER if key in env],
                      ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def verify_action(inputs):
    require(isinstance(inputs, dict) and set(inputs) == {"workspace", "letter_path"},
            "invalid_request", "校验须且只须提供 workspace 与 letter_path。")
    with workspace_handle(inputs["workspace"]) as (root, canonical):
        data = read_letter(root, canonical, inputs["workspace"], inputs["letter_path"])
        with directory_at(root, STORE, private=True) as store:
            policy = load_policy(store)
            result = {**base_result(), "ok": True, "verified": False, "policy_revision": policy["revision"],
                      "envelope_sha256": hashlib.sha256(data).hexdigest()}
            if not policy["enabled"]:
                return {**result, "verdict": "not_checked", "reason_code": "verification_disabled",
                        "message": "校验已关闭：此信件未校验，不能视为认证通过。"}
            try:
                env = decode_json(data)
                validate_envelope(env)
                require(env["from"] in policy["allow"], "sender_not_allowed", "发件人不在当前白名单中。")
                if env["kind"] == "msg":
                    actual = hashlib.sha256(env["body"].encode("utf-8")).hexdigest()
                    require(hmac.compare_digest(actual, env["sha256"]), "body_digest_mismatch", "正文摘要不符；正文或摘要可能被更改。")
                key = sender_key(store, env["from"])
                expected = hmac.new(key, canonical_bytes(env), hashlib.sha256).hexdigest()
                require(hmac.compare_digest(expected, env["mac"]), "mac_mismatch", "HMAC 不符；不能通过完整性校验。")
            except Refusal as err:
                return {**result, "verdict": "rejected", "reason_code": err.code, "message": err.message}
            return {**result, "verified": True, "verdict": "verified", "reason_code": "verified",
                    "message": "信封结构、发件人白名单、适用的正文摘要和 HMAC 校验通过。",
                    "sender": env["from"], "letter_id": env["id"], "kind": env["kind"],
                    "limitations": ["不证明唯一作者身份或内容真实性。", "不检查重放、时效或宿主消息投递。"]}


def dispatch(operation, inputs):
    try:
        if operation == "policy":
            return policy_action(inputs)
        if operation == "verify":
            return verify_action(inputs)
        raise Refusal("invalid_operation", "操作只支持 policy 或 verify。")
    except Refusal as err:
        return {**base_result(), "ok": False, "verified": False,
                "error": {"code": err.code, "message": err.message}}
    except (OSError, ValueError, TypeError, RecursionError):
        return {**base_result(), "ok": False, "verified": False,
                "error": {"code": "local_operation_failed", "message": "本地操作未完成；请检查参数、目录权限或策略状态。不会返回密钥或内部异常。"}}
