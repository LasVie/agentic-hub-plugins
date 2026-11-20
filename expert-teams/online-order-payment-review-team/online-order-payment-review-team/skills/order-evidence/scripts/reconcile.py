"""按引用优先、无引用时双向唯一的规则提出流水去向。"""

from collections import Counter
from datetime import date


def same_party(payment, order):
    return all(payment[key] == order[key] for key in ("merchant", "currency"))


def proposes(register):
    orders, payments, notices = (register[k] for k in ("orders", "payments", "refunds"))
    routes = {}
    candidates = {}
    reserved = set()
    for key, p in payments.items():
        if p["state"] == "待入账":
            routes[key] = ["待入账", "", "", []]
        elif p["kind"] == "退款":
            notice = notices.get(p["notice"])
            if notice is None:
                routes[key] = ["退款缺少可核对的通知", "", "",
                               [p["order"]] if p["order"] in orders else []]
            else:
                order = orders[notice["order"]]
                if (same_party(p, order) and p["date"] >= order["date"]
                        and p["order"] in {"", order["id"]}):
                    routes[key] = ["退款已关联", order["id"], notice["id"], []]
                else:
                    affected = sorted({notice["order"], p["order"]} & orders.keys())
                    routes[key] = ["退款引用冲突", "", "", affected]
        elif p["order"]:
            order = orders.get(p["order"])
            if order:
                reserved.add(order["id"])
            if order and same_party(p, order) and p["date"] >= order["date"]:
                routes[key] = ["扣款已关联", order["id"], "", []]
            else:
                routes[key] = ["订单引用冲突", "", "", [p["order"]] if order else []]
        else:
            day = date.fromisoformat(p["date"])
            candidates[key] = sorted(
                order["id"] for order in orders.values()
                if same_party(p, order) and p["amount"] == order["amount"]
                and 0 <= (day - date.fromisoformat(order["date"])).days <= 7
            )

    counts = Counter(order for choices in candidates.values() for order in choices)
    for key, choices in candidates.items():
        if len(choices) == 1 and counts[choices[0]] == 1 and choices[0] not in reserved:
            routes[key] = ["扣款已关联", choices[0], "", []]
        elif choices:
            routes[key] = ["扣款候选歧义", "", "", choices]
        else:
            routes[key] = ["找不到扣款订单", "", "", []]
    return routes
