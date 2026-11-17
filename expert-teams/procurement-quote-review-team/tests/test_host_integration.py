"""Explicit, no-paid-model checks against a running WorkSwarm backend.

Invoke with --url and --native for import/list evidence. Add --run to execute
the deterministic local-model team fixture only in its fresh isolated instance.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import html
import json
from pathlib import Path
import time
import uuid
import zipfile


SLUG = "procurement-quote-review-team"


async def rpc(url: str, method: str, params: dict, timeout: float = 30) -> dict:
    import websockets
    ws_url = url.replace("http://", "ws://").rstrip("/") + "/ws"
    async with websockets.connect(ws_url, origin=url.rstrip("/"), max_size=8 * 1024 * 1024) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        request_id = "procurement-check-" + uuid.uuid4().hex
        await ws.send(json.dumps({"type": "req", "id": request_id, "method": method, "params": params}))
        while True:
            response = json.loads(await asyncio.wait_for(ws.recv(), timeout))
            if response.get("id") == request_id:
                if response.get("error") or response.get("ok") is False:
                    raise RuntimeError(json.dumps(response, ensure_ascii=False))
                return response


async def main(args):
    import httpx
    runtime = args.runtime.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient() as client:
        deadline = time.monotonic() + 30
        while True:
            try:
                response = await client.get(args.url, timeout=10)
                response.raise_for_status()
                break
            except httpx.ConnectError:
                if time.monotonic() >= deadline:
                    raise
                await asyncio.sleep(.5)
    model_boundary = "scripted local fixture; no reasoning-quality claim" if (args.run or args.verify_recorded_run) else "not invoked (management-only checks)"
    result = {"model": model_boundary, "url": args.url,
              "frontend_http": response.status_code,
              "native_zip_sha256": hashlib.sha256(args.native.read_bytes()).hexdigest()}
    if args.reuse_installed:
        installed = runtime / "data/domain/.agent_teams/agent_groups/local" / SLUG
        with zipfile.ZipFile(args.native) as package:
            for entry in package.infolist():
                if entry.is_dir():
                    continue
                relative = Path(entry.filename)
                if relative.parts[0] == SLUG:
                    relative = relative.relative_to(SLUG)
                if hashlib.sha256((installed / relative).read_bytes()).digest() != hashlib.sha256(package.read(entry)).digest():
                    raise RuntimeError(f"Refused reuse: installed payload differs at {relative}")
        imported = {"payload": {"id": SLUG}, "reused_installed_byte_equal_payload": True}
    else:
        imported = await rpc(args.url, "agent_groups.import_local", {"path": str(args.native.resolve())})
    result["import"] = imported
    payload = imported.get("payload", {})
    group_id = payload.get("id")
    if group_id != SLUG:
        raise RuntimeError(f"Expected genuine AgentGroup id {SLUG}, got {imported}")
    result["install"] = await rpc(args.url, "agent_groups.install", {"id": group_id})
    result["list"] = await rpc(args.url, "agent_groups.list", {"filter": "mine"})
    result["show"] = await rpc(args.url, "agent_groups.show", {"id": group_id})
    group = result["show"]["payload"]["group"]
    if group["memberCount"] != 4 or group["leaderId"] != "leader" or {x["id"] for x in group["members"]} != {"leader", "technical", "commercial", "verifier"}:
        raise RuntimeError("Installed asset is not the expected four-member AgentGroup")
    if args.run or args.verify_recorded_run:
        if not (runtime / "prepared.json").exists() or not (runtime / "plan.json").exists():
            raise RuntimeError("--run requires freshly prepared local-fixture runtime and plan.json")
        expected_url = "http://127.0.0.1:6515/"
        if args.url.rstrip("/") != expected_url.rstrip("/"):
            raise RuntimeError("Refused to run scripted chat against another instance")
        if args.run and ((runtime / "artifacts/delivery").exists() or (runtime / "events.json").exists()):
            raise RuntimeError("Use a fresh fixture runtime for --run; prior results are preserved")
        if args.verify_recorded_run:
            events = json.loads((runtime / "events.json").read_text())
            result["session_id"] = next(e["payload"]["session_id"] for e in events if e.get("payload", {}).get("accepted"))
            result["event_count"] = len(events)
            result["delivery_exists"] = (runtime / "artifacts/delivery/comparison.html").exists()
            result["verification_mode"] = "Readback of preserved real execution; no repeated model calls"
        else:
            await execute_fixture_chat(args, runtime, result)
        if not result["delivery_exists"]:
            raise RuntimeError("Real host did not produce the expected delivery; inspect isolated events/logs")
        traces = [json.loads(line) for line in (runtime / "model-requests.jsonl").read_text().splitlines()]
        collect_execution_evidence(runtime, result, group, traces)
    (runtime / "host-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    if args.record:
        # The permanent summary excludes full prompts, source documents,
        # runtime credentials and transient request IDs.
        compact = {key: value for key, value in result.items() if key not in {"show", "list", "import", "install", "session_create"}}
        compact["evidence_boundary"] = "Real host import, delegation and tool execution; all judgments are fixed synthetic fixtures, not independent model reasoning or human acceptance."
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"show", "list"}}, ensure_ascii=False, indent=2))


async def execute_fixture_chat(args, runtime: Path, result: dict):
    import websockets
    ws_url = args.url.replace("http://", "ws://").rstrip("/") + "/ws"
    session_id = "web_procurement_fixture_" + uuid.uuid4().hex[:16]
    result["session_id"] = session_id
    result["session_create"] = await rpc(args.url, "session.create", {
        "session_id": session_id, "mode": "team", "team": True,
        "persist_session": True, "cwd": str(runtime / "cwd"),
        "title": "采购比选：本地脚本化模型集成测试",
    })
    session_id = result["session_create"]["payload"]["session_id"]
    result["session_id"] = session_id
    async with websockets.connect(ws_url, origin=args.url.rstrip("/"), max_size=16 * 1024 * 1024) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        request_id = "procurement-run-" + uuid.uuid4().hex
        params = {"session_id": session_id, "content": "本次是本地脚本化模型集成测试，请真实分派成员并调用包内工具。",
                  "mode": "team", "team": True, "agent_group_name": SLUG,
                  "team_dispatch_mode": "autonomous", "supports_user_interaction": False,
                  "cwd": str(runtime / "cwd"), "trusted_dirs": [str(args.native.resolve().parents[1]), str(runtime)],
                  "plugin_names": [], "mcp": [], "skills": []}
        await ws.send(json.dumps({"type": "req", "id": request_id, "method": "chat.send", "params": params}, ensure_ascii=False))
        deadline = time.monotonic() + 180
        events = []
        while time.monotonic() < deadline:
            try:
                event = json.loads(await asyncio.wait_for(ws.recv(), 10))
                events.append(event)
                if "chat.error" in json.dumps(event):
                    raise RuntimeError(json.dumps(event, ensure_ascii=False))
            except asyncio.TimeoutError:
                pass
            if (runtime / "artifacts/delivery/comparison.html").exists():
                try:
                    traces = [json.loads(line) for line in (runtime / "model-requests.jsonl").read_text().splitlines()]
                    if leader_delivery_finished(traces):
                        break
                except json.JSONDecodeError:
                    pass  # A concurrent append may not yet contain a full line.
        (runtime / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=2))
        result["event_count"] = len(events)
        result["delivery_exists"] = (runtime / "artifacts/delivery/comparison.html").exists()
        if not result["delivery_exists"]:
            raise RuntimeError("Real host did not produce the expected delivery; inspect isolated events/logs")


def leader_delivery_finished(traces: list) -> bool:
    return any(m.get("role") == "tool" and "Exit Code: 0" in str(m.get("content", "")) and " deliver --case " in str(m.get("content", ""))
               for trace in traces if trace["role"] == "leader" for m in trace["request"]["messages"])


def collect_execution_evidence(runtime: Path, result: dict, group: dict, traces: list):
    plan = json.loads((runtime / "plan.json").read_text())
    installed_script = runtime / "data/domain/.agent_teams/agent_groups/local" / SLUG / "skills/quote-evaluation/scripts/quote_review.py"
    if Path(plan["command_script"]) != installed_script:
        raise RuntimeError("Member commands did not target the real host-installed Skill script")
    if not leader_delivery_finished(traces):
        raise RuntimeError("Missing real Leader deliver-tool completion response")
    completed = {}
    for role in ("technical", "commercial", "verifier"):
        trace_role = "verifier-review" if role == "verifier" and any(x["role"] == "verifier-review" for x in traces) else role
        relevant = [x for x in traces if x["role"] == trace_role]
        shell_ok = any(any(m.get("role") == "tool" and "Exit Code: 0" in str(m.get("content")) and str(installed_script) in str(m.get("content")) for m in x["request"]["messages"][-2:]) for x in relevant)
        completion_ok = any(any(m.get("role") == "tool" and f"Task #fixture-{trace_role} in_progress → completed" in str(m.get("content")) for m in x["request"]["messages"][-2:]) for x in relevant)
        skill_ok = any(any(m.get("role") == "tool" and "name: quote-evaluation" in str(m.get("content")) and "## Directory layout" in str(m.get("content")) for m in x["request"]["messages"][-2:]) for x in relevant)
        if not (shell_ok and completion_ok and skill_ok):
            raise RuntimeError(f"Missing real successful shared-Skill/shell/completion evidence for {role}")
        inspection = json.loads((runtime / f"artifacts/{role}-inspection.json").read_text())
        if not inspection["ok"] or inspection["case_sha256"] != plan["case_sha256"] or inspection["version"] != group["version"]:
            raise RuntimeError(f"Invalid actual installed-script result for {role}")
        completed[role] = {"actual_skill_loaded": True, "actual_shell_exit": 0, "actual_task_status": "completed", "judgment_source": "fixed synthetic fixture"}
    result["member_execution"] = completed
    result["human_testing_passed"] = False
    result["host_revision"] = json.loads((runtime / "prepared.json").read_text())["host_revision"]
    result["actual_group"] = {"id": group["id"], "source": group["source"],
                              "version": group["version"], "leader_id": group["leaderId"],
                              "member_ids": [x["id"] for x in group["members"]]}
    calls = {}
    for trace in traces:
        for message in trace["request"]["messages"]:
            if message.get("role") != "assistant":
                continue
            for call in message.get("tool_calls", []):
                caller = "verifier" if trace["role"].startswith("verifier-") else trace["role"]
                calls[(caller, call["id"])] = call["function"]["name"]
    result["actual_tool_counts"] = {role: {tool: sum(1 for (caller, _), name in calls.items() if caller == role and name == tool)
                                                  for tool in {name for (caller, _), name in calls.items() if caller == role}}
                                    for role in ("leader", "technical", "commercial", "verifier")}
    result["model_endpoint"] = "http://127.0.0.1:6516/v1"
    result["case_sha256"] = plan["case_sha256"]
    evaluation = json.loads((runtime / "artifacts/delivery/evaluation.json").read_text())
    if not evaluation["ok"] or evaluation["case_sha256"] != plan["case_sha256"]:
        raise RuntimeError("Final actual deliver output is not bound to this case")
    result["delivery_status"] = evaluation["status"]
    result["delivery_files"] = ["comparison.html", "compliance.csv", "costs.csv", "evaluation.json", "review.md", "inputs", "artifact.json"]
    if any(not (runtime / "artifacts/delivery" / name).exists() for name in result["delivery_files"]):
        raise RuntimeError("An expected actual delivery file is missing")
    if "scenario" in plan:
        result["scenario"] = plan["scenario"]
        report_notes = {}
        for role in ("technical", "commercial", "verifier"):
            report_bytes = (runtime / f"artifacts/{role}.json").read_bytes()
            frozen_bytes = (runtime / f"artifacts/delivery/inputs/reports/{role}.json").read_bytes()
            report = json.loads(report_bytes)
            if report_bytes != frozen_bytes or report["schema_version"] != 2 or plan["role_notes"][role] not in report["notes"]:
                raise RuntimeError(f"schema2 notes were lost or changed in real {role} handoff")
            report_notes[role] = report["notes"]
            if role != "commercial":
                c_quality = next(a for a in report["assessments"] if a["offer_id"] == "C" and a["criterion_id"] == "quality")
                if c_quality["status"] != "unknown" or c_quality["score"] is not None or plan["c_issue"] not in report["issues"]:
                    raise RuntimeError("C quality unknown or its scoped issue was silently removed")
        verifier_context = "\n".join(str(m.get("content", "")) for t in traces if t["role"] in {"verifier", "verifier-review"} for m in t["request"]["messages"] if m.get("role") == "tool" and "上游交付" in str(m.get("content", "")))
        if plan["handoff_summary"] not in verifier_context:
            raise RuntimeError("Real verifier did not receive upstream notes/uncertainty handoff")
        rendered_notes = json.dumps(evaluation["notes"], ensure_ascii=False)
        if not all(note in rendered_notes for notes in report_notes.values() for note in notes):
            raise RuntimeError("Informational notes did not survive into the actual delivery")
        warning_text = json.dumps(evaluation["warnings"], ensure_ascii=False)
        if "C" not in warning_text or not warning_text:
            raise RuntimeError("Excluded C uncertainty warning is absent")
        rank_ids = [row["offer_id"] for row in evaluation["rankings"]]
        eligibility = {row["offer_id"]: row for row in evaluation["eligibility"]}
        if eligibility["C"]["status"] != "excluded" or "delivery" not in eligibility["C"]["exclusion_criteria"]:
            raise RuntimeError("C is not explicitly excluded by the agreed mandatory delivery failure")
        if any(issue["blocking"] for issue in evaluation["issues"] if issue.get("offer_id") == "C" and issue["category"] == "evaluation"):
            raise RuntimeError("Excluded C evaluation uncertainty incorrectly remains blocking")
        if plan["scenario"] == "excluded-uncertainty":
            if evaluation["status"] != "reviewed" or rank_ids != ["B", "A"]:
                raise RuntimeError("Excluded C uncertainty or informational notes still block legitimate A/B ranking")
        elif evaluation["status"] != "clarification_required" or rank_ids:
            raise RuntimeError("Unresolved eligible B assessment did not block ranking")
        if plan["scenario"] == "eligible-uncertainty" and not any(issue["blocking"] for issue in evaluation["issues"] if issue.get("offer_id") == "B"):
            raise RuntimeError("Eligible B uncertainty lost its explicit blocking status")
        if plan["scenario"] == "eligible-uncertainty":
            case = json.loads(Path(plan["case"]).read_text())
            source_id = next(offer["source_ids"][0] for offer in case["offers"] if offer["id"] == "B")
            source = Path(plan["case"]).parent / next(item["path"] for item in case["sources"] if item["id"] == source_id)
            source_line = source.read_text().splitlines()[4]
            if source_line != "技术质量等级：未提供可核对的质量说明。":
                raise RuntimeError("Negative control did not contain the genuine synthetic B source gap")
            result["synthetic_source_gap"] = {"offer_id": "B", "line": 5, "text": source_line}
        delivery = runtime / "artifacts/delivery"
        html_text = (delivery / "comparison.html").read_text()
        markdown = (delivery / "review.md").read_text()
        for note in evaluation["notes"] + evaluation["warnings"]:
            if html.escape(note, quote=True) not in html_text or note not in markdown:
                raise RuntimeError("Notes/warnings were lost in actual HTML or Markdown output")
        with (delivery / "compliance.csv").open(encoding="utf-8-sig") as stream:
            compliance_csv = list(csv.DictReader(stream))
        c_quality_csv = next(row for row in compliance_csv if row["报价"] == "C" and row["要求"] == "quality")
        if c_quality_csv["技术判断"] != "unknown" or c_quality_csv["复核判断"] != "unknown" or not c_quality_csv["阻断问题或非阻断警示"]:
            raise RuntimeError("Actual compliance CSV lost excluded C unknown/warning")
        if rank_ids:
            if "<tr><td>1</td><td>B</td>" not in html_text or "第1名：报价B" not in markdown:
                raise RuntimeError("Actual HTML/Markdown ranking does not match B>A JSON")
        elif "<tr><td>1</td>" in html_text or "第1名：" in markdown:
            raise RuntimeError("Blocked output still renders a ranking")
        result["scoped_report_checks"] = {"notes_preserved": True, "c_quality_still_unknown": True,
                                           "actual_upstream_handoff": True, "warning_retained": True,
                                           "ranked_offer_ids": rank_ids,
                                           "eligibility": evaluation["eligibility"],
                                           "html_csv_markdown_consistent": True}
        if any(trace["role"] == "verifier-independent" for trace in traces):
            task_specs = {}
            for trace in traces:
                if trace["role"] != "leader":
                    continue
                for message in trace["request"]["messages"]:
                    for call in message.get("tool_calls", []):
                        if call["function"]["name"] == "create_task":
                            task_specs.update({task["task_id"]: task for task in json.loads(call["function"]["arguments"])["tasks"]})
            if task_specs["fixture-verifier-independent"]["depends_on"] or set(task_specs["fixture-verifier-review"]["depends_on"]) != {"fixture-verifier-independent", "fixture-technical", "fixture-commercial"}:
                raise RuntimeError("Actual verifier dependency graph does not enforce two stages")
            independent = [trace for trace in traces if trace["role"] == "verifier-independent"]
            before_complete = [trace for trace in independent if trace["step"] <= 3]
            if any("上游交付" in str(message.get("content", "")) for trace in before_complete for message in trace["request"]["messages"] if message.get("role") == "tool"):
                raise RuntimeError("Independent stage received upstream summaries before saving its first record")
            if not any("Task #fixture-verifier-independent in_progress → completed" in str(message.get("content", "")) for trace in independent for message in trace["request"]["messages"]):
                raise RuntimeError("Missing real independent-stage task completion")
            independent_command = plan["verifier_independent_command"]
            if any(str(runtime / f"artifacts/{name}.json") in independent_command for name in ("technical", "commercial")):
                raise RuntimeError("Independent source stage can read an initial draft")
            independent_completed_index = next(i for i, trace in enumerate(traces) if trace["role"] == "verifier-independent" and trace["step"] == 4)
            review_started_index = next(i for i, trace in enumerate(traces) if trace["role"] == "verifier-review")
            if independent_completed_index >= review_started_index:
                raise RuntimeError("Actual review started before independent-stage completion")
            review_completed_index = next(i for i, trace in enumerate(traces) if trace["role"] == "verifier-review" and trace["step"] == 4)
            leader_delivered_index = next(i for i, trace in enumerate(traces) if trace["role"] == "leader" and leader_delivery_finished([trace]))
            if review_completed_index >= leader_delivered_index:
                raise RuntimeError("Leader delivery did not follow final verifier completion")
            handoff = json.loads((runtime / "artifacts/verifier-handoff.json").read_text())
            first_report = json.loads((runtime / "artifacts/verifier-independent.json").read_text())
            if "independent_source_note" in plan and first_report["notes"] != [plan["independent_source_note"]]:
                raise RuntimeError("Independent fixture note falsely describes draft comparison before review")
            for name in ("verifier-independent", "technical", "commercial"):
                if handoff["files_sha256"][name] != hashlib.sha256((runtime / f"artifacts/{name}.json").read_bytes()).hexdigest():
                    raise RuntimeError("Actual verifier review did not bind all three real prior files")
            if (runtime / "artifacts/verifier-independent.json").stat().st_mtime_ns >= (runtime / "artifacts/verifier.json").stat().st_mtime_ns:
                raise RuntimeError("Independent file was not saved before final review")
            result["independent_review_stages"] = {"no_upstream_before_first_record": True,
                                                    "actual_independent_task_completed": True,
                                                    "review_depends_on_three_prior_tasks": True,
                                                    "leader_delivered_after_final_review": True,
                                                    "independent_note": first_report["notes"],
                                                    "actual_prior_files_sha256": handoff["files_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:6515/")
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--verify-recorded-run", action="store_true", help="Recheck preserved trace assertions without replaying chat/model calls")
    parser.add_argument("--reuse-installed", action="store_true", help="Reuse only a byte-equal package in this isolated runtime")
    parser.add_argument("--record", type=Path, help="Optional sanitized, permanent test summary path")
    asyncio.run(main(parser.parse_args()))
