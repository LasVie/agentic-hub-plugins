"""离线电路实验室：仅本机服务、显式保存和有界数值仿真。"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import threading
import time

VERSION = "1.0.0"
PAYLOAD = Path(__file__).resolve().parents[1]
MAX_BODY = 128 * 1024
IDLE_SECONDS = 1800
_spec = importlib.util.spec_from_file_location("circuit_lab_solver", Path(__file__).with_name("solver.py"))
_solver = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _solver
_spec.loader.exec_module(_solver)


class LabError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def failure(code, message):
    return {"ok": False, "version": VERSION, "error": {"code": code, "message": message}}


def workspace_path(raw):
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        raise LabError("invalid_workspace", "请选择已存在的专用工作目录绝对路径。")
    p = Path(os.path.abspath(raw))
    for q in [*reversed(p.parents), p]:
        if q.is_symlink():
            raise LabError("unsafe_path", "工作目录及其父目录不能是符号链接。")
    if not p.is_dir():
        raise LabError("invalid_workspace", "工作目录不存在或不是目录；请先明确选择并创建专用目录。")
    return p


def state_dir(workspace, create=False):
    p = workspace / ".offline-circuit-lab"
    if create:
        try:
            p.mkdir(mode=0o700)
        except FileExistsError:
            pass
    if p.is_symlink() or (p.exists() and not p.is_dir()):
        raise LabError("unsafe_path", "插件状态目录不能是链接或普通文件。")
    if p.exists() and p.stat().st_mode & 0o077:
        raise LabError("unsafe_permissions", "插件状态目录权限过宽；请为本插件选择新的专用工作目录。")
    return p


def read_json(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BODY:
            raise LabError("invalid_state", "状态文件类型或大小不符合要求。")
        try:
            return json.load(f)
        except (ValueError, UnicodeError):
            raise LabError("invalid_state", "状态文件损坏；不会自动覆盖或删除。")


def atomic_json(path, value):
    if path.is_symlink():
        raise LabError("unsafe_path", "拒绝覆盖符号链接。")
    if path.exists():
        read_json(path)  # Refuse corrupt or special files instead of destroying evidence.
    temp = path.with_name(".tmp-" + secrets.token_hex(12))
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@contextlib.contextmanager
def launch_lock(root):
    fd = os.open(root / ".launch.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise LabError("invalid_state", "锁文件类型无效。")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def contact(meta, endpoint="health", post=False):
    if not isinstance(meta, dict) or not isinstance(meta.get("port"), int) or not 1024 <= meta["port"] <= 65535:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,80}", str(meta.get("token", ""))):
        return None
    conn = http.client.HTTPConnection("127.0.0.1", meta["port"], timeout=2)
    try:
        conn.request("POST" if post else "GET", "/" + meta["token"] + "/api/" + endpoint,
                     body=b"{}" if post else None,
                     headers={"Content-Type": "application/json"} if post else {})
        res = conn.getresponse()
        value = json.loads(res.read(MAX_BODY))
        if res.status == 200 and value.get("session_id") == meta.get("session_id"):
            return value
    except (OSError, ValueError, http.client.HTTPException):
        return None
    finally:
        conn.close()
    return None


def status(root):
    meta = read_json(root / "session.json")
    live = contact(meta)
    if live:
        return {**live, "url": f"http://127.0.0.1:{meta['port']}/{meta['token']}/"}
    return {"ok": True, "version": VERSION, "running": False, "message": "此工作目录没有可验证的运行会话。"}


def local_lab(inputs):
    try:
        if not isinstance(inputs, dict) or set(inputs) - {"workspace", "action", "confirmed"}:
            raise LabError("invalid_input", "参数必须为包含 workspace、action 的对象。")
        action = inputs.get("action")
        if action not in ("start", "status", "stop"):
            raise LabError("invalid_action", "action 只能是 start、status 或 stop。")
        work = workspace_path(inputs.get("workspace"))
        if action != "status" and inputs.get("confirmed") is not True:
            raise LabError("confirmation_required", "启动或关闭服务前需要用户明确授权，随后设置 confirmed=true。")
        root = state_dir(work, create=action == "start")
        if action == "status" or not root.exists():
            return status(root)
        with launch_lock(root):
            live = status(root)
            if action == "stop":
                if not live["running"]:
                    return live
                meta = read_json(root / "session.json")
                reply = contact(meta, "stop", post=True)
                if not reply:
                    raise LabError("stop_failed", "未能确认服务关闭；不会按不可信进程号结束进程。")
                for _ in range(40):
                    if contact(meta) is None:
                        return {"ok": True, "version": VERSION, "running": False, "session_id": meta["session_id"], "message": "已确认本插件会话停止响应；保存的电路保留。"}
                    time.sleep(.1)
                raise LabError("stop_pending", "已请求关闭，但会话仍响应；请稍后查询，不会报告已经关闭。")
            if live["running"]:
                return {**live, "reused": True}
            # Only this plugin's own worker is launched; no host or dependency is altered.
            process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--serve", str(work)],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       start_new_session=True, close_fds=True)
            # Reap this owned child when it exits without keeping the caller alive.
            threading.Thread(target=process.wait, daemon=True).start()
            for _ in range(60):
                time.sleep(.1)
                live = status(root)
                if live["running"]:
                    return {**live, "reused": False, "message": "请在同一台电脑的独立浏览器标签页打开完整地址；空闲30分钟后自动关闭。地址含本机会话凭据，请勿分享。"}
                if process.poll() is not None:
                    break
            raise LabError("start_failed", "本机服务启动未成功；未调用模型或外网服务。")
    except LabError as exc:
        return failure(exc.code, exc.message)
    except (OSError, ValueError, TypeError):
        return failure("filesystem_error", "文件系统操作失败；请检查专用工作目录和权限。")


def simulate(inputs):
    if not isinstance(inputs, dict) or set(inputs) != {"circuit"}:
        return failure("invalid_input", "请提供唯一的 circuit 电路对象。")
    return _solver.simulate(inputs["circuit"])


def serve(work):
    root = state_dir(work, create=True)
    token, session_id = secrets.token_urlsafe(32), secrets.token_hex(12)
    prefix = "/" + token + "/"
    saved_path = root / "circuit.json"
    guard, solve_guard = threading.Lock(), threading.Lock()
    last_access = [time.monotonic()]

    class Handler(BaseHTTPRequestHandler):
        server_version = "CircuitLab"
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass

        def send(self, value, code=200, content_type="application/json; charset=utf-8"):
            data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def route(self):
            authority = f"127.0.0.1:{self.server.server_port}"
            if self.client_address[0] != "127.0.0.1" or self.headers.get("Host") != authority:
                self.send(failure("forbidden", "拒绝非本机会话访问。"), 403)
                return None
            if self.headers.get("Origin") not in (None, "http://" + authority):
                self.send(failure("forbidden", "拒绝跨站请求。"), 403)
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
                    return self.send({"ok": True, "version": VERSION, "running": True, "session_id": session_id})
                if route in ("api/state", "api/load"):
                    with guard:
                        saved = read_json(saved_path)
                    return self.send({"ok": True, "version": VERSION, "circuit": saved.get("circuit") if saved else None})
                if route == "license.txt":
                    return self.send((PAYLOAD / "licenses/circuitjs/LICENSE").read_bytes(), content_type="text/plain; charset=utf-8")
                files = {"": ("index.html", "text/html; charset=utf-8"), "app.js": ("app.js", "text/javascript; charset=utf-8"), "style.css": ("style.css", "text/css; charset=utf-8")}
                if route not in files:
                    return self.send(failure("not_found", "资源不存在。"), 404)
                name, mime = files[route]
                return self.send((PAYLOAD / "web" / name).read_bytes(), content_type=mime)
            except (LabError, OSError, ValueError, AttributeError):
                self.send(failure("invalid_state", "保存的电路或界面资源不可读；未覆盖文件。"), 400)

        def do_POST(self):
            route = self.route()
            if route is None:
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if length < 0 or length > MAX_BODY or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    return self.send(failure("invalid_request", "请求须为有界 JSON 对象。"), 400)
                body = json.loads(self.rfile.read(length))
                if route == "api/stop":
                    self.send({"ok": True, "version": VERSION, "running": False, "session_id": session_id})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                if route not in ("api/simulate", "api/save"):
                    return self.send(failure("not_found", "操作不存在。"), 404)
                if not solve_guard.acquire(blocking=False):
                    return self.send(failure("busy", "已有仿真正在运行，请稍后重试。"), 409)
                try:
                    result = simulate(body)
                finally:
                    solve_guard.release()
                if not result.get("ok") or route == "api/simulate":
                    return self.send(result)
                with guard:
                    atomic_json(saved_path, {"version": VERSION, "circuit": body["circuit"]})
                return self.send({"ok": True, "version": VERSION, "message": "电路已保存；仅更新当前工作目录内的插件电路记录。", "sha256": hashlib.sha256(saved_path.read_bytes()).hexdigest()})
            except (ValueError, TypeError, UnicodeError):
                self.send(failure("invalid_json", "JSON 格式无效。"), 400)
            except (LabError, OSError):
                self.send(failure("save_failed", "保存失败；请检查工作目录，原有记录未主动清除。"), 400)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    atomic_json(root / "session.json", {"port": server.server_port, "token": token, "session_id": session_id, "version": VERSION})
    def idle_watch():
        while time.monotonic() - last_access[0] < IDLE_SECONDS:
            time.sleep(10)
        server.shutdown()
    threading.Thread(target=idle_watch, daemon=True).start()
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        server.server_close()


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--serve":
    serve(workspace_path(sys.argv[2]))
