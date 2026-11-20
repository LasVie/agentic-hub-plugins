"""校验独立基线、规划和复核绑定后交付中文报告。"""
import csv
from io import StringIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/meeting-evidence/scripts"))
from contract import (ChineseParser, canonical, cli, input_state, intake,
                      output_path, read, require, stamp, wall_at, write)
from datetime import timedelta

LABELS = {"ok": "符合", "conflict": "超出可用窗口", "ambiguous": "重复时刻待澄清", "nonexistent": "本地时刻不存在"}


def checked(case, identity, paths):
    receipt, intake_sha = read(paths.intake)
    own, base_sha = read(paths.baseline)
    plan, plan_sha = read(paths.plan)
    review, review_sha = read(paths.review)
    require(canonical(receipt) == canonical(intake(identity)), "梳理回执不属于当前案例或时区数据")
    rows = own.get("rows") if type(own) is dict else None
    expected_keys = [(slot, week + 1, stamp(wall_at(case.start + timedelta(weeks=week), minute)))
                     for slot, minute in case.slots for week in range(case.weeks)]
    require(type(rows) is list and all(type(r) is dict for r in rows) and
            canonical([[r.get(k) for k in ("slot", "week", "organizer_wall")] for r in rows]) ==
            canonical([list(row) for row in expected_keys]), "每个候选及周次须恰好出现一次")
    require(canonical(own) == canonical({"kind": "meeting-baseline/v1", **identity, "rows": rows}),
            "基线不属于当前案例")
    require(canonical(plan) == canonical({"kind": "meeting-plan/v1", **identity, "intake_sha256": intake_sha, "rows": rows}),
            "规划与独立基线不一致")
    expected = {"kind": "meeting-review/v1", **identity, "intake_sha256": intake_sha,
                "baseline_sha256": base_sha, "plan_sha256": plan_sha, "checked_rows": len(rows), "verdict": "pass"}
    require(canonical(review) == canonical(expected), "缺少对本次实际规划和基线的一致复核")
    for r in rows:
        require(type(r.get("status")) is str and r["status"] in LABELS, "规划状态不可识别")
        if r["status"] in ("ok", "conflict"):
            require(type(r.get("people")) is list and all(type(p) is dict for p in r["people"]) and
                    [p.get("id") for p in r["people"]] == [p.id for p in case.people], "参会者记录缺失或次序不一致")
    return rows, dict(intake=intake_sha, baseline=base_sha, plan=plan_sha, review=review_sha)


def safe_cell(text):
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def make_report(case, rows):
    out = StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(["候选", "周次", "组织者本地时刻", "状态", "参会者", "时区", "本地起点", "本地终点",
                     "窗口外分钟", "首次窗口外时刻", "UTC 起点", "UTC 终点", "可能的 UTC 起点"])
    people = {p.id: p for p in case.people}
    summary = [f"# 跨时区例会核验 · {case.id}", "",
               f"组织者时区：{case.organizer_zone}。每期{case.length}分钟，共{case.weeks}周。", "",
               "独立复算与规划逐期一致。以下结论只覆盖已提供的时段、日期例外和本次使用的时区数据。", ""]
    for slot, _ in case.slots:
        selected = [r for r in rows if r["slot"] == slot]
        ok = sum(r["status"] == "ok" for r in selected)
        label = "全部符合给定窗口" if ok == case.weeks else "有冲突或待澄清"
        summary.append(f"- {slot}：{ok}/{case.weeks} 期符合。{label}。")
    summary.extend(["", "## 需关注的期次", ""])
    for r in rows:
        heading = [r["slot"], r["week"], r["organizer_wall"], LABELS[r["status"]]]
        if "people" not in r:
            options = "；".join(r["alternatives_utc"])
            writer.writerow(heading + ["", "", "", "", "", "", "", "", options])
            summary.append(f"- {r['slot']} 第{r['week']}期：{LABELS[r['status']]}。{options}")
            continue
        for data in r["people"]:
            p = people[data["id"]]
            writer.writerow(heading + [safe_cell(p.label), p.zone, data["start"], data["end"],
                                       data["outside_minutes"], data["first_outside"] or "", r["start_utc"], r["end_utc"], ""])
            if data["outside_minutes"]:
                summary.append(f"- {r['slot']} 第{r['week']}期，{p.id}：{data['outside_minutes']}分钟在窗口外，首次为 {data['first_outside']}。")
    summary.extend(["", "完整的参会者起止时间和 UTC 对照见 meetings.csv。时区数据指纹见 audit.json。", ""])
    return "\n".join(summary), out.getvalue()


def main():
    p = ChineseParser(usage="deliver.py --input 案例.json --intake 回执.json --baseline 基线.json --plan 规划.json --review 复核.json --output 新目录", description="核对证据并交付中文版三件套")
    for key in ("input", "intake", "baseline", "plan", "review", "output"):
        p.add_argument("--" + key, required=True)
    args = p.parse_args()
    case, _, identity = input_state(args.input)
    rows, hashes = checked(case, identity, args)
    report, csv_rows = make_report(case, rows)
    dest = output_path(args.output)
    dest.mkdir()
    (dest / "review.md").write_text(report, encoding="utf-8")
    (dest / "meetings.csv").write_bytes(csv_rows.encode("utf-8-sig"))
    write(dest / "audit.json", {"kind": "meeting-audit/v1", **identity, "rows": rows, "handoff_sha256": hashes,
                                "verification": "consistent", "time_precision": "minute", "timezone_data_scope": "same host data"})
    print(f"交付 {len(rows)} 期核验，已写入中文 Markdown、CSV 及 JSON")


if __name__ == "__main__":
    cli(main)
