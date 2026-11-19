"""Original bounded CBS search. The independent replayer does not import this file."""
from __future__ import annotations

import argparse
import heapq
import itertools
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "skills/route-workflow/scripts"))
from protocol import (ContractError, DEFAULT_LIMITS, VERSION, bind, comments,
                      encoded, fail, load_case, packet, read_json, sha, write_new)


class LimitReached(Exception):
    pass


class Budget:
    def __init__(self, limits):
        self.limits = {**DEFAULT_LIMITS, **limits}
        self.start = time.monotonic()
        self.high = self.low = 0

    def tick(self, kind):
        if time.monotonic() - self.start >= self.limits["seconds"]:
            raise LimitReached("已达到墙钟时间限额；尚未完成搜索。")
        attr, key = ("low", "low_level_nodes") if kind == "low" else ("high", "high_level_nodes")
        if getattr(self, attr) >= self.limits[key]:
            raise LimitReached("已达到节点展开限额；尚未完成搜索。")
        setattr(self, attr, getattr(self, attr) + 1)


def position(path, tick):
    return path[min(tick, len(path) - 1)]


def first_conflict(paths):
    names = sorted(paths)
    for tick in range(max(map(len, paths.values()))):
        for a, b in itertools.combinations(names, 2):
            u, v = position(paths[a], tick), position(paths[b], tick)
            if u == v:
                return ("vertex", a, b, tick, u, v)
            if tick and position(paths[a], tick - 1) == v and position(paths[b], tick - 1) == u:
                return ("edge_swap", a, b, tick, position(paths[a], tick - 1), u)
    return None


def shortest(case, robot, constraints, budget):
    """Earliest final arrival in the finite time-expanded graph."""
    width, height = case["grid"]["width"], case["grid"]["height"]
    blocked = {tuple(x) for x in case["grid"]["obstacles"]}
    start, goal, horizon = tuple(robot["start"]), tuple(robot["goal"]), case["horizon"]
    vertices = {(c[2], c[3]) for c in constraints if c[0] == robot["id"] and c[1] == "v"}
    edges = {(c[2], c[3], c[4]) for c in constraints if c[0] == robot["id"] and c[1] == "e"}
    if (0, start) in vertices:
        return None
    h = lambda p: abs(p[0] - goal[0]) + abs(p[1] - goal[1])
    if h(start) > horizon:
        return None
    serial = itertools.count()
    queue = [(h(start), 0, next(serial), start)]
    parents = {(start, 0): None}
    while queue:
        _, tick, _, pos = heapq.heappop(queue)
        budget.tick("low")
        if pos == goal:
            if not any(t >= tick and p == goal for t, p in vertices) and not any(t > tick and a == goal and b == goal for t, a, b in edges):
                path, state = [], (pos, tick)
                while state is not None:
                    path.append(state[0]); state = parents[state]
                return path[::-1]
            # First arrival is permanent; never leave a goal to evade a future constraint.
            continue
        if tick == horizon:
            continue
        for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            nxt, t = (pos[0] + dx, pos[1] + dy), tick + 1
            if not 0 <= nxt[0] < width or not 0 <= nxt[1] < height or nxt in blocked or t + h(nxt) > horizon:
                continue
            if (t, nxt) in vertices or (t, pos, nxt) in edges or (nxt, t) in parents:
                continue
            parents[(nxt, t)] = (pos, tick)
            heapq.heappush(queue, (t + h(nxt), t, next(serial), nxt))
    return None


def solve(case_path: Path, map_report_path: Path):
    case, digest, _ = load_case(case_path)
    map_report, map_raw = read_json(map_report_path)
    bind(map_report, "map-analyst", digest); comments(map_report)
    if map_report.get("case") != case or map_report.get("status") != "inspected" or map_report["issues"]:
        fail("地图报告与本次输入不符或存在未解决问题；先澄清，不能开始规划。")
    budget = Budget(case.get("limits", {}))
    robots = {r["id"]: r for r in case["robots"]}
    common = {"horizon": case["horizon"], "algorithm": "bounded-cbs-v1", "map_report_sha256": sha(map_raw), "notes": [], "issues": []}
    result = packet("planner", digest, **common)
    try:
        paths = {}
        for name in sorted(robots):
            path = shortest(case, robots[name], (), budget)
            if path is None:
                result.update(status="infeasible_within_horizon", paths={}, metrics=None,
                              reason="某机器人在本次时域和规则内没有路径；不表示无限时域/其他模型无解。")
                break
            paths[name] = path
        else:
            serial = itertools.count()
            rank = lambda p: (sum(len(x) - 1 for x in p.values()), max(len(x) - 1 for x in p.values()))
            queue = [(*rank(paths), next(serial), frozenset(), paths)]
            seen = {frozenset()}
            while queue:
                budget.tick("high")
                _, _, _, constraints, paths = heapq.heappop(queue)
                conflict = first_conflict(paths)
                if conflict is None:
                    total, span = rank(paths)
                    result.update(status="found", paths={n: [list(p) for p in path] for n, path in paths.items()},
                                  metrics={"sum_of_costs": total, "makespan": span},
                                  reason="已找到候选路径，须由独立回放器逐步检查后交付。")
                    break
                kind, a, b, tick, u, v = conflict
                for name in (a, b):
                    if kind == "vertex":
                        constraint = (name, "v", tick, u)
                    else:
                        constraint = (name, "e", tick, u, v) if name == a else (name, "e", tick, v, u)
                    child = constraints | {constraint}
                    if child in seen:
                        continue
                    seen.add(child)
                    new_path = shortest(case, robots[name], child, budget)
                    if new_path is not None:
                        new_paths = {**paths, name: new_path}
                        heapq.heappush(queue, (*rank(new_paths), next(serial), child, new_paths))
            else:
                result.update(status="infeasible_within_horizon", paths={}, metrics=None,
                              reason="已穷尽给定时域内的约束搜索；不表示无限时域无解。")
    except LimitReached as error:
        result.update(status="search_limit", paths={}, metrics=None, reason=str(error))
    result["search"] = {"high_level_expanded": budget.high, "low_level_expanded": budget.low,
                        "limits": budget.limits, "complete": result["status"] != "search_limit"}
    return result


def main():
    p = argparse.ArgumentParser(description="有限时域多机器人路径规划；只处理模拟网格。")
    p.add_argument("--case", type=Path, required=True, help="案例 JSON")
    p.add_argument("--map-report", type=Path, required=True, help="地图员实际报告，必须没有未解决问题")
    p.add_argument("--output", type=Path, required=True, help="新的候选计划 JSON")
    a = p.parse_args()
    try:
        result = solve(a.case, a.map_report)
        write_new(a.output, encoded(result))
        print(encoded({"ok": True, "version": VERSION, "status": result["status"], "metrics": result["metrics"], "report": str(a.output.absolute())}).decode())
    except (ContractError, OSError) as error:
        print(encoded({"ok": False, "version": VERSION, "error": str(error)}).decode()); sys.exit(2)


if __name__ == "__main__":
    main()
