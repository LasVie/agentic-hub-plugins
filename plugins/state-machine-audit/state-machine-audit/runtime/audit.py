"""状态机行为审计：有限模型的只读、精确有界探索。

Ported/adapted from AmethystLuna/logicprobe, pinned e1b5ac4a426c43878863092bc79387700a8189cb.
Copyright (c) 2026 Amethyst Luna. MIT; full text: licenses/logicprobe/LICENSE.
Original upstream file header: licenses/logicprobe/UPSTREAM_HEADER.txt.
Changed 2026-10-26: narrow schema, strict finite domains, Chinese results, hash-bound
confirmation, enabled-transition dead ends and explicit incomplete search results.
Guard/fallback/update semantics and breadth-first invariant search are adapted from
tools/python/logicprobe-engine.py. This module does not expose the broader engine.
"""
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

VERSION = "1.0.1"
MAX_BYTES = 262144
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 20000
MAX_CONFIGURATIONS = 200000
LIMITS = {"max_states": (1, 2000, 2000), "max_edges": (1, 20000, 10000),
          "max_steps": (1, 64, 64)}
RESULT_BYTES = 196608


class Refusal(ValueError):
    def __init__(self, code, message, location=""):
        super().__init__(message)
        self.code, self.message, self.location = code, message, location


def require(condition, message, location="", code="model_invalid"):
    if not condition:
        raise Refusal(code, message, location)


def _object(value, allowed, required, location):
    require(type(value) is dict, "此处必须是对象。", location)
    require(set(value) <= set(allowed), "存在未知字段；不会忽略未支持的构造。", location)
    require(set(required) <= set(value), "缺少必需字段。", location)


def _array(value, low, high, location):
    require(type(value) is list and low <= len(value) <= high,
            f"此处必须是包含 {low} 至 {high} 项的数组。", location)


def _identifier(value, location):
    require(type(value) is str and 0 < len(value) <= 32 and value.strip() == value
            and all(ord(c) >= 32 and not 0xD800 <= ord(c) <= 0xDFFF for c in value),
            "标识符须为 1 至 32 个字符，不能含控制字符、孤立代理字符或首尾空白。", location)
    return value


def _integer(value, location, low=-1000000, high=1000000):
    require(type(value) is int and low <= value <= high,
            f"必须是 {low} 至 {high} 的整数；布尔值、浮点数及超范围数不被接受。", location)
    return value


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "JSON 含重复键；拒绝静默覆盖。", key, "duplicate_json_key")
        out[key] = value
    return out


def _constant(value):
    raise Refusal("model_invalid", "不接受 NaN 或 Infinity。")


def parse_json(raw):
    require(len(raw) <= MAX_BYTES, "输入超过 256 KiB。", code="input_too_large")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except Refusal:
        raise
    except RecursionError:
        raise Refusal("model_too_deep", "JSON 嵌套过深。") from None
    except (ValueError, UnicodeError):
        raise Refusal("invalid_json", "输入必须是严格的 UTF-8 JSON。") from None
    todo, count = [(value, 0)], 0
    while todo:
        item, depth = todo.pop()
        count += 1
        require(depth <= MAX_JSON_DEPTH, "JSON 嵌套超过 16 层。", code="model_too_deep")
        require(count <= MAX_JSON_NODES, "JSON 节点数量过多。", code="model_too_large")
        if type(item) is dict:
            todo.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            todo.extend((child, depth + 1) for child in item)
    return value


def _guard(guard, variables, location):
    require(type(guard) is dict, "守卫必须使用结构化对象，不能使用代码字符串。", location)
    if "variable" in guard:
        _object(guard, ("variable", "op", "value"), ("variable", "op", "value"), location)
        name = guard["variable"]
        require(type(name) is str and name in variables, "守卫引用了未声明的变量。", location)
        var = variables[name]
        allowed = ("==", "!=") if var["kind"] == "boolean" else ("==", "!=", "<", "<=", ">", ">=")
        require(guard["op"] in allowed, "此变量类型不支持该比较运算。", location)
        if var["kind"] == "boolean":
            require(type(guard["value"]) is bool, "布尔守卫只能比较布尔值。", location)
        else:
            _integer(guard["value"], location + ".value")
        return
    require(len(guard) == 1 and next(iter(guard), "") in ("all", "any", "not"),
            "复合守卫只允许单一 all、any 或 not 字段。", location)
    if "not" in guard:
        _guard(guard["not"], variables, location + ".not")
    else:
        key = next(iter(guard))
        _array(guard[key], 1, 16, location + "." + key)
        for i, child in enumerate(guard[key]):
            _guard(child, variables, f"{location}.{key}[{i}]")


