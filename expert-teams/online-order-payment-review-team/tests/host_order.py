"""Exercise the installed team through the existing isolated WorkSwarm fixture."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import sys
import time


ASSET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSET.parent / "business-interruption-rehearsal-team/tests"))
import host_integration as host


PRIVATE = {
    "leader": "order-delivery", "analyst": "order-intake", "matcher": "order-matching",
    "verifier": "order-verification",
}
FILES = {
    "analyst": "intake/register.json", "matcher": "match/matches.json", "baseline": "baseline/baseline.json",
    "verifier": "verify/verification.json",
}
SHARED = "order-evidence"


def make_plan(runtime, case_path):
    a = runtime / "artifacts"
    inputs = a / "source"
    shutil.copytree(case_path, inputs)
    group = runtime / "data/domain/.agent_teams/agent_groups/local" / ASSET.name
    script = group / "skills/order-evidence/scripts/review.py"
    if not script.is_file():
        raise ValueError("Import package before creating plan")

    def command(stage, args):
        return shlex.join([host.settings(runtime)["python"], "-B", str(script), stage,
                           *args, "--out", str(a / stage)])

    source = ["--source", str(inputs), "--as-of", "2026-11-20"]
    evidence = ["--baseline", str(a / FILES["baseline"]), "--proposal", str(a / FILES["matcher"])]
    commands = {
        "analyst": command("intake", source),
        "baseline": command("baseline", source),
        "matcher": command("match", ["--register", str(a / FILES["analyst"])]),
        "verifier": command("verify", source + evidence),
        "leader": command("deliver", source + evidence + ["--verification", str(a / FILES["verifier"])]),
    }
    host.save(runtime / "plan.json", {
        "commands": commands, "inputs": {p.name: host.digest(p) for p in sorted(inputs.glob("*.csv"))}
    })


class OrderProvider(host.ScriptedProvider):
    def actions(self, role, plan):
        prefix = "order-"
        if role == "leader":
            actions = [("build_team", {"display_name": "网购核对本地夹具", "team_desc": "固定响应验证原生四角色。",
                                      "leader_display_name": "核对主理人", "leader_desc": "校验交接",
                                      "enable_hitt": False, "call_goal": "运行已安装专家团"})]
        else:
            actions = [("claim_task", {"task_id": prefix + role, "status": "claimed"})]
        actions += [("skill_tool", {"skill_name": skill, "call_goal": "读取技能"})
                    for skill in (PRIVATE[role], SHARED)]
        if role == "leader":
            actions.append(("create_task", {"tasks": [
                {"task_id": prefix + member, "title": "本地核对：" + member,
                 "content": f"REHEARSAL_FIXTURE_ROLE={member}\n按已授权原始资料执行本角色流程。",
                 "assignee": member, "depends_on": [prefix + "analyst"] if member == "matcher" else []}
                for member in host.ROLES
            ]}))
        if role == "verifier":
            actions += [
                ("bash", {"command": plan["commands"]["baseline"], "timeout": 40, "description": "仅凭原始表生成基线"}),
                ("send_message", {"to": "team-leader", "content": f"独立基线：{self.runtime / 'artifacts' / FILES['baseline']}"}),
            ]
        actions.append(("bash", {"command": plan["commands"][role], "timeout": 40, "description": "运行实际安装包命令"}))
        if role != "leader":
            report = self.runtime / "artifacts" / FILES[role]
            actions += [
                ("send_message", {"to": "team-leader", "content": f"执行回执与交接：{report}"}),
                ("claim_task", {"task_id": prefix + role, "status": "completed", "summary": "已执行本成员命令。"}),
            ]
        return actions

    def await_handoff(self, role, blind):
        needed = {
            "matcher": ("analyst", "baseline"),
            "verifier": ("matcher", "baseline"),
            "leader": tuple(FILES),
        }
        paths = [self.runtime / "artifacts" / FILES[key]
                 for key in (() if blind else needed.get(role, ()))]
        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            with self.lock:
                finished = role != "leader" or set(host.ROLES) <= self.done
            if finished and all(p.is_file() for p in paths):
                return
            time.sleep(0.1)
        raise RuntimeError(f"Missing artifact for {role}")


def verify_execution(runtime, result, events, record):
    if not any(e.get("payload", {}).get("accepted") for e in events):
        raise RuntimeError("Actual WorkSwarm did not accept session")
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    plan = json.loads((runtime / "plan.json").read_text())
    role_records = {}
    for role in PRIVATE:
        rows = [item for item in requests if item["role"] == role]
        if not rows:
            raise RuntimeError(f"No actual model transport for {role}")
        messages = rows[-1]["request"]["messages"]
        tools = [c["function"] for m in messages if m.get("role") == "assistant" for c in m.get("tool_calls", [])]
        used = {c["name"] for c in tools}
        skills = {json.loads(c["arguments"])["skill_name"] for c in tools if c["name"] == "skill_tool"}
        if not {PRIVATE[role], SHARED} <= skills:
            raise RuntimeError(f"Skill read missing for {role}")
        receipts = [str(m.get("content", "")) for m in messages if m.get("role") == "tool"]
        commands = {json.loads(c["arguments"])["command"] for c in tools if c["name"] == "bash"}
        expected = {plan["commands"][role]}
        if role == "verifier":
            expected.add(plan["commands"]["baseline"])
        successes = sum("已生成" in r for r in receipts)
        if commands != expected or successes < len(expected):
            raise RuntimeError(f"Missing successful installed-package command for {role}")
        if role != "leader":
            if "send_message" not in used or not any(f"Task #order-{role} in_progress → completed" in r for r in receipts):
                raise RuntimeError(f"Missing actual handoff or task status for {role}")
        role_records[role] = {"calls": len(rows), "tools": sorted(used), "skills": sorted(skills),
                              "successful_stage_receipts": successes}

    a = runtime / "artifacts"
    if (a / FILES["baseline"]).stat().st_mtime_ns >= (a / FILES["matcher"]).stat().st_mtime_ns:
        raise RuntimeError("Baseline did not precede proposal")
    output = a / "deliver"
    audit = json.loads((output / "audit.json").read_text())
    if audit["输入摘要"] != plan["inputs"] or audit["独立核验"]["结论"] != "独立核验一致":
        raise RuntimeError("Delivery fingerprint or independent decision mismatch")
    for name, digest in audit["输出摘要"].items():
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Output fingerprint differs")
    if (audit["流水去向"]["P005"] != ["扣款候选歧义", "", "", ["A101", "A102"]]
            or audit["流水去向"]["P006"][1] != "A103"
            or audit["待跟进计数"].get("退款部分入账") != 1):
        raise RuntimeError("Chinese sample conclusions differ")
    result.update({"role_execution": role_records, "events": len(events),
                   "model_request_counts": dict(Counter(r["role"] for r in requests)),
                   "source_only_baseline_preceded_match": True, "sample_verified": True,
                   "outputs": audit["输出摘要"]})
    host.save(runtime / "execution.json", result)
    if record:
        host.save(record, result)
    print(json.dumps({"integration": "passed", "roles": role_records, "events": len(events)}, ensure_ascii=False))


if __name__ == "__main__":
    # Reuse transport, setup and cleanup without changing the host or other teams.
    host.__file__ = __file__
    host.ASSET = ASSET
    host.SLUG = ASSET.name
    host.ROLES = tuple(name for name in PRIVATE if name != "leader")
    host.PORTS.update({"model": 6736, "agent": 28736, "web": 29736, "gateway": 30736})
    host.ScriptedProvider = OrderProvider
    host.make_plan = make_plan
    host.verify_execution = verify_execution
    host.main()
