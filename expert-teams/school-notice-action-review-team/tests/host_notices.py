"""Exercise installed native tasks, Skills, handoffs and commands on loopback."""

from collections import Counter
import json
from pathlib import Path
import shlex
import shutil
import sys
import time

ASSET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ASSET.parent / "business-interruption-rehearsal-team/tests"))
import host_integration as host

PRIVATE = {"leader":"notice-delivery", "notice-analyst":"notice-analysis", "verifier":"notice-verification"}
SHARED = "notice-evidence"
FILES = {"draft": "draft/draft.json", "baseline": "baseline/baseline.json",
         "verify": "verify/verification.json", "deliver": "deliver/audit.json"}


def make_plan(runtime, fixture):
    a = runtime / "artifacts"
    source = a / "source.json"
    shutil.copyfile(fixture, source)
    extracted = ASSET / "tests/fixtures/weekly-extraction.json"
    for role in ("notice-analyst", "verifier"):
        shutil.copyfile(extracted, a / f"{role}-fixture.json")
    native = runtime / "data/domain/.agent_teams/agent_groups/local" / ASSET.name
    script = native / "skills/notice-evidence/scripts/review.py"
    if not script.is_file():
        raise ValueError("Import the exact group before making an integration plan")

    def command(stage, args):
        return shlex.join([host.settings(runtime)["python"], "-B", str(script), stage,
                           "--source", str(source), *args, "--out", str(a/stage)])

    receipts = ["--draft", str(a/FILES["draft"]), "--baseline", str(a/FILES["baseline"])]
    commands = {
        "baseline": command("baseline", ["--extraction", str(a/"verifier-fixture.json")]),
        "notice-analyst": command("draft", ["--extraction", str(a/"notice-analyst-fixture.json")]),
        "verifier": command("verify", receipts),
        "leader": command("deliver", receipts + ["--receipt", str(a/FILES["verify"])]),
    }
    host.save(runtime/"plan.json", {"commands":commands, "source_sha256":host.digest(source)})


class NoticeProvider(host.ScriptedProvider):
    def actions(self, role, plan):
        a = self.runtime / "artifacts"
        actions = []
        if role == "leader":
            actions.append(("build_team", {"display_name":"家校核对本地夹具","team_desc":"固定响应运行三角色。",
                                          "leader_display_name":"核对主理人","leader_desc":"校验实际交接",
                                          "enable_hitt":False,"call_goal":"启动安装包"}))
        else:
            actions.append(("claim_task", {"task_id":f"notice-{role}", "status":"claimed"}))
        actions.extend(("skill_tool", {"skill_name":skill, "call_goal":"读取技能"}) for skill in (PRIVATE[role], SHARED))
        if role == "leader":
            actions.append(("create_task", {"tasks":[
                {"task_id":f"notice-{member}", "title":"固定夹具：" + member,
                 "content":f"REHEARSAL_FIXTURE_ROLE={member}\n仅提供原始通知和范围：{a/'source.json'}。",
                 "assignee":member, "depends_on":[]}
                for member in host.ROLES
            ]}))
        if role == "verifier":
            actions.append(("bash", {"command":plan["commands"]["baseline"], "timeout":40,
                                     "description":"仅凭原始通知和核验员摘录封存基线"}))
            actions.append(("send_message", {"to":"team-leader","content":f"仅根据原文建立的基线：{a/FILES['baseline']}"}))
        actions.append(("bash", {"command":plan["commands"][role], "timeout":40, "description":"运行实际安装脚本"}))
        if role != "leader":
            key = "draft" if role == "notice-analyst" else "verify"
            actions.extend([
                ("send_message", {"to":"team-leader","content":f"实际产物交接：{a/FILES[key]}"}),
                ("claim_task", {"task_id":f"notice-{role}","status":"completed","summary":"已运行阶段并交接实际回执。"}),
            ])
        return actions

    def await_handoff(self, role, blind):
        waits = {"notice-analyst": ("baseline",), "verifier": ("draft",), "leader": ("draft", "baseline", "verify")}
        required = [self.runtime/"artifacts"/FILES[k] for k in (() if blind else waits[role])]
        deadline = time.monotonic() + 70
        while time.monotonic() < deadline:
            with self.lock:
                done = role != "leader" or set(host.ROLES) <= self.done
            if done and all(f.is_file() for f in required):
                return
            time.sleep(0.1)
        raise RuntimeError(f"Missing real handoff for {role}")