def validate(model):
    _object(model, ("schemaVersion", "init", "states", "transitions", "variables", "invariants"),
            ("schemaVersion", "init", "states", "transitions"), "model")
    require(type(model["schemaVersion"]) is int and model["schemaVersion"] == 1,
            "仅支持 schemaVersion=1。", "schemaVersion")
    _array(model["states"], 1, 100, "states")
    _array(model["transitions"], 0, 500, "transitions")
    states = {}
    for i, state in enumerate(model["states"]):
        loc = f"states[{i}]"
        _object(state, ("id", "terminal"), ("id",), loc)
        sid = _identifier(state["id"], loc + ".id")
        require(sid not in states, "状态标识符重复。", loc)
        require("terminal" not in state or type(state["terminal"]) is bool,
                "terminal 必须是布尔值。", loc)
        states[sid] = state
    require(type(model["init"]) is str and model["init"] in states,
            "初始状态必须是已声明的状态。", "init")
    variable_list = model.get("variables", [])
    _array(variable_list, 0, 6, "variables")
    variables, product = {}, len(states)
    for i, variable in enumerate(variable_list):
        loc = f"variables[{i}]"
        _object(variable, ("name", "kind", "init", "min", "max"), ("name", "kind", "init"), loc)
        name = _identifier(variable["name"], loc + ".name")
        require(name not in variables, "变量名重复。", loc)
        require(variable["kind"] in ("boolean", "integer"), "变量仅支持 boolean 或 integer。", loc)
        if variable["kind"] == "boolean":
            require(type(variable["init"]) is bool and "min" not in variable and "max" not in variable,
                    "布尔变量须使用布尔初值，且不能声明 min/max。", loc)
            width = 2
        else:
            require("min" in variable and "max" in variable, "整数变量必须声明有限 min/max。", loc)
            low, high = _integer(variable["min"], loc + ".min"), _integer(variable["max"], loc + ".max")
            initial = _integer(variable["init"], loc + ".init")
            require(low <= initial <= high and high - low < 64,
                    "初值必须在声明域内；每个整数域最多 64 个值。", loc)
            width = high - low + 1
        variables[name] = variable
        product *= width
    require(product <= MAX_CONFIGURATIONS, "控制状态与变量域的乘积超过 200000。", code="model_too_large")
    groups, events, transition_ids = {}, set(), set()
    for i, transition in enumerate(model["transitions"]):
        loc = f"transitions[{i}]"
        _object(transition, ("from", "event", "to", "guard", "updates"), ("from", "event", "to"), loc)
        for key in ("from", "to"):
            require(type(transition[key]) is str and transition[key] in states,
                    "迁移端点必须引用已声明状态。", loc + "." + key)
        require(not states[transition["from"]].get("terminal", False), "终态不允许有出边。", loc)
        event = _identifier(transition["event"], loc + ".event")
        events.add(event)
        if "guard" in transition:
            _guard(transition["guard"], variables, loc + ".guard")
        updates = transition.get("updates", [])
        _array(updates, 0, 6, loc + ".updates")
        updated = set()
        for j, update in enumerate(updates):
            uloc = f"{loc}.updates[{j}]"
            _object(update, ("variable", "op", "value"), ("variable", "op", "value"), uloc)
            name = update["variable"]
            require(type(name) is str and name in variables and name not in updated,
                    "更新须引用已声明变量，同一迁移不能重复更新同一变量。", uloc)
            updated.add(name)
            if variables[name]["kind"] == "boolean":
                require(update["op"] == "set" and type(update["value"]) is bool,
                        "布尔变量只允许 set 布尔值。", uloc)
            else:
                require(update["op"] in ("set", "inc", "dec"), "整数更新只允许 set/inc/dec。", uloc)
                _integer(update["value"], uloc + ".value")
        encoded = json.dumps(transition, ensure_ascii=False, sort_keys=True)
        require(encoded not in transition_ids, "迁移记录完全重复。", loc)
        transition_ids.add(encoded)
        groups.setdefault((transition["from"], event), []).append(transition)
    invariants = model.get("invariants", [])
    _array(invariants, 0, 8, "invariants")
    ids, monitored = set(), set()
    for i, inv in enumerate(invariants):
        loc = f"invariants[{i}]"
        require(type(inv) is dict, "不变量必须是对象。", loc)
        kind = inv.get("kind")
        if kind == "never-states":
            _object(inv, ("id", "kind", "description", "states"), ("id", "kind", "description", "states"), loc)
            _array(inv["states"], 1, 100, loc + ".states")
            seen = set()
            for sid in inv["states"]:
                require(type(sid) is str and sid in states and sid not in seen,
                        "禁止状态须引用已声明状态且不能重复。", loc)
                seen.add(sid)
        elif kind == "event-before-state":
            _object(inv, ("id", "kind", "description", "event", "state"),
                    ("id", "kind", "description", "event", "state"), loc)
            require(type(inv["event"]) is str and inv["event"] in events,
                    "先决事件必须在迁移中声明。", loc)
            require(type(inv["state"]) is str and inv["state"] in states,
                    "目标状态必须已声明。", loc)
            monitored.add(inv["event"])
        else:
            raise Refusal("model_invalid", "不支持该不变量类型；不会退化为空检查。", loc)
        iid = _identifier(inv["id"], loc + ".id")
        require(iid not in ids, "不变量标识符重复。", loc)
        ids.add(iid)
        description = inv["description"]
        require(type(description) is str and 0 < len(description.strip()) <= 300
                and not any(0xD800 <= ord(c) <= 0xDFFF for c in description),
                "不变量必须有 1 至 300 字的说明。", loc)
    for group in groups.values():
        group.sort(key=lambda t: json.dumps(t, sort_keys=True, ensure_ascii=False))
    return {"model": model, "states": states, "variables": variables, "groups": groups,
            "events": sorted(events), "monitored": {event: 1 << i for i, event in enumerate(sorted(monitored))},
            "theoretical_configurations": product * (2 ** len(monitored))}


