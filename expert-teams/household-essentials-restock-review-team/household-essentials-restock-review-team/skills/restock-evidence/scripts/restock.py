"""核对家庭日用品的库存、缺货时间和补货包装。"""
import argparse
import csv
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import sys

from forecast import cross_check, project, simulate
from stock import intake, read_json


STATUSES = {"buy": "建议购买", "wait": "可等待", "check": "待确认"}
REASONS = {
    "missing_use": "缺少预计日耗",
    "existing_capacity": "计入确认到货后会超过存放上限",
    "covered": "当前可用库存与确认到货可覆盖到下次采购",
    "uncertain_stock": "盘点量或适配存量还需确认",
    "missing_pack": "缺少已知适配的包装",
    "pack_capacity": "可用包装无法同时满足缺口和存放上限",
    "shortage": "按最早缺口和窗口内最大缺口选包",
}


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def projection(facts, stage, calculate):
    return {
        "type": stage, "schema": 1, "source_sha256": facts["source_sha256"],
        "as_of": facts["as_of"], "next_shop": facts["next_shop"],
        "items": project(facts, calculate),
    }


def verify(facts, baseline, proposal):
    expected = projection(facts, "baseline", cross_check)
    if json_text(baseline) != json_text(expected):
        raise ValueError("基线与原始盘点的独立计算不一致")
    expected["type"] = "proposal"
    if json_text(proposal) != json_text(expected):
        rows = proposal.get("items")
        different = [
            original["name"]
            for index, original in enumerate(expected["items"])
            if isinstance(rows, list)
            and (index >= len(rows) or json_text(original) != json_text(rows[index]))
        ]
        items = "、".join(different) if different else "来源、日期或清单范围"
        raise ValueError(f"方案核验存在分歧：{items}")
    return {
        "type": "verification", "schema": 1, "status": "matched",
        "source_sha256": facts["source_sha256"], "matched_items": len(facts["items"]),
        "issues": [],
    }


def amount(number):
    if number is None:
        return ""
    whole, fraction = divmod(number, 1000)
    return f"{whole}.{fraction:03d}".rstrip("0").rstrip(".")


def markdown(value):
    escaped = escape(value)
    markup = r"\|[]*_!" + chr(96)
    return "".join("\\" + char if char in markup else char for char in escaped)


def shopping_list(proposal):
    lines = [
        "# 家庭日用品补货清单", "",
        f"盘点日 {proposal['as_of']}，覆盖至 {proposal['next_shop']} 下次采购当天开始前。"
        "先按确认日期计入当天可用到货，再扣除预计日耗。", "",
    ]
    for status, title in STATUSES.items():
        lines.extend([f"## {title}", ""])
        rows = [row for row in proposal["items"] if row["status"] == status]
        if not rows:
            lines.extend(["本次无。", ""])
        for row in rows:
            unit = markdown(row["unit"])
            item = markdown(row["name"])
            if row["variant"]:
                item += f"（规格 {markdown(row['variant'])}）"
            text = f"- **{item}**。{REASONS[row['reason']]}。"
            if row["first_shortage"]:
                text += f" 预计首次缺货 {row['first_shortage']}，覆盖期最大缺口 {amount(row['shortfall'])} {unit}。"
            pack = row["purchase"]
            if pack:
                text += f" 买 {pack['count']} 包，每包 {amount(pack['size'])} {unit}，共 {amount(pack['total'])} {unit}。"
            if row["notes"]:
                text += " " + "；".join(row["notes"]) + "。"
            lines.append(text)
        if rows:
            lines.append("")
    lines.append("使用量为估计值。实际盘点或已确认到货变化时可重新核对。")
    return "\n".join(lines) + "\n"


def csv_text(proposal):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["用品", "规格", "单位", "决定", "预计首次缺货", "最大缺口", "未补货时存量峰值",
                     "建议包数", "每包数量", "建议合计", "原因", "备注"])
    for row in proposal["items"]:
        pack = row["purchase"] or {}
        labels = [row["name"], row["variant"] or "", row["unit"]]
        # 在电子表格中仍以文字显示用户提供的标签。
        safe_labels = ["'" + label if label.startswith(("=", "+", "-", "@")) else label for label in labels]
        writer.writerow([*safe_labels, STATUSES[row["status"]], row["first_shortage"] or "", amount(row["shortfall"]),
                         amount(row["peak_before_purchase"]), pack.get("count", ""), amount(pack.get("size")),
                         amount(pack.get("total")), REASONS[row["reason"]], "；".join(row["notes"])])
    return "\ufeff" + stream.getvalue()


