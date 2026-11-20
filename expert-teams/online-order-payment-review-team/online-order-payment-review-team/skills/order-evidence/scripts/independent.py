"""从原始记录从订单方向重建基线，不读取匹配阶段的结果。"""

from collections import defaultdict
from datetime import date


def baseline(register):
    orders, payments, notices = (register[k] for k in ("orders", "payments", "refunds"))
    routes = {}
    explicit = {p["order"] for p in payments.values()
                if p["state"] == "已入账" and p["kind"] == "扣款" and p["order"]}
    unknown_debits = {
        k: p for k, p in payments.items()
        if p["state"] == "已入账" and p["kind"] == "扣款" and not p["order"]
    }
    by_order = defaultdict(list)
    by_payment = defaultdict(list)
    for oid, order in sorted(orders.items()):
        start = date.fromisoformat(order["date"]).toordinal()
        for key, p in unknown_debits.items():
            if ((order["merchant"], order["currency"], order["amount"])
                    == (p["merchant"], p["currency"], p["amount"])
                    and start <= date.fromisoformat(p["date"]).toordinal() <= start + 7):
                by_order[oid].append(key)
                by_payment[key].append(oid)

    for key, p in payments.items():
        if p["state"] != "已入账":
            routes[key] = ["待入账", "", "", []]
            continue
        oid = p["order"]
        if p["kind"] == "退款":
            notice = notices.get(p["notice"])
            if notice is None:
                routes[key] = ["退款缺少可核对的通知", "", "", [oid] if oid in orders else []]
                continue
            target = orders[notice["order"]]
            valid = (
                (p["merchant"], p["currency"]) == (target["merchant"], notice["currency"])
                and p["date"] >= target["date"]
                and (not oid or oid == target["id"])
            )
            routes[key] = (["退款已关联", target["id"], notice["id"], []] if valid
                           else ["退款引用冲突", "", "", sorted({target["id"], oid} & orders.keys())])
        elif oid:
            target = orders.get(oid)
            valid = target and (
                (p["merchant"], p["currency"]) == (target["merchant"], target["currency"])
                and p["date"] >= target["date"]
            )
            routes[key] = (["扣款已关联", oid, "", []] if valid
                           else ["订单引用冲突", "", "", [oid] if target else []])
        else:
            choices = by_payment[key]
            if not choices:
                routes[key] = ["找不到扣款订单", "", "", []]
            elif len(choices) == 1 and len(by_order[choices[0]]) == 1 and choices[0] not in explicit:
                routes[key] = ["扣款已关联", choices[0], "", []]
            else:
                routes[key] = ["扣款候选歧义", "", "", choices]

    amounts = defaultdict(lambda: {"扣款": [0, 0], "退款": [0, 0]})
    for key, p in payments.items():
        if p["state"] != "已入账":
            continue
        totals = amounts[p["currency"]][p["kind"]]
        totals[0] += p["amount"]
        if routes[key][1]:
            totals[1] += p["amount"]
    return routes, dict(amounts)
