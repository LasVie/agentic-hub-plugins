"""网购扣款与退款核对的独立阶段入口。"""

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import sys

from independent import baseline
from reconcile import proposes
from records import json_hash, money, read_register


def independent_record(register):
    routes, totals = baseline(register)
    return {"原始登记摘要": json_hash(register), "流水去向": routes, "原始及关联金额": totals}


def match_record(register):
    return {"原始登记摘要": json_hash(register), "流水去向": proposes(register)}


def checked(register, original, proposal):
    expected = independent_record(register)
    if json_hash(original) != json_hash(expected):
        raise ValueError("独立基线缺失、已修改或属于其他输入")
    if proposal.get("原始登记摘要") != expected["原始登记摘要"]:
        raise ValueError("匹配结果使用了不同的原始登记")
    proposed = proposal.get("流水去向")
    if proposed != expected["流水去向"]:
        if isinstance(proposed, dict):
            differences = sorted(k for k in proposed.keys() | expected["流水去向"].keys()
                                 if proposed.get(k) != expected["流水去向"].get(k))
            raise ValueError("独立核验发现不同去向，涉及流水 " + "、".join(differences[:10]))
        raise ValueError("匹配结果缺少合法流水去向")
    return {
        "结论": "独立核验一致",
        "原始登记摘要": expected["原始登记摘要"],
        "基线摘要": json_hash(original),
        "匹配摘要": json_hash(proposal),
        "逐币种核验": expected["原始及关联金额"],
    }


def row_counts(register, proposal):
    routes = proposal["流水去向"]
    orders, payments, notices = (register[k] for k in ("orders", "payments", "refunds"))
    debits, credits, credited_notice = Counter(), Counter(), Counter()
    payment_rows = []
    disputed_orders = defaultdict(list)
    for key, p in payments.items():
        state, order, notice, choices = routes[key]
        if state == "扣款已关联":
            debits[order] += p["amount"]
        elif state == "退款已关联":
            credits[order] += p["amount"]
            credited_notice[notice] += p["amount"]
        for oid in choices:
            disputed_orders[oid].append(key)
        refs = [p["source"]]
        if order:
            refs.append(orders[order]["source"])
        if notice:
            refs.append(notices[notice]["source"])
        detail = f"{p['kind']}；{p['state']}"
        if choices:
            detail += "；候选或冲突订单 " + "、".join(choices)
        elif p["state"] == "待入账":
            detail += "；原记录金额 " + money(p["amount"])
        payment_rows.append(["流水", key, order or p["order"], p["currency"], "",
                             money(p["amount"]) if p["state"] == "已入账" else "",
                             "", state, "；".join(refs), detail])

    rows = []
    notice_rows = []
    for key, n in notices.items():
        actual = credited_notice[key]
        difference = n["amount"] - actual
        if difference < 0:
            status = "退款入账超额"
        elif difference == 0:
            status = "退款金额相符"
        elif actual:
            status = "退款部分入账"
        else:
            status = "未见退款入账"
        notice_rows.append(["退款通知", key, n["order"], n["currency"], money(n["amount"]),
                            money(actual), money(difference), status, n["source"], "确认金额减已关联入账"])
    for key, o in orders.items():
        difference = o["amount"] - debits[key]
        if disputed_orders[key]:
            state = "存在引用冲突或候选歧义"
        elif difference < 0:
            state = "扣款超额"
        elif difference:
            state = "缺少足额扣款证据"
        else:
            state = "扣款金额相符"
        detail = f"已关联退款 {money(credits[key])}；已关联净扣款 {money(debits[key] - credits[key])}"
        if disputed_orders[key]:
            detail += "；待核查流水 " + "、".join(sorted(disputed_orders[key]))
        if credits[key] > debits[key]:
            detail += "；已关联退款高于已关联扣款，请补核证据"
            if state == "扣款金额相符":
                state = "退款与扣款需核查"
        rows.append(["订单", key, key, o["currency"], money(o["amount"]), money(debits[key]),
                     money(difference), state, o["source"], detail])
    return rows + notice_rows + payment_rows


