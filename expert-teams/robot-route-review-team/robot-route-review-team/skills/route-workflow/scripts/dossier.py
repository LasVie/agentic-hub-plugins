"""Bind member artifacts, replay again and export an offline Chinese dossier."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys

from protocol import (ContractError, VERSION, bind, comments, encoded, fail,
                      load_case, object_keys, read_json, sha, write_new)

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("independent_route_replay", ROOT / "agents/verifier/skills/route-replay/scripts/replay.py")
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)
STATUS = {"reviewed": "候选路径已逐步复核，等待人工检查", "blocked": "存在阻断项，不得作为通过的规划交付",
          "infeasible_within_horizon": "规划器报告本次时域内无解；没有可回放路径", "search_limit": "搜索达到限额，结论未定；没有可回放路径"}


def deliver(case_path, analyst_path, model_path, plan_path, review_path, output):
    case, digest, case_raw = load_case(case_path)
    analyst, analyst_raw = read_json(analyst_path)
    bind(analyst, "map-analyst", digest); comments(analyst)
    object_keys(analyst, ("schema_version", "version", "role", "case_sha256", "model", "status", "case", "notes", "issues"))
    if analyst["status"] != "inspected" or analyst["case"] != case:
        fail("地图约束报告不是冻结的本次案例。")
    plan, plan_raw = read_json(plan_path)
    model, model_raw = read_json(model_path)
    report, report_raw = read_json(review_path)
    bind(report, "verifier", digest); comments(report)
    object_keys(report, ("schema_version", "version", "role", "case_sha256", "model", "plan_sha256", "model_report_sha256",
                         "verdict", "findings", "metrics", "notes", "issues"))
    expected = REPLAY.review_records(case, digest, model, model_raw, plan, plan_raw)
    if plan["map_report_sha256"] != sha(analyst_raw):
        fail("规划所用地图报告已变更；先重新规划和复核。")
    if report["plan_sha256"] != sha(plan_raw) or report["model_report_sha256"] != sha(model_raw):
        fail("复核绑定的候选/独立记录已变更；必须重新复核。")
    if any(report[key] != expected[key] for key in ("verdict", "findings", "metrics")):
        fail("复核报告与当前输入的独立回放不一致；保留分歧并停止交付。")
    blockers = [{"role": role, "message": item} for role, record in
                (("map-analyst", analyst), ("verifier-model", model), ("planner", plan), ("verifier", report))
                for item in record["issues"]]
    if report["verdict"] == "route_invalid":
        blockers.append({"role": "verifier", "message": "独立回放发现非法路径或费用不一致。"})
    status = "blocked" if blockers else "reviewed" if report["verdict"] == "route_valid" else plan["status"]
    result = {"schema_version": 1, "version": VERSION, "case_sha256": digest, "status": status,
              "status_zh": STATUS[status], "case": case, "plan": plan, "review": report,
              "model_review": model, "map_review": analyst, "blocking_issues": blockers,
              "human_testing_passed": False,
              "evidence_boundary": "脚本检查结构与离散路径，不证明成员参与、盲审、用户建模正确或真实设备安全；人工验收由用户确认。"}
    # Bind the exact bytes read for each member, not only their textual role claim.
    snapshots = {"case.json": case_raw, "map-report.json": analyst_raw, "model-review.json": model_raw,
                 "plan.json": plan_raw, "review.json": report_raw}
    out = Path(output)
    if out.is_symlink():
        fail("输出目录不能是符号链接。")
    # A successful mkdir reserves a new directory exclusively. A failed run is
    # left as evidence; artifact.json is written last as the completion marker.
    try:
        out.mkdir()
    except FileExistsError:
        fail("结果目录已存在；不会删除或覆盖，请明确授权新的目录。")
    (out / "inputs").mkdir()
    files = {}
    for name, raw in snapshots.items():
        files["inputs/" + name] = raw
    files["evaluation.json"] = encoded(result)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["时刻", "机器人", "横坐标", "纵坐标", "到达后停留", "回放判定"])
    if plan["status"] == "found":
        for tick in range(case["horizon"] + 1):
            for robot in case["robots"]:
                path = plan["paths"][robot["id"]]
                pos = path[min(tick, len(path) - 1)]
                writer.writerow([tick, robot["id"], *pos, "是" if pos == robot["goal"] else "否", report["verdict"]])
    files["timesteps.csv"] = ("\ufeff" + stream.getvalue()).encode("utf-8")
    notes = [f"# {case['title']}\n\n多机器人路径规划复核专家团 v{VERSION}\n\n{STATUS[status]}\n",
             f"输入 SHA-256：`{digest}`\n\n规划状态：`{plan['status']}`；回放：`{report['verdict']}`。",
             "\n## 阻断事项\n" + ("\n".join("- " + x["role"] + "：" + x["message"] for x in blockers) or "- 无已记录阻断项。"),
             "\n## 回放发现\n" + ("\n".join("- " + json.dumps(x, ensure_ascii=False) for x in report["findings"]) or "- 没有已记录的路径错误；无路径时不代表已完成独立无解证明。"),
             "\n## 信息说明\n" + "\n".join("- " + role + "：" + note for role, record in
                        (("map-analyst", analyst), ("verifier-model", model), ("planner", plan), ("verifier", report)) for note in record["notes"]),
             "\n## 边界\n" + result["evidence_boundary"]]
    files["review.md"] = ("\n\n".join(notes) + "\n").encode("utf-8")
    template = (ROOT / "skills/route-workflow/viewer.html").read_text(encoding="utf-8")
    safe_json = json.dumps(result, ensure_ascii=False, allow_nan=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    files["routes.html"] = template.replace("__DOSSIER_JSON__", safe_json).encode("utf-8")
    for name, raw in files.items():
        write_new(out / name, raw)
    manifest = {"version": VERSION, "status": status, "case_sha256": digest,
                "files_sha256": {name: sha(raw) for name, raw in sorted(files.items())},
                "member_report_sha256": {name: sha(raw) for name, raw in snapshots.items()},
                "human_testing_passed": False}
    write_new(out / "artifact.json", encoded(manifest))
    return {"ok": True, "version": VERSION, "status": status, "metrics": report["metrics"],
            "html": str((out / "routes.html").absolute()), "output_dir": str(out.absolute()), "case_sha256": digest}


def main():
    p = argparse.ArgumentParser(description="核对所有成员证据并交付中文离线回放档案，不覆盖旧目录。")
    for flag, help_text in (("case", "冻结案例"), ("map-report", "地图约束员报告"), ("model-report", "复核员先前独立模型审查"),
                            ("plan", "规划员候选"), ("review", "复核员实际逐步审查"), ("output", "新结果目录")):
        p.add_argument("--" + flag, type=Path, required=True, help=help_text)
    a = p.parse_args()
    try:
        print(encoded(deliver(a.case, a.map_report, a.model_report, a.plan, a.review, a.output)).decode())
    except (ContractError, OSError) as error:
        print(encoded({"ok": False, "version": VERSION, "error": str(error)}).decode()); sys.exit(2)


if __name__ == "__main__":
    main()
