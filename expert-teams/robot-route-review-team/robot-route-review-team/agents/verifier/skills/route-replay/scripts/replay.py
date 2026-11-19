"""Independent, linear replay of original grid and candidate timesteps.

No dependency on the planner, its search state or its conflict detector.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "skills/route-workflow/scripts"))
from protocol import (ContractError, DEFAULT_LIMITS, MODEL, VERSION, bind, comments, encoded,
                      fail, integer, load_case, object_keys, packet, read_json, sha, write_new)


def audit(case_path: Path):
    case, digest, _ = load_case(case_path)
    return packet("verifier-model", digest, status="model_reviewed",
                  horizon=case["horizon"], robot_ids=[r["id"] for r in case["robots"]],
                  notes=["原始模型独立审查记录；此阶段未读取规划结果。", "输入只表示离散格点占用，不涵盖机器人尺寸、动力学、传感器与连续时间碰撞。"], issues=[])


def check_plan(case, digest, plan):
    bind(plan, "planner", digest)
    object_keys(plan, ("schema_version", "version", "role", "case_sha256", "model", "horizon", "algorithm",
                       "notes", "issues", "status", "paths", "metrics", "reason", "search", "map_report_sha256"))
    comments(plan)
    if type(plan["horizon"]) is not int or plan["horizon"] != case["horizon"] or plan["algorithm"] != "bounded-cbs-v1":
        fail("候选计划的时域或算法声明不一致。")
    if not isinstance(plan["reason"], str) or len(plan["reason"]) > 1000:
        fail("候选计划说明无效。")
    search = plan["search"]
    object_keys(search, ("high_level_expanded", "low_level_expanded", "limits", "complete"))
    if type(search["complete"]) is not bool:
        fail("搜索完成标记须为布尔值。")
    if search["limits"] != {**DEFAULT_LIMITS, **case.get("limits", {})}:
        fail("搜索限额声明与原始案例不一致。")
    integer(search["high_level_expanded"], 0, search["limits"]["high_level_nodes"], "高层展开数")
    integer(search["low_level_expanded"], 0, search["limits"]["low_level_nodes"], "低层展开数")
    if not isinstance(plan["map_report_sha256"], str) or len(plan["map_report_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in plan["map_report_sha256"]):
        fail("地图报告摘要格式错误。")
    if plan["status"] in ("infeasible_within_horizon", "search_limit"):
        if plan["paths"] != {} or plan["metrics"] is not None or search["complete"] != (plan["status"] != "search_limit"):
            fail("无路径/限额状态与路径、费用或完成标记矛盾。")
        return {"verdict": "no_route_to_verify", "findings": [], "metrics": None,
                "notes": ["没有可回放路径；独立回放器不证明规划器的无解/搜索完成声明。"]}
    if plan["status"] != "found" or search["complete"] is not True:
        fail("未知或自相矛盾的规划状态。")
    paths = plan["paths"]
    robots = {r["id"]: r for r in case["robots"]}
    if not isinstance(paths, dict) or set(paths) != set(robots):
        fail("路径必须恰好包含案例中的所有机器人，不能遗漏或增加。")
    width, height = case["grid"]["width"], case["grid"]["height"]
    walls = {tuple(c) for c in case["grid"]["obstacles"]}
    findings, arrivals = [], {}
    def issue(code, tick, names, message):
        findings.append({"code": code, "tick": tick, "robots": names, "message": message})
    for name, path in paths.items():
        if not isinstance(path, list) or not 1 <= len(path) <= case["horizon"] + 1:
            fail("路径为空、格式错误或超过本次时域。")
        goal, reached = robots[name]["goal"], None
        for tick, pos in enumerate(path):
            if not isinstance(pos, list) or len(pos) != 2 or any(type(n) is not int for n in pos):
                fail("路径坐标须为两个整数，不能使用布尔值或浮点值。")
            if not 0 <= pos[0] < width or not 0 <= pos[1] < height:
                issue("out_of_bounds", tick, [name], "位置超出网格。")
            if tuple(pos) in walls:
                issue("obstacle", tick, [name], "路径进入障碍格。")
            if tick and sum(abs(pos[k] - path[tick - 1][k]) for k in (0, 1)) > 1:
                issue("illegal_move", tick, [name], "一步只能上下左右移动一格或等待。")
            if reached is not None and pos != goal:
                issue("left_goal", tick, [name], "首次到达终点后不允许离开。")
            if pos == goal and reached is None:
                reached = tick
        if path[0] != robots[name]["start"]:
            issue("wrong_start", 0, [name], "路径起点与冻结案例不一致。")
        if path[-1] != goal:
            issue("wrong_goal", len(path) - 1, [name], "路径没有在规定时域内到达目标。")
        arrivals[name] = reached
    # Replay all declared ticks including implicit permanent goal occupation.
    names = list(robots)
    at = lambda name, tick: paths[name][min(tick, len(paths[name]) - 1)]
    for tick in range(case["horizon"] + 1):
        for index, a in enumerate(names):
            for b in names[index + 1:]:
                if at(a, tick) == at(b, tick):
                    issue("vertex", tick, [a, b], "两机器人在同一时刻占用同一格。")
                if tick and at(a, tick) != at(a, tick - 1) and at(a, tick - 1) == at(b, tick) and at(b, tick - 1) == at(a, tick):
                    issue("edge_swap", tick, [a, b], "两机器人同时反向交换同一条边。")
    computed = None
    if all(t is not None for t in arrivals.values()):
        computed = {"sum_of_costs": sum(arrivals.values()), "makespan": max(arrivals.values())}
    claimed = plan["metrics"]
    if (not isinstance(claimed, dict) or set(claimed) != {"sum_of_costs", "makespan"} or
        any(type(v) is not int or v < 0 for v in claimed.values()) or claimed != computed):
        issue("metrics_mismatch", None, names, "规划器费用与独立复算不一致；不得用声明费用代替回放。")
    return {"verdict": "route_invalid" if findings else "route_valid", "findings": findings,
            "metrics": computed, "notes": ["按冻结模型逐时刻回放；不是物理安全、最优性或成员独立推理能力的证明。"]}


def review_records(case, digest, model, model_raw, plan, plan_raw):
    bind(model, "verifier-model", digest); comments(model)
    object_keys(model, ("schema_version", "version", "role", "case_sha256", "model", "status", "horizon", "robot_ids", "notes", "issues"))
    if (model["status"] != "model_reviewed" or model["horizon"] != case["horizon"] or
        model["robot_ids"] != [r["id"] for r in case["robots"]]):
        fail("独立模型审查与本次输入不一致。")
    checks = check_plan(case, digest, plan)
    return packet("verifier", digest, plan_sha256=sha(plan_raw), model_report_sha256=sha(model_raw),
                  verdict=checks["verdict"], findings=checks["findings"], metrics=checks["metrics"],
                  notes=checks["notes"], issues=list(model["issues"]))


def review(case_path: Path, model_path: Path, plan_path: Path):
    case, digest, _ = load_case(case_path)
    model, model_raw = read_json(model_path)
    plan, plan_raw = read_json(plan_path)
    return review_records(case, digest, model, model_raw, plan, plan_raw)


def main():
    p = argparse.ArgumentParser(description="独立模型审查与逐步路径复核，不调用规划算法。")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("audit-model", "review"):
        s = sub.add_parser(command, help="仅审查原始模型" if command == "audit-model" else "读取候选并逐步复核")
        s.add_argument("--case", required=True, type=Path, help="原始案例 JSON")
        s.add_argument("--output", required=True, type=Path, help="新的报告 JSON，不覆盖")
        if command == "review":
            s.add_argument("--model-report", required=True, type=Path, help="先前保存的独立模型审查")
            s.add_argument("--plan", required=True, type=Path, help="规划员实际输出")
    a = p.parse_args()
    try:
        result = audit(a.case) if a.command == "audit-model" else review(a.case, a.model_report, a.plan)
        write_new(a.output, encoded(result))
        print(encoded({"ok": True, "version": VERSION, "status": result.get("verdict", result.get("status")), "report": str(a.output.absolute())}).decode())
    except (ContractError, OSError) as error:
        print(encoded({"ok": False, "version": VERSION, "error": str(error)}).decode()); sys.exit(2)


if __name__ == "__main__":
    main()
