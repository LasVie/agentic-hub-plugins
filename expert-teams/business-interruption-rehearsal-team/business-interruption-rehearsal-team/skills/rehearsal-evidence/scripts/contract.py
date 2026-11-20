"""输入、阶段证据及交付文件的共同契约。"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys


GATES = ("writable", "snapshot_verified", "owner_approved")
MAX_BYTES = 512 * 1024
ID_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", flags=re.ASCII)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, expected, where):
    require(type(value) is dict and set(value) == set(expected.split()),
            f"{where}的字段不完整或含未知字段，应为 {expected}")
    return value


def number(value, low, high, where):
    require(type(value) is int and low <= value <= high, f"{where}须为 {low}–{high} 范围内的整数")
    return value


def identifier(value, where):
    require(type(value) is str and len(value) <= 40 and ID_PATTERN.fullmatch(value),
            f"{where}须为不超过40字符的小写标识符")
    return value


def label(value, where):
    require(type(value) is str and 1 <= len(value.strip()) <= 120
            and all(ch.isprintable() for ch in value), f"{where}须为可读的单行文字")
    return value


def sequence(value, low, high, where):
    require(type(value) is list and low <= len(value) <= high, f"{where}须含 {low}–{high} 项")
    return value


def indexed(rows, where):
    result = {}
    for row in rows:
        key = identifier(row["id"], where + "标识")
        require(key not in result, f"{where}标识重复：{key}")
        result[key] = row
    return result


def json_pairs(pairs):
    result = {}
    for key, val in pairs:
        require(key not in result, f"JSON 字段重复：{key}")
        result[key] = val
    return result


def reject_constant(value):
    raise ValueError(f"JSON 数值无效：{value}")


def encode(value, *, compact=False):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(",", ":") if compact else None,
                       indent=None if compact else 2) + "\n").encode("utf-8")


def read(path):
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, "JSON 文件超过 512 KiB")
    value = json.loads(data.decode("utf-8"), object_pairs_hook=json_pairs, parse_constant=reject_constant)
    return value, sha256(data).hexdigest()


def same(left, right):
    return encode(left, compact=True) == encode(right, compact=True)


def dependency_order(flows):
    done = []
    pending = set(flows)
    while pending:
        ready = sorted(key for key in pending if set(flows[key]["needs"]).issubset(done))
        require(bool(ready), "流程依赖存在循环，请核实原始约定")
        done.extend(ready)
        pending.difference_update(ready)
    return done


def read_case(path):
    case, digest = read(path)
    fields(case, "schema id title staff workflows scenarios", "案例")
    number(case["schema"], 1, 1, "案例版本")
    identifier(case["id"], "案例")
    label(case["title"], "案例标题")
    staff = indexed([fields(s, "id name capacity", "人员")
                     for s in sequence(case["staff"], 1, 8, "人员")], "人员")
    for person in staff.values():
        label(person["name"], "人员名称")
        number(person["capacity"], 0, 40, "中断期人员登记限额")
    flows = indexed([fields(f, "id name owner needs manual_limit startup source", "流程")
                     for f in sequence(case["workflows"], 2, 4, "流程")], "流程")
    for key, flow in flows.items():
        label(flow["name"], "流程名称")
        label(flow["source"], f"流程 {key} 的证据位置")
        require(identifier(flow["owner"], "负责人") in staff, f"流程 {key} 缺少明确负责人")
        needs = [identifier(dep, "依赖流程") for dep in sequence(flow["needs"], 0, 3, "依赖")]
        require(len(set(needs)) == len(needs) and set(needs) <= flows.keys(), f"流程 {key} 依赖无效")
        number(flow["manual_limit"], 0, 40, "流程登记限额")
        number(flow["startup"], 0, 120, "准备分钟")
    dependency_order(flows)
    scenarios = indexed([fields(s, "id title horizon target events items snapshot", "情景")
                         for s in sequence(case["scenarios"], 2, 2, "情景")], "情景")
    for scenario in scenarios.values():
        validate_scenario(scenario, flows)
    return case, digest


def validate_scenario(scenario, flows):
    label(scenario["title"], "情景标题")
    horizon = number(scenario["horizon"], 20, 480, "情景时长")
    number(scenario["target"], 1, horizon, "复工目标分钟")
    events = indexed([fields(e, "id minute kind", "事件")
                      for e in sequence(scenario["events"], 0, 4, "情景事件")], "事件")
    timeline = {}
    for event in events.values():
        kind = event["kind"]
        require(type(kind) is str and kind in ("readonly", *GATES) and kind not in timeline,
                "情景事件种类无效或重复")
        timeline[kind] = number(event["minute"], 1, horizon, "事件时间")
    if "readonly" in timeline and "writable" in timeline:
        require(timeline["readonly"] < timeline["writable"], "只读必须早于写入恢复")
    if "snapshot_verified" in timeline:
        readable = min(timeline.get("readonly", horizon + 1), timeline.get("writable", horizon + 1))
        require(readable <= timeline["snapshot_verified"], "快照核验不能早于服务可读")
    else:
        require(scenario["snapshot"] == [], "没有快照核验事件时须使用空快照")
    items = indexed([fields(i, "id flow arrival due revision", "工作项")
                     for i in sequence(scenario["items"], 1, 24, "工作项")], "工作项")
    for item in items.values():
        require(identifier(item["flow"], "工作项流程") in flows, f"工作项 {item['id']} 引用未知流程")
        arrival = number(item["arrival"], 0, horizon, "到达分钟")
        number(item["due"], arrival, horizon, "工作项目标分钟")
        number(item["revision"], 1, 999, "工作项版本")
    snapshot = indexed([fields(s, "id revision", "快照行")
                        for s in sequence(scenario["snapshot"], 0, 48, "快照")], "快照")
    for row in snapshot.values():
        number(row["revision"], 1, 999, "快照版本")
        if row["id"] in items:
            require(items[row["id"]]["arrival"] <= timeline["snapshot_verified"],
                    f"快照含尚未到达的工作项：{row['id']}")


def members(case):
    return {r["id"]: r for r in case["staff"]}, {r["id"]: r for r in case["workflows"]}


def envelope(kind, case_hash, data, **parents):
    return {"schema": 1, "kind": kind, "case_sha256": case_hash, "parents": parents, "data": data}


def stage(path, kind, case_hash, **parents):
    value, digest = read(path)
    fields(value, "schema kind case_sha256 parents data", kind)
    require(type(value["schema"]) is int and value["schema"] == 1 and value["kind"] == kind
            and value["case_sha256"] == case_hash and same(value["parents"], parents),
            f"交接 {kind} 的类型、输入或上游摘要不一致")
    return value["data"], digest


def write_files(output, **files):
    directory = Path(output)
    directory.mkdir(exist_ok=False)
    for name, data in files.items():
        with (directory / name).open("xb") as stream:
            stream.write(data)


def write_stage(output, kind, case_hash, data, **parents):
    write_files(output, **{kind + ".json": encode(envelope(kind, case_hash, data, **parents))})


class ChineseParser(argparse.ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace("usage:", "用法：")

    def error(self, message):
        self.exit(2, f"参数无效。请使用 --help 查看命令。({message})\n")


def parser(purpose):
    p = ChineseParser(description=purpose, add_help=False)
    p.add_argument("-h", "--help", action="help", help="显示说明")
    p.add_argument("--input", required=True, help="用户确认的案例 JSON")
    p.add_argument("--output", required=True, help="尚不存在的独立输出子目录")
    return p


def run(function):
    try:
        return function() or 0
    except (ValueError, OSError, RecursionError) as exc:
        print(f"流程停止：{exc}", file=sys.stderr)
        return 2
