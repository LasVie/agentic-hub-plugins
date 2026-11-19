"""一周家务轮值的数据契约；不注册新的宿主工具。"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from datetime import date, timedelta
from pathlib import Path

VERSION = "1.0.0"
MAX_BYTES = 512 * 1024
ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{0,39}\Z")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def keys(obj: object, expected: set[str], label: str, optional: set[str] = frozenset()) -> dict:
    require(type(obj) is dict, f"{label}必须是对象")
    require(expected <= obj.keys() and obj.keys() <= expected | optional, f"{label}字段不完整或含未知字段")
    return obj


def integer(value: object, low: int, high: int, label: str) -> int:
    require(type(value) is int and low <= value <= high, f"{label}必须是{low}至{high}的整数")
    return value


def text(value: object, label: str, limit: int = 100) -> str:
    require(type(value) is str and 0 < len(value.strip()) <= limit, f"{label}须为非空短文本")
    require(not any(ord(c) < 32 for c in value), f"{label}不能包含控制字符")
    return value


def identifier(value: object, label: str) -> str:
    require(type(value) is str and ID.fullmatch(value) is not None, f"{label}须以英文字母开头，只含字母、数字、连字符或下划线，最多40字符")
    return value


def unique_list(value: object, label: str, maximum: int) -> list:
    require(type(value) is list and len(value) <= maximum, f"{label}须为不超过{maximum}项的列表")
    require(all(type(x) in (str, int) for x in value), f"{label}条目类型无效")
    require(len(value) == len(set(value)), f"{label}不能重复")
    return value


def _pairs(pairs: list[tuple]) -> dict:
    result = {}
    for k, v in pairs:
        require(k not in result, "JSON含重复字段")
        result[k] = v
    return result


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path: Path) -> tuple[dict, str]:
    require(path.is_absolute(), "输入文件须使用绝对路径")
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), "只接受普通文件，不接受符号链接")
    require(0 < info.st_size <= MAX_BYTES, "输入文件为空或超过512 KiB")
    data = path.read_bytes()
    require(len(data) <= MAX_BYTES, "读取后的文件超过512 KiB")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("JSON不能含非有限数")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("输入必须是有效的UTF-8 JSON") from exc
    require(type(value) is dict, "输入顶层须为对象")
    return value, hashlib.sha256(data).hexdigest()


def validate_case(case: dict) -> dict:
    keys(case, {"schema_version", "case_id", "household", "start_date", "participants", "duties"}, "家务案例", {"notes"})
    require(type(case["schema_version"]) is int and case["schema_version"] == 1, "案例版本只支持1")
    identifier(case["case_id"], "案例编号")
    text(case["household"], "家庭名称")
    require(type(case["start_date"]) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", case["start_date"]) is not None, "开始日期须为YYYY-MM-DD")
    try:
        start = date.fromisoformat(case["start_date"])
        start + timedelta(days=6)
    except (ValueError, OverflowError) as exc:
        raise ValueError("开始日期或七日期间无效") from exc
    persons, duties = case["participants"], case["duties"]
    require(type(persons) is list and 2 <= len(persons) <= 6, "参与者须为2至6人")
    require(type(duties) is list and 1 <= len(duties) <= 21, "一周须有1至21次家务")
    people = set()
    for p in persons:
        keys(p, {"id", "name", "daily_limits", "weekly_limit", "unavailable_days"}, "参与者")
        pid = identifier(p["id"], "参与者编号")
        require(pid not in people, "参与者编号重复")
        people.add(pid)
        text(p["name"], "参与者姓名")
        require(type(p["daily_limits"]) is list and len(p["daily_limits"]) == 7, "每日分钟上限须包含七天")
        for cap in p["daily_limits"]:
            integer(cap, 0, 480, "每日分钟上限")
        integer(p["weekly_limit"], 0, 3360, "每周分钟上限")
        for day in unique_list(p["unavailable_days"], "不可用日期", 7):
            integer(day, 0, 6, "不可用日期")
    ids = set()
    for duty in duties:
        keys(duty, {"id", "name", "day", "minutes", "eligible", "preferred"}, "家务条目")
        did = identifier(duty["id"], "家务编号")
        require(did not in ids, "家务编号重复")
        ids.add(did)
        text(duty["name"], "家务名称")
        integer(duty["day"], 0, 6, "家务日期")
        integer(duty["minutes"], 1, 480, "家务分钟数")
        eligible = unique_list(duty["eligible"], "可承担人员", 6)
        preferred = unique_list(duty["preferred"], "偏好人员", 6)
        require(all(type(x) is str and x in people for x in eligible + preferred), "家务引用了不存在的参与者")
        require(set(preferred) <= set(eligible), "偏好人员必须属于可承担人员")
    if "notes" in case:
        require(type(case["notes"]) is list and len(case["notes"]) <= 20, "备注须为不超过20项的列表")
        for note in case["notes"]:
            text(note, "备注", 1000)
    return case


def loads_for(case: dict, assignments: list) -> tuple[dict, list[str], list[str]]:
    """Leader的直接约束复算；独立核验员另有实现。"""
    people = {p["id"]: p for p in case["participants"]}
    duties = {d["id"]: d for d in case["duties"]}
    require(type(assignments) is list and len(assignments) <= 21, "分配须为不超过21项的列表")
    loads = {pid: {"daily_minutes": [0] * 7, "weekly_minutes": 0} for pid in people}
    seen, issues, misses = set(), [], []
    for a in assignments:
        keys(a, {"duty_id", "participant_id"}, "分配条目")
        require(type(a["duty_id"]) is str and a["duty_id"] in duties, "分配引用未知家务")
        require(type(a["participant_id"]) is str and a["participant_id"] in people, "分配引用未知参与者")
        did, pid = a["duty_id"], a["participant_id"]
        require(did not in seen, "同一家务被重复分配")
        seen.add(did)
        d, p = duties[did], people[pid]
        if pid not in d["eligible"]:
            issues.append(f"{did}分配给未获约定资格的{pid}")
        if d["day"] in p["unavailable_days"]:
            issues.append(f"{did}落在{pid}的不可用日")
        loads[pid]["daily_minutes"][d["day"]] += d["minutes"]
        loads[pid]["weekly_minutes"] += d["minutes"]
        if d["preferred"] and pid not in d["preferred"]:
            misses.append(did)
    if seen != set(duties):
        issues.append("家务未完整覆盖：" + "、".join(sorted(set(duties) - seen)))
    for pid, load in loads.items():
        p = people[pid]
        for day, minutes in enumerate(load["daily_minutes"]):
            if minutes > p["daily_limits"][day]:
                issues.append(f"{pid}第{day + 1}天分钟数超过约定上限")
        if load["weekly_minutes"] > p["weekly_limit"]:
            issues.append(f"{pid}每周分钟数超过约定上限")
    return loads, issues, sorted(misses)


def verify_intake(intake: dict, case: dict, source_sha: str) -> None:
    keys(intake, {"schema_version", "kind", "version", "source_sha256", "case_sha256", "case", "summary"}, "梳理报告")
    require(intake["schema_version"] == 1 and type(intake["schema_version"]) is int and intake["kind"] == "rota-intake/v1" and intake["version"] == VERSION, "梳理报告版本不匹配")
    require(intake["source_sha256"] == source_sha and intake["case_sha256"] == digest(case) and canonical(intake["case"]) == canonical(case), "梳理报告与当前原始输入不一致，请重新梳理")
    summary = keys(intake["summary"], {"participants", "occurrences", "total_minutes", "boundary"}, "梳理摘要")
    expected = {"participants": len(case["participants"]), "occurrences": len(case["duties"]),
                "total_minutes": sum(d["minutes"] for d in case["duties"])}
    for field, value in expected.items():
        require(type(summary[field]) is int and summary[field] == value, "梳理摘要计数或分钟数不一致")
    text(summary["boundary"], "梳理范围说明", 1000)


def new_dir(path: Path) -> Path:
    require(path.is_absolute(), "输出目录须使用绝对路径")
    require(not path.exists() and not path.is_symlink(), "输出目录已存在，拒绝覆盖；请换用新目录")
    require(path.parent.is_dir(), "输出父目录必须已存在")
    target = path.parent.resolve() / path.name
    target.mkdir(mode=0o700, exist_ok=False)
    return target


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write("\n")
    path.chmod(0o600)


class ChineseParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError("命令参数不完整或无效，请查看--help及随包用法")


def cli(run) -> None:
    try:
        code = run()
    except (ValueError, OSError, UnicodeError, RecursionError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else "文件读写、编码或结构深度异常，请核对路径、权限及输入"
        print(json.dumps({"ok": False, "error": detail}, ensure_ascii=False))
        raise SystemExit(2)
    raise SystemExit(code or 0)
