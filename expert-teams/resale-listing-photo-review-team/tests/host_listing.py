"""Verify installed AgentGroup tasks and native image input using a loopback model."""
from base64 import b64decode
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shlex
import shutil
import sys
import time

TEAM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM.parent / "business-interruption-rehearsal-team/tests"))
import host_integration as host


MEMBERS = ("evidence", "verifier")
SKILL = "listing-photo-review"
REPORTS = {"evidence": "evidence/review.json", "verifier": "verifier/review.json"}
BASELINE = "batch/batch.json"
original_setup = host.setup


def setup(runtime):
    original_setup(runtime)
    from ruamel.yaml import YAML

    config = runtime / "data/infra/config/config.yaml"
    yaml = YAML()
    settings = yaml.load(config.read_text())
    settings["models"]["defaults"][0]["model_client_config"]["supports_vision"] = True
    with config.open("w", encoding="utf-8") as stream:
        yaml.dump(settings, stream)


def make_plan(runtime, case):
    fixtures = TEAM / "tests/fixtures"
    artifacts = runtime / "artifacts"
    source = artifacts / "products.json"
    with source.open("xb") as out:
        out.write(case.read_bytes())
    photos = artifacts / "photos"
    shutil.copytree(fixtures / "photos", photos)
    answers = {"evidence": "evidence-answer.json", "verifier": "verify-answer.json"}
    for name in answers.values():
        with (artifacts / name).open("xb") as out:
            out.write((fixtures / name).read_bytes())
    installed = runtime / "data/domain/.agent_teams/agent_groups/local" / TEAM.name
    script = installed / f"skills/{SKILL}/scripts/review.py"
    if not script.is_file():
        raise ValueError("Import the exact native ZIP first")

    def command(stage, folder, *args):
        return shlex.join([host.settings(runtime)["python"], "-B", str(script), stage,
                           "--source", str(source), "--photos", str(photos),
                           "--out", str(artifacts / folder), *args])

    batch = ["--batch", str(artifacts / BASELINE)]
    commands = {"baseline": command("prepare", "batch")}
    for role, name in answers.items():
        commands[role] = command("seal", role, *batch, "--role", role, "--answer", str(artifacts / name))
    commands["deliver"] = command("deliver", "delivery", *batch,
                                  "--evidence", str(artifacts / REPORTS["evidence"]),
                                  "--verify", str(artifacts / REPORTS["verifier"]))
    files = [str(photos / name) for item in json.loads(source.read_bytes())["items"] for name in item["photos"]]
    host.save(runtime / "plan.json", {"commands": commands, "photos": files, "source_sha256": host.digest(source)})


class ListingProvider(host.ScriptedProvider):
    def answer(self, request):
        # Let both members finish before asking the leader to inspect their tasks.
        keys = {entry["function"]["name"] for entry in request.get("tools", []) if entry.get("type") == "function"}
        with self.lock:
            leader_stage = self.steps.get("leader", 0)
        if "create_task" in keys and leader_stage == 4:
            self.wait_for_members()
        return super().answer(request)

    def actions(self, role, plan):
        a = self.runtime / "artifacts"
        task = "listing-" + role

        def command(key):
            return "bash", {"command": plan["commands"][key], "description": "运行已安装的照片复核阶段", "timeout": 35}

        def load_skill():
            return "skill_tool", {"skill_name": SKILL, "call_goal": "从真实安装包读取复核流程"}

        if role == "leader":
            return [
                ("build_team", {"display_name": "二手商品照片本机测试",
                                "team_desc": "从原图独立复核并核对回执。",
                                "leader_display_name": "上架复核主理人", "leader_desc": "冻结并交付",
                                "enable_hitt": False, "call_goal": "启动原生专家团"}),
                load_skill(), command("baseline"),
                ("create_task", {"tasks": [
                    {"task_id": "listing-" + member, "title": "独立读取原始照片：" + member,
                     "content": f"REHEARSAL_FIXTURE_ROLE={member}\n请独立查看合成原图，读取批次 {a / BASELINE} 后封存意见。",
                     "assignee": member, "depends_on": []}
                    for member in MEMBERS
                ]}),
                *[("view_task", {"action": "get", "task_id": "listing-" + member}) for member in MEMBERS],
                command("deliver"),
            ]
        return [
            ("claim_task", {"task_id": task, "status": "claimed"}), load_skill(),
            *[("read_file", {"file_path": path}) for path in plan["photos"]],
            command(role),
            ("send_message", {"to": "team-leader", "content": f"本轮封存意见：{a / REPORTS[role]}"}),
            ("claim_task", {"task_id": task, "status": "completed", "summary": "独立读取照片并封存固定测试意见。"}),
        ]

    def await_handoff(self, role, baseline):
        if role == "leader" and not baseline:
            self.wait_for_members()

    def wait_for_members(self):
        deadline = time.monotonic() + 55
        while time.monotonic() < deadline:
            with self.lock:
                finished = set(MEMBERS) <= self.done
            if finished and all((self.runtime / "artifacts" / p).is_file() for p in REPORTS.values()):
                return
            time.sleep(0.15)
        raise RuntimeError("Missing real completed member handoff")


def image_digests(request):
    result = set()
    for message in request["messages"]:
        if not isinstance(message.get("content"), list):
            continue
        for part in message["content"]:
            if part.get("type") == "image_url":
                url = part["image_url"]["url"]
                if url.startswith("data:image/") and ";base64," in url:
                    result.add(sha256(b64decode(url.split(",", 1)[1], validate=True)).hexdigest())
    return result


