"""复核两个摘录观点，再逐个孩子应用明确的变更。"""

from collections import defaultdict

from evidence import precedes


def compare(draft, baseline):
    accepted = {}
    disagreements = {}
    for ref in sorted(draft.keys() | baseline.keys()):
        first, second = draft.get(ref), baseline.get(ref)
        if first == second:
            accepted[ref] = first
        else:
            disagreements[ref] = [row for row in (first, second) if row is not None]
    return accepted, disagreements


def resolve(bundle, accepted, disagreements):
    notices, children = bundle["notices"], bundle["children"]

    blocked = set()
    routes = defaultdict(list)
    pending = []
    changes = []
    checklist = []

    def scope(row):
        return notices[row["notice"]]["scope"]

    def uncertain(ref, row, reason, child=None):
        pending.append({"ref": ref, "quote": row["quote"], "child": child, "reason": reason})

    def protect_previous(row, subset):
        previous = row["previous"]
        affected = set(children if subset is None else subset)
        if previous and previous in accepted:
            blocked.update((c, previous) for c in affected)
        elif row["op"] in {"更正", "取消"}:
            correction = notices[row["notice"]]
            for ref, alternative in accepted.items():
                older = notices[alternative["notice"]]
                if (alternative["op"] in {"新增", "更正"} and alternative["notice"] != row["notice"]
                        and (not correction["issuer"] or correction["issuer"] == older["issuer"])
                        and not precedes(correction["sent"], older["sent"])):
                    blocked.update((c, ref) for c in affected.intersection(older["scope"] or ()))

    for ref, readings in disagreements.items():
        uncertain(ref, readings[0], "两份独立摘录有遗漏、取值或关联分歧")
        for reading in readings:
            protect_previous(reading, scope(reading))
            blocked.update((child, ref) for child in children)

    for ref, row in accepted.items():
        op, previous = row["op"], row["previous"]
        audience = scope(row)
        if op == "待确认" or audience is None:
            uncertain(ref, row, "条目含义或适用对象待确认")
            protect_previous(row, audience)
            continue
        if not audience or op == "新增":
            continue
        older = accepted.get(previous)
        if older is None or older["op"] not in {"新增", "更正"}:
            uncertain(ref, row, "无法确认此前有效条目")
            protect_previous(row, audience)
            continue
        now, then = notices[row["notice"]], notices[older["notice"]]
        same_issuer = bool(now["issuer"]) and now["issuer"] == then["issuer"]
        for child in audience:
            if child not in (scope(older) or ()):
                uncertain(ref, row, "更改不适用于该孩子的原条目", child)
            elif not same_issuer or not precedes(then["sent"], now["sent"]):
                reason = "发文方不同或无法确认发布先后"
                uncertain(ref, row, reason, child)
                blocked.add((child, previous))
            elif op == "提醒":
                if ((row["when"] is not None and (not row["date_iso"] or row["date_iso"] != older["date_iso"]))
                        or (row["clock"] is not None and (not row["time_iso"] or row["time_iso"] != older["time_iso"]))):
                    uncertain(ref, row, "提醒与所引用条目的时间不一致", child)
                    blocked.add((child, previous))
            else:
                routes[(child, previous)].append(ref)

    used = set()
    for base, initial in accepted.items():
        if initial["op"] != "新增":
            continue
        for child in scope(initial) or ():
            ref = base
            row = initial
            while True:
                options = routes[(child, ref)]
                if (child, ref) in blocked:
                    uncertain(ref, row, "存在未决更正，需确认最后有效版本", child)
                    break
                if len(options) > 1:
                    uncertain(ref, row, "多份更正同时引用同一版本，需确认有效版本", child)
                    used.update((child, edit) for edit in options)
                    break
                if options:
                    next_ref = options[0]
                    new = accepted[next_ref]
                    used.add((child, next_ref))
                    changes.append({
                        "child": child, "op": new["op"], "old_ref": ref, "new_ref": next_ref,
                        "old_date": row["date_iso"], "old_time": row["time_iso"],
                        "new_date": new["date_iso"], "new_time": new["time_iso"],
                    })
                    if new["op"] == "取消":
                        break
                    ref, row = next_ref, new
                    continue
                if not notices[row["notice"]]["issuer"]:
                    uncertain(ref, row, "发文来源待确认", child)
                elif not row["date_iso"] or (row["clock"] is not None and not row["time_iso"]):
                    uncertain(ref, row, "日期或时刻欠明确，需核对原始通知", child)
                elif bundle["start"] <= row["date_iso"] <= bundle["end"]:
                    checklist.append({"child": child, "ref": ref, "quote": row["quote"],
                                      "date": row["date_iso"], "time": row["time_iso"],
                                      "caregiver": children[child]["caregiver"]})
                break

    for (child, _), options in routes.items():
        for ref in options:
            if (child, ref) not in used:
                uncertain(ref, accepted[ref], "变更无法追溯到该孩子的有效原条目", child)

    checklist.sort(key=lambda r: (r["date"], r["time"] or "", r["child"], r["ref"]))
    return {"actions": checklist, "changes": changes, "pending": pending}