def _eval_guard(guard, values):
    if "variable" in guard:
        actual, expected, op = values[guard["variable"]], guard["value"], guard["op"]
        return {"==": lambda: actual == expected, "!=": lambda: actual != expected,
                "<": lambda: actual < expected, "<=": lambda: actual <= expected,
                ">": lambda: actual > expected, ">=": lambda: actual >= expected}[op]()
    if "all" in guard:
        return all(_eval_guard(child, values) for child in guard["all"])
    if "any" in guard:
        return any(_eval_guard(child, values) for child in guard["any"])
    return not _eval_guard(guard["not"], values)


def _applicable_transitions(group, values):
    # Upstream semantics: matching guarded branches precede unguarded fallback.
    matched = [t for t in group if "guard" in t and _eval_guard(t["guard"], values)]
    return matched or [t for t in group if "guard" not in t]


def _apply_updates(transition, values):
    result = dict(values)
    for update in transition.get("updates", []):
        name, op, value = update["variable"], update["op"], update["value"]
        if op == "set":
            result[name] = value
        elif op == "inc":
            result[name] += value
        else:
            result[name] -= value
    return result


def _path(parents, key):
    path = []
    while parents[key] is not None:
        key, step = parents[key]
        path.append(step)
    path.reverse()
    return path


def explore(compiled, options):
    model, variables = compiled["model"], compiled["variables"]
    names = sorted(variables)
    initial_values = tuple(variables[name]["init"] for name in names)
    initial = (model["init"], initial_values, 0)
    parents, queue, depth = {initial: None}, deque([initial]), {initial: 0}
    reached, explored, edges, reasons = {model["init"]}, 0, 0, set()
    findings, failed_properties = {}, set()

    def record(identity, code, message, key, step=None, property_id=None):
        if identity in findings:
            return
        trace = _path(parents, key)
        if step is not None:
            trace.append(step)
        item = {"code": code, "message": message, "trace_length": len(trace), "trace": trace}
        if property_id is not None:
            item["property_id"] = property_id
            failed_properties.add(property_id)
        findings[identity] = item

    def properties(key, predecessor=None, step=None):
        state, _, seen = key
        for inv in model.get("invariants", []):
            violates = (state in inv["states"]) if inv["kind"] == "never-states" else (
                state == inv["state"] and not seen & compiled["monitored"][inv["event"]])
            if violates:
                record(("property", inv["id"]), "invariant_violated",
                       "违反不变量：" + inv["description"], key if predecessor is None else predecessor,
                       step, inv["id"])

    properties(initial)
    while queue:
        if explored >= options["max_states"]:
            reasons.add("state_limit")
            break
        key = queue.popleft()
        explored += 1
        state, vals, seen = key
        values = dict(zip(names, vals))
        enabled = []
        for event in compiled["events"]:
            group = compiled["groups"].get((state, event), [])
            enabled.extend(_applicable_transitions(group, values))
        if not enabled and not compiled["states"][state].get("terminal", False):
            record(("dead_end", state), "enabled_dead_end", "可达的非终态没有可启用迁移：" + state, key)
        for transition in enabled:
            if edges >= options["max_edges"]:
                reasons.add("edge_limit")
                break
            edges += 1
            next_values = _apply_updates(transition, values)
            step = {"from": state, "event": transition["event"], "to": transition["to"],
                    "before": values, "after": next_values}
            escaped = [name for name in names if variables[name]["kind"] == "integer"
                       and not variables[name]["min"] <= next_values[name] <= variables[name]["max"]]
            if escaped:
                reasons.add("domain_escape")
                for name in escaped:
                    record(("domain", name), "domain_escape", "迁移更新越出已声明的有限变量域：" + name, key, step)
                continue
            nxt = (transition["to"], tuple(next_values[name] for name in names),
                   seen | compiled["monitored"].get(transition["event"], 0))
            # A violation at a generated successor is decisive, even when further
            # exploration is capped; absence of a violation never becomes a proof.
            properties(nxt, key, step)
            reached.add(nxt[0])
            if nxt in parents:
                continue
            if depth[key] + 1 > options["max_steps"]:
                reasons.add("depth_limit")
                continue
            if len(parents) >= options["max_states"]:
                reasons.add("state_limit")
                continue
            parents[nxt], depth[nxt] = (key, step), depth[key] + 1
            queue.append(nxt)
        if "edge_limit" in reasons:
            break
    complete = not reasons
    verdict = "fail" if findings else ("pass" if complete else "incomplete")
    labels = {"pass": "模型检查通过", "fail": "发现模型违例", "incomplete": "搜索未完成，结论未决"}
    report = {"ok": True, "ran": True, "version": VERSION, "verdict": verdict,
              "message": labels[verdict], "analysis_complete": complete,
              "summary": {"explored_configurations": explored, "discovered_configurations": len(parents),
                          "examined_transitions": edges, "finding_count": len(findings),
                          "reachable_states": sorted(reached),
                          "unreachable_states": sorted(set(compiled["states"]) - reached) if complete else [],
                          "unresolved_states": sorted(set(compiled["states"]) - reached) if not complete else []},
              "properties": [{"id": inv["id"], "description": inv["description"],
                              "status": "fail" if inv["id"] in failed_properties else (
                                  "pass" if complete else "incomplete")}
                             for inv in model.get("invariants", [])],
              "incomplete_reasons": sorted(reasons), "limits": options,
              "findings": list(findings.values())[:20], "findings_omitted": max(0, len(findings) - 20),
              "coverage_note": "仅核验本次明确提供的有限模型；不证明源代码、真实并发、时钟或概率性质。无不变量时不会声称已验证安全属性。"}
    while len(json.dumps(report, ensure_ascii=False).encode()) > RESULT_BYTES and report["findings"]:
        report["findings"].pop()
        report["findings_omitted"] += 1
    return report


