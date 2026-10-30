"""离线光学实验室：插件私有进程、本机会话与显式场景保存。

沿用本仓已维护的离线服务边界；不修改宿主、SDK、其他插件或安装依赖。
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import threading
import time

VERSION = "1.0.0"
PLUGIN = "offline-optics-lab"
PAYLOAD = Path(__file__).resolve().parents[1]
MAX_BODY = 128 * 1024
MAX_RESULT = 8 * 1024 * 1024
IDLE_SECONDS = 1800


class LabError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def failure(code, message):
    return {"ok": False, "version": VERSION, "error": {"code": code, "message": message}}


def runtime_id():
    digest = hashlib.sha256(str(PAYLOAD).encode())
    for part in ("runtime", "engine", "web", "tools"):
        for path in sorted((PAYLOAD / part).rglob("*")):
            if path.is_file() and path.suffix in (".py", ".mjs", ".js", ".json", ".html", ".css"):
                digest.update(path.relative_to(PAYLOAD).as_posix().encode())
                digest.update(path.read_bytes())
    digest.update((PAYLOAD / "manifest.json").read_bytes())
    return digest.hexdigest()


def clean_env(node=None):
    # No provider credentials, Node preload hooks or host runtime injection.
    return {"PATH": (str(Path(node).parent) + os.pathsep if node else "") + os.defpath,
            "HOME": str(Path.home()), "LANG": "en_US.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}


def select_node(explicit=None):
    if explicit is not None and (not isinstance(explicit, str) or not Path(explicit).is_absolute()):
        raise LabError("invalid_node_path", "node_path 必须是已安装 Node.js 的绝对路径。")
    candidates = [explicit] if explicit else [shutil.which("node"), "/opt/homebrew/bin/node", "/usr/local/bin/node",
        str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")]
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file() or not os.access(candidate, os.X_OK):
            continue
        try:
            result = subprocess.run([candidate, "--version"], capture_output=True, timeout=3,
                                    env=clean_env(candidate), check=False)
            match = re.fullmatch(rb"v(\d+)\.\d+\.\d+\s*", result.stdout)
            if result.returncode == 0 and match and int(match.group(1)) >= 18:
                return str(Path(candidate).resolve())
        except (OSError, subprocess.TimeoutExpired):
            pass
    raise LabError("node_unavailable", "需要已安装的 Node.js 18+。可提供 node_path 绝对路径；插件不会安装软件或修改宿主环境。")


def engine_call(inputs, node=None, validate=False):
    try:
        if not isinstance(inputs, dict) or "scene" not in inputs or set(inputs) - {"scene", "node_path"}:
            raise LabError("invalid_input", "请提供 scene 光学场景对象；可选 node_path 为已安装 Node.js 的绝对路径。")
        data = json.dumps({"action": "validate" if validate else "simulate", "scene": inputs["scene"]},
                          ensure_ascii=False, allow_nan=False).encode()
        if len(data) > MAX_BODY:
            raise LabError("input_limit", "场景 JSON 超过 128 KiB 限制。")
        executable = node or select_node(inputs.get("node_path"))
        result = subprocess.run([executable, str(PAYLOAD / "engine/cli.mjs")], input=data,
                                capture_output=True, timeout=10, cwd=PAYLOAD,
                                env=clean_env(executable), check=False)
        if len(result.stdout) > MAX_RESULT:
            raise LabError("output_limit", "数值输出超限；请减少光源或场景复杂度。")
        if result.returncode != 0:
            raise LabError("engine_error", "光线引擎未正常完成；未生成替代结果。请检查运行环境及输入。")
        value = json.loads(result.stdout)
        if not isinstance(value, dict) or not isinstance(value.get("ok"), bool):
            raise LabError("engine_error", "引擎返回格式无效，无法报告仿真成功。")
        value["version"] = VERSION
        return value
    except LabError as exc:
        return failure(exc.code, exc.message)
    except subprocess.TimeoutExpired:
        return failure("time_limit", "仿真超过 10 秒限制，已结束本次引擎进程；没有完成结果。")
    except (OSError, ValueError, TypeError, UnicodeError):
        return failure("invalid_input", "场景或运行环境无效；请检查 JSON、数值和 Node.js 路径。")


def workspace_path(raw):
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        raise LabError("invalid_workspace", "请选择已存在的专用工作目录绝对路径。")
    path = Path(os.path.abspath(raw))
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise LabError("unsafe_path", "工作目录及父目录不能是符号链接。")
    if not path.is_dir():
        raise LabError("invalid_workspace", "专用工作目录不存在或不是目录；不会自动选用其他目录。")
    return path


def state_dir(workspace, create=False):
    path = workspace / ".offline-optics-lab"
    if create:
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise LabError("unsafe_path", "状态目录不能是链接或普通文件。")
    if path.exists() and (path.stat().st_mode & 0o077 or path.stat().st_uid != os.getuid()):
        raise LabError("unsafe_permissions", "状态目录所有者或权限不符；请选择新的专用工作目录。")
    return path


def read_json(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BODY or info.st_uid != os.getuid():
            raise LabError("invalid_state", "状态文件类型、所有者或大小无效。")
        try:
            value = json.load(stream)
        except (ValueError, UnicodeError):
            raise LabError("invalid_state", "状态文件损坏；不会自动覆盖或删除。")
        if not isinstance(value, dict):
            raise LabError("invalid_state", "状态文件不是对象；原文件保留。")
        return value


def atomic_json(path, value):
    read_json(path)  # Preserve corrupt/symlink/special existing records.
    temp = path.with_name(".tmp-" + secrets.token_hex(12))
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@contextlib.contextmanager
def launch_lock(root):
    fd = os.open(root / ".launch.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise LabError("invalid_state", "锁文件类型或所有者无效。")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def checked_meta(root):
    meta = read_json(root / "session.json")
    if meta is None:
        return None
    if meta.get("plugin") != PLUGIN or meta.get("version") != VERSION or meta.get("runtime_id") != runtime_id():
        raise LabError("foreign_session", "此目录会话属于另一个插件安装位置或版本。原记录和服务保留；请为当前安装选择新的专用目录。")
    if type(meta.get("port")) is not int or not 1024 <= meta["port"] <= 65535 or not re.fullmatch(r"[A-Za-z0-9_-]{32,80}", str(meta.get("token", ""))) or not re.fullmatch(r"[a-f0-9]{24}", str(meta.get("session_id", ""))):
        raise LabError("invalid_state", "会话记录字段无效；原记录保留。")
    return meta


def contact(meta, endpoint="health", post=False):
    if meta is None:
        return None
    conn = http.client.HTTPConnection("127.0.0.1", meta["port"], timeout=2)
    try:
        conn.request("POST" if post else "GET", "/" + meta["token"] + "/api/" + endpoint,
                     body=b"{}" if post else None, headers={"Content-Type": "application/json"} if post else {})
        response = conn.getresponse()
        value = json.loads(response.read(MAX_BODY))
        if response.status == 200 and isinstance(value, dict) and value.get("session_id") == meta["session_id"] and value.get("runtime_id") == meta["runtime_id"] and value.get("plugin") == PLUGIN and value.get("version") == VERSION:
            return value
    except (OSError, ValueError, http.client.HTTPException):
        pass
    finally:
        conn.close()
    return None


def status(root):
    meta = checked_meta(root)
    live = contact(meta)
    if live:
        return {**live, "url": f"http://127.0.0.1:{meta['port']}/{meta['token']}/"}
    return {"ok": True, "version": VERSION, "running": False, "message": "此工作目录没有可验证的运行会话。"}


def local_lab(inputs):
    try:
        if not isinstance(inputs, dict) or set(inputs) - {"workspace", "action", "confirmed", "node_path"}:
            raise LabError("invalid_input", "参数必须包含 workspace、action；可选 confirmed、node_path。")
        action = inputs.get("action")
        if action not in ("start", "status", "stop"):
            raise LabError("invalid_action", "action 只能是 start、status 或 stop。")
        work = workspace_path(inputs.get("workspace"))
        if action != "status" and inputs.get("confirmed") is not True:
            raise LabError("confirmation_required", "启动或关闭服务须先获用户明确授权，随后设置 confirmed=true。")
        root = state_dir(work, create=action == "start")
        if action == "status" or not root.exists():
            return status(root)
        with launch_lock(root):
            live = status(root)
            if action == "stop":
                if not live["running"]:
                    return live
                meta = checked_meta(root)
                if not contact(meta, "stop", True):
                    raise LabError("stop_failed", "未能确认关闭请求；不会按记录中的进程号结束进程。")
                for _ in range(40):
                    if contact(meta) is None:
                        return {"ok": True, "version": VERSION, "running": False, "session_id": meta["session_id"], "message": "已确认本插件会话停止；保存场景仍保留。"}
                    time.sleep(.1)
                raise LabError("stop_pending", "已请求关闭但仍有响应；请稍后查询。")
            if live["running"]:
                return {**live, "reused": True}
            node = select_node(inputs.get("node_path"))
            process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--serve", str(work), node],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       start_new_session=True, close_fds=True, env=clean_env(node))
            threading.Thread(target=process.wait, daemon=True).start()
            for _ in range(60):
                time.sleep(.1)
                live = status(root)
                if live["running"]:
                    return {**live, "reused": False, "message": "请在独立浏览器打开实际返回的完整地址；空闲30分钟后关闭。地址含本机凭据，截图请隐藏地址栏。"}
                if process.poll() is not None:
                    break
            raise LabError("start_failed", "服务未成功启动；未调用模型或外网。")
    except LabError as exc:
        return failure(exc.code, exc.message)
    except (OSError, ValueError, TypeError):
        return failure("filesystem_error", "文件系统操作失败；请检查目录和权限，原记录保留。")


def serve(work, node):
    root = state_dir(work, True)
    token, session_id = secrets.token_urlsafe(32), secrets.token_hex(12)
    identity = runtime_id()
    prefix, saved = "/" + token + "/", root / "scene.json"
    guard, solve_guard = threading.Lock(), threading.Lock()
    last_access = [time.monotonic()]
    health = {"ok": True, "version": VERSION, "plugin": PLUGIN, "running": True, "session_id": session_id, "runtime_id": identity}

    class Handler(BaseHTTPRequestHandler):
        server_version = "OfflineOpticsLab"
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass

        def send(self, value, code=200, content_type="application/json; charset=utf-8"):
            data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(code)
            for key, val in {"Content-Type": content_type, "Content-Length": str(len(data)), "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data: blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"}.items():
                self.send_header(key, val)
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def route(self):
            authority = f"127.0.0.1:{self.server.server_port}"
            if self.client_address[0] != "127.0.0.1" or self.headers.get("Host") != authority or self.headers.get("Origin") not in (None, "http://" + authority):
                self.send(failure("forbidden", "拒绝非本机或跨站访问。"), 403)
                return None
            if not self.path.startswith(prefix):
                self.send(failure("not_found", "地址无效或缺少本机会话凭据。"), 404)
                return None
            last_access[0] = time.monotonic()
            return self.path[len(prefix):]

        def do_GET(self):
            route = self.route()
            if route is None:
                return
            try:
                if route == "api/health":
                    return self.send(health)
                if route == "api/examples":
                    return self.send({"ok": True, "version": VERSION, "examples": json.loads((PAYLOAD / "engine/examples.json").read_text())})
                if route == "api/state":
                    with guard:
                        record = read_json(saved)
                    if record and (record.get("version") != VERSION or "scene" not in record):
                        raise LabError("invalid_state", "保存的场景格式或版本不符。")
                    return self.send({"ok": True, "version": VERSION, "scene": record.get("scene") if record else None})
                if route == "notices.md":
                    return self.send((PAYLOAD / "THIRD_PARTY_NOTICES.md").read_bytes(), content_type="text/plain; charset=utf-8")
                if route == "licenses.txt":
                    return self.send((PAYLOAD / "licenses/ray-optics/LICENSE").read_bytes(), content_type="text/plain; charset=utf-8")
                files = {"": ("index.html", "text/html"), "app.js": ("app.js", "text/javascript"), "style.css": ("style.css", "text/css")}
                if route not in files:
                    return self.send(failure("not_found", "资源不存在。"), 404)
                name, mime = files[route]
                return self.send((PAYLOAD / "web" / name).read_bytes(), content_type=mime + "; charset=utf-8")
            except (LabError, OSError, ValueError, AttributeError):
                self.send(failure("invalid_state", "保存场景或界面资源不可读；原记录保留。"), 400)

        def do_POST(self):
            route = self.route()
            if route is None:
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 <= length <= MAX_BODY or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    return self.send(failure("invalid_request", "请求须为不超过128 KiB的JSON。"), 400)
                body = json.loads(self.rfile.read(length))
                if route == "api/stop":
                    if body != {}:
                        return self.send(failure("invalid_input", "关闭请求格式无效。"), 400)
                    self.send({**health, "running": False})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                if route not in ("api/simulate", "api/state", "api/validate"):
                    return self.send(failure("not_found", "操作不存在。"), 404)
                if not isinstance(body, dict) or set(body) != {"scene"}:
                    return self.send(failure("invalid_input", "请求只能包含scene。"), 400)
                if not solve_guard.acquire(False):
                    return self.send(failure("busy", "已有计算正在运行，请稍后重试。"), 409)
                try:
                    result = engine_call(body, node, validate=route != "api/simulate")
                finally:
                    solve_guard.release()
                if not result.get("ok") or route != "api/state":
                    return self.send(result)
                with guard:
                    atomic_json(saved, {"version": VERSION, "scene": result["scene"]})
                return self.send({"ok": True, "version": VERSION, "message": "场景已保存；仅更新当前专用目录中的插件场景记录。", "sha256": hashlib.sha256(saved.read_bytes()).hexdigest()})
            except (ValueError, TypeError, UnicodeError):
                self.send(failure("invalid_json", "JSON格式无效。"), 400)
            except (LabError, OSError):
                self.send(failure("save_failed", "保存失败；原有记录未主动清除。"), 400)

    class LimitedServer(ThreadingHTTPServer):
        daemon_threads = True
        def __init__(self, *args):
            self.slots = threading.BoundedSemaphore(8)
            super().__init__(*args)
        def process_request(self, request, client_address):
            if not self.slots.acquire(False):
                self.shutdown_request(request)
                return
            try:
                super().process_request(request, client_address)
            except BaseException:
                self.slots.release()
                raise
        def process_request_thread(self, request, client_address):
            try:
                super().process_request_thread(request, client_address)
            finally:
                self.slots.release()

    server = LimitedServer(("127.0.0.1", 0), Handler)
    atomic_json(root / "session.json", {"port": server.server_port, "token": token, "session_id": session_id,
                                       "plugin": PLUGIN, "version": VERSION, "runtime_id": identity})
    def idle_watch():
        while time.monotonic() - last_access[0] < IDLE_SECONDS:
            time.sleep(10)
        server.shutdown()
    threading.Thread(target=idle_watch, daemon=True).start()
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        server.server_close()


if __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] == "--serve":
    serve(workspace_path(sys.argv[2]), select_node(sys.argv[3]))
