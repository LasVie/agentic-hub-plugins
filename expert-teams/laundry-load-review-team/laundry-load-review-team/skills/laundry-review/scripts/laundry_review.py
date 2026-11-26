"""Produce a Chinese wash and drying checklist from frozen, verified handoffs."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from contract import ACTION, DRY, HOLD, VERSION, InputError, decoded, digest, encoded, fields, load_case, read_file, require
from planner import plan
from reviewer import independent, review

FINDING = {
    "duplicate_in_load": "同一组别在同一批重复列出",
    "program_conflict": "程序温度、动作强度或机洗条件不相容",
    "dry_conflict": "干燥动作与确认标签不一致",
    "color_conflict": "同一批混入不同颜色组",
    "separate_conflict": "须分洗的衣物未独自成批",
    "count_limit": "批次超过已约定件数",
    "duplicate_hold": "待处理组重复",
    "incorrect_hold": "待处理原因或件数不成立",
    "coverage": "分配和待处理件数与原衣篮不符",
}
STATUS_ZH = {
    "reviewed": "洗涤与干燥清单已复核",
    "reviewed_with_holds": "可用批次已复核，另有待处理项",
    "blocked": "候选需要修正，暂不提供可执行批次",
}


def bind(case, stage, result, **dependencies):
    return {"stage": stage, "case_sha256": case.sha256, "version": VERSION, **dependencies, "result": result}


def read_bound(body, case, stage):
    report = decoded(body)
    fields(report, "stage case_sha256 version result", "交接报告")
    require(report["stage"] == stage and report["case_sha256"] == case.sha256 and report["version"] == VERSION,
            "交接报告不属于当前案例或当前版本。")
    return report["result"]


def evaluate(case, baseline_body, plan_body):
    expected = independent(case)
    recorded = read_bound(baseline_body, case, "baseline")
    require(encoded(recorded) == encoded(expected), "保存的独立清单与冻结原案不一致。")
    candidate = read_bound(plan_body, case, "plan")
    findings = review(case, candidate, expected)
    return bind(case, "verify", findings, baseline_sha256=digest(baseline_body), plan_sha256=digest(plan_body))


def render(case, data):
    def group_name(group):
        return escape(case.profiles[group]["name"])

    loads = []
    for index, batch in enumerate(data["batches"], 1):
        program = case.programs[batch["program"]]
        mode = f"{program['celsius']}°C · {ACTION[program['action']]}"
        cap = program["max_items"]
        capacity = f"本次件数上限 {cap} 件" if cap is not None else "开始前按机器说明核对装载量"
        rows = "".join(f"<tr><th>{group_name(row['profile'])}</th><td>{row['count']}</td>"
                       f"<td>{DRY[row['dry']]}</td></tr>" for row in batch["items"])
        count = sum(item["count"] for item in batch["items"])
        loads.append(
            f"<section><h2>第 {index} 批 · {escape(program['name'])}</h2>"
            f"<p>{mode} · {count} 件 · {capacity}</p>"
            "<table><thead><tr><th>衣物</th><th>件数</th><th>洗后干燥</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></section>"
        )
    hold_list = []
    for item in data["held"]:
        hold_list.append(f"<li>{group_name(item['profile'])} · {item['count']} 件 · {HOLD[item['reason']]}</li>")
    for item in data["dry_pending"]:
        hold_list.append(f"<li>{group_name(item['profile'])} · {item['count']} 件 · 洗后先确认干燥标签</li>")
    holds = f"<section><h2>待处理</h2><ul>{''.join(hold_list)}</ul></section>" if hold_list else ""
    problems = []
    for issue in data["findings"]:
        location = []
        if issue["batch"] is not None:
            location.append(f"第 {issue['batch']} 批")
        if issue["profile"] is not None:
            location.append(group_name(issue["profile"]))
        location.append(FINDING[issue["code"]])
        problems.append("<li>" + " · ".join(location) + "</li>")
    findings = f"<section><h2>复核问题</h2><ul>{''.join(problems)}</ul></section>" if problems else ""
    amount = f"{data['checked_pieces']} 件 · {len(data['batches'])} 个可用洗涤批次"
    styles = """
    *{box-sizing:border-box}body{margin:0;background:#f0f4f6;color:#173039;font:16px/1.6 system-ui,sans-serif}
    main{max-width:900px;margin:auto;padding:clamp(18px,5vw,54px)}h1,h2{line-height:1.25;margin-top:0}
    h1{font-size:clamp(28px,5vw,44px);margin-bottom:6px}
    .status{background:#cfe8e4;border-left:5px solid #166c64;padding:12px 16px;font-weight:650}
    .blocked{background:#fae3d9;border-color:#a04d36}section{margin:20px 0;padding:18px;background:white;border:1px solid #c5d8de;border-radius:10px}
    table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #dce6ea}
    th:nth-child(2),td:nth-child(2){white-space:nowrap;width:62px}a{color:#145a63}
    """
    state = data["status"]
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>日常洗衣分批清单</title><style>{styles}</style></head><body>
<main><h1>日常洗衣分批清单</h1><p>{escape(case.title)} · v{VERSION}</p>
<p class="status {state}">{STATUS_ZH[state]}</p><p>{amount}</p>
{''.join(loads)}{holds}{findings}
<p>请按衣物标签和机器说明核对实际装载、程序与干燥设置。</p>
<p><a href="evaluation.json">复核记录 JSON</a> · <a href="artifact.json">文件摘要清单</a></p>
</main></body></html>
"""


def deliver(case, baseline_body, plan_body, review_body, output):
    verified = evaluate(case, baseline_body, plan_body)
    require(encoded(decoded(review_body)) == encoded(verified), "最终复核报告已过期或与证据不一致。")
    checks = verified["result"]
    candidate = decoded(plan_body)["result"]
    is_usable = checks["status"] != "blocked"
    data = {
        "version": VERSION, "case_sha256": case.sha256, "human_testing_passed": False,
        "status": "blocked", "batches": [], "held": [], "dry_pending": [],
        "checked_pieces": checks["checked_pieces"], "findings": checks["findings"],
    }
    if is_usable:
        batches = candidate["batches"]
        data["batches"] = batches
        data["held"] = candidate["held"]
        pending = {}
        for batch in batches:
            for item in batch["items"]:
                if item["dry"] == "unknown":
                    group = item["profile"]
                    pending[group] = pending.get(group, 0) + item["count"]
        data["dry_pending"] = [{"profile": group, "count": count} for group, count in pending.items()]
        data["status"] = "reviewed_with_holds" if data["held"] or pending else "reviewed"
    files = {
        "inputs/case.json": case.data,
        "handoffs/baseline.json": baseline_body, "handoffs/plan.json": plan_body, "handoffs/review.json": review_body,
        "evaluation.json": encoded(data), "checklist.html": render(case, data).encode("utf-8"),
    }
    manifest = {"version": VERSION, "status": data["status"], "files_sha256": {name: digest(body) for name, body in files.items()}}
    files["artifact.json"] = encoded(manifest)
    # Write exclusively and publish the manifest last so a partial run cannot appear complete.
    output.mkdir()
    for relative, body in files.items():
        dest = output / relative
        dest.parent.mkdir(exist_ok=True)
        with dest.open("xb") as stream:
            stream.write(body)
    return data["status"]


def main():
    parser = argparse.ArgumentParser(description="核查一篮衣物，生成中文版洗涤与干燥清单。",
                                     usage="laundry_review.py {baseline,plan,verify,deliver} --case 案例 --output 新路径")
    parser.add_argument("stage", choices=("baseline", "plan", "verify", "deliver"), help="独立初核、规划、复核或交付")
    parser.add_argument("--case", required=True, type=Path, help="用户确认的冻结案例 JSON")
    parser.add_argument("--output", required=True, type=Path, help="新报告路径或新交付目录")
    parser.add_argument("--baseline", type=Path, help="先保存的独立可用程序清单")
    parser.add_argument("--plan", type=Path, help="候选分批")
    parser.add_argument("--review", type=Path, help="候选复核")
    args = parser.parse_args()
    try:
        require(not args.output.exists() and not args.output.is_symlink(), "输出已存在，请选新路径。")
        needed = {"baseline": set(), "plan": set(), "verify": {"baseline", "plan"},
                  "deliver": {"baseline", "plan", "review"}}[args.stage]
        provided = {name for name in ("baseline", "plan", "review") if getattr(args, name) is not None}
        require(provided == needed, "交接参数不符合当前步骤。")
        case = load_case(args.case)
        if args.stage == "deliver":
            status = deliver(case, read_file(args.baseline), read_file(args.plan), read_file(args.review), args.output)
        else:
            if args.stage == "baseline":
                record = bind(case, "baseline", independent(case))
            elif args.stage == "plan":
                record = bind(case, "plan", plan(case))
            else:
                record = evaluate(case, read_file(args.baseline), read_file(args.plan))
            with args.output.open("xb") as stream:
                stream.write(encoded(record))
            status = record["result"]["status"] if args.stage == "verify" else "recorded"
        print(json.dumps({"ok": True, "status": status, "version": VERSION, "output": str(args.output)}, ensure_ascii=False))
        return 0
    except InputError as error:
        message = str(error)
    except (ValueError, RecursionError):
        message = "JSON 或文件编码无效。"
    except OSError:
        message = "文件不可读或输出不可写，请检查目录、路径与权限。"
    print(json.dumps({"ok": False, "status": "blocked", "message": message, "version": VERSION}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