def _safe_path(raw, directory):
    require(type(raw) is str and len(raw) <= 4096 and Path(raw).is_absolute(),
            "路径必须是完整绝对路径。", code="invalid_path")
    path = Path(raw)
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        require(part not in ("..", "."), "路径不能含父目录跳转。", code="invalid_path")
        cursor /= part
        require(not cursor.is_symlink(), "不接受符号链接路径。", code="unsafe_path")
    require(path.is_dir() if directory else path.is_file(), "指定目录或文件不存在。", code="path_missing")
    return path


def load_model(workspace, path):
    root = _safe_path(workspace, True)
    source = _safe_path(path, False)
    require(source.resolve().is_relative_to(root.resolve()), "输入文件必须位于指定工作目录内。", code="outside_workspace")
    require(os.name == "posix", "当前版本仅支持具备目录文件描述符的 macOS/Linux。", code="unsupported_platform")
    # Hold every directory open and traverse without following links. A parent
    # replacement after preflight cannot redirect this read outside the workspace.
    directories = []
    try:
        directory = os.open(root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        directories.append(directory)
        for part in root.parts[1:]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            directories.append(directory)
        relative = source.relative_to(root)
        for part in relative.parts[:-1]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            directories.append(directory)
        fd = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except BaseException:
        for directory in reversed(directories):
            os.close(directory)
        raise
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode), "只接受普通文件。", code="unsafe_path")
        require(before.st_size <= MAX_BYTES, "输入超过 256 KiB。", code="input_too_large")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            raw = handle.read(MAX_BYTES + 1)
        after = os.fstat(fd)
        current = os.stat(relative.name, dir_fd=directory, follow_symlinks=False)
        require((before.st_ino, before.st_dev, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                and (current.st_ino, current.st_dev) == (after.st_ino, after.st_dev),
                "读取时输入发生变化，请重新检查模型。", code="model_changed")
    finally:
        os.close(fd)
        for directory in reversed(directories):
            os.close(directory)
    return validate(parse_json(raw)), hashlib.sha256(raw).hexdigest()


def dispatch(operation, params):
    try:
        require(operation in ("inspect", "audit"), "未知操作。", code="invalid_request")
        allowed = {"workspace", "path"} if operation == "inspect" else {
            "workspace", "path", "confirmed", "expected_sha256", *LIMITS}
        required = {"workspace", "path"} if operation == "inspect" else {
            "workspace", "path", "confirmed", "expected_sha256"}
        _object(params, allowed, required, "request")
        if operation == "audit":
            require(params["confirmed"] is True, "须先展示模型并取得用户明确确认，再运行审计。", code="confirmation_required")
            expected = params["expected_sha256"]
            require(type(expected) is str and len(expected) == 64 and all(c in "0123456789abcdef" for c in expected),
                    "expected_sha256 必须是 inspect 实际返回的完整小写 SHA-256。", code="invalid_request")
        compiled, digest = load_model(params["workspace"], params["path"])
        if operation == "inspect":
            m = compiled["model"]
            return {"ok": True, "ran": True, "version": VERSION, "message": "模型格式有效，请先核对状态、守卫、更新与不变量，再确认此哈希。",
                    "model_sha256": digest, "init": m["init"], "states": m["states"], "variables": m.get("variables", []),
                    "invariants": m.get("invariants", []), "transition_count": len(m["transitions"]),
                    "transition_table": m["transitions"][:50], "transitions_omitted": max(0, len(m["transitions"]) - 50),
                    "configuration_upper_bound": compiled["theoretical_configurations"],
                    "semantics": "同一状态和事件下，若有守卫分支匹配则仅执行所有匹配分支；否则执行所有无守卫回退分支。初始事件历史为空。"}
        require(digest == params["expected_sha256"], "模型字节与已确认哈希不符；请重新 inspect 并取得确认。", code="model_changed")
        options = {}
        for key, (low, high, default) in LIMITS.items():
            options[key] = _integer(params.get(key, default), key, low, high)
        result = explore(compiled, options)
        result["model_sha256"] = digest
        return result
    except Refusal as exc:
        return {"ok": False, "ran": False, "version": VERSION,
                "error": {"code": exc.code, "message": exc.message, "location": exc.location}}
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        return {"ok": False, "ran": False, "version": VERSION,
                "error": {"code": "input_unavailable", "message": "无法安全读取或核验输入；本次未完成审计。"}}


def main():
    class ChineseParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "参数无效；请使用 --help 查看中文说明。\n")

        def format_help(self):
            return super().format_help().replace("usage:", "用法：")

    parser = ChineseParser(description="状态机行为审计：只读检查模型，按已确认哈希执行有限探索。", add_help=False)
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示中文帮助并退出")
    parser.add_argument("operation", choices=("inspect", "audit"), help="inspect 展示模型；audit 核验已确认模型")
    parser.add_argument("--input-json", required=True, help="工具参数的完整 JSON 对象")
    args = parser.parse_args()
    try:
        params = parse_json(args.input_json.encode("utf-8"))
        result = dispatch(args.operation, params)
    except Refusal as exc:
        result = {"ok": False, "ran": False, "version": VERSION,
                  "error": {"code": exc.code, "message": exc.message}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("verdict") == "pass" or result.get("ok") and args.operation == "inspect" else 2


if __name__ == "__main__":
    raise SystemExit(main())
