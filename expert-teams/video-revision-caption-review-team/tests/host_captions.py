"""Run the installed caption team through a fixed-response WorkSwarm session."""
from collections import Counter
import json
from pathlib import Path
import shlex
import sys
import time

ASSET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSET.parent / "business-interruption-rehearsal-team/tests"))
import host_integration as host

PRIVATE = {"leader": "caption-delivery", "timeline-analyst": "caption-timeline", "verifier": "caption-verification"}
SHARED = "caption-evidence"
STAGES = {"leader": ("deliver",), "timeline-analyst": ("propose",), "verifier": ("baseline", "verify")}
FILES = {"baseline": "baseline/baseline.json", "propose": "propose/proposal.json",
         "verify": "verify/verification.json", "deliver": "deliver/audit.json"}


def make_plan(runtime, case_dir):
    work = runtime / "artifacts"
    for name in ("approved.srt", "revised.srt", "edits.json"):
        with (work / name).open("xb") as stream:
            stream.write((case_dir / name).read_bytes())
    package = runtime / "data/domain/.agent_teams/agent_groups/local" / ASSET.name
    script = package / "skills/caption-evidence/scripts/captions.py"
    if not script.is_file():
        raise ValueError("Import the exact native ZIP before planning the run")
    evidence = ["--approved", str(work / "approved.srt"), "--edits", str(work / "edits.json")]
    revised = [*evidence, "--revised", str(work / "revised.srt")]
    verified = [*revised, "--baseline", str(work / FILES["baseline"]), "--proposal", str(work / FILES["propose"])]
    arguments = {"baseline": evidence, "propose": revised, "verify": verified,
                 "deliver": [*verified, "--verification", str(work / FILES["verify"])]}
    prefix = [host.settings(runtime)["python"], "-B", str(script)]
    commands = {stage: shlex.join([*prefix, stage, *args, "--out", str(work / stage)])
                for stage, args in arguments.items()}
    host.save(runtime / "plan.json", {"commands": commands})


class CaptionProvider(host.ScriptedProvider):
    def ready(self, stages, predicate):
        deadline = time.monotonic() + 55
        while time.monotonic() < deadline:
            with self.lock:
                handoff = predicate()
            if handoff and all((self.runtime / "artifacts" / FILES[s]).is_file() for s in stages):
                return
            time.sleep(0.1)
        raise RuntimeError(f"Missing actual handoff: {stages}")

    def answer(self, request):
        leader = any(tool["function"]["name"] == "create_task" for tool in request.get("tools", [])
                     if tool.get("type") == "function")
        if leader and self.steps.get("leader") == 4:
            self.ready(("baseline", "propose"), lambda: self.steps.get("verifier", 0) >= 5
                       and "timeline-analyst" in self.done)
        return super().answer(request)

    def actions(self, role, plan):
        work = self.runtime / "artifacts"

        def command(stage):
            return "bash", {"command": plan["commands"][stage], "timeout": 40, "description": "运行安装脚本 " + stage}

        if role == "leader":
            result = [("build_team", {"display_name": "字幕改版本地测试", "team_desc": "验证实际分派与交接",
                                      "leader_display_name": "改版核验主理人", "leader_desc": "运行安装包",
                                      "enable_hitt": False, "call_goal": "启动三角色专家团"})]
        else:
            result = [("claim_task", {"task_id": f"caption-{role}", "status": "claimed"})]
        result.extend(("skill_tool", {"skill_name": skill, "call_goal": "读取技能"}) for skill in (PRIVATE[role], SHARED))
        if role == "leader":
            initial = f"已确认字幕 {work / 'approved.srt'}；剪辑记录 {work / 'edits.json'}"
            tasks = []
            for member in host.ROLES:
                content = initial if member == "verifier" else f"{initial}；改版字幕 {work / 'revised.srt'}"
                tasks.append({"task_id": f"caption-{member}", "title": "字幕核对：" + member,
                              "content": f"REHEARSAL_FIXTURE_ROLE={member}\n{content}",
                              "assignee": member, "depends_on": []})
            return result + [("create_task", {"tasks": tasks}),
                             ("send_message", {"to": "verifier", "content": f"基线已封存。改版字幕 {work / 'revised.srt'}；"
                                                                           f"方案 {work / FILES['propose']}"}),
                             command("deliver")]
        if role == "verifier":
            result.extend([command("baseline"), ("send_message", {"to": "team-leader",
                           "content": f"基线已封存：{work / FILES['baseline']}"})])
        stage = "verify" if role == "verifier" else "propose"
        return result + [command(stage), ("send_message", {"to": "team-leader", "content": f"回执：{work / FILES[stage]}"}),
                         ("claim_task", {"task_id": f"caption-{role}", "status": "completed", "summary": "已交接真实回执"})]

    def await_handoff(self, role, blind):
        if blind or role == "timeline-analyst":
            return
        if role == "leader":
            self.ready(("verify",), lambda: set(host.ROLES) <= self.done)
        else:
            self.ready(("propose",), lambda: self.steps.get("leader", 0) >= 5)


