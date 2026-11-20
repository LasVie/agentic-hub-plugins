"""Owned local host fixture adapted from the repository's existing mechanism.
Fixed responses test actual orchestration, never autonomous reasoning/acceptance.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, shlex, signal, socket, subprocess, sys, threading, time, urllib.request, uuid, zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ASSET=Path(__file__).resolve().parents[1]
SLUG="tou-bill-review-team"
ROLES=("meter-analyst", "reviewer", "tariff-analyst")
STAGES=("meter-analyst", "reviewer", "tariff-analyst")
BASE_PORTS={"http":6705,"model":6706,"agent":28705,"web":29705,"gateway":30705}
PORTS=BASE_PORTS.copy()
BOUNDARY="Real host and tool execution with fixed local responses; no semantic model or manual pass."

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
        "MODEL_NAME": "tou-bill-scripted-fixture", "HF_HUB_OFFLINE": "1",
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
        "model_id": "tou-bill-scripted-fixture", "is_default": True,
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
        identifier = "tou-rpc-" + uuid.uuid4().hex
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


def model_server(runtime: Path) -> None:
    provider = ScriptedProvider(runtime)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = json.dumps({"object": "list", "data": [{"id": "tou-bill-scripted-fixture", "object": "model"}]}).encode()
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
                common = {"id": "chatcmpl_" + uuid.uuid4().hex, "created": int(time.time()), "model": "tou-bill-scripted-fixture"}
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


def make_plan(runtime, scenario):
    import shutil

    if (runtime / "plan.json").exists():
        raise ValueError("Fresh run required; preserve previous plan/evidence")
    python = settings(runtime)["python"]
    package = runtime / "data/domain/.agent_teams/agent_groups/local" / SLUG
    artifacts = runtime / "artifacts"
    case = artifacts / "case"
    shutil.copytree(ASSET / "tests/fixtures/two-hour", case)
    script = package / "skills/bill-review/scripts/bill_review.py"

    def command(stage, filename, *flags):
        return shlex.join([python, "-B", str(script), stage, "--case", str(case),
                           "--output", str(artifacts / filename), *map(str, flags)])

    meter = artifacts / "meter.json"
    candidate = artifacts / "candidate.json"
    independent = artifacts / "independent.json"
    commands = {
        "meter-analyst": command("inspect", meter.name),
        "reviewer": command("replay", independent.name),
        "tariff-analyst": command("calculate", candidate.name, "--meter", meter),
        "leader": command("deliver", "delivery", "--meter", meter, "--candidate", candidate,
                          "--independent", independent),
    }
    if scenario == "bad-band":
        # Mutate only this fresh test candidate. Preserve the independent report and originals.
        inject = (
            "from pathlib import Path; import json, sys; p=Path(sys.argv[1]); "
            "candidate=json.loads(p.read_bytes()); candidate['result']={"
            "'interval_bands':['off_peak','peak','peak','peak'],"
            "'energy_micro_kwh':{'off_peak':1000000,'peak':3000000},"
            "'amount_minor':{'off_peak':10,'peak':90}}; p.write_text(json.dumps(candidate))"
        )
        commands["tariff-analyst"] += " && " + shlex.join([python, "-B", "-c", inject, str(candidate)])
    save(runtime / "plan.json", {
        "commands": commands, "skills": {role: ["bill-review"] for role in ("leader", *STAGES)},
        "scenario": scenario, "source_digests": {p.name: digest(p) for p in case.iterdir()},
        "boundary": BOUNDARY,
    })


class ScriptedProvider:
    def __init__(self, runtime):
        self.runtime = runtime
        self.lock = threading.Lock()
        self.steps = {}
        self.done = set()
        self.total = 0

    def answer(self, request):
        tools = {t["function"]["name"] for t in request.get("tools", []) if t.get("type") == "function"}
        users = "\n".join(str(m.get("content", "")) for m in request.get("messages", []) if m.get("role") == "user")
        role = "leader" if "create_task" in tools else "other"
        if role == "other":
            markers = [(users.rfind("TOU_FIXTURE_STAGE=" + name), name) for name in STAGES]
            index, name = max(markers)
            if index >= 0: role = name
        with self.lock:
            self.total += 1
            if self.total > 100: raise RuntimeError("Bounded fixture request allowance exhausted")
            step = self.steps.get(role, 0); self.steps[role] = step + 1
            with (self.runtime / "requests.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"role": role, "index": step, "request": request}, ensure_ascii=False) + "\n")
        planfile = self.runtime / "plan.json"
        if role == "other" or not planfile.exists():
            return {"role": "assistant", "content": "本机脚本化集成夹具；未配置真实推理，不表示电费判断或人工通过。"}
        plan = json.loads(planfile.read_text())
        actions = []
        if role == "leader":
            actions.append(("build_team", {"display_name": "分时账单本地集成夹具", "team_desc": "只验证真实任务与工具通道；固定响应不证明语义独立。",
                "leader_display_name": "本地测试主理人", "leader_desc": "仅核对电量费", "enable_hitt": False, "call_goal": "建立真实四成员专家团"}))
        else:
            actions.append(("claim_task", {"task_id": "tou-" + role, "status": "claimed"}))
        for skill in plan["skills"][role]:
            actions.append(("skill_tool", {"skill_name": skill, "call_goal": "读取本角色真实安装技能"}))
        if role == "leader":
            dependencies = {"meter-analyst": [], "reviewer": [],
                            "tariff-analyst": ["tou-meter-analyst", "tou-reviewer"]}
            tasks = [{"task_id": "tou-" + stage, "title": "夹具：" + stage, "content": "TOU_FIXTURE_STAGE=" + stage +
                      "\n仅运行已授权合成案例的真实包内命令。", "assignee": stage,
                      "depends_on": dependencies[stage]} for stage in STAGES]
            actions.append(("create_task", {"tasks": tasks}))
        actions.append(("bash", {"command": plan["commands"][role], "timeout": 90, "description": "运行实际分时复核工具与证据交付"}))
        if role != "leader":
            actions.append(("claim_task", {"task_id": "tou-" + role, "status": "completed", "summary": "固定夹具已执行真实命令；文件 " + str(self.runtime / "artifacts") + "; stage=" + role}))
        if step < len(actions):
            name, args = actions[step]
            if name == "bash" and role in {"leader", "tariff-analyst"}:
                needed = set(STAGES) if role == "leader" else {"meter-analyst", "reviewer"}
                deadline = time.monotonic() + 75
                while not needed <= self.done and time.monotonic() < deadline: time.sleep(.1)
                if not needed <= self.done: raise RuntimeError("Actual prerequisite tasks did not complete")
            if name not in tools: raise RuntimeError("Required host tool unavailable: " + name)
            return {"role": "assistant", "content": None, "tool_calls": [{"id": "route_" + uuid.uuid4().hex,
                "type": "function", "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]}
        with self.lock:
            self.done.add(role)
            if role == "leader": save(self.runtime / "fixture-finished.json", {"stages": sorted(self.done), "boundary": BOUNDARY})
        return {"role": "assistant", "content": role + " 真实通道检查完成；不是语义独立或人工验收证明。"}


async def run(runtime, native, record):
    if not (runtime / "plan.json").exists() or (runtime / "events.json").exists():
        raise ValueError("Fresh configured run only; never replay preserved execution")
    result = await check(runtime, native, None, True)
    session = await rpc(runtime, "session.create", {"mode": "team", "team": True, "persist_session": True,
        "cwd": str(runtime / "cwd"), "title": "分时电量费：本机固定响应集成测试"})
    session_id = session["payload"]["session_id"]
    import websockets
    url = f"http://127.0.0.1:{PORTS['http']}"; events = []
    try:
        async with websockets.connect(url.replace("http", "ws") + "/ws", origin=url, max_size=16 * 1024 * 1024) as ws:
            await asyncio.wait_for(ws.recv(), 15)
            await ws.send(json.dumps({"type": "req", "id": "tou-run-" + uuid.uuid4().hex, "method": "chat.send", "params": {
                "session_id": session_id, "content": "本机合成数据通道测试：请实际建队、委派、读技能与运行工具；不是人工测试。",
                "mode": "team", "team": True, "agent_group_name": SLUG, "team_dispatch_mode": "autonomous",
                "supports_user_interaction": False, "cwd": str(runtime / "cwd"), "trusted_dirs": [str(runtime)],
                "plugin_names": [], "mcp": [], "skills": []}}, ensure_ascii=False))
            deadline = time.monotonic() + 240
            while time.monotonic() < deadline:
                try:
                    event = json.loads(await asyncio.wait_for(ws.recv(), 5)); events.append(event)
                    if event.get("event") == "chat.error": raise RuntimeError(str(event))
                except asyncio.TimeoutError: pass
                if (runtime / "fixture-finished.json").exists(): break
    finally:
        save(runtime / "events.json", events)
    result["session_id"] = session_id
    verify_execution(runtime, result, events, record)


def verify_execution(runtime, result, events, record):
    plan = json.loads((runtime / "plan.json").read_text())
    requests = [json.loads(line) for line in (runtime / "requests.jsonl").read_text().splitlines()]
    evidence = {}
    for stage in ("leader", *STAGES):
        rows = [row for row in requests if row["role"] == stage]
        messages = [message for row in rows for message in row["request"]["messages"]]
        calls = [call for message in messages if message.get("role") == "assistant" for call in message.get("tool_calls", [])]
        names = {call["function"]["name"] for call in calls}
        results = [str(message.get("content", "")) for message in messages if message.get("role") == "tool"]
        if not {"bash", "skill_tool"} <= names or not any("Exit Code: 0" in item and plan["commands"][stage] in item for item in results):
            raise RuntimeError("Missing real Skill or successful tool receipt for " + stage)
        if stage != "leader" and not any("Task #tou-" + stage + " in_progress → completed" in item for item in results):
            raise RuntimeError("Missing real task completion for " + stage)
        if stage == "tariff-analyst":
            for predecessor in ("meter-analyst", "reviewer"):
                if not any("上游交付" in receipt and "stage=" + predecessor in receipt for receipt in results):
                    raise RuntimeError("Missing actual upstream delivery " + predecessor)
        if stage == "reviewer":
            if any("candidate.json" in str(message.get("content", "")) for message in messages
                   if message.get("role") in {"user", "tool"}):
                raise RuntimeError("Candidate appeared in the independent review context")
        evidence[stage] = {"requests": len(rows), "tools": sorted(names), "real_command_exit": 0}
    artifacts = runtime / "artifacts"
    out = artifacts / "delivery"
    order_verified = (artifacts / "independent.json").stat().st_mtime_ns < (artifacts / "candidate.json").stat().st_mtime_ns
    if not order_verified:
        raise RuntimeError("Independent report must predate candidate creation")
    summary = json.loads((out / "evaluation.json").read_text())
    manifest = json.loads((out / "artifact.json").read_text())
    expected = "verified" if plan["scenario"] == "positive" else "blocked"
    assert summary["status"] == expected and manifest["status"] == expected
    for name in ("readings.csv", "tariff.json", "bill.json"):
        assert (artifacts / "case" / name).read_bytes() == (out / "inputs" / name).read_bytes()
    for name in ("meter.json", "candidate.json", "independent.json"):
        assert (artifacts / name).read_bytes() == (out / "handoffs" / name).read_bytes()
    assert len(manifest["files_sha256"]) == 9
    for name, checksum in manifest["files_sha256"].items():
        assert digest(out / name) == checksum
    rows = (out / "intervals.csv").read_text(encoding="utf-8-sig").splitlines()
    draft = json.loads((artifacts / "candidate.json").read_text())["result"]
    independent = json.loads((artifacts / "independent.json").read_text())["result"]
    if expected == "verified":
        assert len(rows) == 5 and "off_peak" in rows[-1]
        assert (summary["billed_minor"], summary["computed_minor"], summary["difference_minor"]) == (100, 80, 20)
    else:
        assert len(rows) == 1 and "computed_minor" not in summary
        assert sum(draft["amount_minor"].values()) == 100 and draft["interval_bands"][-1] == "peak"
        assert sum(independent["amount_minor"].values()) == 80 and independent["interval_bands"][-1] == "off_peak"
    result.update({
        "scenario": plan["scenario"], "status": expected, "findings": summary["findings"],
        "reported_amounts_minor": {key: summary.get(key) for key in ("billed_minor", "computed_minor", "difference_minor")},
        "role_execution": evidence, "actual_upstream_receipts_verified": True,
        "independent_before_candidate_verified": order_verified, "exact_snapshots": True,
        "artifact_hashes_verified": True, "events": len(events), "request_count": len(requests),
        "model_calls": "loopback fixed responses only", "human_testing_passed": False, "semantic_acceptance": False,
    })
    save(runtime / "execution.json", result)
    if record:
        save(record, result)
    print(json.dumps({"integration": "passed", "scenario": plan["scenario"], "status": expected, "boundary": BOUNDARY}))



def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "start", "validate", "check", "plan", "run", "verify", "status", "stop", "_setup", "_model"))
    for name in ("runtime", "host", "python", "payload", "native", "record"): p.add_argument("--" + name, type=Path, required=name == "runtime")
    p.add_argument("--reuse", action="store_true")
    p.add_argument("--port-offset", type=int, default=0, help="Add to the isolated ports when preparing a new run")
    p.add_argument("--scenario", choices=("positive", "bad-band"), default="positive")
    a = p.parse_args(); runtime = owned(a.runtime)
    if a.action == "prepare":
        if not 0 <= a.port_offset <= 10_000:
            p.error("--port-offset must be between 0 and 10000")
        PORTS.update({name: port + a.port_offset for name, port in BASE_PORTS.items()})
    else:
        PORTS.update(settings(runtime)["ports"])
    if a.record and not a.record.resolve().is_relative_to(ASSET / "tests/records"): p.error("Records must stay in own tests/records")
    if a.action == "prepare": prepare(a)
    elif a.action == "_setup": setup(runtime)
    elif a.action == "_model": model_server(runtime)
    elif a.action == "start": start(runtime)
    elif a.action == "validate": validate(runtime, a.payload)
    elif a.action == "check": print(json.dumps(asyncio.run(check(runtime, a.native, a.record, a.reuse))))
    elif a.action == "plan": make_plan(runtime, a.scenario)
    elif a.action == "run": asyncio.run(run(runtime, a.native, a.record))
    elif a.action == "verify": verify_execution(runtime, json.loads((runtime / "import.json").read_text()), json.loads((runtime / "events.json").read_text()), a.record)
    elif a.action == "status": status(runtime)
    elif a.action == "stop": stop(runtime)


if __name__ == "__main__":
    main()
