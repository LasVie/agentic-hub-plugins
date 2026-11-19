"""独立解析原始案例并复算分配；不导入规划器或共享约束实现。"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import re
import stat

VERSION = "1.0.0"


def insist(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def fields(obj, expected, label, optional=()):
    insist(type(obj) is dict and set(expected) <= set(obj) <= set(expected) | set(optional), f"{label}结构或字段无效")


def number(n, low, high, label):
    insist(type(n) is int and low <= n <= high, f"{label}须为{low}至{high}的整数")


def label(s, name, maximum=100):
    insist(type(s) is str and 0 < len(s.strip()) <= maximum and all(ord(c) >= 32 for c in s), f"{name}文本无效")


def code(s):
    insist(type(s) is str and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,39}", s) is not None, "编号格式无效")


def distinct(xs, maximum):
    insist(type(xs) is list and len(xs) <= maximum and all(type(x) in (str, int) for x in xs), "列表类型或长度无效")
    insist(len(set(xs)) == len(xs), "列表不能重复")


def canonical_hash(obj):
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def pairs(items):
    result = {}
    for k, v in items:
        insist(k not in result, "JSON含重复字段")
        result[k] = v
    return result


def load(path):
    insist(path.is_absolute(), "核验输入须使用绝对路径")
    info = path.lstat()
    insist(stat.S_ISREG(info.st_mode) and not path.is_symlink() and 0 < info.st_size <= 524288, "核验只接受512 KiB以内的普通文件")
    raw = path.read_bytes()
    insist(len(raw) <= 524288, "读取后的文件超过大小限制")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("JSON不能含非有限数")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("核验文件须为有效UTF-8 JSON") from exc
    insist(type(data) is dict, "核验文件顶层须为对象")
    return data, hashlib.sha256(raw).hexdigest()


def inspect_case(case):
    fields(case, {"schema_version", "case_id", "household", "start_date", "participants", "duties"}, "原始案例", {"notes"})
    insist(type(case["schema_version"]) is int and case["schema_version"] == 1, "案例版本不支持")
    code(case["case_id"])
    label(case["household"], "家庭名称")
    insist(type(case["start_date"]) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", case["start_date"]) is not None, "日期格式无效")
    try:
        date.fromisoformat(case["start_date"]) + timedelta(days=6)
    except (ValueError, OverflowError) as exc:
        raise ValueError("日期或七日期间无效") from exc
    ps, ds = case["participants"], case["duties"]
    insist(type(ps) is list and 2 <= len(ps) <= 6, "参与者须为2至6人")
    insist(type(ds) is list and 1 <= len(ds) <= 21, "家务须为1至21次")
    persons, duties = {}, {}
    for p in ps:
        fields(p, {"id", "name", "daily_limits", "weekly_limit", "unavailable_days"}, "参与者")
        code(p["id"])
        insist(p["id"] not in persons, "参与者编号重复")
        label(p["name"], "姓名")
        insist(type(p["daily_limits"]) is list and len(p["daily_limits"]) == 7, "每日上限必须覆盖七天")
        for cap in p["daily_limits"]:
            number(cap, 0, 480, "每日上限")
        number(p["weekly_limit"], 0, 3360, "每周上限")
        distinct(p["unavailable_days"], 7)
        for d in p["unavailable_days"]:
            number(d, 0, 6, "不可用日")
        persons[p["id"]] = p
    for d in ds:
        fields(d, {"id", "name", "day", "minutes", "eligible", "preferred"}, "家务")
        code(d["id"])
        insist(d["id"] not in duties, "家务编号重复")
        label(d["name"], "家务名称")
        number(d["day"], 0, 6, "日期序号")
        number(d["minutes"], 1, 480, "分钟数")
        for f in ("eligible", "preferred"):
            distinct(d[f], 6)
            insist(all(type(pid) is str and pid in persons for pid in d[f]), "家务引用未知人员")
        insist(set(d["preferred"]) <= set(d["eligible"]), "偏好人员不属于可承担人员")
        duties[d["id"]] = d
    if "notes" in case:
        insist(type(case["notes"]) is list and len(case["notes"]) <= 20, "案例备注无效")
        for n in case["notes"]:
            label(n, "备注", 1000)
    return persons, duties


def check(case, plan, source_sha, plan_sha):
    persons, duties = inspect_case(case)
    fields(plan, {"schema_version", "kind", "version", "source_sha256", "case_sha256", "intake_sha256", "status", "assignments", "search", "loads", "preference_misses", "message"}, "规划报告")
    insist(type(plan["schema_version"]) is int and plan["schema_version"] == 1 and plan["kind"] == "rota-plan/v1" and plan["version"] == VERSION, "规划报告版本无效")
    insist(plan["source_sha256"] == source_sha and plan["case_sha256"] == canonical_hash(case), "规划报告不属于当前原始案例")
    insist(type(plan["intake_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", plan["intake_sha256"]), "梳理报告摘要无效")
    insist(plan["status"] in ("feasible", "infeasible", "unknown"), "规划状态无效")
    fields(plan["search"], {"nodes", "node_limit", "space_exhausted", "optimality_claim", "strategy"}, "搜索记录")
    number(plan["search"]["node_limit"], 1, 500000, "搜索上限")
    number(plan["search"]["nodes"], 1, plan["search"]["node_limit"], "搜索节点")
    insist(type(plan["search"]["space_exhausted"]) is bool and plan["search"]["space_exhausted"] == (plan["status"] == "infeasible"), "穷尽标识不一致")
    insist(plan["search"]["optimality_claim"] is False and plan["search"]["strategy"] == "bounded-balanced-first-feasible", "不能把本版规划改称最优")
    label(plan["message"], "规划说明", 1000)
    issues, misses = [], []
    rows = plan["assignments"]
    insist(type(rows) is list and len(rows) <= 21, "分配列表无效")
    loads = None
    if plan["status"] != "feasible":
        insist(rows == [] and plan["loads"] is None and plan["preference_misses"] is None, "未决或无解报告不能携带可执行轮值或零值负担")
        issues.append("没有可独立复核的完整轮值；规划器的无解或未决声明不是已通过的轮值")
    else:
        per_duty = {}
        for row in rows:
            fields(row, {"duty_id", "participant_id"}, "分配")
            did, pid = row["duty_id"], row["participant_id"]
            insist(type(did) is str and did in duties and type(pid) is str and pid in persons, "分配包含未知引用")
            if did in per_duty:
                issues.append(f"家务{did}重复分配")
            per_duty.setdefault(did, []).append(pid)
        if set(per_duty) != set(duties):
            issues.append("存在未分配家务：" + "、".join(sorted(set(duties) - set(per_duty))))
        # Coverage is enumerated from authoritative duties, not reported totals.
        if not issues:
            loads = {}
            for pid, person in persons.items():
                days = []
                for day in range(7):
                    selected = [d for did, d in duties.items() if per_duty[did][0] == pid and d["day"] == day]
                    minutes = sum(d["minutes"] for d in selected)
                    if selected and day in person["unavailable_days"]:
                        issues.append(f"{pid}在第{day + 1}天不可用，却被安排家务")
                    if minutes > person["daily_limits"][day]:
                        issues.append(f"{pid}第{day + 1}天负担超过约定上限")
                    days.append(minutes)
                total = sum(days)
                if total > person["weekly_limit"]:
                    issues.append(f"{pid}每周负担超过约定上限")
                loads[pid] = {"daily_minutes": days, "weekly_minutes": total}
            for did, duty in duties.items():
                pid = per_duty[did][0]
                if pid not in duty["eligible"]:
                    issues.append(f"{did}的负责人不在约定可承担名单")
                if duty["preferred"] and pid not in duty["preferred"]:
                    misses.append(did)
            if canonical_hash(plan["loads"]) != canonical_hash(loads):
                issues.append("规划器负担合计与独立复算不一致")
            if plan["preference_misses"] != sorted(misses):
                issues.append("规划器偏好未满足清单与独立复算不一致")
    return {"schema_version": 1, "kind": "rota-review/v1", "version": VERSION,
            "source_sha256": source_sha, "case_sha256": canonical_hash(case), "plan_sha256": plan_sha,
            "verdict": "block" if issues else "pass", "issues": issues, "loads": loads,
            "preference_misses": sorted(misses) if loads is not None else None,
            "coverage": "complete" if loads is not None else "unverified",
            "boundary": "独立程序只复核约定输入与分配；用户原话、家庭可接受性及成员参与需另行核对"}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("核验命令参数无效，请查看--help及随包说明")


def main():
    try:
        parser = Parser(description="独立复核原始家务案例及规划报告")
        parser.add_argument("--input", required=True, type=Path, help="原始案例绝对路径")
        parser.add_argument("--plan", required=True, type=Path, help="规划报告绝对路径")
        parser.add_argument("--output", required=True, type=Path, help="新的复核目录")
        args = parser.parse_args()
        case, source = load(args.input)
        plan, plan_sha = load(args.plan)
        result = check(case, plan, source, plan_sha)
        dest = args.output
        insist(dest.is_absolute() and not dest.exists() and not dest.is_symlink() and dest.parent.is_dir(), "输出须为父目录已存在的新绝对目录，拒绝覆盖")
        dest = dest.parent.resolve() / dest.name
        dest.mkdir(mode=0o700)
        with (dest / "review.json").open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=2, allow_nan=False)
            out.write("\n")
        (dest / "review.json").chmod(0o600)
        print(json.dumps({"ok": True, "结论": result["verdict"], "问题": result["issues"], "报告": str(dest / "review.json")}, ensure_ascii=False))
        return 0 if result["verdict"] == "pass" else 1
    except (ValueError, OSError, UnicodeError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else "文件、编码或结构深度异常，请核对核验输入"
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
