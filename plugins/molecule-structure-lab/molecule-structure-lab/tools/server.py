"""只读本机静态服务，具有不可猜路径、严格 Host 校验及空闲过期。"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.1"
ASSETS = {
    "web/index.html": "text/html; charset=utf-8",
    "web/app.js": "text/javascript; charset=utf-8",
    "web/styles.css": "text/css; charset=utf-8",
    "web/worker.js": "text/javascript; charset=utf-8",
    "engine/core.js": "text/javascript; charset=utf-8",
    "vendor/rdkit/RDKit_minimal.js": "text/javascript; charset=utf-8",
    "vendor/rdkit/RDKit_minimal.wasm": "application/wasm",
}


class WorkbenchServer(HTTPServer):
    allow_reuse_address = False
    timeout = 1


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # URLs include the capability token; do not write them to logs.

    def reply(self, status, body, content_type="application/json; charset=utf-8", worker=False):
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        # Unmodified Emscripten embind builds JS wrappers with new Function in the worker only.
        # No user text is evaluated; the page and all other routes keep the stricter policy.
        script_policy = "'self' 'unsafe-eval'" if worker else "'self' 'wasm-unsafe-eval'"
        self.send_header("Content-Security-Policy", f"default-src 'none'; script-src {script_policy}; worker-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True

    def route(self):
        expected_host = f"127.0.0.1:{self.server.server_port}"
        parsed = urlsplit(self.path)
        prefix = "/" + self.server.token + "/"
        # A click from WorkSwarm crosses ports (and sometimes hostnames). Admit
        # only a user-activated top-level GET of the capability-protected entry
        # page. Assets and service control retain the same-origin restriction.
        entry_navigation = (
            self.command == "GET" and self.path == prefix + "web/index.html"
            and self.headers.get("Origin") is None
            and self.headers.get("Sec-Fetch-Site") in {"same-site", "cross-site"}
            and self.headers.get("Sec-Fetch-Mode") == "navigate"
            and self.headers.get("Sec-Fetch-Dest") == "document"
            and self.headers.get("Sec-Fetch-User") == "?1"
        )
        if (self.headers.get_all("Host") != [expected_host] or
                self.headers.get("Origin") not in {None, "http://" + expected_host} or
                (self.headers.get("Sec-Fetch-Site") not in {None, "none", "same-origin"}
                 and not entry_navigation)):
            self.reply(403, {"error": "仅接受本机同源请求。"})
            return None
        # Never decode a path into filenames: encoded traversal and malformed routes stay rejected.
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not parsed.path.startswith(prefix):
            self.reply(404, {"error": "未找到插件资源。"})
            return None
        return parsed.path[len(prefix):]

    def do_GET(self):
        route = self.route()
        if route is None:
            return
        if route == "__health":
            self.server.last_activity = time.monotonic()
            self.reply(200, {"version": VERSION, "instance": self.server.instance, "running": True})
            return
        if route not in ASSETS:
            self.reply(404, {"error": "未找到插件资源。"})
            return
        path = ROOT / route
        try:
            if any(part.is_symlink() for part in [path, *path.parents]):
                raise OSError("链接不允许")
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 9000000:
                    raise OSError("资源不符合要求")
                body = stream.read(9000001)
            if len(body) > 9000000:
                raise OSError("资源过大")
        except OSError:
            self.reply(404, {"error": "插件资源不可用。"})
            return
        self.server.last_activity = time.monotonic()
        self.reply(200, body, ASSETS[route], worker=route == "web/worker.js")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        route = self.route()
        if route is None:
            return
        if route != "__stop" or self.headers.get("Content-Length", "0") != "0" or self.headers.get("Transfer-Encoding"):
            self.reply(405, {"error": "此服务不接收分子数据或文件写入。"})
            return
        self.reply(200, {"version": VERSION, "instance": self.server.instance, "running": False})
        self.server.stopping = True

    def setup(self):
        super().setup()
        self.connection.settimeout(3)


def main():
    raw = sys.stdin.buffer.read(4097)
    data = json.loads(raw)
    if (len(raw) > 4096 or not re.fullmatch(r"[0-9a-f]{64}", data.get("token", "")) or
            not re.fullmatch(r"[0-9a-f]{32}", data.get("instance", ""))):
        raise ValueError("运行参数无效")
    with WorkbenchServer(("127.0.0.1", 0), Handler) as server:
        server.token, server.instance = data["token"], data["instance"]
        server.stopping, server.last_activity = False, time.monotonic()
        print(json.dumps({"port": server.server_port}), flush=True)
        sys.stdout.close()
        while not server.stopping and time.monotonic() - server.last_activity < 1800:
            server.handle_request()


if __name__ == "__main__":
    main()
