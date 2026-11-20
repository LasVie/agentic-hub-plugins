"""按阶段检查、规划、复核并交付中文下料档案。"""
import argparse
from pathlib import Path
import sys

from audit import audit_cut
from contract import InputError, VERSION, accept_stock, case_from, document, encoded, integer, same_value, stock_report, write_new
from planner import DEFAULT_STATES, MAX_STATES, plan_cut
from report import dossier


class ChineseParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, add_help=False, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助并退出")

    def format_help(self) -> str:
        return super().format_help().replace("usage:", "用法：", 1).replace("\noptions:\n", "\n选项：\n")

    def error(self, message: str) -> None:
        self.exit(2, "参数错误。请运行 --help 查看必填路径和选项。\n")


def run(args: argparse.Namespace) -> dict:
    case_raw, case = case_from(args.case)
    if args.stage == "inspect":
        result = stock_report(case, args.note, args.issue)
    else:
        stock_raw, stock = document(args.stock)
        accept_stock(case, stock)
        if args.stage == "plan":
            limit = integer(args.max_states, 1, MAX_STATES, "搜索上限")
            result = plan_cut(case, stock_raw, limit)
        else:
            plan_raw, candidate = document(args.plan)
            result = audit_cut(case, stock_raw, plan_raw, candidate)
            if args.stage == "deliver":
                review_raw, review = document(args.review)
                if not same_value(review, result):
                    raise InputError("复核记录与候选摘要或独立验算不一致。")
                snapshots = {"case.json": case_raw, "stock.json": stock_raw, "plan.json": plan_raw, "review.json": review_raw}
                return dossier(case, result, snapshots, args.output)
    write_new(args.output, encoded(result))
    return result


def main() -> int:
    parser = ChineseParser(description=__doc__)
    stages = parser.add_subparsers(dest="stage", title="操作", required=True)
    for stage, title, required in (("inspect", "库存核对", ()), ("plan", "候选分配", ("stock",)),
                                   ("verify", "独立复核", ("stock", "plan")),
                                   ("deliver", "交付档案", ("stock", "plan", "review"))):
        step = stages.add_parser(stage, help=title)
        descriptions = {"case": "原始案例 JSON", "stock": "库存报告 JSON", "plan": "候选 JSON",
                        "review": "独立复核 JSON", "output": "尚不存在的文件或目录"}
        for flag in ("case", *required, "output"):
            step.add_argument("--" + flag, type=Path, required=True, help=descriptions[flag])
        if stage == "inspect":
            step.add_argument("--note", action="append", default=[], help="库存补充说明，可重复")
            step.add_argument("--issue", action="append", default=[], help="阻断规划的待澄清项，可重复")
        if stage == "plan":
            step.add_argument("--max-states", type=int, default=DEFAULT_STATES, help="规划搜索状态上限")
    args = parser.parse_args()
    try:
        result = run(args)
    except InputError as error:
        print(encoded({"ok": False, "version": VERSION, "error": str(error)}).decode(), end="")
        return 2
    except OSError:
        print(encoded({"ok": False, "version": VERSION, "error": "文件读取或创建失败。请核对权限、输入路径和输出是否已存在。"}).decode(), end="")
        return 2
    print(encoded({"ok": True, "version": VERSION, **result}).decode(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
