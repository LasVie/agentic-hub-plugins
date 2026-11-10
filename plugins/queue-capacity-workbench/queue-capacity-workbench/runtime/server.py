"""Private loopback HTTP workbench; fixed assets and one cancellable engine job."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
import re
import socket
import stat
import sys
import threading
import time
from urllib.parse import urlsplit

import runtime

ASSETS = {"index.html": "web/index.html", "app.js": "web/app.js", "style.css": "web/style.css",
          "licenses.txt": "THIRD_PARTY_NOTICES.md", "licenses/simpy/LICENSE": "licenses/simpy/LICENSE",
          "licenses/simpy/AUTHORS.rst": "licenses/simpy/AUTHORS.rst"}
IDLE_SECONDS = 1800


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False
    request_queue_size = 8

    def __init__(self, config):
        self.token = config["token"]
        self.session_id = config["session_id"]
        self.stopping = threading.Event()
        self.activity = time.monotonic()
        self.job_lock = threading.Lock()
        self.active_job = None
        self.seen_jobs = set()
        self.cancelled_jobs = set()
        self.seen_order = []
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(("127.0.0.1", 0), Handler)
        self.timeout = 0.5

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
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

    def handle_error(self, request, client_address):
        # HTTP paths contain access tokens; never log request details/tracebacks.
        pass

    def information(self):
        with self.job_lock:
            busy = self.active_job is not None
        return {"ok": True, "plugin_id": runtime.PLUGIN_ID, "version": runtime.VERSION,
                "session_id": self.session_id, "running": not self.stopping.is_set(), "busy": busy}

    def stop(self):
        with self.job_lock:
            if self.active_job:
                self.active_job[1].set()
            self.stopping.set()

    def remember_job(self, request_id, *, cancelled=False):
        """Called with job_lock held; cancellation also fences a late POST."""
        if request_id not in self.seen_jobs:
            self.seen_jobs.add(request_id)
            self.seen_order.append(request_id)
        if cancelled:
            self.cancelled_jobs.add(request_id)
        if len(self.seen_order) > 256:
            expired = self.seen_order.pop(0)
            self.seen_jobs.discard(expired)
            self.cancelled_jobs.discard(expired)


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalWorkbench"
    sys_version = ""

    def setup(self):
        self.request.settimeout(5)
        super().setup()

    def log_message(self, *_args):
        pass

    def send_error(self, code, message=None, explain=None):
        self.send_json(code, runtime.failure("请求无法处理。"))

    def send_bytes(self, status, data: bytes, media_type):
        try:
            self.send_response(status)
            self.send_header("Content-Type", media_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; worker-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(data)
        except (OSError, ValueError):
            # A disconnected browser cannot cancel a different or later job.
            pass

    def send_json(self, status, result):
        data = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
        self.send_bytes(status, data, "application/json; charset=utf-8")

    def route(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get_all("Host") != [f"127.0.0.1:{self.server.server_port}"]:
            self.send_json(403, runtime.failure("仅接受本机工作台地址。"))
            return None
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            self.send_json(404, runtime.failure("工作台地址无效。"))
            return None
        prefix = f"/{self.server.token}/"
        if (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
                or not parsed.path.startswith(prefix) or "%" in parsed.path or "\\" in parsed.path):
            self.send_json(404, runtime.failure("工作台地址无效或已失效。"))
            return None
        route = parsed.path[len(prefix):]
        origins = self.headers.get_all("Origin")
        if origins is not None and origins != [origin]:
            self.send_json(403, runtime.failure("拒绝来自其他页面的请求。"))
            return None
        site = self.headers.get("Sec-Fetch-Site")
        # A human may open a WorkSwarm link in another tab. Only that top-level
        # user navigation is exempt; APIs/assets remain same-origin.
        entry_navigation = (self.command == "GET" and route == "index.html" and origins is None
                            and self.headers.get("Sec-Fetch-Mode") == "navigate"
                            and self.headers.get("Sec-Fetch-Dest") == "document"
                            and self.headers.get("Sec-Fetch-User") == "?1")
        if site not in (None, "none", "same-origin") and not entry_navigation:
            self.send_json(403, runtime.failure("拒绝跨站访问工作台。"))
            return None
        self.server.activity = time.monotonic()
        return route

    def do_GET(self):
        route = self.route()
        if route is None:
            return
        if route in {"api/health", "api/session"}:
            self.send_json(200, self.server.information())
            return
        relative = ASSETS.get(route)
        if relative is None:
            self.send_json(404, runtime.failure("未找到工作台文件。"))
            return
        path = runtime.ROOT / relative
        try:
            if any(parent.is_symlink() for parent in (path, *path.parents)):
                raise ValueError("symlink")
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                info = os.fstat(descriptor)
                if not stat.S_ISREG(info.st_mode) or info.st_size > 2 * 1024 * 1024:
                    raise ValueError("asset")
                data = os.read(descriptor, 2 * 1024 * 1024 + 1)
            finally:
                os.close(descriptor)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("asset size")
        except (OSError, ValueError):
            self.send_json(404, runtime.failure("工作台文件不可读取。"))
            return
        media_type = mimetypes.guess_type(route)[0] or "text/plain"
        if route.endswith((".js", ".mjs")):
            media_type = "text/javascript"
        if media_type.startswith("text/") or route.endswith(".js"):
            media_type += "; charset=utf-8"
        self.send_bytes(200, data, media_type)

    def body(self):
        lengths = self.headers.get_all("Content-Length")
        if self.headers.get_all("Transfer-Encoding") or not lengths or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
            raise runtime.WorkbenchError("请求必须包含有效的 Content-Length。")
        length = int(lengths[0])
        if length > runtime.MAX_INPUT + 1024:
            raise runtime.WorkbenchError("请求超过 256 KiB 上限。")
        if self.headers.get_all("Content-Type") not in (["application/json"], ["application/json; charset=utf-8"]):
            raise runtime.WorkbenchError("请求必须使用 application/json。")
        data = self.rfile.read(length)
        if len(data) != length:
            raise runtime.WorkbenchError("请求内容不完整。")
        try:
            result = runtime.strict_json(data)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise runtime.WorkbenchError("请求 JSON 无效或包含重复字段。") from exc
        if not isinstance(result, dict):
            raise runtime.WorkbenchError("请求必须是 JSON 对象。")
        return result

    def do_POST(self):
        route = self.route()
        if route is None:
            return
        if route not in {"api/calculate", "api/cancel", "api/stop"}:
            self.send_json(404, runtime.failure("未找到工作台操作。"))
            return
        try:
            body = self.body()
            if route == "api/stop":
                if body:
                    raise runtime.WorkbenchError("停止请求必须是空对象。")
                # Finish the authenticated acknowledgement before the main
                # thread exits; daemon HTTP workers must not lose its body.
                self.send_json(200, {**self.server.information(), "running": False})
                self.server.stop()
                return
            request_id = body.get("request_id")
            if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request_id):
                raise runtime.WorkbenchError("request_id 必须是 1 至 64 位字母、数字、下划线或连字符。")
            if route == "api/cancel":
                if set(body) != {"request_id"}:
                    raise runtime.WorkbenchError("取消请求仅接受 request_id。")
                with self.server.job_lock:
                    matched = bool(self.server.active_job and self.server.active_job[0] == request_id)
                    if matched:
                        self.server.active_job[1].set()
                    self.server.remember_job(request_id, cancelled=True)
                self.send_json(200, {"ok": True, "version": runtime.VERSION, "request_id": request_id,
                                     "cancelled": matched, "cancellation_recorded": True})
                return
            if set(body) != {"request_id", "project"} or not isinstance(body["project"], dict):
                raise runtime.WorkbenchError("计算请求仅接受 request_id 和 project 对象。")
            cancelled = threading.Event()
            with self.server.job_lock:
                if self.server.stopping.is_set():
                    self.send_json(409, runtime.failure("工作台正在关闭。", request_id=request_id))
                    return
                if request_id in self.server.cancelled_jobs:
                    self.send_json(409, runtime.failure("本次计算已取消，请为新计算生成新标识。", cancelled=True, request_id=request_id))
                    return
                if self.server.active_job is not None:
                    self.send_json(409, runtime.failure("已有计算正在运行。", busy=True, request_id=request_id))
                    return
                if request_id in self.server.seen_jobs:
                    self.send_json(409, runtime.failure("request_id 已使用，请为新计算生成新标识。", request_id=request_id))
                    return
                self.server.active_job = (request_id, cancelled)
                self.server.remember_job(request_id)
            try:
                result = runtime.run_engine(body["project"], cancelled)
                self.send_json(200, {**result, "request_id": request_id})
            finally:
                with self.server.job_lock:
                    if self.server.active_job and self.server.active_job[0] == request_id:
                        self.server.active_job = None
                self.server.activity = time.monotonic()
        except runtime.WorkbenchError as exc:
            self.send_json(400, runtime.failure(str(exc)))
        except (OSError, ValueError, socket.timeout):
            self.send_json(400, runtime.failure("请求读取失败。"))


def main():
    data = sys.stdin.buffer.read(4097)
    if len(data) > 4096:
        raise ValueError("invalid startup")
    config = runtime.strict_json(data)
    if (not isinstance(config, dict) or set(config) != {"token", "session_id"}
            or not isinstance(config["token"], str) or not re.fullmatch(r"[0-9a-f]{64}", config["token"])
            or not isinstance(config["session_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", config["session_id"])):
        raise ValueError("invalid startup")
    server = WorkbenchServer(config)
    print(json.dumps({"ok": True, "port": server.server_port}), flush=True)
    sys.stdout.close()
    try:
        while not server.stopping.is_set():
            server.handle_request()
            with server.job_lock:
                idle = server.active_job is None
            if idle and time.monotonic() - server.activity > IDLE_SECONDS:
                server.stop()
    finally:
        server.stop()
        server.server_close()
        # Let an active bounded engine job observe cancellation and reap its own
        # child; never leave a Python calculation behind when the UI closes.
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            with server.job_lock:
                if server.active_job is None:
                    break
            time.sleep(0.02)


if __name__ == "__main__":
    main()
