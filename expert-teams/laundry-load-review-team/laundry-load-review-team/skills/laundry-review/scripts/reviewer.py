"""Validate the frozen constraints independently of the candidate grouping."""
from collections import Counter

from contract import DRY, HOLD, choice, fields, integer, key, require

# Acceptable programs are enumerated for each limit. Candidate ranking and program
# preference order do not participate in this direct constraint check.
COMPATIBLE = {
    "normal": {"normal", "gentle", "very_gentle"},
    "gentle": {"gentle", "very_gentle"},
    "very_gentle": {"very_gentle"},
}


def independent(case):
    result = {}
    for ident in case.basket:
        profile = case.profiles[ident]
        wash = profile["wash"]
        options = []
        if wash["method"] in {"hand", "no_machine"}:
            reason = wash["method"]
        elif wash["method"] != "machine" or None in (wash["max_celsius"], wash["max_action"]):
            reason = "unknown_wash"
        elif profile["separate"] is None:
            reason = "unknown_separate"
        elif not profile["separate"] and profile["color"] is None:
            reason = "unknown_color"
        else:
            actions = COMPATIBLE[wash["max_action"]]
            options = sorted(
                code for code, p in case.programs.items()
                if p["action"] in actions and p["celsius"] <= wash["max_celsius"]
            )
            reason = None if options else "no_program"
        result[ident] = {"programs": options, "hold_reason": reason}
    return result


def check_item(item, names, case):
    fields(item, names, "衣物交接项")
    require(key(item["profile"]) and item["profile"] in case.basket, "交接项指向本篮之外的组别。")
    require(integer(item["count"], 1, 80), "交接项件数无效。")
    return item["profile"]


def review(case, proposed, baseline):
    fields(proposed, "batches held", "候选")
    batches, holds = proposed["batches"], proposed["held"]
    require(isinstance(batches, list) and len(batches) <= 80, "候选批次数无效。")
    require(isinstance(holds, list) and len(holds) <= 40, "待处理组数无效。")
    found = []

    def issue(code, batch=None, ident=None):
        found.append({"code": code, "batch": batch, "profile": ident})

    totals = Counter()
    for number, batch in enumerate(batches, start=1):
        fields(batch, "program items", "洗涤批次")
        ident = batch["program"]
        require(key(ident) and ident in case.programs, "候选引用未知洗衣程序。")
        items = batch["items"]
        require(isinstance(items, list) and 1 <= len(items) <= 40, "候选批次为空或组数无效。")
        total = 0
        colors = set()
        used = set()
        separate = False
        for item in items:
            group = check_item(item, "profile count dry", case)
            require(choice(item["dry"], DRY), "候选干燥方式无效。")
            profile = case.profiles[group]
            if group in used:
                issue("duplicate_in_load", number, group)
            used.add(group)
            totals[group] += item["count"]
            total += item["count"]
            if ident not in baseline[group]["programs"]:
                issue("program_conflict", number, group)
            if item["dry"] != profile["dry"]:
                issue("dry_conflict", number, group)
            if profile["color"] is not None:
                colors.add(profile["color"])
            separate = separate or profile["separate"] is True
        if len(colors) > 1:
            issue("color_conflict", number)
        if separate and total != 1:
            issue("separate_conflict", number)
        cap = case.programs[ident]["max_items"]
        if cap is not None and total > cap:
            issue("count_limit", number)
    held = set()
    for item in holds:
        group = check_item(item, "profile count reason", case)
        require(choice(item["reason"], HOLD), "候选搁置原因无效。")
        if group in held:
            issue("duplicate_hold", ident=group)
        held.add(group)
        if item["count"] != case.basket[group] or item["reason"] != baseline[group]["hold_reason"]:
            issue("incorrect_hold", ident=group)
        totals[group] += item["count"]
    for group, count in case.basket.items():
        if totals[group] != count:
            issue("coverage", ident=group)
    return {"status": "blocked" if found else "reviewed", "findings": found, "checked_pieces": sum(case.basket.values())}
