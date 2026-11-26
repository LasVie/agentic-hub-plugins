"""逐日模拟方案，并以累计供需独立核验。"""
from datetime import date, timedelta
from itertools import accumulate
from math import prod


def simulate(item, days):
    balance = item["on_hand"]
    openings, closings = [], []
    for offset in range(days):
        balance += sum(amount for due, amount in item["arrivals"] if due == offset)
        openings.append(balance)
        balance -= item["daily"]
        closings.append(balance)
    needed = max(0, -min(closings))
    shortage = next((offset for offset, closing in enumerate(closings) if closing < 0), None)
    peak = max(openings)
    choices = []
    for size in item["packs"]:
        count, remainder = divmod(needed, size)
        count += bool(remainder)
        total = size * count
        if item["capacity"] is None or peak + total <= item["capacity"]:
            choices.append((total, count, size))
    return needed, shortage, peak, min(choices, default=None)


def cross_check(item, days):
    by_date = [0] * days
    for offset, amount in item["arrivals"]:
        by_date[offset] += amount
    supplies = (item["on_hand"] + received for received in accumulate(by_date))
    gaps = [day * item["daily"] - available for day, available in enumerate(supplies, 1)]
    needed = max(0, *gaps)
    peak = item["daily"] - min(gaps)
    shortage = next((idx for idx, gap in enumerate(gaps) if gap > 0), None)
    sizes_and_counts = [((needed + size - 1) // size, size) for size in item["packs"]]
    limit = item["capacity"]
    ordered = sorted((prod(pair), *pair) for pair in sizes_and_counts)
    best = next((pack for pack in ordered if limit is None or pack[0] <= limit - peak), None)
    return needed, shortage, peak, best


def action(item, horizon, start, calculate):
    row = {
        "name": item["name"], "unit": item["unit"], "variant": item["variant"],
        "status": "check", "reason": "missing_use", "first_shortage": None,
        "shortfall": None, "peak_before_purchase": None, "purchase": None,
        "notes": item["notes"],
    }
    if item["daily"] is None:
        return row
    needed, shortage, peak, pack = calculate(item, horizon)
    row.update(
        first_shortage=(start + timedelta(days=shortage)).isoformat() if shortage is not None else None,
        shortfall=needed,
        peak_before_purchase=peak,
    )
    if item["capacity"] is not None and peak > item["capacity"]:
        row["reason"] = "existing_capacity"
    elif needed == 0:
        row.update(status="wait", reason="covered")
    elif item["stock_uncertain"]:
        row["reason"] = "uncertain_stock"
    elif not item["packs"]:
        row["reason"] = "missing_pack"
    elif pack is None:
        row["reason"] = "pack_capacity"
    else:
        total, count, size = pack
        row.update(status="buy", reason="shortage", purchase={"total": total, "count": count, "size": size})
    return row


def project(facts, calculate):
    start = date.fromisoformat(facts["as_of"])
    return [action(item, facts["horizon"], start, calculate) for item in facts["items"]]
