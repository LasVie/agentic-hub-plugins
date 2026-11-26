"""Exercise the installed restock team with local WorkSwarm and fixed responses."""
from collections import Counter
import json
from pathlib import Path
import shlex
import sys
import time

ASSET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSET.parent / "business-interruption-rehearsal-team/tests"))
import host_integration as host

PRIVATE = {"leader": "restock-planning", "inventory-analyst": "stock-intake",
           "verifier": "restock-verification"}
SHARED = "restock-evidence"
FILES = {"intake": "intake/intake.json", "baseline": "baseline/baseline.json",
         "plan": "plan/proposal.json", "verify": "verify/verification.json",
         "deliver": "deliver/audit.json"}
STAGES = {"leader": ("plan", "deliver"), "inventory-analyst": ("intake",),
          "verifier": ("baseline", "verify")}


def make_plan(runtime, case):
    artifacts = runtime / "artifacts"
    source = artifacts / "source.json"
    with source.open("xb") as stream:
        stream.write(case.read_bytes())
    package = runtime / "data/domain/.agent_teams/agent_groups/local" / ASSET.name
    script = package / "skills/restock-evidence/scripts/restock.py"
    if not script.is_file():
        raise ValueError("Import the exact native ZIP before configuring this run")

    receipt_inputs = ["--source", str(source), "--baseline", str(artifacts / FILES["baseline"]),
                      "--proposal", str(artifacts / FILES["plan"])]
    inputs = {
        "intake": ["--source", str(source)],
        "baseline": ["--source", str(source)],
        "plan": ["--intake", str(artifacts / FILES["intake"])],
        "verify": receipt_inputs,
        "deliver": receipt_inputs + ["--verification", str(artifacts / FILES["verify"])],
    }
    prefix = [host.settings(runtime)["python"], "-B", str(script)]
    commands = {stage: shlex.join([*prefix, stage, *args, "--out", str(artifacts / stage)])
                for stage, args in inputs.items()}
    host.save(runtime / "plan.json", {"commands": commands, "source_sha256": host.digest(source)})


class RestockProvider(host.ScriptedProvider):
    def actions(self, role, plan):
        a = self.runtime / "artifacts"

        def shell(stage):
            return "bash", {"command": plan["commands"][stage], "timeout": 40, "description": "运行安装包阶段 " + stage}

        if role == "leader":
            actions = [("build_team", {"display_name": "日用品补货本地测试", "team_desc": "验证原生分派与交接。",
                                       "leader_display_name": "补货核对主理人", "leader_desc": "运行安装包",
                                       "enable_hitt": False, "call_goal": "启动原生专家团"})]
        else:
            actions = [("claim_task", {"task_id": "restock-" + role, "status": "claimed"})]
        actions.extend(("skill_tool", {"skill_name": skill, "call_goal": "读取技能"}) for skill in (PRIVATE[role], SHARED))
        if role == "leader":
            return actions + [
                ("create_task", {"tasks": [
                    {"task_id": "restock-" + member, "title": "读取原始盘点：" + member,
                     "content": f"REHEARSAL_FIXTURE_ROLE={member}\n原始盘点：{a / 'source.json'}。",
                     "assignee": member, "depends_on": []}
                    for member in host.ROLES
                ]}),
                shell("plan"),
                ("send_message", {"to": "verifier", "content": f"基线已封存，提交方案：{a / FILES['plan']}"}),
                shell("deliver"),
            ]
        if role == "verifier":
            actions.extend([shell("baseline"), ("send_message", {"to": "team-leader",
                             "content": f"原文独立基线：{a / FILES['baseline']}"})])
        stage = "verify" if role == "verifier" else "intake"
        return actions + [
            shell(stage),
            ("send_message", {"to": "team-leader", "content": f"实际阶段回执：{a / FILES[stage]}"}),
            ("claim_task", {"task_id": "restock-" + role, "status": "completed", "summary": "已交接脚本回执。"}),
        ]

    def await_handoff(self, role, blind):
        if blind or role == "inventory-analyst":
            return
        with self.lock:
            is_planning = role == "leader" and self.steps[role] == 5
        if is_planning:
            required = ("intake", "baseline")
        elif role == "leader":
            required = ("verify",)
        else:
            required = ("plan",)
        deadline = time.monotonic() + 65
        while time.monotonic() < deadline:
            with self.lock:
                if is_planning:
                    ready = "inventory-analyst" in self.done and self.steps.get("verifier", 0) >= 5
                elif role == "leader":
                    ready = set(host.ROLES) <= self.done
                else:
                    ready = self.steps.get("leader", 0) >= 6
            if ready and all((self.runtime / "artifacts" / FILES[stage]).is_file() for stage in required):
                return
            time.sleep(0.1)
        raise RuntimeError(f"No native handoff for {role}: {required}")


