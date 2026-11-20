"""依据已冻结计划推进模拟时钟并记录三阶段的工作项状态。"""
from collections import Counter, defaultdict

from contract import members, parser, read_case, run, write_stage
from plan import read_plans


def exercise(case, fallback, restart):
    _, flows = members(case)
    return [exercise_scenario(scenario, flows, fallback, restart) for scenario in case["scenarios"]]


def exercise_scenario(scenario, flows, fallback, restart):
    events = defaultdict(list)
    arrivals = defaultdict(list)
    for event in sorted(scenario["events"], key=lambda event: event["id"]):
        events[event["minute"]].append(event)
    for item in sorted(scenario["items"], key=lambda item: item["id"]):
        arrivals[item["arrival"]].append(item)
    snapshot = {row["id"]: row["revision"] for row in scenario["snapshot"]}
    staff_used, flow_used = Counter(), Counter()
    seen_gates, ready, earliest = set(), {}, {}
    intake, final, pending, trace = {}, {}, [], []

    def log(minute, event, subject, value):
        trace.append([minute, event, subject, value])

    for minute in range(scenario["horizon"] + 1):
        for event in events[minute]:
            seen_gates.add(event["kind"])
            log(minute, "condition", event["id"], event["kind"])
        if seen_gates.issuperset(restart["gates"]):
            for key in restart["order"]:
                rule = restart["workflows"][key]
                if key in ready or not ready.keys() >= set(rule["needs"]):
                    continue
                earliest.setdefault(key, minute + rule["startup"])
                if earliest[key] == minute:
                    ready[key] = minute
                    log(minute, "reopen", key, "simulated")
        for item in arrivals[minute]:
            key, ident = item["flow"], item["id"]
            owner = flows[key]["owner"]
            if key in ready:
                route = "online"
            elif (staff_used[owner] < fallback["staff_limits"][owner]
                  and flow_used[key] < fallback["workflow_limits"][key]):
                staff_used[owner] += 1
                flow_used[key] += 1
                route = "manual"
            else:
                route = "deferred"
            intake[ident] = route
            log(minute, "capture", ident, route)
            pending.append(item)
        for item in pending[:]:
            ident, key = item["id"], item["flow"]
            if key not in ready:
                continue
            if ident in snapshot:
                matched = snapshot[ident] == item["revision"]
                disposition = "present" if matched else "hold_conflict"
            else:
                disposition = "online" if intake[ident] == "online" else "backfilled"
            final[ident] = disposition, minute
            log(minute, "account", ident, disposition)
            pending.remove(item)

    for item in pending:
        ident = item["id"]
        final[ident] = "hold_closed", scenario["horizon"]
        log(scenario["horizon"], "account", ident, "hold_closed")

    items = {}
    for item in scenario["items"]:
        key = item["id"]
        disposition, minute = final[key]
        items[key] = {"flow": item["flow"], "intake": intake[key], "disposition": disposition,
                      "minute": minute, "due": item["due"],
                      "met_due": not disposition.startswith("hold_") and minute <= item["due"]}
    completion = max(ready.values()) if len(ready) == len(flows) else None
    met_target = completion is not None and completion <= scenario["target"]
    return {"id": scenario["id"], "ready": ready, "events": trace, "items": items,
            "completion": completion, "met_target": met_target,
            "met": met_target and all(entry["met_due"] for entry in items.values())}


def main():
    p = parser("按冻结计划离线执行两种桌面情景")
    for name in ("map", "fallback", "restart"):
        p.add_argument("--" + name, required=True, help="对应成员的上游交接 JSON")
    args = p.parse_args()
    case, source = read_case(args.input)
    fallback, restart, hashes = read_plans(args, case, source)
    write_stage(args.output, "exercise-trace", source, exercise(case, fallback, restart), **hashes)
    print("已完成两种模拟情景并保存有序证据。")


if __name__ == "__main__":
    raise SystemExit(run(main))
