"""核对两版 SRT，交付字幕改版检查清单。"""
import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import sys

from inputs import clock, encode_srt, load_inputs, record, srt
from timeline import planner, reconcile, verifier


LABELS = {
    "same": "时间和正文一致",
    "same_without_edits": "两版相同，未确认剪辑范围",
    "removed": "旧字幕位于明确删除段",
    "timing_fix": "可按剪辑记录修正时间",
    "crosses_edit": "旧字幕跨越剪辑点或位于替换段",
    "ambiguous": "正文重复，归属待确认",
    "missing": "缺少可核对的对应字幕",
    "timing_unconfirmed": "两版时间有差异，需播放确认",
    "new_material": "新字幕位于变更范围或跨越切点",
    "deleted_text_present": "已删除段的旧文字仍出现在改版",
    "revised_unlinked": "改版字幕未找到可验证来源",
    "check_new_span": "播放确认新增或改录区间是否需要字幕",
    "overlap": "候选字幕时间重叠",
    "out_of_bounds": "候选字幕超出改版时长",
    "order": "候选字幕起始时间倒序",
}


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def chosen_baseline(approved, scope, evidence):
    return {"type": "baseline", "schema": 1, "evidence": evidence, "expected": verifier(approved, scope)}


def build_proposal(approved, revised, scope, evidence, timeline):
    return {"type": "proposal", "schema": 1, "evidence": evidence,
            **reconcile(approved, revised, scope, timeline)}


def make_receipt(approved, revised, scope, evidence, revised_evidence, args):
    baseline, baseline_sha = record(args.baseline)
    calculated = chosen_baseline(approved, scope, evidence)
    if dump(baseline) != dump(calculated):
        raise ValueError("独立基线与当前旧字幕或剪辑记录不符")
    proposal, proposal_sha = record(args.proposal)
    expected = build_proposal(approved, revised, scope, revised_evidence, calculated["expected"])
    if dump(proposal) != dump(expected):
        raise ValueError("方案与独立核验不一致，请检查输入摘要、时间和字幕去向")
    return proposal, {
        "type": "verification", "schema": 1, "result": "matched",
        "evidence": expected["evidence"], "baseline_sha256": baseline_sha, "proposal_sha256": proposal_sha,
        "track_status": proposal["status"], "unresolved": proposal["unresolved"],
        "approved_count": len(approved), "revised_count": len(revised),
    }


def interval(span):
    return " → ".join(clock(value) for value in span) if span else ""


def csv_literal(value):
    if value and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value or ""


def review_csv(proposal):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["判定", "旧编号", "旧时间", "旧正文", "新编号", "新时间", "新正文", "建议或预期时间", "改版播放区间"])
    for row in proposal["rows"]:
        writer.writerow([LABELS[row["kind"]], row["approved"], interval(row["approved_time"]),
                         csv_literal(row["approved_text"]), row["revised"], interval(row["revised_time"]),
                         csv_literal(row["revised_text"]), interval(row["suggested_time"]), interval(row["playback"])])
    return "\ufeff" + stream.getvalue()


def cards(proposal):
    lines = [
        "# 视频改版字幕核对", "",
        f"已确认版 {proposal['approved_count']} 条，改版 {proposal['revised_count']} 条。",
        "分析方案与独立基线一致。以下结果仅基于两版字幕和所提供的剪辑记录。", "",
    ]
    if proposal["mode"] == "comparison_only":
        lines.append("缺少剪辑记录，本次只对照两版字幕，时间差异需结合成片确认。")
    if proposal["status"] == "verified_track":
        lines.append("已生成可重新导入的 reviewed.srt。播放后确认原声与字幕一致。")
    else:
        lines.append(f"核对记录有 {proposal['unresolved']} 条需确认；本次交付核对表供继续编辑。")
    lines.extend(["", "## 变更和待播放项", ""])
    for row in proposal["rows"]:
        if row["kind"] in ("same", "same_without_edits"):
            continue
        old = f"旧 #{row['approved']} {interval(row['approved_time'])}" if row["approved"] else ""
        new = f"新 #{row['revised']} {interval(row['revised_time'])}" if row["revised"] else ""
        target = f"核对时间 {interval(row['suggested_time'])}" if row["suggested_time"] else ""
        playback = f"改版播放 {interval(row['playback'])}" if row["playback"] else ""
        items = [LABELS[row["kind"]], old, new, target, playback]
        lines.append("- " + " · ".join(item for item in items if item))
    if lines[-1] == "":
        lines.append("两版字幕没有需要列出的变更。")
    lines.extend(["", "逐条文字与完整时间见 cue-review.csv。"])
    return "\n".join(lines) + "\n"


