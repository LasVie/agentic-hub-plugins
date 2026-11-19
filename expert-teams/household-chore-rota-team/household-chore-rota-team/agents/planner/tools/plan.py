"""按约定限制进行有界首个可行轮值搜索；不声称最优或家庭公平。"""
from fractions import Fraction
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/rota-evidence/scripts"))
from contract import (ChineseParser, VERSION, cli, digest, integer, loads_for,
                      new_dir, read_json, require, validate_case, verify_intake, write_json)


class SearchLimit(Exception):
    pass


def search(case: dict, limit: int) -> dict:
    people = {p["id"]: p for p in case["participants"]}
    weekly = {pid: 0 for pid in people}
    daily = {pid: [0] * 7 for pid in people}
    choices = {d["id"]: [pid for pid in d["eligible"] if d["day"] not in people[pid]["unavailable_days"]
                        and d["minutes"] <= people[pid]["daily_limits"][d["day"]]
                        and d["minutes"] <= people[pid]["weekly_limit"]] for d in case["duties"]}
    ordered = sorted(case["duties"], key=lambda d: (len(choices[d["id"]]), -d["minutes"], d["day"], d["id"]))
    assignment, nodes = {}, 0

    def visit(index: int) -> bool:
        nonlocal nodes
        if nodes >= limit:
            raise SearchLimit
        nodes += 1
        if index == len(ordered):
            return True
        duty = ordered[index]
        day, minutes = duty["day"], duty["minutes"]
        candidates = sorted(choices[duty["id"]], key=lambda pid: (
            Fraction(weekly[pid] + minutes, people[pid]["weekly_limit"]),
            int(bool(duty["preferred"]) and pid not in duty["preferred"]), weekly[pid], daily[pid][day], pid))
        for pid in candidates:
            p = people[pid]
            if weekly[pid] + minutes > p["weekly_limit"] or daily[pid][day] + minutes > p["daily_limits"][day]:
                continue
            assignment[duty["id"]] = pid
            weekly[pid] += minutes
            daily[pid][day] += minutes
            if visit(index + 1):
                return True
            weekly[pid] -= minutes
            daily[pid][day] -= minutes
            del assignment[duty["id"]]
        return False

    try:
        status = "feasible" if visit(0) else "infeasible"
    except SearchLimit:
        status = "unknown"
    result = [{"duty_id": d["id"], "participant_id": assignment[d["id"]]} for d in case["duties"]] if status == "feasible" else []
    return {"status": status, "assignments": result, "search": {"nodes": nodes, "node_limit": limit,
            "space_exhausted": status == "infeasible", "optimality_claim": False,
            "strategy": "bounded-balanced-first-feasible"}}


def run() -> int:
    parser = ChineseParser(description="从已梳理案例编制一周轮值；不作最优承诺")
    parser.add_argument("--input", required=True, type=Path, help="原始案例JSON绝对路径")
    parser.add_argument("--intake", required=True, type=Path, help="梳理员intake.json绝对路径")
    parser.add_argument("--output", required=True, type=Path, help="新的规划报告目录")
    parser.add_argument("--node-limit", type=int, default=100000, help="搜索节点上限，1至500000")
    args = parser.parse_args()
    integer(args.node_limit, 1, 500000, "搜索节点上限")
    case, source = read_json(args.input)
    validate_case(case)
    intake, intake_sha = read_json(args.intake)
    verify_intake(intake, case, source)
    result = {"schema_version": 1, "kind": "rota-plan/v1", "version": VERSION,
              "source_sha256": source, "case_sha256": digest(case), "intake_sha256": intake_sha,
              **search(case, args.node_limit)}
    if result["status"] == "feasible":
        loads, issues, misses = loads_for(case, result["assignments"])
        require(not issues, "规划器内部复算发现限制冲突，不能交付")
        result.update({"loads": loads, "preference_misses": misses, "message": "找到满足约定硬限制的轮值；不保证最优或家庭成员已接受"})
    else:
        result.update({"loads": None, "preference_misses": None,
                       "message": "已穷尽本版搜索空间但未找到可行轮值" if result["status"] == "infeasible" else "达到搜索上限，结论未决；不能宣称无解"})
    dest = new_dir(args.output)
    write_json(dest / "plan.json", result)
    print(json.dumps({"ok": True, "状态": result["status"], "说明": result["message"], "报告": str(dest / "plan.json"), "搜索": result["search"]}, ensure_ascii=False))
    return 0 if result["status"] == "feasible" else 1


if __name__ == "__main__":
    cli(run)
