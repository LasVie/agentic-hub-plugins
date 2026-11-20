"""根据已核验的阶段证据交付中文演练包。"""
import csv
import io

from contract import encode, members, parser, read_case, require, run, same, stage, write_files
from verify import comparison, read_review_inputs, review_args


DISPOSITIONS = {"present": "已在快照，无需补录", "backfilled": "模拟补录一次", "online": "模拟在线接收",
                "hold_conflict": "版本冲突，保留待确认", "hold_closed": "复工条件未齐，保留待办"}
ROUTES = {"online": "在线", "manual": "离线登记", "deferred": "超限待办"}


def escape(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;").replace("`", "\\`")


def csv_bytes(records):
    def cell(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerows([cell(value) for value in row] for row in records)
    return text.getvalue().encode("utf-8-sig")


def render(case, trace, audit):
    people, flows = members(case)
    scenarios = {s["id"]: s for s in case["scenarios"]}
    lines = [f"# 业务中断演练与复工核验 · {escape(case['title'])}", "",
             "独立复盘与演练证据一致。以下结论仅适用于本次模拟约定。", "",
             "## 中断期间", "",
             "新工作项按到达分钟和编号依次登记。人员与流程登记限额同时适用，超限继续保留在待办清单。",
             "", "| 流程 | 负责人 | 流程限额 | 负责人合计限额 | 来源 |", "| --- | --- | ---: | ---: | --- |"]
    for flow in case["workflows"]:
        owner = people[flow["owner"]]
        lines.append(f"| {escape(flow['name'])} | {escape(owner['name'])} | {flow['manual_limit']} | "
                     f"{owner['capacity']} | {escape(flow['source'])} |")
    lines.extend(["", "## 复工与回填", "",
                  "写入可用、权威快照已核、负责人模拟批准三项齐备才可以开始复工。每个流程另需等待其依赖和准备时间。",
                  "工作项按原始编号与快照一一核对。同版只记已存在；不同版须人工处理；其余已登记或排队件模拟补录一次。",
                  "", "## 两种情景的结果", ""])
    records = [["情景", "发现", "责任人", "工作项", "后续动作"]]
    journal = []
    for result in trace:
        scenario = scenarios[result["id"]]
        title = escape(scenario["title"])
        completion = result["completion"] if result["completion"] is not None else "未全部复工"
        lines.extend([f"### {title}", "",
                      f"结果 **{'符合情景目标' if result['met'] else '未满足情景目标'}**。"
                      f"全部流程在第 {completion} 分钟（目标 {scenario['target']} 分钟）。"
                      if isinstance(completion, int) else
                      "结果 **未满足情景目标**。模拟期内未全部复工。",
                      "", "| 流程 | 模拟开放分钟 |", "| --- | ---: |"])
        for key, flow in flows.items():
            lines.append(f"| {escape(flow['name'])} | {result['ready'].get(key, '未开放')} |")
        lines.extend(["", "| 工作项 | 登记路径 | 核对去向 | 分钟 | 完整按时 |",
                      "| --- | --- | --- | ---: | --- |"])
        if not result["met_target"]:
            for key, flow in flows.items():
                opening = result["ready"].get(key)
                if opening is None or opening > scenario["target"]:
                    records.append([scenario["title"], "复工超时或未开放", people[flow["owner"]]["name"], "",
                                    f"复查{flow['name']}的依赖、证据和目标，重新演练"])
        for ident, item in sorted(result["items"].items()):
            outcome = DISPOSITIONS[item["disposition"]]
            lines.append(f"| {ident} | {ROUTES[item['intake']]} | {outcome} | {item['minute']} | "
                         f"{'是' if item['met_due'] else '否'} |")
            if not item["met_due"]:
                owner = people[flows[item["flow"]]["owner"]]["name"]
                finding = outcome if item["disposition"].startswith("hold_") else "超出约定完成分钟"
                records.append([scenario["title"], finding, owner, ident, "核对原始记录并由责任人确认处置"])
        lines.append("")
        for minute, event, subject, value in result["events"]:
            journal.append(encode({"scenario": result["id"], "minute": minute, "event": event,
                                   "subject": subject, "value": value}, compact=True))
    lines.extend(["实际复工及行动项承诺由负责人另行确认。轨迹、证据摘要和行动清单随本报告交付。", ""])
    return {"playbook.md": "\n".join(lines).encode("utf-8"), "scenario-trace.jsonl": b"".join(journal),
            "actions.csv": csv_bytes(records), "audit.json": encode(audit)}


def main():
    p = parser("核查独立意见和原始阶段证据后生成中文报告")
    review_args(p, required=True)
    p.add_argument("--review", required=True, help="独立复盘核验员的 JSON")
    args = p.parse_args()
    case, source = read_case(args.input)
    baseline, trace, hashes = read_review_inputs(args, case, source)
    review, review_hash = stage(args.review, "independent-review", source, **hashes)
    checked = comparison(baseline, trace)
    require(same(review, checked) and checked["verdict"] == "matched", "独立复盘不一致或交接不完整，停止交付")
    audit = {"schema": 1, "kind": "rehearsal-audit", "case": case["id"], "case_sha256": source,
             "evidence_sha256": {**hashes, "review": review_hash}, "verification": checked,
             "scenarios": [{k: v for k, v in result.items() if k != "events"} for result in trace]}
    write_files(args.output, **render(case, trace, audit))
    print("已交付中文手册、情景轨迹、行动清单和审计文件；结果只适用于模拟。")


if __name__ == "__main__":
    raise SystemExit(run(main))