def verify_execution(runtime, result, events, record):
    if not any(event.get("payload", {}).get("accepted") for event in events):
        raise RuntimeError("No accepted native session")
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    plan = json.loads((runtime / "plan.json").read_text())
    roles = {}
    for role, stages in STAGES.items():
        messages = [row["request"]["messages"] for row in requests if row["role"] == role]
        if not messages:
            raise RuntimeError(f"Missing role {role}")
        calls = [call["function"] for msg in messages[-1] if msg.get("role") == "assistant" for call in msg.get("tool_calls", [])]
        receipts = [str(msg.get("content", "")) for msg in messages[-1] if msg.get("role") == "tool"]
        skills = {json.loads(call["arguments"])["skill_name"] for call in calls if call["name"] == "skill_tool"}
        tools = {call["name"] for call in calls}
        if skills != {PRIVATE[role], SHARED}:
            raise RuntimeError(f"Wrong skills in actual session for {role}")
        for stage in stages:
            if not any(plan["commands"][stage] in value and "Exit Code: 0" in value for value in receipts):
                raise RuntimeError(f"Missing successful command receipt for {role} {stage}")
        if "send_message" not in tools or (role != "leader" and not any(
                f"Task #caption-{role} in_progress → completed" in receipt for receipt in receipts)):
            raise RuntimeError(f"Missing handoff or task completion for {role}")
        if role == "verifier" and any(str(runtime / "artifacts/revised.srt") in json.dumps(msg)
                                      for msg in messages[3]):
            raise RuntimeError("Verifier was sent the revised SRT before baseline calculation")
        roles[role] = {"skills": sorted(skills), "tools": sorted(tools), "stages": list(stages)}

    work = runtime / "artifacts"
    stage_times = [(work / FILES[stage]).stat().st_mtime_ns for stage in ("baseline", "verify", "deliver")]
    assert stage_times == sorted(set(stage_times))
    proposal = json.loads((work / FILES["propose"]).read_text())
    audit = json.loads((work / FILES["deliver"]).read_text())
    assert proposal["repairs"] == {"3": [2500, 3500]}
    assert (audit["result"], audit["track_status"], audit["unresolved"]) == ("matched", "review_required", 5)
    assert not (work / "deliver/reviewed.srt").exists()
    for name, expected in audit["files_sha256"].items():
        assert host.digest(work / "deliver" / name) == expected
    result.update({"role_execution": roles, "request_counts": dict(Counter(r["role"] for r in requests)),
                   "events": len(events), "baseline_preceded_verification": True,
                   "reviewed_approved_cues": audit["approved_count"], "reviewed_revised_cues": audit["revised_count"],
                   "playback_review_rows": 5, "known_timing_fixes": proposal["repairs"],
                   "output_digests": {name: host.digest(work / "deliver" / name)
                                      for name in ("review.md", "cue-review.csv", "audit.json")}})
    host.save(runtime / "execution.json", result)
    if record:
        host.save(record, result)
    print(json.dumps({"integration": "passed", "roles": roles, "events": len(events)}, ensure_ascii=False))


if __name__ == "__main__":
    host.__file__ = __file__
    host.ASSET = ASSET
    host.SLUG = ASSET.name
    host.ROLES = ("timeline-analyst", "verifier")
    host.PORTS.update({"model": 6766, "agent": 28766, "web": 29766, "gateway": 30766})
    host.ScriptedProvider = CaptionProvider
    host.make_plan = make_plan
    host.verify_execution = verify_execution
    host.main()