def verify_execution(runtime, result, events, record):
    if not any(e.get("payload", {}).get("accepted") for e in events):
        raise RuntimeError("No accepted actual WorkSwarm session")
    req = [json.loads(line) for line in (runtime/"requests.jsonl").read_text().splitlines()]
    plan = json.loads((runtime/"plan.json").read_text())
    roles = {}
    for role in PRIVATE:
        requests = [r for r in req if r["role"] == role]
        if not requests:
            raise RuntimeError(f"Missing runtime role {role}")
        messages = requests[-1]["request"]["messages"]
        calls = [c["function"] for m in messages if m.get("role") == "assistant" for c in m.get("tool_calls", [])]
        skills = {json.loads(c["arguments"])["skill_name"] for c in calls if c["name"] == "skill_tool"}
        receipts = [str(m.get("content", "")) for m in messages if m.get("role") == "tool"]
        commands = [json.loads(c["arguments"])["command"] for c in calls if c["name"] == "bash"]
        want = [plan["commands"]["baseline"]] if role == "verifier" else []
        want.append(plan["commands"][role])
        if skills != {PRIVATE[role], SHARED} or commands != want or sum("已生成" in r for r in receipts) < len(want):
            raise RuntimeError(f"Expected installed skills and successful commands for {role}")
        tools = {c["name"] for c in calls}
        if role != "leader" and ("send_message" not in tools or not any(
                f"Task #notice-{role} in_progress → completed" in r for r in receipts)):
            raise RuntimeError(f"Native completion or handoff missing for {role}")
        roles[role] = {"skills":sorted(skills),"tools":sorted(tools),"successful_stage_receipts":len(want)}

    a = runtime/"artifacts"
    times = [(a/FILES[k]).stat().st_mtime_ns for k in ("baseline","draft","verify","deliver")]
    if times != sorted(set(times)):
        raise RuntimeError("Actual stage outputs are out of order")
    audit = json.loads((a/FILES["deliver"]).read_text())
    if audit != json.loads((a/FILES["verify"]).read_text()):
        raise RuntimeError("Delivery audit differs from real reviewed result")
    pick = {(item["child"], item["time"]) for item in audit["actions"] if item["time"]}
    if pick != {("A","17:00"),("B","16:30")} or len(audit["actions"]) != 4:
        raise RuntimeError("Wrong class or time in final checklist")
    if {r["op"] for r in audit["changes"]} != {"取消","更正"} or {r["ref"] for r in audit["pending"]} != {"N6:1:1"}:
        raise RuntimeError("Missing canceled item or unresolved relative date")
    result.update({"role_execution":roles,"request_counts":dict(Counter(r["role"] for r in req)),
                   "events":len(events),"baseline_preceded_draft":True,"verified_sample_actions":len(audit["actions"]),
                   "output_digests":{n:host.digest(a/"deliver"/n) for n in ("checklist.md","changes.csv","audit.json")}})
    host.save(runtime/"execution.json", result)
    if record:
        host.save(record,result)
    print(json.dumps({"integration":"passed","roles":roles,"events":len(events),"actions":len(audit["actions"])},ensure_ascii=False))


if __name__ == "__main__":
    # The external model transport is a fixed local fixture; the real installed
    # team, processes and tools run in a fresh asset-owned WorkSwarm directory.
    host.__file__ = __file__
    host.ASSET = ASSET
    host.SLUG = ASSET.name
    host.ROLES = ("notice-analyst", "verifier")
    host.PORTS.update({"model":6746,"agent":28746,"web":29746,"gateway":30746})
    host.ScriptedProvider = NoticeProvider
    host.make_plan = make_plan
    host.verify_execution = verify_execution
    host.main()