def expected_photo_encodings(path):
    from PIL import Image

    original = Path(path).read_bytes()
    variants = {sha256(original).hexdigest()}
    with Image.open(BytesIO(original)) as image:
        thumbnail = image.copy()
        thumbnail.thumbnail((1536, 1536))
        stream = BytesIO()
        thumbnail.save(stream, format=image.format)
        variants.add(sha256(stream.getvalue()).hexdigest())
    return variants


def verify_execution(runtime, result, events, record):
    if not any(event.get("payload", {}).get("accepted") for event in events):
        raise RuntimeError("WorkSwarm did not accept the test session")
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    plan = json.loads((runtime / "plan.json").read_bytes())
    expected = [expected_photo_encodings(path) for path in plan["photos"]]
    roles = {}
    for role in ("leader", *MEMBERS):
        matching = [row["request"] for row in requests if row["role"] == role]
        if not matching:
            raise RuntimeError(f"Missing role: {role}")
        messages = matching[-1]["messages"]
        calls = [call["function"] for msg in messages if msg["role"] == "assistant" for call in msg.get("tool_calls", [])]
        receipts = [str(msg["content"]) for msg in messages if msg["role"] == "tool"]
        names = {call["name"] for call in calls}
        if not any(call["name"] == "skill_tool" and SKILL in call["arguments"] for call in calls):
            raise RuntimeError(f"Installed skill missing for {role}")
        stages = ("baseline", "deliver") if role == "leader" else (role,)
        for stage in stages:
            if not any("Exit Code: 0" in receipt and plan["commands"][stage] in receipt for receipt in receipts):
                raise RuntimeError(f"Missing actual CLI receipt: {stage}")
        matched_photos = 0
        if role in MEMBERS:
            supplied = {json.loads(call["arguments"])["file_path"] for call in calls if call["name"] == "read_file"}
            sibling = next(member for member in MEMBERS if member != role)
            before_seal = []
            for request in matching:
                if any(call["function"]["name"] == "bash" for msg in request["messages"]
                       for call in msg.get("tool_calls", [])):
                    break
                before_seal.append(request)
            sibling_path = runtime / "artifacts" / REPORTS[sibling]
            other_note = {
                "evidence": "右侧中央可见浅色斜划痕。",
                "verifier": "右侧近照有两条浅色线条。",
            }[sibling]
            if any(str(sibling_path) in str(r["messages"]) or other_note in str(r["messages"])
                   for r in before_seal):
                raise RuntimeError(f"Sibling opinion entered {role}'s pre-seal context")
            sent = set().union(*(image_digests(request) for request in before_seal))
            matched_photos = sum(bool(encodings & sent) for encodings in expected)
            if supplied != set(plan["photos"]) or matched_photos != len(expected):
                raise RuntimeError(f"Actual {role} model requests lack matching images: {matched_photos}/{len(expected)}")
            if not any(f"Task #listing-{role} in_progress → completed" in r for r in receipts) or "send_message" not in names:
                raise RuntimeError(f"Missing real task completion: {role}")
        else:
            for member in MEMBERS:
                if not any(f"Task #listing-{member}:" in receipt and "Status: completed" in receipt
                           for receipt in receipts):
                    raise RuntimeError(f"Leader did not verify completed task for {member}")
        roles[role] = {"tools": sorted(names), "matched_original_photos_before_seal": matched_photos,
                       "successful_stages": stages}
    a = runtime / "artifacts"
    if host.digest(a / "products.json") != plan["source_sha256"]:
        raise RuntimeError("Input notes changed")
    if [host.digest(Path(path)) for path in plan["photos"]] != [
        host.digest(TEAM / "tests/fixtures/photos" / Path(path).relative_to(a / "photos")) for path in plan["photos"]
    ]:
        raise RuntimeError("Input photos changed")
    report = json.loads((a / "delivery/report.json").read_bytes())
    expected_order = ["camera/front.jpg", "camera/right-scratch.png", "camera/charger.png"]
    if report["items"][0]["order"] != expected_order or report["items"][1]["status"] != "hold":
        raise RuntimeError("Unexpected order or hold")
    if report["items"][1]["issues"][0]["status"] != "retake":
        raise RuntimeError("Missing actionable retake")
    result.update({"role_execution": roles, "request_counts": dict(Counter(row["role"] for row in requests)),
                   "model_scope": "Fixed loopback decisions with real image content and tool calls",
                   "original_photos": len(expected), "ready": ["C01"], "held": ["D02"],
                   "order": expected_order, "outputs": {name: host.digest(a / "delivery" / name)
                                                        for name in ("report.json", "checklist.html")}})
    host.save(runtime / "execution.json", result)
    if record:
        host.save(record, result)
    print(json.dumps({"passed": True, "roles": roles, "photos": len(expected)}, ensure_ascii=False))


if __name__ == "__main__":
    host.__file__ = __file__
    host.ASSET = TEAM
    host.SLUG = TEAM.name
    host.ROLES = MEMBERS
    host.PORTS.update({"model": 6768, "agent": 28768, "web": 29768, "gateway": 30768})
    host.ScriptedProvider = ListingProvider
    host.setup = setup
    host.make_plan = make_plan
    host.verify_execution = verify_execution
    host.main()
