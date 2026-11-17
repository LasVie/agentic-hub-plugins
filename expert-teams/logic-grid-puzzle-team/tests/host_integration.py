"""Owned WorkSwarm instance and explicit scripted-model integration checks.

The loopback provider is a protocol fixture. It never evaluates puzzle prose or
claims independent LLM reasoning. All persistent state is below this asset.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
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
import urllib.request
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ASSET = Path(__file__).resolve().parents[1]
SLUG = "logic-grid-puzzle-team"
ROLES = ("author", "modeler", "reviewer")
PORTS = {"http": 6535, "model": 6536, "agent": 28535, "web": 29535, "gateway": 30535}
BOUNDARY = "Real host integration with fixed local responses; not autonomous reasoning or manual acceptance."


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owned(path: Path) -> Path:
    result = path.expanduser().resolve()
    if not result.is_relative_to(ASSET / ".local"):
        raise ValueError("Runtime must be inside this asset's .local directory")
    return result


def settings(runtime: Path) -> dict:
    return json.loads((runtime / "owner.json").read_text(encoding="utf-8"))


def environment(runtime: Path, host: Path, python: Path) -> dict[str, str]:
    # Copy only identity variables; never carry provider keys/proxies into tests.
    env = {key: os.environ[key] for key in ("HOME", "USER", "LOGNAME", "SHELL") if key in os.environ}
    env.update({
        "PATH": f"{python.parent}:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "PYTHONPATH": str(host), "PYTHONDONTWRITEBYTECODE": "1", "LANG": "en_US.UTF-8",
        "JIUWENSWARM_DATA_DIR": str(runtime / "data"),
        "JIUWENSWARM_TASKS_DIR": str(runtime / "tasks"),
        "JIUWENSWARM_TASK_REGISTRY_DIR": str(runtime / "registry"),
        "JIUWENSWARM_IDENTITY_CACHE_DIR": str(runtime / "cache/identity"),
        "JIUWENSWARM_STARTUP_DIAGNOSTICS_DIR": str(runtime / "diagnostics"),
        "XDG_CACHE_HOME": str(runtime / "cache"), "TMPDIR": str(runtime / "tmp"),
        "AGENT_SERVER_HOST": "127.0.0.1", "AGENT_SERVER_PORT": str(PORTS["agent"]),
        "WEB_HOST": "127.0.0.1", "WEB_PORT": str(PORTS["web"]), "WEB_PATH": "/ws",
        "GATEWAY_HOST": "127.0.0.1", "GATEWAY_PORT": str(PORTS["gateway"]),
        "JIUWENSWARM_AGENT_PREWARM": "0", "MODEL_PROVIDER": "OpenAI", "ENDPOINT_PROFILE": "openai",
        "API_BASE": f"http://127.0.0.1:{PORTS['model']}/v1", "API_KEY": "fixture-no-credential",
        "MODEL_NAME": "logic-grid-scripted-fixture", "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1", "OTEL_SDK_DISABLED": "true",
    })
    return env


def prepare(args) -> None:
    runtime = owned(args.runtime)
    if runtime.exists():
        raise ValueError("Use a new runtime path; existing evidence is preserved")
    host, python = args.host.resolve(), args.python.expanduser().absolute()
    if not (host / "jiuwenswarm/app.py").is_file() or not python.is_file():
        raise ValueError("Need actual host source and its Python interpreter")
    runtime.mkdir(parents=True)
    for name in ("cwd", "logs", "tmp", "cache", "tasks", "registry", "diagnostics", "artifacts"):
        (runtime / name).mkdir()
    save(runtime / "owner.json", {"asset": SLUG, "host": str(host), "python": str(python),
                                  "ports": PORTS, "boundary": BOUNDARY, "created": time.time()})
    command = [str(python), "-B", str(Path(__file__).resolve()), "_setup", "--runtime", str(runtime)]
    subprocess.run(command, env=environment(runtime, host, python), cwd=runtime / "cwd", check=True)


def setup(runtime: Path) -> None:
    config = settings(runtime)
    host, python = Path(config["host"]), Path(config["python"])
    env = environment(runtime, host, python)
    os.environ.clear()
    os.environ.update(env)
    sys.path.insert(0, str(host))
    from jiuwenswarm.common.utils import get_user_workspace_dir, prepare_workspace
    from ruamel.yaml import YAML
    if get_user_workspace_dir().resolve() != (runtime / "data").resolve():
        raise RuntimeError("Host data path escaped isolation")
    prepare_workspace(overwrite=False, preferred_language="zh", workspace_dir=runtime / "data", migrate_config=False)
    yaml = YAML()
    location = runtime / "data/infra/config/config.yaml"
    cfg = yaml.load(location.read_text(encoding="utf-8"))
    cfg["preferred_language"] = "zh"
    cfg["models"] = {"defaults": [{
        "model_id": "logic-grid-scripted-fixture", "is_default": True,
        "model_client_config": {"api_base": env["API_BASE"], "api_key": env["API_KEY"],
                                "model_name": env["MODEL_NAME"], "client_provider": "OpenAI",
                                "endpoint_profile": "openai", "supports_vision": False,
                                "timeout": 100, "stream_first_chunk_timeout": 90},
        "model_config_obj": {"temperature": 0},
    }], "agentos": [], "backups": [], "video": [], "audio": [], "vision": [], "image_gen": []}
    for key in ("setup_guide", "updater", "proactive_recommendation", "task_memory"):
        cfg.setdefault(key, {})["enabled"] = False
    with location.open("w", encoding="utf-8") as stream:
        yaml.dump(cfg, stream)
    dot = runtime / "data/infra/config/.env"
    excluded = {"HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG"}
    dot.write_text("".join(f"{key}={json.dumps(value)}\n" for key, value in env.items() if key not in excluded), encoding="utf-8")
    dot.chmod(0o600)
    save(runtime / "prepared.json", {"data": str(runtime / "data"), "credentials_copied": False,
                                     "migrate_config": False, "model": "loopback scripted fixture"})


def ports_free() -> None:
    holders = []
    try:
        for port in PORTS.values():
            holder = socket.socket()
            holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            holder.bind(("127.0.0.1", port))
            holders.append(holder)
    finally:
        for holder in holders:
            holder.close()


def start(runtime: Path) -> None:
    cfg = settings(runtime)
    if (runtime / "pids.json").exists():
        raise ValueError("This instance already has process records; inspect it first")
    ports_free()
    host, python = Path(cfg["host"]), Path(cfg["python"])
    dot = str(runtime / "data/infra/config/.env")
    dist = host / "local-only/connector-import/dist"
    if not (dist / "index.html").is_file():
        dist = host / "jiuwenswarm/channels/web/frontend/dist"
    if not (dist / "index.html").is_file():
        raise ValueError("No existing frontend distribution; do not rebuild the host")
    commands = {
        "fixture": [str(python), "-B", str(Path(__file__).resolve()), "_model", "--runtime", str(runtime)],
        "backend": [str(python), "-B", "-m", "jiuwenswarm.app", "--dotenv", dot],
        "web": [str(python), "-B", "-m", "jiuwenswarm.channels.web.app_web", "--dotenv", dot,
                "--host", "127.0.0.1", "--port", str(PORTS["http"]), "--dist", str(dist),
                "--proxy-target", f"http://127.0.0.1:{PORTS['web']}"],
    }
    processes = {}
    for name, command in commands.items():
        with (runtime / "logs" / f"{name}.log").open("a", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=runtime / "cwd", env=environment(runtime, host, python),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        processes[name] = {"pid": process.pid, "command": command}
        save(runtime / "pids.json", processes)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            for port in (PORTS["model"], PORTS["http"], PORTS["agent"], PORTS["web"]):
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    pass
            break
        except OSError:
            time.sleep(0.2)
    else:
        raise RuntimeError("Owned host not ready within 30 seconds; logs preserved")
    print(json.dumps({"url": f"http://127.0.0.1:{PORTS['http']}/", "runtime": str(runtime), "boundary": BOUNDARY}))


def validate(runtime: Path, payload: Path) -> None:
    cfg = settings(runtime)
    host, python = Path(cfg["host"]), Path(cfg["python"])
    creator = host / "jiuwenswarm/resources/agent/workspace/skills/agent-group-creator/scripts/register_group.py"
    command = [str(python), "-B", str(creator), str(payload.resolve()), "--validate-only"]
    result = subprocess.run(command, cwd=runtime / "cwd", env=environment(runtime, host, python),
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (runtime / "logs/creator.log").write_text(result.stdout, encoding="utf-8")
    save(runtime / "creator.json", {"command": command, "exit": result.returncode, "pass": "RESULT: PASS" in result.stdout})
    print(result.stdout)
    if result.returncode or "RESULT: PASS" not in result.stdout:
        raise RuntimeError("Actual creator validation failed")


async def rpc(runtime: Path, method: str, params: dict, timeout: float = 30) -> dict:
    import websockets
    url = f"http://127.0.0.1:{PORTS['http']}"
    async with websockets.connect(url.replace("http", "ws") + "/ws", origin=url, max_size=16 * 1024 * 1024) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        identifier = "logic-" + uuid.uuid4().hex
        await ws.send(json.dumps({"type": "req", "id": identifier, "method": method, "params": params}))
        while True:
            reply = json.loads(await asyncio.wait_for(ws.recv(), timeout))
            if reply.get("id") == identifier:
                if reply.get("error") or reply.get("ok") is False:
                    raise RuntimeError(str(reply))
                return reply


def zip_payload(native: Path) -> dict[str, str]:
    with zipfile.ZipFile(native) as package:
        return {item.filename: hashlib.sha256(package.read(item)).hexdigest()
                for item in package.infolist() if not item.is_dir()}


async def check(runtime: Path, native: Path, record: Path | None, reuse: bool) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTS['http']}/", timeout=10) as response:
        http = response.status
    if reuse:
        imported = {"payload": {"id": SLUG}, "reuse": True}
    else:
        imported = await rpc(runtime, "agent_groups.import_local", {"path": str(native.resolve())})
    if imported.get("payload", {}).get("id") != SLUG:
        raise RuntimeError("Wrong imported type or identity")
    await rpc(runtime, "agent_groups.install", {"id": SLUG})
    show = await rpc(runtime, "agent_groups.show", {"id": SLUG})
    group = show["payload"]["group"]
    if {item["id"] for item in group["members"]} != {"leader", *ROLES} or group["leaderId"] != "leader":
        raise RuntimeError("Wrong AgentGroup roster")
    installed = runtime / "data/domain/.agent_teams/agent_groups/local" / SLUG
    expected = zip_payload(native)
    actual = {path.relative_to(installed).as_posix(): digest(path) for path in installed.rglob("*") if path.is_file()}
    if actual != expected:
        raise RuntimeError("Installed files differ from exact native ZIP")
    await rpc(runtime, "agent_groups.list", {"filter": "mine"})
    result = {"frontend_http": http, "native_sha256": digest(native), "payload": expected,
              "group": SLUG, "member_ids": ["leader", *ROLES], "version": group.get("version"),
              "installed_equal": True, "model_calls": "none for management", "boundary": BOUNDARY}
    save(runtime / "import.json", result)
    if record:
        save(record, result)
    return result


def make_plan(runtime: Path, model: Path, expected: str) -> None:
    if (runtime / "plan.json").exists():
        raise ValueError("Preserve previous plan; use a fresh instance")
    cfg = settings(runtime)
    python = cfg["python"]
    group = runtime / "data/domain/.agent_teams/agent_groups/local" / SLUG
    if not group.is_dir():
        raise ValueError("Import exact ZIP before planning")
    # The author fixture copies synthetic input; this is expressly not generation.
    fixed = runtime / "artifacts/fixed-model.json"
    fixed.write_bytes(model.read_bytes())
    authored = runtime / "artifacts/authored.json"
    copier = "from pathlib import Path; import sys; Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes())"
    commands = {"author": shlex.join([python, "-B", "-c", copier, str(fixed), str(authored)])}
    commands["modeler"] = shlex.join([python, "-B", str(group / "agents/modeler/tools/model.py"),
                                      "--input", str(authored), "--output", str(runtime / "artifacts/model")])
    commands["reviewer"] = shlex.join([python, "-B", str(group / "agents/reviewer/tools/review.py"),
                                       "--input", str(runtime / "artifacts/model/learner.json"),
                                       "--output", str(runtime / "artifacts/review")])
    commands["leader"] = shlex.join([python, "-B", str(group / "agents/leader/tools/deliver.py"),
                                     "--model", str(authored), "--review", str(runtime / "artifacts/review/review.json"),
                                     "--output", str(runtime / "artifacts/delivery")])
    skills = {}
    for role in ("leader", *ROLES):
        paths = sorted((group / "agents" / role / "skills").glob("*/SKILL.md"))
        paths += sorted((group / "skills").glob("*/SKILL.md"))
        skills[role] = [path.parent.name for path in paths]
    save(runtime / "plan.json", {"commands": commands, "skills": skills, "expected": expected, "fixed_model_sha256": digest(fixed),
                                 "boundary": BOUNDARY})


class ScriptedProvider:
    def __init__(self, runtime: Path):
        self.runtime = runtime
        self.lock = threading.Lock()
        self.steps: dict[str, int] = {}
        self.done: set[str] = set()
        self.total = 0

    def answer(self, request: dict) -> dict:
        available = {item["function"]["name"] for item in request.get("tools", []) if item.get("type") == "function"}
        user = "\n".join(str(item.get("content", "")) for item in request.get("messages", []) if item.get("role") == "user")
        role = "leader" if "create_task" in available else next((name for name in ROLES if f"GRID_FIXTURE_ROLE={name}" in user), "other")
        with self.lock:
            self.total += 1
            if self.total > 90:
                raise RuntimeError("Local fixture exhausted its 90-request bound")
            index = self.steps.get(role, 0)
            self.steps[role] = index + 1
            with (self.runtime / "requests.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"role": role, "index": index, "request": request}, ensure_ascii=False) + "\n")
        planfile = self.runtime / "plan.json"
        if not planfile.exists() or role == "other":
            return {"role": "assistant", "content": "这是本地脚本夹具，尚未配置推理计划。请勿把此回复当作逻辑题生成或人工验收。"}
        plan = json.loads(planfile.read_text(encoding="utf-8"))
        actions = []
        if role == "leader":
            actions.append(("build_team", {"display_name": "逻辑题本地集成夹具", "team_desc": "验证真实调度；所有模型回复是固定脚本。",
                            "leader_display_name": "集成测试主理人", "leader_desc": "不作语义质量结论", "enable_hitt": False,
                            "call_goal": "加载真实四成员专家团"}))
        else:
            actions.append(("claim_task", {"task_id": "grid-" + role, "status": "claimed"}))
        for skill in plan["skills"][role]:
            actions.append(("skill_tool", {"skill_name": skill, "call_goal": "读取已安装成员实际技能"}))
        if role == "leader":
            tasks = []
            for name in ROLES:
                dependencies = [] if name == "author" else ["grid-author"] if name == "modeler" else ["grid-modeler"]
                tasks.append({"task_id": "grid-" + name, "title": "夹具：" + name,
                              "content": f"GRID_FIXTURE_ROLE={name}\n执行固定测试数据的真实包工具，非自主创作。reviewer 只接收 learner.json。",
                              "assignee": name, "depends_on": dependencies})
            actions.append(("create_task", {"tasks": tasks}))
        actions.append(("bash", {"command": plan["commands"][role], "timeout": 100,
                                  "description": "执行本地固定输入的真实工具并保存中文结果"}))
        if role != "leader":
            actions.append(("claim_task", {"task_id": "grid-" + role, "status": "completed",
                                            "summary": "真实工具已返回；固定脚本仅验证接线，不证明自主推理。"}))
        if index < len(actions):
            name, arguments = actions[index]
            if role == "leader" and name == "bash":
                deadline = time.monotonic() + 70
                while time.monotonic() < deadline:
                    with self.lock:
                        complete = set(ROLES) <= self.done
                    if complete:
                        break
                    time.sleep(0.1)
                if not complete:
                    raise RuntimeError("Real member tasks did not finish")
            if name not in available:
                raise RuntimeError(f"Actual host lacks required tool {name}")
            return {"role": "assistant", "content": None, "tool_calls": [{"id": "grid_" + uuid.uuid4().hex,
                    "type": "function", "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)}}]}
        with self.lock:
            self.done.add(role)
            if role == "leader":
                save(self.runtime / "fixture-finished.json", {"roles": sorted(self.done), "boundary": BOUNDARY})
        return {"role": "assistant", "content": f"{role} 固定夹具流程完成。请核验真实产物；这不代表自主推理或人工测试通过。"}


def model_server(runtime: Path) -> None:
    provider = ScriptedProvider(runtime)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = json.dumps({"object": "list", "data": [{"id": "logic-grid-scripted-fixture", "object": "model"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 6 * 1024 * 1024:
                    raise ValueError("Bounded request length required")
                request = json.loads(self.rfile.read(length))
                message = provider.answer(request)
                common = {"id": "chatcmpl_" + uuid.uuid4().hex, "created": int(time.time()), "model": "logic-grid-scripted-fixture"}
                reason = "tool_calls" if message.get("tool_calls") else "stop"
                if request.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    delta = {"role": "assistant"}
                    if message.get("content") is not None:
                        delta["content"] = message["content"]
                    if message.get("tool_calls"):
                        delta["tool_calls"] = [{"index": n, **call} for n, call in enumerate(message["tool_calls"])]
                    chunks = [{**common, "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                              {**common, "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {}, "finish_reason": reason}]}]
                    for chunk in chunks:
                        self.wfile.write(("data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n").encode())
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                else:
                    body = json.dumps({**common, "object": "chat.completion", "choices": [{"index": 0, "message": message, "finish_reason": reason}]}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            except Exception as error:
                body = json.dumps({"error": {"type": "fixture_error", "message": str(error)}}).encode()
                self.send_response(400)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

    ThreadingHTTPServer(("127.0.0.1", PORTS["model"]), Handler).serve_forever()


async def run(runtime: Path, native: Path, record: Path | None) -> None:
    if not (runtime / "plan.json").exists() or (runtime / "events.json").exists():
        raise ValueError("Need configured fresh fixture; never replay a preserved run")
    result = await check(runtime, native, None, True)
    session = await rpc(runtime, "session.create", {"mode": "team", "team": True, "persist_session": True,
                        "cwd": str(runtime / "cwd"), "title": "逻辑题：固定脚本集成测试"})
    session_id = session["payload"]["session_id"]
    import websockets
    url = f"http://127.0.0.1:{PORTS['http']}"
    events = []
    async with websockets.connect(url.replace("http", "ws") + "/ws", origin=url, max_size=16 * 1024 * 1024) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        await ws.send(json.dumps({"type": "req", "id": "grid-run-" + uuid.uuid4().hex, "method": "chat.send", "params": {
            "session_id": session_id, "content": "本地固定脚本集成测试：请实际分派，读技能和运行工具；不作语义质量判断。",
            "mode": "team", "team": True, "agent_group_name": SLUG, "team_dispatch_mode": "autonomous",
            "supports_user_interaction": False, "cwd": str(runtime / "cwd"), "trusted_dirs": [str(runtime)],
            "plugin_names": [], "mcp": [], "skills": []}}, ensure_ascii=False))
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            try:
                event = json.loads(await asyncio.wait_for(ws.recv(), 5))
                events.append(event)
                if event.get("event") == "chat.error":
                    raise RuntimeError(str(event))
            except asyncio.TimeoutError:
                pass
            if (runtime / "fixture-finished.json").exists():
                break
            delivery = runtime / "artifacts/delivery"
            if (delivery / "puzzle.html").is_file() and (delivery / "audit.json").is_file():
                requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
                leader = [item for item in requests if item["role"] == "leader"]
                after_bash = leader and any(
                    call.get("function", {}).get("name") == "bash"
                    for message in leader[-1]["request"]["messages"]
                    for call in message.get("tool_calls", [])
                )
                if after_bash:
                    break
    save(runtime / "events.json", events)
    result["session_id"] = session_id
    verify_execution(runtime, result, events, record)


def verify_execution(runtime: Path, result: dict, events: list, record: Path | None) -> None:
    accepted = [event.get("payload", {}) for event in events if event.get("payload", {}).get("accepted")]
    if not accepted or not accepted[0].get("session_id"):
        raise RuntimeError("No actual accepted host session in execution events")
    result["session_id"] = accepted[0]["session_id"]
    plan = json.loads((runtime / "plan.json").read_text(encoding="utf-8"))
    expected = plan.get("expected", "unique")
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    evidence = {}
    for role in ("leader", *ROLES):
        rows = [item for item in requests if item["role"] == role]
        calls = [call for row in rows for message in row["request"]["messages"] if message.get("role") == "assistant" for call in message.get("tool_calls", [])]
        names = sorted({call["function"]["name"] for call in calls})
        if not rows or "bash" not in names:
            raise RuntimeError(f"No actual tool exchange for {role}")
        outputs = [str(message.get("content", "")) for row in rows for message in row["request"]["messages"]
                   if message.get("role") == "tool" and plan["commands"][role] in str(message.get("content", ""))]
        exit_code = 2 if role == "leader" and expected != "unique" else 0
        if not any(f"Exit Code: {exit_code}" in value for value in outputs):
            raise RuntimeError(f"No actual exit {exit_code} response for {role}")
        skill_calls = {json.loads(call["function"]["arguments"])["skill_name"] for call in calls
                       if call["function"]["name"] == "skill_tool"}
        required = {"puzzle-collaboration", role + "-workflow"}
        if not required <= skill_calls:
            raise RuntimeError(f"Actual skills not read by {role}: {required - skill_calls}")
        private_others = {name + "-workflow" for name in ("leader", *ROLES) if name != role}
        for row in rows:
            exposed = "\n".join(str(message.get("content", "")) for message in row["request"]["messages"]
                                if message.get("role") == "system")
            if not all(skill in exposed for skill in required):
                raise RuntimeError(f"Own/shared skill absent from assembled prompt for {role}")
            if any(other in exposed for other in private_others):
                raise RuntimeError(f"Unexpected private skill exposure to {role}")
        if role != "leader" and not any(
            f"Task #grid-{role} in_progress → completed" in str(message.get("content", ""))
            for row in rows for message in row["request"]["messages"] if message.get("role") == "tool"
        ):
            raise RuntimeError(f"No completed-task response for {role}")
        evidence[role] = {"model_requests": len(rows), "tools_exchanged": names,
                          "skills_read": sorted(skill_calls), "private_skills_scoped": True, "command_exit": exit_code,
                          "judgment": "fixed fixture",
                          "assembled_tools": sorted({tool["function"]["name"] for row in rows
                                                      for tool in row["request"].get("tools", [])
                                                      if tool.get("type") == "function"})}
    delivery = runtime / "artifacts/delivery"
    expected_files = ("puzzle.html", "answer.md", "audit.json")
    if expected == "unique" and not all((delivery / name).is_file() for name in expected_files):
        raise RuntimeError("Required delivery missing")
    if expected != "unique" and delivery.exists():
        raise RuntimeError("Invalid puzzle unexpectedly produced a delivery")
    artifacts = {path.relative_to(runtime / "artifacts").as_posix(): digest(path) for path in (runtime / "artifacts").rglob("*") if path.is_file()}
    required_paths = ["model/learner.json", "review/review.json"]
    if expected == "unique":
        required_paths += ["delivery/" + name for name in expected_files]
    for name in required_paths:
        if name not in artifacts:
            raise RuntimeError(f"Missing true artifact {name}")
    reviewed = json.loads((runtime / "artifacts/review/review.json").read_text(encoding="utf-8"))
    wanted = "unique_review_model" if expected == "unique" else expected
    if reviewed["status"] != wanted:
        raise RuntimeError(f"Expected {wanted}, got {reviewed['status']}")
    result.update({"role_execution": evidence, "artifacts": artifacts, "expected": expected,
                   "review_status": reviewed["status"], "solution_count": reviewed["solution_count"],
                   "delivery_produced": delivery.exists(),
                   "event_count": len(events), "model_calls": "loopback only", "semantic_acceptance": False})
    save(runtime / "execution.json", result)
    if record:
        save(record, result)
    print(json.dumps({"integration": "passed", "boundary": BOUNDARY, "roles": list(evidence)}, ensure_ascii=False))


def status(runtime: Path) -> None:
    result = {"url": f"http://127.0.0.1:{PORTS['http']}/", "runtime": str(runtime), "boundary": BOUNDARY}
    result["processes"] = json.loads((runtime / "pids.json").read_text()) if (runtime / "pids.json").exists() else {}
    try:
        with urllib.request.urlopen(result["url"], timeout=3) as response:
            result["http"] = response.status
    except Exception as error:
        result["http_error"] = str(error)
    print(json.dumps(result, indent=2))


def stop(runtime: Path) -> None:
    # Process identity is checked using the actual host's psutil before any kill.
    import psutil
    processes = json.loads((runtime / "pids.json").read_text())
    for item in processes.values():
        try:
            process = psutil.Process(item["pid"])
            if Path(process.cwd()).resolve() != runtime / "cwd" or process.cmdline() != item["command"]:
                raise RuntimeError("Process changed identity; refusing cleanup")
            os.killpg(item["pid"], signal.SIGTERM)
        except psutil.NoSuchProcess:
            continue
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            ports_free()
            break
        except OSError:
            time.sleep(0.2)
    save(runtime / "stopped.json", {"time": time.time(), "pids": [item["pid"] for item in processes.values()]})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "start", "validate", "check", "plan", "run", "verify", "status", "stop", "_setup", "_model"))
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--host", type=Path)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--expect", choices=("unique", "ambiguous", "inconsistent"), default="unique")
    args = parser.parse_args()
    runtime = owned(args.runtime)
    if args.record and not args.record.resolve().is_relative_to(ASSET / "tests/records"):
        parser.error("Records must stay in this asset's tests/records")
    if args.action == "prepare":
        prepare(args)
    elif args.action == "_setup":
        setup(runtime)
    elif args.action == "start":
        start(runtime)
    elif args.action == "validate":
        validate(runtime, args.payload)
    elif args.action == "check":
        print(json.dumps(asyncio.run(check(runtime, args.native, args.record, args.reuse)), ensure_ascii=False))
    elif args.action == "plan":
        make_plan(runtime, args.model, args.expect)
    elif args.action == "run":
        asyncio.run(run(runtime, args.native, args.record))
    elif args.action == "verify":
        result = json.loads((runtime / "import.json").read_text(encoding="utf-8"))
        events = json.loads((runtime / "events.json").read_text(encoding="utf-8"))
        verify_execution(runtime, result, events, args.record)
    elif args.action == "_model":
        model_server(runtime)
    elif args.action == "status":
        status(runtime)
    else:
        stop(runtime)


if __name__ == "__main__":
    main()
