"""Plugin-owned loopback service lifecycle; never patches WorkSwarm."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time
from urllib.request import Request, ProxyHandler, build_opener
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "runtime/config.json").read_text(encoding="utf-8"))
OPENER = build_opener(ProxyHandler({}))
PROCESSES = {}


def workspace_path(raw):
    p = Path(raw).expanduser()
    if not p.is_absolute() or not p.is_dir() or p.is_symlink():
        raise ValueError("工作目录必须是已存在的绝对路径，且不能是符号链接")
    if any(x.is_symlink() for x in [p, *p.parents]):
        raise ValueError("工作目录路径不能经过符号链接")
    state = p / ("." + CONFIG["slug"])
    if state.is_symlink():
        raise ValueError("插件数据目录不能是符号链接")
    return p, state


def node_binary():
    candidates = [os.environ.get("JIUWEN_NODE_BINARY"), shutil.which("node"),
                  "/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node"]
    for path in candidates:
        if path and Path(path).is_file():
            version = subprocess.check_output([path, "--version"], text=True, timeout=5).strip()
            if int(version.lstrip("v").split(".")[0]) >= 22:
                return path
    raise ValueError("需要 Node.js 22 或更高版本；可设置 JIUWEN_NODE_BINARY 指向现有运行时")


def request(record, route, data=None):
    url = record["url"] + route
    body = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = {"X-Workbench-Owner": record["nonce"]}
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        with OPENER.open(Request(url, data=body, headers=headers), timeout=70) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            return json.load(error)
        except (ValueError, OSError):
            raise ValueError("本机服务返回错误：" + str(error.code)) from error


def read_record(state, allow_previous=False):
    p = state / "service.json"
    if not p.exists():
        return None
    if p.is_symlink():
        raise ValueError("服务记录不能是符号链接")
    record = json.loads(p.read_text())
    if record.get("payload") != str(ROOT) or record.get("slug") != CONFIG["slug"]:
        raise ValueError("服务记录属于其他安装，拒绝接管；请使用新的专用工作目录")
    if not record.get("url", "").startswith("http://127.0.0.1:"):
        raise ValueError("服务记录地址无效")
    try:
        health = request(record, "/health")
    except OSError:
        return None
    if health.get("nonce") != record["nonce"] or health.get("payload") != str(ROOT):
        raise ValueError("本地端口所有权不符，拒绝复用或关闭")
    if health.get("version") != CONFIG["version"] and not allow_previous:
        raise ValueError("旧版工作台仍在运行，请先调用 stop 关闭，再重新启动")
    return record


def run(inputs):
    try:
        workspace, state = workspace_path(inputs.get("workspace", ""))
        action = inputs.get("action", "status")
        if action not in {"start", "status", "stop", "operate"}:
            raise ValueError("操作必须是 start、status、stop 或 operate")
        record = read_record(state, allow_previous=action == "stop")
        if action == "status":
            return {"ok": True, "slug": CONFIG["slug"], "version": CONFIG["version"], "running": bool(record),
                    **({"url": record["url"], "workspace": str(workspace)} if record else {})}
        if inputs.get("confirmed") is not True:
            raise ValueError("启动、写入、执行或关闭操作需要用户明确授权后设置 confirmed=true")
        if action == "start" and record:
            return {"ok": True, "version": CONFIG["version"], "reused": True, "url": record["url"], "workspace": str(workspace)}
        if action == "start":
            state.mkdir(mode=0o700, exist_ok=True)
            with (state / "service.log").open("ab") as log:
                nonce = secrets.token_hex(24)
                process = subprocess.Popen([node_binary(), str(ROOT / "runtime/service.cjs"), str(workspace), nonce],
                                 cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 start_new_session=True, close_fds=True)
                PROCESSES[nonce] = process
            for _ in range(100):
                time.sleep(.1)
                record = read_record(state)
                if record:
                    return {"ok": True, "version": CONFIG["version"], "url": record["url"], "workspace": str(workspace),
                            "message": "中文工作台已启动；请打开链接。所有结果来自真实引擎。"}
            raise ValueError("工作台启动失败；请查看专用目录内的 service.log")
        if not record:
            raise ValueError("当前工作台未启动，请先执行 start")
        result = request(record, "/shutdown" if action == "stop" else "/api/operate", inputs.get("params", {}))
        if action == "stop" and record["nonce"] in PROCESSES:
            process = PROCESSES.pop(record["nonce"])
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        result["version"] = CONFIG["version"]
        return result
    except Exception as error:
        return {"ok": False, "version": CONFIG["version"], "error": str(error)}


async def invoke(inputs):
    return await asyncio.to_thread(run, inputs)


def compact_result(result):
    """Keep binary files/local reports out of the host/model message budget."""
    notes=[]
    def visit(value, path="", depth=0):
        if depth>10:
            notes.append(path+": nested preview omitted")
            return "（深层内容保存在本机工作台）"
        if path in {"original", "optimized"} and isinstance(value,str):
            body=base64.b64decode(value,validate=True)
            notes.append(path+": binary retained in local workbench")
            return {"binary_omitted":True,"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()}
        if isinstance(value,dict):
            return {k:visit(v,path+"."+k if path else k,depth+1) for k,v in list(value.items())[:80]}
        if isinstance(value,list):
            if len(value)>30:notes.append(path+": preview limited to30 of "+str(len(value)))
            return [visit(v,path+"[]",depth+1) for v in value[:30]]
        if isinstance(value,str) and len(value)>3500:
            notes.append(path+": long text preview truncated")
            return value[:3500]+"\n（预览已截断；完整内容保存在本机工作台）"
        return value
    compact=visit(result)
    if notes:compact["preview_notes"]=notes
    if len(json.dumps(compact,ensure_ascii=False).encode())>16000:
        return {"ok":result.get("ok",False),"version":result.get("version"),
                "message":"操作已返回；内容超过会话预览预算，请在本机工作台查看完整结果。",
                "result_sha256":hashlib.sha256(json.dumps(result,ensure_ascii=False).encode()).hexdigest(),
                "preview_omitted":True}
    return compact
