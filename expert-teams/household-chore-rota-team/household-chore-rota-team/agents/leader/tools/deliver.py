"""交付同一快照的中文轮值、CSV和审查档案；程序不证明成员参与。"""
from __future__ import annotations

import csv
from datetime import date, timedelta
from html import escape
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills/rota-evidence/scripts"))
from contract import (ChineseParser, VERSION, cli, digest, integer, keys, loads_for, new_dir,
                      read_json, require, text, validate_case, verify_intake, write_json)


def csv_cell(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")) else value


def check_reports(case, source, intake, intake_sha, plan, plan_sha, review, notes):
    verify_intake(intake, case, source)
    keys(plan, {"schema_version", "kind", "version", "source_sha256", "case_sha256", "intake_sha256", "status", "assignments", "search", "loads", "preference_misses", "message"}, "规划报告")
    keys(review, {"schema_version", "kind", "version", "source_sha256", "case_sha256", "plan_sha256", "verdict", "issues", "loads", "preference_misses", "coverage", "boundary"}, "独立复核报告")
    keys(notes, {"schema_version", "case_sha256", "plan_sha256", "conclusion", "reasons"}, "内容复核说明")
    for obj in (plan, review, notes):
        require(type(obj["schema_version"]) is int and obj["schema_version"] == 1, "报告结构版本不匹配")
        require(obj["case_sha256"] == digest(case), "报告不属于当前约定案例")
    require(plan["kind"] == "rota-plan/v1" and review["kind"] == "rota-review/v1" and plan["version"] == review["version"] == VERSION, "报告种类或包版本不匹配")
    require(plan["source_sha256"] == review["source_sha256"] == source and plan["intake_sha256"] == intake_sha, "报告来源已变化，请重新执行交接")
    require(review["plan_sha256"] == notes["plan_sha256"] == plan_sha, "规划报告已变化，请重新独立复核")
    require(plan["status"] in ("feasible", "infeasible", "unknown"), "规划状态无效")
    search = keys(plan["search"], {"nodes", "node_limit", "space_exhausted", "optimality_claim", "strategy"}, "搜索记录")
    integer(search["node_limit"], 1, 500000, "搜索上限")
    integer(search["nodes"], 1, search["node_limit"], "搜索节点数")
    require(search["optimality_claim"] is False and search["strategy"] == "bounded-balanced-first-feasible", "本版不能交付最优性声明或未知搜索方式")
    require(type(search["space_exhausted"]) is bool and search["space_exhausted"] == (plan["status"] == "infeasible"), "搜索状态与穷尽标识矛盾")
    require(review["verdict"] in ("pass", "block") and notes["conclusion"] in ("pass", "block"), "复核结论无效")
    require(type(review["issues"]) is list and len(review["issues"]) <= 100, "复核问题列表无效")
    require(type(notes["reasons"]) is list and 1 <= len(notes["reasons"]) <= 20, "内容复核须写明1至20项实际依据")
    for line in review["issues"] + notes["reasons"]:
        text(line, "复核说明", 1000)
    require((review["verdict"] == "pass") == (review["issues"] == []), "复核通过标识与问题清单矛盾")
    blockers = list(review["issues"])
    loads, misses, assignments = None, None, []
    if plan["status"] == "feasible":
        loads, hard, misses = loads_for(case, plan["assignments"])
        blockers.extend(hard)
        require(digest(loads) == digest(plan["loads"]), "规划负担的数值或类型与主理人复算不一致")
        require(misses == plan["preference_misses"], "规划偏好清单与主理人复算不一致")
        # A blocking verifier may provide no totals when assignment coverage failed.
        if review["verdict"] == "pass":
            require(digest(review["loads"]) == digest(loads) and review["preference_misses"] == misses and review["coverage"] == "complete", "独立复算与交付复算不一致")
        assignments = plan["assignments"]
    else:
        require(plan["assignments"] == [] and plan["loads"] is None and plan["preference_misses"] is None, "未得到轮值时不能交付分配或虚构零负担")
        blockers.append("尚无通过复核的完整轮值；搜索未决不等于无解")
    if notes["conclusion"] == "block":
        blockers.extend("内容复核阻塞：" + x for x in notes["reasons"])
    if review["verdict"] != "pass":
        blockers.append("独立核验尚未通过")
    return {"status": "draft" if blockers else "verified", "blockers": list(dict.fromkeys(blockers)),
            "loads": loads, "preference_misses": misses, "assignments": assignments}


def html_page(case, result, notes):
    e = lambda x: escape(str(x), quote=True)
    people = {p["id"]: p for p in case["participants"]}
    chosen = {x["duty_id"]: x["participant_id"] for x in result["assignments"]}
    start = date.fromisoformat(case["start_date"])
    verified = result["status"] == "verified"
    badge = "约定检查通过" if verified else "待澄清草稿 · 请勿视为已确认轮值"
    cards = []
    for day in range(7):
        current = start + timedelta(days=day)
        duties = []
        for d in case["duties"]:
            if d["day"] != day:
                continue
            pid = chosen.get(d["id"])
            name = people[pid]["name"] if pid else "待分配"
            tag = " · 偏好未满足" if result["preference_misses"] and d["id"] in result["preference_misses"] else ""
            duties.append(f'<li><strong>{e(d["name"])}</strong><span>{e(name)} · {d["minutes"]}分钟{e(tag)}</span><small>{e(d["id"])}</small></li>')
        cards.append(f'<section class="day"><h3>{e(current.isoformat())}<span>星期{"一二三四五六日"[current.weekday()]}</span></h3><ul>{"".join(duties) or "<li>无约定家务</li>"}</ul></section>')
    totals = []
    for p in case["participants"]:
        load = result["loads"].get(p["id"]) if result["loads"] is not None else None
        total = f'{load["weekly_minutes"]} / {p["weekly_limit"]} 分钟' if load is not None else "未核验，不记为零"
        daily = "、".join(str(x) for x in load["daily_minutes"]) if load is not None else "未核验"
        totals.append(f'<tr><th>{e(p["name"])}</th><td>{e(total)}</td><td>{e(daily)}</td></tr>')
    problems = "".join(f"<li>{e(x)}</li>" for x in result["blockers"]) or "<li>未发现本版已核对的约定限制冲突。</li>"
    reasons = "".join(f"<li>{e(x)}</li>" for x in notes["reasons"])
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(case["household"])} · 一周家务轮值</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f2;color:#20332c;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1250px;margin:auto;padding:32px}}header{{border-left:6px solid #25775e;padding:8px 24px;margin-bottom:24px}}h1{{font-size:32px;margin:8px 0}}h2{{margin-top:32px}}.eyebrow{{color:#527268;letter-spacing:.12em}}.badge{{display:inline-block;background:{"#d5ece0" if verified else "#ffe2be"};border-radius:30px;padding:5px 14px;font-weight:650}}.week{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}}.day{{background:white;border:1px solid #dbe5dc;border-radius:12px;padding:16px}}h3{{font-size:16px;margin:0 0 12px;border-bottom:1px solid #e5ebe7;padding-bottom:10px}}h3 span,li span,li small{{display:block}}small{{color:#6c8177}}ul{{padding-left:20px}}.day ul{{padding-left:0;list-style:none}}.day li{{margin:12px 0}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{border:1px solid #d5e0d8;padding:12px;text-align:left}}.note{{background:#e5eee7;border-radius:12px;padding:16px 20px}}footer{{font-size:13px;color:#5b756a;margin-top:30px}}@media print{{body{{background:white}}main{{padding:8px}}.day{{break-inside:avoid}}}}@media(max-width:600px){{main{{padding:16px}}h1{{font-size:25px}}table{{font-size:13px}}}}
</style><main><header><div class="eyebrow">家务轮值与负担复核专家团 · {VERSION}</div><h1>{e(case["household"])}的一周家务</h1><p>{e(start.isoformat())} 至 {e((start + timedelta(days=6)).isoformat())} · {len(case["duties"])}次家务 · 约定{sum(d["minutes"] for d in case["duties"])}分钟</p><p class="badge">{badge}</p></header>
<div class="week">{"".join(cards)}</div><h2>约定负担核对</h2><table><thead><tr><th>参与者</th><th>本周已排 / 约定上限</th><th>第一天至第七天的分钟数</th></tr></thead><tbody>{"".join(totals)}</tbody></table>
<h2>核对结果与待澄清项</h2><ul>{problems}</ul><h2>独立内容复核说明</h2><ul>{reasons}</ul>
<div class="note">分钟数来自用户约定，不是实际计时。偏好是软条件，不能覆盖不可用日或负担上限。通过只表示本版已核对的结构、覆盖和限制相符；不代表全局最优、所有家务已被发现或家庭成员已经接受。各成员实际参与请查看宿主任务与消息。</div>
<footer>案例：{e(case["case_id"])} · 约定快照摘要：{digest(case)}<br>配套文件：assignments.csv 与 review.json。原始资料保持不变。</footer></main></html>'''


def run():
    parser = ChineseParser(description="核对三方证据后交付中文轮值；存在问题则只交付待澄清草稿")
    for name, help_text in (("input", "原始案例"), ("intake", "梳理报告"), ("plan", "规划报告"), ("review", "独立程序复核报告"), ("notes", "核验员内容复核说明"), ("output", "新的交付目录")):
        parser.add_argument("--" + name, required=True, type=Path, help=help_text + "绝对路径")
    args = parser.parse_args()
    case, source = read_json(args.input)
    validate_case(case)
    intake, intake_sha = read_json(args.intake)
    plan, plan_sha = read_json(args.plan)
    review, review_sha = read_json(args.review)
    notes, notes_sha = read_json(args.notes)
    result = check_reports(case, source, intake, intake_sha, plan, plan_sha, review, notes)
    require(read_json(args.input)[1] == source, "交付前原始输入已变化，请重新执行整轮交接")
    dest = new_dir(args.output)
    with (dest / "rota.html").open("x", encoding="utf-8") as out:
        out.write(html_page(case, result, notes))
    chosen = {a["duty_id"]: a["participant_id"] for a in result["assignments"]}
    people = {p["id"]: p["name"] for p in case["participants"]}
    start = date.fromisoformat(case["start_date"])
    with (dest / "assignments.csv").open("x", encoding="utf-8-sig", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["家务编号", "家务", "日期", "负责人", "分钟数", "复核状态", "偏好"])
        for d in case["duties"]:
            if d["id"] in chosen:
                writer.writerow([csv_cell(x) for x in [d["id"], d["name"], (start + timedelta(days=d["day"])).isoformat(), people[chosen[d["id"]]], d["minutes"], "约定检查通过" if result["status"] == "verified" else "待澄清草稿", "未满足" if d["id"] in (result["preference_misses"] or []) else "符合或未指定"]])
    dossier = {"schema_version": 1, "kind": "rota-delivery/v1", "version": VERSION,
               "delivery_status": result["status"], "source_sha256": source, "case_sha256": digest(case),
               "report_sha256": {"intake": intake_sha, "plan": plan_sha, "review": review_sha, "notes": notes_sha},
               "case_snapshot": case, "result": result, "independent_review": review, "content_review": notes,
               "boundary": "程序不认证成员身份、实际参与或家庭共识；不得用角色文字代替真实宿主执行证据"}
    write_json(dest / "review.json", dossier)
    for name in ("rota.html", "assignments.csv"):
        (dest / name).chmod(0o600)
    print(json.dumps({"ok": True, "状态": "约定检查通过" if result["status"] == "verified" else "待澄清草稿", "阻塞项": result["blockers"], "输出": [str(dest / name) for name in ("rota.html", "assignments.csv", "review.json")]}, ensure_ascii=False))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    cli(run)
