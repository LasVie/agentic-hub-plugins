"""从原始约定独立推导开放时间和逐项账目，再核对演练记录。"""
from collections import Counter
from functools import lru_cache

from contract import GATES, dependency_order, members, parser, read_case, require, run, same, stage, write_stage
from plan import read_plans


def independent(case):
    people, flows = members(case)
    return [expected_scenario(scenario, people, flows) for scenario in case["scenarios"]]


def expected_scenario(scenario, people, flows):
    times = {event["kind"]: event["minute"] for event in scenario["events"]}
    horizon = scenario["horizon"]
    gates_at = max(times.get(gate, horizon + 1) for gate in GATES)

    @lru_cache(maxsize=None)
    def opening(key):
        flow = flows[key]
        return max([gates_at] + [opening(dep) for dep in flow["needs"]]) + flow["startup"]

    order = dependency_order(flows)
    ready = {key: opening(key) for key in order if opening(key) <= horizon}
    staff_consumed, flow_consumed = Counter(), Counter()
    indexed_events = [(e["minute"], 0, e["id"], e["id"], e["kind"]) for e in scenario["events"]]
    for index, key in enumerate(order):
        if key in ready:
            indexed_events.append((ready[key], 1, f"{index:02d}", key, "simulated"))
    snapshot = {row["id"]: row["revision"] for row in scenario["snapshot"]}
    items = {}
    for item in sorted(scenario["items"], key=lambda row: (row["arrival"], row["id"])):
        ident, key, arrival = item["id"], item["flow"], item["arrival"]
        owner = flows[key]["owner"]
        opened = ready.get(key)
        capacity = min(people[owner]["capacity"] - staff_consumed[owner],
                       flows[key]["manual_limit"] - flow_consumed[key])
        if opened is not None and arrival >= opened:
            capture = "online"
        elif capacity > 0:
            capture = "manual"
            staff_consumed[owner] += 1
            flow_consumed[key] += 1
        else:
            capture = "deferred"
        indexed_events.append((arrival, 2, ident, ident, capture))
        if opened is None:
            disposition = "hold_closed"
        elif ident in snapshot:
            disposition = "present" if snapshot[ident] == item["revision"] else "hold_conflict"
        else:
            disposition = "online" if capture == "online" else "backfilled"
        minute = horizon if opened is None else max(arrival, opened)
        met_due = disposition in ("present", "backfilled", "online") and minute <= item["due"]
        items[ident] = {"flow": key, "intake": capture, "disposition": disposition,
                        "minute": minute, "due": item["due"], "met_due": met_due}
        rank = 4 if opened is None else 3
        indexed_events.append((minute, rank, f"{arrival:03d}:{ident}", ident, disposition))
    event_names = ["condition", "reopen", "capture", "account", "account"]
    trace = [[minute, event_names[phase], key, value]
             for minute, phase, _, key, value in sorted(indexed_events)]
    all_ready = max(ready.values()) if ready.keys() == flows.keys() else None
    met_target = all_ready is not None and all_ready <= scenario["target"]
    return {"id": scenario["id"], "ready": ready, "events": trace, "items": items,
            "completion": all_ready, "met_target": met_target,
            "met": met_target and all(entry["met_due"] for entry in items.values())}


def differences(expected, actual):
    result = []
    if type(actual) is not list or len(actual) != len(expected):
        return ["情景缺失、重复或数量不符"]
    for reference, observed in zip(expected, actual):
        scenario = reference["id"]
        if type(observed) is not dict or set(observed) != set(reference) or observed["id"] != scenario:
            result.append(f"{scenario}：情景标识或结构不一致")
            continue
        for field in ("ready", "completion", "met_target", "met"):
            if not same(reference[field], observed[field]):
                result.append(f"{scenario}：{field} 与独立基线不一致")
        actual_items = observed["items"]
        if type(actual_items) is not dict:
            result.append(f"{scenario}：工作项账目无效")
        else:
            for ident in sorted(reference["items"].keys() | actual_items.keys()):
                if not same(reference["items"].get(ident), actual_items.get(ident)) or ident not in reference["items"]:
                    result.append(f"{scenario}：工作项 {ident} 的去向、时间或记录数量不符")
        events = observed["events"]
        if type(events) is not list:
            result.append(f"{scenario}：事件记录无效")
        elif not same(reference["events"], events):
            for offset in range(max(len(reference["events"]), len(events))):
                exp = reference["events"][offset] if offset < len(reference["events"]) else None
                act = events[offset] if offset < len(events) else None
                if not same(exp, act):
                    key = act[2] if type(act) is list and len(act) == 4 and type(act[2]) is str \
                        else exp[2] if exp else "未知工作项"
                    result.append(f"{scenario}：事件第 {offset + 1} 行不符（{key[:40]}）")
                    break
    return result


def comparison(expected, actual):
    issues = differences(expected, actual)
    return {"verdict": "unverified" if issues else "matched", "issues": issues,
            "scenarios": len(expected), "items": sum(len(s["items"]) for s in expected)}


def read_review_inputs(args, case, source):
    _, _, plan_hashes = read_plans(args, case, source)
    baseline, bh = stage(args.baseline, "review-baseline", source)
    require(same(baseline, independent(case)), "基线与原始约定不符")
    trace, th = stage(args.trace, "exercise-trace", source, **plan_hashes)
    return baseline, trace, {**plan_hashes, "baseline": bh, "trace": th}


def review_args(p, *, required):
    for name in ("map", "fallback", "restart", "baseline", "trace"):
        p.add_argument("--" + name, required=required, help="已完成角色的原始交接 JSON")


def main():
    p = parser("先生成独立基线，再对照完整情景证据核验")
    p.add_argument("phase", choices=("baseline", "compare"), help="选择基线或正式核验")
    review_args(p, required=False)
    args = p.parse_args()
    case, source = read_case(args.input)
    if args.phase == "baseline":
        require(not any((args.map, args.fallback, args.restart, args.baseline, args.trace)),
                "独立基线只接受原始案例")
        write_stage(args.output, "review-baseline", source, independent(case))
        print("已从原始案例保存独立基线。")
        return 0
    require(all((args.map, args.fallback, args.restart, args.baseline, args.trace)), "正式核验缺少阶段证据")
    baseline, trace, hashes = read_review_inputs(args, case, source)
    result = comparison(baseline, trace)
    write_stage(args.output, "independent-review", source, result, **hashes)
    if result["verdict"] == "unverified":
        for issue in result["issues"]:
            print(issue)
        return 3
    print(f"独立复核一致，已核对 {result['items']} 个模拟工作项。")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
