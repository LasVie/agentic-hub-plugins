"""Draft compatible batches from confirmed preferences and limits."""
RANK = {"very_gentle": 0, "gentle": 1, "normal": 2}


def choose_program(profile, programs):
    wash = profile["wash"]
    if wash["method"] in ("hand", "no_machine"):
        return None, wash["method"]
    if wash["method"] == "unknown" or wash["max_celsius"] is None or wash["max_action"] is None:
        return None, "unknown_wash"
    if profile["separate"] is None:
        return None, "unknown_separate"
    if profile["color"] is None and not profile["separate"]:
        return None, "unknown_color"
    for ident, program in programs.items():
        if program["celsius"] <= wash["max_celsius"] and RANK[program["action"]] <= RANK[wash["max_action"]]:
            return ident, None
    return None, "no_program"


def plan(case):
    batches = []
    held = []
    combined = {}
    for ident, count in case.basket.items():
        profile = case.profiles[ident]
        program, reason = choose_program(profile, case.programs)
        if reason:
            held.append({"profile": ident, "count": count, "reason": reason})
            continue
        item = {"profile": ident, "count": count, "dry": profile["dry"]}
        if profile["separate"]:
            for _ in range(count):
                batches.append({"program": program, "items": [{**item, "count": 1}]})
        else:
            combined.setdefault((program, profile["color"]), []).append(item)
    for (program, _), items in combined.items():
        limit = case.programs[program]["max_items"] or 80
        current = []
        used = 0
        for item in items:
            remaining = item["count"]
            while remaining:
                take = min(remaining, limit - used)
                current.append({**item, "count": take})
                used += take
                remaining -= take
                if used == limit:
                    batches.append({"program": program, "items": current})
                    current, used = [], 0
        if current:
            batches.append({"program": program, "items": current})
    return {"batches": batches, "held": held}
