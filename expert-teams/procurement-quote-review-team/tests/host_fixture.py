"""Local-only deterministic model fixture and isolated WorkSwarm launcher.

This is test code, never included in the AgentGroup payload. Scripted model
responses exercise real host orchestration, not model reasoning quality.
No credentials or configuration are copied from another running instance.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PORTS = {"http": 6515, "web": 29515, "agent": 28515, "gateway": 30515, "model": 6516}
ROLES = ("technical", "commercial", "verifier")


def make_plan(host: Path, runtime: Path, payload: Path, case_path: Path, installed_payload: bool = False,
              scenario: str = "excluded-uncertainty") -> None:
    """Build explicit synthetic-role commands against an extracted test ZIP."""
    import importlib.util
    import shutil
    python = host / "local-only/connector-import/venv/bin/python"
    script = payload / "skills/quote-evaluation/scripts/quote_review.py"
    command_script = (runtime / "data/domain/.agent_teams/agent_groups/local/procurement-quote-review-team/skills/quote-evaluation/scripts/quote_review.py"
                      if installed_payload else script)
    inputs = runtime / "inputs"
    shutil.copytree(case_path.parent, inputs)
    case = inputs / case_path.name
    if scenario == "eligible-uncertainty":
        case_record = json.loads(case.read_text())
        b_source_id = next(offer["source_ids"][0] for offer in case_record["offers"] if offer["id"] == "B")
        b_source = inputs / next(source["path"] for source in case_record["sources"] if source["id"] == b_source_id)
        lines = b_source.read_text(encoding="utf-8").splitlines()
        lines[4] = "技术质量等级：未提供可核对的质量说明。"
        b_source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    inspected = json.loads(subprocess.check_output([str(python), "-B", str(script), "inspect", "--case", str(case)], text=True))
    # Reports are known synthetic fixtures, deliberately not LLM judgments.
    tests = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("procurement_test_cases", tests / "test_quote_review.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reports = module.synthetic_reports(json.loads(case.read_text()), inspected["case_sha256"])
    if any(report["schema_version"] != 2 for report in reports):
        raise RuntimeError("v1.0.1 host fixture requires explicit schema2 reports")
    role_notes = {
        "technical": "夹具核验记录：仅按案例所列规则核对，不验证供应商真实性。",
        "commercial": "夹具核验记录：本案例列示成本已复算一致，不保证真实采购全成本。",
        "verifier": "夹具核验记录：初稿与固定独立复算金额一致；不是供应商真实性证明。",
    }
    c_issue = {"scope": "offer", "offer_id": "C", "category": "evaluation",
               "message": "丙报价质量前提不明，保留unknown/null；其必备交期已不合格。"}
    for report in reports:
        report["notes"] = [role_notes[report["role"]]]
        if report["role"] in {"technical", "verifier"}:
            report["issues"] = [dict(c_issue)]
            if scenario == "eligible-uncertainty":
                for assessment in report["assessments"]:
                    if assessment["offer_id"] == "B" and assessment["criterion_id"] == "quality":
                        assessment.update(status="unknown", score=None, evidence=[],
                                          rationale="合成阻断夹具：合格乙报价的质量证据仍不明确，必须澄清。")
                report["issues"].append({"scope": "offer", "offer_id": "B", "category": "evaluation",
                                        "message": "合格乙报价的质量证据待澄清，不得生成当前排名。"})
    plan = {"fixture_model": True, "payload": str(payload), "command_script": str(command_script), "case": str(case),
            "case_sha256": inspected["case_sha256"], "scenario": scenario,
            "role_notes": role_notes, "c_issue": c_issue,
            "handoff_summary": "schema2说明已保留；C质量unknown/null且交期fail。" +
                               ("B质量unknown为真实评估阻断。" if scenario == "eligible-uncertainty" else "C不合格，不用其成本作合格基准。")}
    for role, report in zip(ROLES, reports):
        inspection_path = runtime / f"artifacts/{role}-inspection.json"
        report_path = runtime / f"artifacts/{role}.json"
        # No shell interpolation of document contents: every argument is quoted
        # and the report is fixed synthetic JSON from the test fixture.
        inspect_command = shlex.join([str(python), "-B", str(command_script), "inspect", "--case", str(case)])
        writer = ("import json;from pathlib import Path;"
                  f"p=Path({str(report_path)!r});"
                  f"p.write_text({json.dumps(report, ensure_ascii=False)!r},encoding='utf-8');"
                  "print('synthetic role report saved')")
        plan[role + "_command"] = inspect_command + " > " + shlex.quote(str(inspection_path)) + " && " + shlex.join([str(python), "-B", "-c", writer])
        if role == "verifier":
            independent_report = json.loads(json.dumps(report, ensure_ascii=False))
            independent_report["notes"] = ["夹具独立记录：仅依据原始来源形成，尚未读取技术或商务初稿。"]
            plan["independent_source_note"] = independent_report["notes"][0]
            independent = runtime / "artifacts/verifier-independent.json"
            independent_inspection = runtime / "artifacts/verifier-independent-inspection.json"
            independent_writer = f"from pathlib import Path;Path({str(independent)!r}).write_text({json.dumps(independent_report, ensure_ascii=False)!r},encoding='utf-8');print('fixed independent source report saved; no drafts read')"
            plan["verifier_independent_command"] = inspect_command + " > " + shlex.quote(str(independent_inspection)) + " && " + shlex.join([str(python), "-B", "-c", independent_writer])
            handoff_paths = {name: str(runtime / f"artifacts/{name}.json") for name in ("verifier-independent", "technical", "commercial")}
            review_writer = ("import json,hashlib;from pathlib import Path;"
                             f"paths={handoff_paths!r};"
                             "raw={name:Path(path).read_bytes() for name,path in paths.items()};"
                             "parsed={name:json.loads(value) for name,value in raw.items()};"
                             f"assert parsed['verifier-independent']==json.loads({json.dumps(independent_report, ensure_ascii=False)!r});"
                             f"Path({str(runtime / 'artifacts/verifier-handoff.json')!r}).write_text(json.dumps({{'files_sha256':{{name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}},'judgment_source':'fixed synthetic fixture'}},ensure_ascii=False),encoding='utf-8');" + writer)
            plan["verifier_command"] = inspect_command + " > " + shlex.quote(str(inspection_path)) + " && " + shlex.join([str(python), "-B", "-c", review_writer])
    wait = ("import time;from pathlib import Path;"
            f"p=Path({str(runtime / 'artifacts/verifier.json')!r});"
            "deadline=time.monotonic()+90\n"
            "while not p.exists() and time.monotonic()<deadline: time.sleep(.2)\n"
            "assert p.exists(),'review did not arrive'\n")
    deliver = [str(python), "-B", str(command_script), "deliver", "--case", str(case),
               "--technical", str(runtime / "artifacts/technical.json"),
               "--commercial", str(runtime / "artifacts/commercial.json"),
               "--review", str(runtime / "artifacts/verifier.json"),
               "--output-dir", str(runtime / "artifacts/delivery")]
    plan["leader_command"] = shlex.join([str(python), "-B", "-c", wait]) + " && " + shlex.join(deliver)
    (runtime / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2))


def environment(host: Path, runtime: Path, ports: dict[str, int]) -> dict[str, str]:
    """Build a fresh environment with a loopback model and no inherited keys."""
    python = host / "local-only/connector-import/venv/bin/python"
    env = {k: os.environ[k] for k in ("HOME", "USER", "LOGNAME", "SHELL") if k in os.environ}
    env.update({
        "PATH": f"{python.parent}:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "PYTHONPATH": str(host), "PYTHONDONTWRITEBYTECODE": "1", "LANG": "en_US.UTF-8",
        "JIUWENSWARM_DATA_DIR": str(runtime / "data"),
        "JIUWENSWARM_TASKS_DIR": str(runtime / "tasks"),
        "JIUWENSWARM_TASK_REGISTRY_DIR": str(runtime / "task-registry"),
        "JIUWENSWARM_IDENTITY_CACHE_DIR": str(runtime / "cache/identity"),
        "JIUWENSWARM_STARTUP_DIAGNOSTICS_DIR": str(runtime / "diagnostics"),
        "XDG_CACHE_HOME": str(runtime / "cache"), "TMPDIR": str(runtime / "tmp"),
        "AGENT_SERVER_HOST": "127.0.0.1", "AGENT_SERVER_PORT": str(ports["agent"]),
        "WEB_HOST": "127.0.0.1", "WEB_PORT": str(ports["web"]), "WEB_PATH": "/ws",
        "GATEWAY_HOST": "127.0.0.1", "GATEWAY_PORT": str(ports["gateway"]),
        "JIUWENSWARM_AGENT_PREWARM": "0", "API_BASE": f"http://127.0.0.1:{ports['model']}/v1",
        "API_KEY": "local-fixture-no-real-key", "MODEL_NAME": "procurement-local-fixture",
        "MODEL_PROVIDER": "OpenAI", "ENDPOINT_PROFILE": "openai",
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "OTEL_SDK_DISABLED": "true",
    })
    return env


def prepare(host: Path, runtime: Path, ports: dict[str, int]) -> None:
    if (runtime / "prepared.json").exists():
        raise RuntimeError("Use a new runtime directory; existing fixture state is preserved")
    for name in ("cwd", "tasks", "task-registry", "cache", "logs", "tmp", "artifacts"):
        (runtime / name).mkdir(parents=True, exist_ok=True)
    env = environment(host, runtime, ports)
    os.environ.clear()
    os.environ.update(env)
    sys.path.insert(0, str(host))
    os.chdir(runtime / "cwd")
    from jiuwenswarm.common.utils import get_user_workspace_dir, prepare_workspace
    from ruamel.yaml import YAML
    assert get_user_workspace_dir().resolve() == (runtime / "data").resolve()
    prepare_workspace(overwrite=False, preferred_language="zh", workspace_dir=runtime / "data")
    dot = runtime / "data/config/.env"
    dot.write_text("".join(k + "=" + json.dumps(v) + "\n" for k, v in env.items()
                           if k not in {"HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG"}))
    dot.chmod(0o600)
    yaml = YAML()
    config = runtime / "data/config/config.yaml"
    cfg = yaml.load(config.read_text())
    cfg["preferred_language"] = "zh"
    cfg["models"] = {"defaults": [{
        "model_id": "procurement-local-fixture", "is_default": True,
        "model_client_config": {"api_base": env["API_BASE"], "api_key": env["API_KEY"],
                                "model_name": env["MODEL_NAME"], "client_provider": "OpenAI",
                                "endpoint_profile": "openai", "supports_vision": False,
                                "timeout": 90, "stream_first_chunk_timeout": 80},
        "model_config_obj": {"temperature": 0},
    }], "agentos": [], "backups": [], "video": [], "audio": [], "vision": [], "image_gen": []}
    for name in ("setup_guide", "updater", "proactive_recommendation", "task_memory"):
        cfg.setdefault(name, {})["enabled"] = False
    cfg.setdefault("react", {})["enable_read_image_multimodal"] = False
    cfg.setdefault("health_check", {})["every"] = 86400
    cfg.setdefault("agents", {}).setdefault("agent_teammate", {})["max_iterations"] = 25
    cfg["agents"]["agent_teammate"]["completion_timeout"] = 180
    cfg["agents"].setdefault("agent_leader", {})["completion_timeout"] = 180
    with config.open("w") as stream:
        yaml.dump(cfg, stream)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=host, text=True).strip()
    (runtime / "prepared.json").write_text(json.dumps({"host_revision": revision, "ports": ports,
                                                      "model": "scripted local fixture", "credentials_copied": False}, indent=2))


class Fixture:
    def __init__(self, runtime: Path):
        self.runtime = runtime
        self.plan = json.loads((runtime / "plan.json").read_text())
        self.lock = threading.Lock()
        self.steps: dict[str, int] = {}
        self.completed_roles: set[str] = set()
        self.calls = 0

    def respond(self, request: dict) -> dict:
        tools = {x["function"]["name"]: x["function"] for x in request.get("tools", []) if "function" in x}
        # Only Leader receives create_task. Task body markers disambiguate the
        # scripted workers without changing any package persona or host prompt.
        role = "leader" if "create_task" in tools else "unknown"
        user_text = "\n".join(str(x.get("content", "")) for x in request.get("messages", []) if x.get("role") == "user")
        if role != "leader":
            for candidate in ROLES:
                if f"HOST_FIXTURE_ROLE={candidate}" in user_text:
                    role = candidate
                    break
            if role == "verifier":
                marker = user_text.rfind("HOST_FIXTURE_STAGE=")
                stage = user_text[marker:].splitlines()[0].split("=", 1)[1] if marker >= 0 else ""
                role = "verifier-independent" if stage.startswith("independent") else "verifier-review"
        with self.lock:
            self.calls += 1
            if self.calls > 80:
                raise RuntimeError("Fixture request budget exhausted")
            step = self.steps.get(role, 0)
            self.steps[role] = step + 1
            with (self.runtime / "model-requests.jsonl").open("a") as stream:
                stream.write(json.dumps({"role": role, "step": step, "request": request}, ensure_ascii=False) + "\n")
        def tool(name: str, arguments: dict) -> dict:
            if name not in tools:
                raise RuntimeError(f"Required real host tool missing: {name}; available={list(tools)}")
            return {"role": "assistant", "content": None, "tool_calls": [{"id": "call_" + uuid.uuid4().hex,
                     "type": "function", "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)}}]}
        if role == "leader":
            if step == 0:
                return tool("build_team", {"display_name": "采购比选脚本化集成测试", "team_desc": "仅核验实际宿主成员、委派与包内工具；合成测试，不证明语义质量。",
                                          "leader_display_name": "本地测试主理人", "leader_desc": "脚本化模型夹具，非采购建议", "enable_hitt": False,
                                          "call_goal": "建立真实专家团集成测试"})
            if step == 1:
                return tool("skill_tool", {"skill_name": "quote-evaluation", "call_goal": "读取真实安装的共享比选技能"})
            if step == 2:
                tasks = [{
                    "task_id": f"fixture-{member}", "title": f"本地夹具：{member}",
                    "content": f"HOST_FIXTURE_ROLE={member}\n运行真实包内工具并保留本角色结果；这是脚本化模型集成测试。",
                    "assignee": member,
                    "depends_on": [],
                } for member in ("technical", "commercial")]
                tasks.extend([{"task_id": "fixture-verifier-independent", "title": "先独立检查原文",
                               "content": "HOST_FIXTURE_ROLE=verifier\nHOST_FIXTURE_STAGE=independent\n仅检查原始来源并保存独立记录，不读取初稿。", "assignee": "verifier", "depends_on": []},
                              {"task_id": "fixture-verifier-review", "title": "再审阅实际初稿",
                               "content": "HOST_FIXTURE_ROLE=verifier\nHOST_FIXTURE_STAGE=review\n读取自己的原始记录和技术商务初稿，保存复核记录。", "assignee": "verifier",
                               "depends_on": ["fixture-verifier-independent", "fixture-technical", "fixture-commercial"]}])
                return tool("create_task", {"tasks": tasks})
            if step == 3:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    with self.lock:
                        complete = set(ROLES) <= self.completed_roles
                    if complete:
                        break
                    time.sleep(.1)
                if not complete:
                    raise RuntimeError("Real member completion responses did not arrive")
                return tool("bash", {"command": self.plan["leader_command"], "timeout": 120,
                                     "description": "等待独立复核交付并运行真实包内导出工具"})
            return {"role": "assistant", "content": "本地脚本化模型集成检查结束。真实成员任务、工具结果和交付文件请按测试报告核验；本结果不证明模型推理质量或人工测试通过。"}
        if role in ROLES or role.startswith("verifier-"):
            task_id = "fixture-" + role
            if step == 0:
                return tool("claim_task", {"task_id": task_id, "status": "claimed"})
            if step == 1:
                return tool("skill_tool", {"skill_name": "quote-evaluation", "call_goal": "读取本成员可见的真实共享技能"})
            if step == 2:
                command_key = "verifier_independent_command" if role == "verifier-independent" else "verifier_command" if role == "verifier-review" else role + "_command"
                return tool("bash", {"command": self.plan[command_key], "timeout": 60,
                                     "description": f"执行真实包内工具并写入{role}夹具评估"})
            if step == 3:
                if role in {"technical", "commercial"}:
                    deadline = time.monotonic() + 45
                    while "verifier-independent" not in self.completed_roles and time.monotonic() < deadline:
                        time.sleep(.1)
                    if "verifier-independent" not in self.completed_roles:
                        raise RuntimeError("Independent source review did not complete")
                summary = "独立原文记录已保存，尚未读取技术或商务初稿。" if role == "verifier-independent" else self.plan["handoff_summary"]
                return tool("claim_task", {"task_id": task_id, "status": "completed",
                                           "summary": f"{role}固定合成记录；脚本化模型。" + summary})
            with self.lock:
                self.completed_roles.add(role)
                if role == "verifier-review":
                    self.completed_roles.add("verifier")
            return {"role": "assistant", "content": f"{role}本地夹具任务已完成。"}
        # Diagnostics must fail visibly rather than pretending an unrecognized
        # bootstrap/warm-up request exercised a team member.
        return {"role": "assistant", "content": "本地测试夹具：未匹配成员任务，仅记录请求；未作业务判断。"}


def serve_model(runtime: Path, port: int) -> None:
    fixture = Fixture(runtime)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return
        def do_GET(self):
            body = json.dumps({"object": "list", "data": [{"id": "procurement-local-fixture", "object": "model"}]}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 4 * 1024 * 1024:
                    raise ValueError("Invalid bounded request size")
                request = json.loads(self.rfile.read(size))
                message = fixture.respond(request)
                response_id = "chatcmpl_fixture_" + uuid.uuid4().hex
                reason = "tool_calls" if message.get("tool_calls") else "stop"
                if request.get("stream"):
                    self.send_response(200); self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Connection", "close"); self.end_headers()
                    delta = {"role": "assistant"}
                    if message.get("content") is not None:
                        delta["content"] = message["content"]
                    if message.get("tool_calls"):
                        delta["tool_calls"] = [{"index": i, **x} for i, x in enumerate(message["tool_calls"])]
                    for content in [{"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                                    {"choices": [{"index": 0, "delta": {}, "finish_reason": reason}],
                                     "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}]:
                        content.update({"id": response_id, "object": "chat.completion.chunk", "created": int(time.time()),
                                        "model": "procurement-local-fixture"})
                        self.wfile.write(("data: " + json.dumps(content, ensure_ascii=False) + "\n\n").encode())
                    self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
                else:
                    content = {"id": response_id, "object": "chat.completion", "created": int(time.time()),
                               "model": "procurement-local-fixture", "choices": [{"index": 0, "message": message, "finish_reason": reason}],
                               "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
                    body = json.dumps(content, ensure_ascii=False).encode()
                    self.send_response(200); self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            except Exception as error:
                body = json.dumps({"error": {"message": str(error), "type": "local_fixture_error"}}).encode()
                self.send_response(400); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def start(host: Path, runtime: Path, ports: dict[str, int]) -> None:
    if not (runtime / "prepared.json").exists():
        raise RuntimeError("Run prepare first")
    for port in ports.values():
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
    python = host / "local-only/connector-import/venv/bin/python"
    env = environment(host, runtime, ports)
    dot = str(runtime / "data/config/.env")
    commands = {
        "model": [str(python), "-B", str(Path(__file__).resolve()), "serve-model", "--runtime", str(runtime), "--port", str(ports["model"])],
        "backend": [str(python), "-B", "-m", "jiuwenswarm.app", "--dotenv", dot],
        "web": [str(python), "-B", "-m", "jiuwenswarm.channels.web.app_web", "--dotenv", dot,
                "--host", "127.0.0.1", "--port", str(ports["http"]),
                "--dist", str(host / "local-only/connector-import/dist"),
                "--proxy-target", f"http://127.0.0.1:{ports['web']}"],
    }
    owned = {}
    try:
        for name, command in commands.items():
            with (runtime / f"logs/{name}.log").open("a") as log:
                process = subprocess.Popen(command, cwd=runtime / "cwd", env=env, stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            owned[name] = {"pid": process.pid, "command": command}
        (runtime / "pids.json").write_text(json.dumps(owned, indent=2))
    except Exception:
        for item in owned.values():
            os.killpg(item["pid"], signal.SIGTERM)
        raise


def stop(runtime: Path) -> None:
    import psutil
    path = runtime / "pids.json"
    if not path.exists():
        return
    owned = []
    for item in json.loads(path.read_text()).values():
        try:
            process = psutil.Process(item["pid"])
            if process.cmdline() != item["command"]:
                raise RuntimeError(f"Preserved unrelated/reused process ID {process.pid}")
            os.killpg(process.pid, signal.SIGTERM)
            owned.append(process)
        except psutil.NoSuchProcess:
            continue
    _, alive = psutil.wait_procs(owned, timeout=10)
    if alive:
        raise RuntimeError("Owned fixture processes are still stopping; ports must not be reused yet")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "plan", "start", "stop", "serve-model"))
    parser.add_argument("--host", type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--port", type=int, default=PORTS["model"])
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--installed-payload", action="store_true", help="Run host member commands against its real installed package after import")
    parser.add_argument("--scenario", choices=("excluded-uncertainty", "eligible-uncertainty"), default="excluded-uncertainty")
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    if args.action == "serve-model":
        serve_model(runtime, args.port)
    elif args.action == "stop":
        stop(runtime)
    elif args.action == "prepare":
        prepare(args.host.resolve(), runtime, PORTS)
    elif args.action == "plan":
        make_plan(args.host.resolve(), runtime, args.payload.resolve(), args.case.resolve(), args.installed_payload, args.scenario)
    else:
        start(args.host.resolve(), runtime, PORTS)


if __name__ == "__main__":
    main()