def outputs(args):
    approved, scope, evidence = load_inputs(args.approved, args.edits)
    if args.stage == "baseline":
        return {"baseline.json": dump(chosen_baseline(approved, scope, evidence))}
    revised, revised_sha = srt(args.revised)
    revised_evidence = {**evidence, "revised_sha256": revised_sha}
    if args.stage == "propose":
        data = build_proposal(approved, revised, scope, revised_evidence,
                              planner(approved, scope))
        return {"proposal.json": dump(data)}
    proposal, expected = make_receipt(approved, revised, scope, evidence, revised_evidence, args)
    if args.stage == "verify":
        return {"verification.json": dump(expected)}
    receipt, receipt_sha = record(args.verification)
    if dump(receipt) != dump(expected):
        raise ValueError("交付必须使用与当前文件及方案一致的独立核验回执")
    files = {"review.md": cards(proposal), "cue-review.csv": review_csv(proposal)}
    if proposal["status"] == "verified_track":
        files["reviewed.srt"] = encode_srt(revised, proposal["repairs"])
    audit = {**receipt, "type": "audit", "verification_sha256": receipt_sha,
             "files_sha256": {name: sha256(body.encode("utf-8")).hexdigest() for name, body in files.items()}}
    return {**files, "audit.json": dump(audit)}


class ChineseParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, add_help=False, **kwargs)
        self._positionals.title = "位置参数"
        self._optionals.title = "选项"
        self.add_argument("-h", "--help", action="help", help="显示帮助")

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "参数错误，请用 --help 查看所需路径。\n")


def main():
    parser = ChineseParser(description=__doc__, usage="%(prog)s 阶段 [路径选项]")
    commands = parser.add_subparsers(dest="stage", required=True, title="阶段", metavar="阶段")
    descriptions = {
        "approved": "已确认 SRT 文件", "edits": "可选的旧版剪辑 JSON 文件", "revised": "改版 SRT 文件",
        "baseline": "独立基线 JSON 文件", "proposal": "分析员方案 JSON 文件",
        "verification": "独立核验回执 JSON 文件", "out": "此前不存在的阶段输出目录",
    }
    for stage, label, inputs in (
        ("baseline", "封存独立基线", ()),
        ("propose", "生成改版核对方案", ("revised",)),
        ("verify", "独立复核方案", ("revised", "baseline", "proposal")),
        ("deliver", "交付核对清单", ("revised", "baseline", "proposal", "verification")),
    ):
        command = commands.add_parser(stage, help=label, description=label, usage="%(prog)s [路径选项]")
        for name in ("approved", "edits", *inputs, "out"):
            command.add_argument("--" + name, required=name != "edits", type=Path, metavar="路径",
                                 help=descriptions[name])
    args = parser.parse_args()
    try:
        files = outputs(args)
        args.out.mkdir()
        for filename, body in files.items():
            with (args.out / filename).open("x", encoding="utf-8", newline="") as stream:
                stream.write(body)
    except (ValueError, OverflowError, RecursionError) as error:
        parser.exit(2, f"核对失败：{error}\n")
    except FileExistsError:
        parser.exit(2, "输出目录已存在，请换用新目录。\n")
    except OSError as error:
        parser.exit(2, f"无法读取或写入，请检查路径和权限（{error.filename}）。\n")
    for filename in files:
        print(f"已生成 {args.out.resolve() / filename}")


if __name__ == "__main__":
    main()