def verify_execution(runtime, result, events, record):
    if not any(event.get("payload", {}).get("accepted") for event in events):
        raise RuntimeError("The WorkSwarm session did not accept this run")
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    plan = json.loads((runtime / "plan.json").read_text())
    roles = {}
    for role, stages in STAGES.items():
        messages = [row["request"]["messages"] for row in requests if row["role"] == role]
        if not messages:
            raise RuntimeError(f"Missing role {role}")
        calls = [call["function"] for message in messages[-1]
                 if message.get("role") == "assistant" for call in message.get("tool_calls", [])]
        skills = {json.loads(call["arguments"])["skill_name"] for call in calls if call["name"] == "skill_tool"}
        tools = {call["name"] for call in calls}
        receipts = [str(message["content"]) for message in messages[-1] if message.get("role") == "tool"]
        if skills != {PRIVATE[role], SHARED}:
            raise RuntimeError(f"Missing private or shared skill for {role}")
        if not all(any(plan["commands"][stage] in receipt and "Exit Code: 0" in receipt for receipt in receipts)
                   for stage in stages):
            raise RuntimeError(f"Missing successful command receipt for {role}")
        if "send_message" not in tools or (role != "leader" and not any(
                f"Task #restock-{role} in_progress → completed" in receipt for receipt in receipts)):
            raise RuntimeError(f"Missing native handoff or task completion from {role}")
        roles[role] = {"skills": sorted(skills), "tools": sorted(tools), "successful_stages": list(stages)}

    a = runtime / "artifacts"
    baseline_time, plan_time, verify_time, deliver_time = [
        (a / FILES[stage]).stat().st_mtime_ns for stage in ("baseline", "plan", "verify", "deliver")
    ]
    if not baseline_time < plan_time < verify_time < deliver_time:
        raise RuntimeError("Baseline must precede proposal, verification and delivery")
    audit = json.loads((a / FILES["deliver"]).read_text())
    proposal = json.loads((a / FILES["plan"]).read_text())
    rows = [(row["status"], (row["purchase"] or {}).get("total")) for row in proposal["items"]]
    if rows != [("buy", 10000), ("buy", 2000), ("check", None), ("wait", None)]:
        raise RuntimeError(f"Unexpected stock decisions: {rows}")
    if (audit["status"], audit["issues"], audit["matched_items"]) != ("matched", [], 4):
        raise RuntimeError("Report did not bind to the full verified proposal")
    for file, digest in audit["files_sha256"].items():
        if host.digest(a / "deliver" / file) != digest:
            raise RuntimeError(f"Delivery digest mismatch for {file}")
    result.update({"role_execution": roles, "request_counts": dict(Counter(r["role"] for r in requests)),
                   "events": len(events), "baseline_preceded_proposal": True,
                   "checked_items": audit["matched_items"], "fixture_decisions": rows,
                   "output_digests": {file: host.digest(a / "deliver" / file)
                                      for file in ("shopping-list.md", "restock.csv", "audit.json")}})
    host.save(runtime / "execution.json", result)
    if record:
        host.save(record, result)
    print(json.dumps({"integration": "passed", "roles": roles, "events": len(events)}, ensure_ascii=False))


if __name__ == "__main__":
    host.__file__ = __file__
    host.ASSET = ASSET
    host.SLUG = ASSET.name
    host.ROLES = ("inventory-analyst", "verifier")
    host.PORTS.update({"model": 6756, "agent": 28756, "web": 29756, "gateway": 30756})
    host.ScriptedProvider = RestockProvider
    host.make_plan = make_plan
    host.verify_execution = verify_execution
    host.main()
