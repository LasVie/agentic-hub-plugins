"""Owned WorkSwarm instance and explicit scripted-model integration checks.

The loopback provider is a protocol fixture. It never evaluates continuity decisions or
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
SLUG = "business-interruption-rehearsal-team"
ROLES = ("analyst", "fallback", "recovery", "facilitator", "verifier")
PORTS = {"http": 6697, "model": 6698, "agent": 28697, "web": 29697, "gateway": 30697}
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
        "MODEL_NAME": "rehearsal-scripted-fixture", "HF_HUB_OFFLINE": "1",
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
        "model_id": "rehearsal-scripted-fixture", "is_default": True,
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
        identifier = "rehearsal-" + uuid.uuid4().hex
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


PRIVATE = {
    "leader": "rehearsal-delivery", "analyst": "rehearsal-dependencies",
    "fallback": "rehearsal-fallback", "recovery": "rehearsal-restart",
    "facilitator": "rehearsal-scenario", "verifier": "rehearsal-review",
}
FILES = {
    "map": "map/dependency-map.json", "fallback": "fallback/fallback-plan.json",
    "restart": "restart/restart-plan.json", "baseline": "baseline/review-baseline.json",
    "trace": "trace/exercise-trace.json", "review": "review/independent-review.json",
}


def make_plan(runtime: Path, case_path: Path) -> None:
    if (runtime / "plan.json").exists():
        raise ValueError("Fixture already configured. Preserve the previous evidence.")
    python = settings(runtime)["python"]
    group = runtime / "data/domain/.agent_teams/agent_groups/local" / SLUG
    scripts = group / "skills/rehearsal-evidence/scripts"
    if not scripts.is_dir():
        raise ValueError("Import the exact native ZIP first")
    a = runtime / "artifacts"
    fixed = a / "input.json"
    with fixed.open("xb") as stream:
        stream.write(case_path.read_bytes())

    def command(tool, *extra, output, upstream=()):
        argv = [python, "-B", str(scripts / (tool + ".py")), *extra,
                "--input", str(fixed), "--output", str(a / output)]
        for key in upstream:
            argv.extend(["--" + key, str(a / FILES[key])])
        return shlex.join(argv)

    commands = {
        "analyst": command("plan", "map", output="map"),
        "fallback": command("plan", "fallback", output="fallback", upstream=("map",)),
        "recovery": command("plan", "restart", output="restart", upstream=("map", "fallback")),
        "baseline": command("verify", "baseline", output="baseline"),
        "facilitator": command("simulate", output="trace", upstream=("map", "fallback", "restart")),
        "verifier": command("verify", "compare", output="review",
                            upstream=("map", "fallback", "restart", "baseline", "trace")),
        "leader": command("deliver", output="delivery", upstream=tuple(FILES)),
    }
    save(runtime / "plan.json", {"commands": commands, "case_sha256": digest(fixed), "boundary": BOUNDARY})


class ScriptedProvider:
    def __init__(self, runtime: Path):
        self.runtime = runtime
        self.lock = threading.Lock()
        self.steps = {}
        self.done = set()
        self.total = 0

    def answer(self, request: dict) -> dict:
        tools = {item["function"]["name"] for item in request.get("tools", []) if item.get("type") == "function"}
        user = "\n".join(str(item.get("content", "")) for item in request.get("messages", []) if item.get("role") == "user")
        role = "leader" if "create_task" in tools else next((n for n in ROLES if f"REHEARSAL_FIXTURE_ROLE={n}" in user), "other")
        with self.lock:
            self.total += 1
            if self.total > 120:
                raise RuntimeError("Local fixture exceeded 120 requests")
            index = self.steps.get(role, 0)
            self.steps[role] = index + 1
            with (self.runtime / "requests.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps({"role": role, "index": index, "request": request}, ensure_ascii=False) + "\n")
        if not (self.runtime / "plan.json").exists() or role == "other":
            return {"role": "assistant", "content": "此本地模型只用于固定响应工程测试。手工测试请选择已授权的模型。"}
        plan = json.loads((self.runtime / "plan.json").read_text())
        actions = self.actions(role, plan)
        if index < len(actions):
            tool, args = actions[index]
            if tool == "bash":
                self.await_handoff(role, args["command"] == plan["commands"]["baseline"])
            if tool not in tools:
                raise RuntimeError(f"Actual host has no tool {tool}")
            return {"role": "assistant", "content": None, "tool_calls": [{
                "id": "rehearsal_" + uuid.uuid4().hex, "type": "function",
                "function": {"name": tool, "arguments": json.dumps(args, ensure_ascii=False)}}]}
        with self.lock:
            self.done.add(role)
            if role == "leader":
                save(self.runtime / "fixture-finished.json", {"roles": sorted(self.done), "boundary": BOUNDARY})
        return {"role": "assistant", "content": f"{role} 固定响应接线检查完成。请检查实际证据。"}

    def actions(self, role, plan):
        task_prefix = "rehearsal-"
        if role == "leader":
            actions = [("build_team", {"display_name": "复工演练本地接线夹具", "team_desc": "固定响应，验证原生六成员和文件交接。",
                                      "leader_display_name": "接线主理人", "leader_desc": "不作语义验收", "enable_hitt": False,
                                      "call_goal": "启动已安装的六成员原生专家团"})]
        else:
            actions = [("claim_task", {"task_id": task_prefix + role, "status": "claimed"})]
        for skill in (PRIVATE[role], "rehearsal-evidence"):
            actions.append(("skill_tool", {"skill_name": skill, "call_goal": "读取角色和共享技能"}))
        if role == "leader":
            needs = {"fallback": ["analyst"], "recovery": ["fallback"], "facilitator": ["recovery"]}
            tasks = [{"task_id": task_prefix + name, "title": "固定夹具：" + name,
                      "content": f"REHEARSAL_FIXTURE_ROLE={name}\n如为核验员，先仅用原始输入生成基线，再收演练记录。",
                      "assignee": name, "depends_on": [task_prefix + dep for dep in needs.get(name, [])]}
                     for name in ROLES]
            actions.append(("create_task", {"tasks": tasks}))
        if role == "verifier":
            actions.append(("bash", {"command": plan["commands"]["baseline"], "timeout": 100,
                                    "description": "仅根据原始输入生成独立复盘基线"}))
            actions.append(("send_message", {"to": "team-leader",
                                             "content": f"独立基线交接：{self.runtime / 'artifacts' / FILES['baseline']}。"}))
        actions.append(("bash", {"command": plan["commands"][role], "timeout": 100,
                                "description": "执行安装包对应阶段并保留进程结果"}))
        if role != "leader":
            fname = {"analyst": "map", "fallback": "fallback", "recovery": "restart",
                     "facilitator": "trace", "verifier": "review"}[role]
            report = self.runtime / "artifacts" / FILES[fname]
            actions.append(("send_message", {"to": "team-leader", "content": f"角色 {role} 实际产物交接：{report}"}))
            actions.append(("claim_task", {"task_id": task_prefix + role, "status": "completed",
                                          "summary": f"固定夹具阶段 {role} 已运行，具体结论以文件和退出码为准。"}))
        return actions

    def await_handoff(self, role, baseline):
        needed = {
            "fallback": ("map",), "recovery": ("map", "fallback"),
            "facilitator": ("map", "fallback", "restart", "baseline"),
            "verifier": ("trace",), "leader": tuple(FILES),
        }
        paths = [self.runtime / "artifacts" / FILES[name]
                 for name in (() if baseline else needed.get(role, ()))]
        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            with self.lock:
                finished = role != "leader" or set(ROLES) <= self.done
            if finished and all(path.is_file() for path in paths):
                return
            time.sleep(0.1)
        raise RuntimeError("Required real role output did not arrive")


def model_server(runtime: Path) -> None:
    provider = ScriptedProvider(runtime)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = json.dumps({"object": "list", "data": [{"id": "rehearsal-scripted-fixture", "object": "model"}]}).encode()
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
                common = {"id": "chatcmpl_" + uuid.uuid4().hex, "created": int(time.time()), "model": "rehearsal-scripted-fixture"}
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
                        "cwd": str(runtime / "cwd"), "title": "复工演练：固定脚本集成测试"})
    session_id = session["payload"]["session_id"]
    import websockets
    url = f"http://127.0.0.1:{PORTS['http']}"
    events = []
    async with websockets.connect(url.replace("http", "ws") + "/ws", origin=url, max_size=16 * 1024 * 1024) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        await ws.send(json.dumps({"type": "req", "id": "rehearsal-run-" + uuid.uuid4().hex, "method": "chat.send", "params": {
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
            if (delivery / "playbook.md").is_file() and (delivery / "audit.json").is_file():
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
    accepted = [e.get("payload", {}) for e in events if e.get("payload", {}).get("accepted")]
    if not accepted or not accepted[0].get("session_id"):
        raise RuntimeError("The actual WorkSwarm session did not accept the request")
    result["session_id"] = accepted[0]["session_id"]
    plan = json.loads((runtime / "plan.json").read_text())
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    evidence = {}
    for role in ("leader", *ROLES):
        rows = [item for item in requests if item["role"] == role]
        messages = [m for row in rows for m in row["request"]["messages"]]
        calls = [call for m in messages if m.get("role") == "assistant" for call in m.get("tool_calls", [])]
        tools_used = {call["function"]["name"] for call in calls}
        results = [str(m.get("content", "")) for m in messages if m.get("role") == "tool"]
        commands = [plan["commands"][role]]
        if role == "verifier":
            commands.append(plan["commands"]["baseline"])
        for cli in commands:
            if not any(cli in value and "Exit Code: 0" in value for value in results):
                raise RuntimeError(f"No successful real tool receipt for {role}")
        skills = {json.loads(c["function"]["arguments"])["skill_name"] for c in calls if c["function"]["name"] == "skill_tool"}
        if not {PRIVATE[role], "rehearsal-evidence"} <= skills:
            raise RuntimeError(f"Shared or private Skill was not read by {role}")
        for row in rows:
            content = "\n".join(str(m.get("content", "")) for m in row["request"]["messages"] if m.get("role") == "system")
            if not all(skill in content for skill in (PRIVATE[role], "rehearsal-evidence")):
                raise RuntimeError(f"Skill was not mounted for {role}")
            if any(skill in content for other, skill in PRIVATE.items() if other != role):
                raise RuntimeError(f"Unexpected private Skill for {role}")
        if role != "leader" and ("send_message" not in tools_used or not any(
                f"Task #rehearsal-{role} in_progress → completed" in value for value in results)):
            raise RuntimeError(f"No completed host task/actual handoff for {role}")
        evidence[role] = {"model_requests": len(rows), "tools_used": sorted(tools_used),
                          "skills_read": sorted(skills), "private_skill_scoped": True,
                          "command_exit": 0, "judgment": "fixed fixture"}
    a = runtime / "artifacts"
    dossier = json.loads((a / "delivery/audit.json").read_text())
    baseline = json.loads((a / FILES["baseline"]).read_text())
    review = json.loads((a / FILES["review"]).read_text())
    if dossier["verification"]["verdict"] != "matched" or review["data"]["verdict"] != "matched":
        raise RuntimeError("Independent verification is missing or failed")
    for name in ("trace", "review"):
        if (a / FILES["baseline"]).stat().st_mtime_ns > (a / FILES[name]).stat().st_mtime_ns:
            raise RuntimeError("Source-only baseline happened after the facilitated replay")
    for role, name in FILES.items():
        key = "mapping" if role == "map" else role
        if digest(a / name) != dossier["evidence_sha256"][key]:
            raise RuntimeError(f"Evidence digest mismatch for {role}")
    if baseline["case_sha256"] != digest(a / "input.json"):
        raise RuntimeError("Baseline bound to another case")
    routine, readonly = dossier["scenarios"]
    if not routine["met"] or routine["ready"] != {"intake": 30, "assign": 35, "close": 40}:
        raise RuntimeError("Routine restart did not match the test oracle")
    if readonly["met"] or readonly["ready"] or any(row["disposition"] != "hold_closed" for row in readonly["items"].values()):
        raise RuntimeError("Read-only scenario was not held")
    outputs = ("playbook.md", "scenario-trace.jsonl", "audit.json", "actions.csv")
    result.update({"role_execution": evidence, "events": len(events),
                   "model_calls": sum(item["model_requests"] for item in evidence.values()),
                   "model_provider": "scripted loopback only", "semantic_acceptance": False,
                   "source_first_baseline": True, "matched_items": dossier["verification"]["items"],
                   "scenario_results": [routine["met"], readonly["met"]],
                   "output_sha256": {name: digest(a / "delivery" / name) for name in outputs}})
    save(runtime / "execution.json", result)
    if record:
        save(record, result)
    print(json.dumps({"integration": "passed", "roles": list(evidence), "scenarios": [True, False],
                      "items": dossier["verification"]["items"], "boundary": BOUNDARY}, ensure_ascii=False))


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
    parser.add_argument("--http-port", type=int, default=6707, help="Loopback HTTP port for a new instance")
    parser.add_argument("--host", type=Path)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    runtime = owned(args.runtime)
    if args.action == "prepare":
        PORTS["http"] = args.http_port
    else:
        PORTS.update(settings(runtime)["ports"])
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
        make_plan(runtime, args.case)
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