def checked_inputs(args):
    facts = intake(args.source)
    baseline, baseline_hash = read_json(args.baseline)
    proposal, proposal_hash = read_json(args.proposal)
    receipt = verify(facts, baseline, proposal)
    receipt.update(baseline_sha256=baseline_hash, proposal_sha256=proposal_hash)
    return proposal, receipt


def stage(args):
    if args.stage == "plan":
        facts, _ = read_json(args.intake)
        if facts.get("type") != "intake" or facts.get("schema") != 1:
            raise ValueError("需要库存登记回执")
        return {"proposal.json": json_text(projection(facts, "proposal", simulate))}
    if args.stage == "intake":
        return {"intake.json": json_text(intake(args.source))}
    if args.stage == "baseline":
        return {"baseline.json": json_text(projection(intake(args.source), "baseline", cross_check))}
    proposal, expected = checked_inputs(args)
    if args.stage == "verify":
        return {"verification.json": json_text(expected)}
    receipt, receipt_hash = read_json(args.verification)
    if json_text(receipt) != json_text(expected):
        raise ValueError("需要与当前原文、基线和方案相符的核验回执")
    outputs = {"shopping-list.md": shopping_list(proposal), "restock.csv": csv_text(proposal)}
    audit = {
        **receipt, "type": "audit", "scope": {"as_of": proposal["as_of"], "next_shop": proposal["next_shop"]},
        "verification_sha256": receipt_hash,
        "files_sha256": {name: sha256(value.encode("utf-8")).hexdigest() for name, value in outputs.items()},
    }
    return {**outputs, "audit.json": json_text(audit)}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "参数错误，请用 --help 查看本阶段所需的路径。\n")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, add_help=False, **kwargs)
        self._positionals.title = "位置参数"
        self._optionals.title = "选项"
        self.add_argument("-h", "--help", action="help", help="显示帮助")


def main():
    parser = Parser(description=__doc__, usage="%(prog)s 阶段 [路径选项]")
    steps = parser.add_subparsers(dest="stage", required=True, title="阶段", metavar="阶段")
    paths = {
        "source": "原始盘点 JSON", "intake": "库存登记回执路径", "baseline": "独立基线路径",
        "proposal": "主理人方案路径", "verification": "独立核验回执路径", "out": "新的输出目录路径",
    }
    for name, title, inputs in (
        ("intake", "登记库存", ["source"]),
        ("baseline", "记录独立基线", ["source"]),
        ("plan", "选择补货包装", ["intake"]),
        ("verify", "复核补货方案", ["source", "baseline", "proposal"]),
        ("deliver", "交付核对清单", ["source", "baseline", "proposal", "verification"]),
    ):
        command = steps.add_parser(name, help=title, description=title, usage="%(prog)s [路径选项]")
        for key in [*inputs, "out"]:
            command.add_argument("--" + key, type=Path, required=True, metavar="路径", help=paths[key])
    args = parser.parse_args()
    try:
        files = stage(args)
        args.out.mkdir()
        for name, body in files.items():
            with (args.out / name).open("x", encoding="utf-8", newline="") as stream:
                stream.write(body)
    except ValueError as error:
        parser.exit(2, f"处理失败：{error}\n")
    except (KeyError, TypeError, IndexError, OverflowError, RecursionError):
        parser.exit(2, "处理失败：输入或回执的数据结构不符合要求。\n")
    except FileExistsError:
        parser.exit(2, "处理失败：输出目录已存在，请换用新路径。\n")
    except OSError as error:
        parser.exit(2, f"处理失败：无法读取输入或写入输出，请检查路径和权限（{error.filename}）。\n")
    for name in files:
        print(f"已生成 {args.out.resolve() / name}")


if __name__ == "__main__":
    main()