def render(out, register, proposal, verification):
    rows = row_counts(register, proposal)
    header = ["记录类型", "标识", "订单号或原引用", "币种", "应扣或确认金额", "已入账金额",
              "差额", "结论", "来源", "说明"]
    accepted = {"扣款金额相符", "退款金额相符", "扣款已关联", "退款已关联"}
    attention = Counter(row[7] for row in rows if row[7] not in accepted)
    totals = verification["逐币种核验"]
    lines = [
        "# 网购扣款与退款核对",
        "",
        f"核对截至 {register['截至日期']}。独立核验与匹配结果一致。",
        f"原始记录共 {len(register['orders'])} 笔订单、{len(register['payments'])} 条流水、"
        f"{len(register['refunds'])} 张退款通知。",
        "",
        "## 需要跟进",
        "",
    ]
    lines.extend(f"- {label} {count} 项" for label, count in sorted(attention.items()))
    if not attention:
        lines.append("给定记录内未发现待核查项。")
    lines += [
        "",
        "待入账与商户退款确认均不计入已入账。未分配金额需查原始流水，"
        "退款差额只表示确认金额与已关联入账之差。",
        "",
        "## 已入账金额",
        "",
        "| 币种 | 方向 | 原始记录 | 已关联 | 未分配 |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for currency, by_kind in sorted(totals.items()):
        for kind, (entered, allocated) in sorted(by_kind.items()):
            lines.append(f"| {currency} | {kind} | {money(entered)} | {money(allocated)} | "
                         f"{money(entered - allocated)} |")
    if not totals:
        lines.append("| — | 尚无已入账流水 | — | — | — |")
    lines += ["", "逐条去向、差额、原始行号见 reconciliation.csv。证据摘要见 audit.json。", ""]

    out.mkdir(parents=True, exist_ok=False)
    summary_path = out / "review.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    table_path = out / "reconciliation.csv"
    with table_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for row in rows:
            for col in (1, 2, 9):
                if row[col].startswith(("=", "+", "-", "@")):
                    row[col] = "'" + row[col]
            writer.writerow(row)
    write_json(out / "audit.json", {
        "版本": "1.0.0", "截至日期": register["截至日期"], "输入摘要": register["文件摘要"],
        "独立核验": verification, "流水去向": proposal["流水去向"],
        "输出摘要": {p.name: file_hash(p) for p in (summary_path, table_path)},
        "待跟进计数": dict(attention),
    })


def file_hash(path):
    from hashlib import sha256

    return sha256(path.read_bytes()).hexdigest()


def read_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8_000_000:
        raise ValueError("阶段交接须为不超过 8 MB 的普通 JSON 文件")
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, obj):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


class ChineseParser(argparse.ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace("usage:", "用法：", 1)

    def format_help(self):
        return (super().format_help().replace("usage:", "用法：", 1)
                .replace("positional arguments:", "阶段：").replace("options:", "选项：")
                .replace("show this help message and exit", "查看帮助并退出"))

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "核对停止：阶段或参数无效，请查看 --help。\n")


def parser():
    cli = ChineseParser(description="核对本地网购订单、入账流水和退款通知")
    cli.add_argument("stage", choices=("intake", "match", "baseline", "verify", "deliver"),
                     help="阶段，顺序由主理人依据交接安排")
    cli.add_argument("--source", type=Path, help="用户授权的三张 CSV 所在目录")
    cli.add_argument("--as-of", help="核对截至日期 YYYY-MM-DD")
    cli.add_argument("--register", type=Path, help="资料梳理员生成的 register.json")
    cli.add_argument("--baseline", type=Path, help="核验员生成的 baseline.json")
    cli.add_argument("--proposal", type=Path, help="匹配员生成的 matches.json")
    cli.add_argument("--verification", type=Path, help="核验员生成的 verification.json")
    cli.add_argument("--out", type=Path, required=True, help="必须使用尚未存在的独立输出目录")
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.stage == "match":
            if not args.register:
                raise ValueError("匹配阶段需提供 --register")
            name, result = "matches.json", match_record(read_json(args.register))
        else:
            if not args.source or not args.as_of:
                raise ValueError("此阶段需提供 --source 和 --as-of")
            register = read_register(args.source, args.as_of)
            if args.stage == "intake":
                name, result = "register.json", register
            elif args.stage == "baseline":
                if args.proposal or args.register or args.baseline or args.verification:
                    raise ValueError("基线阶段只接收原始资料和截至日期")
                name, result = "baseline.json", independent_record(register)
            else:
                if not args.baseline or not args.proposal:
                    raise ValueError("核验及交付需提供 --baseline 和 --proposal")
                proposal = read_json(args.proposal)
                result = checked(register, read_json(args.baseline), proposal)
                if args.stage == "deliver":
                    if not args.verification or json_hash(read_json(args.verification)) != json_hash(result):
                        raise ValueError("缺少与该输入、基线和匹配一致的核验回执")
                    render(args.out, register, proposal, result)
                    print(f"中文摘要、核对表与审计记录已生成 {args.out.resolve()}")
                    return 0
                name = "verification.json"
        args.out.mkdir(parents=True, exist_ok=False)
        write_json(args.out / name, result)
        print(f"阶段回执已生成 {args.out.resolve() / name}")
        return 0
    except FileExistsError:
        print("核对停止：输出目录或文件已存在，请使用独立的新目录", file=sys.stderr)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"核对停止：{error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
