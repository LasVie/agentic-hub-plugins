"""插件静态网页服务：随机本机端口、独立身份和空闲过期，无轨道要素上传接口。

沿用仓库 offline-pipe-network-workbench 1.0.0 的用户点击入口规则；仅服务本插件资源。
"""
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
VERSION = "1.0.0"
PLUGIN = "offline-satellite-orbit-workbench"
IDLE_SECONDS = 1800
MAX_ASSET_BYTES = 2 * 1024 * 1024
MIME = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
    ".tle": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
}
# The chosen engine consists of ordinary local ES modules. Dynamic JavaScript,
# WebAssembly, external resources and embedding are not enabled.
CSP = ("default-src 'none'; script-src 'self'; worker-src 'self'; "
       "style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; "
       "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")


def asset_type(route):
    # URL decoding is intentionally absent: no encoded filenames or traversal.
    parts = route.split("/")
    if (len(parts) < 2 or parts[0] != "web"
            or any(not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part) for part in parts)):
        return None
    return MIME.get(Path(parts[-1]).suffix)


def read_asset(route):
    """Open every path component relative to its checked parent, without links."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    directory = os.open(ROOT, flags | os.O_DIRECTORY)
    try:
        parts = route.split("/")
        for part in parts[:-1]:
            child = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(parts[-1], flags, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or info.st_size > MAX_ASSET_BYTES):
                raise OSError("资源不符合要求")
            body = stream.read(MAX_ASSET_BYTES + 1)
            if len(body) > MAX_ASSET_BYTES:
                raise OSError("资源过大")
            return body
    finally:
        os.close(directory)


class WorkbenchServer(HTTPServer):
    allow_reuse_address = False
    timeout = 1


class Handler(BaseHTTPRequestHandler):
    server_version = "SatelliteOrbitWorkbench"

    def log_message(self, *_):
        pass  # Do not log capability URLs or user content.

    def reply(self, status, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        for key, value in {
            "Content-Type": content_type, "Content-Length": str(len(body)),
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer", "Content-Security-Policy": CSP,
            "Connection": "close",
        }.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
        self.close_connection = True

    def route(self):
        if (len(self.path) > 2048 or sum(len(k) + len(v) for k, v in self.headers.items()) > 8192
                or len(list(self.headers)) > 40):
            self.reply(431, {"error": "请求过大；此服务只提供插件静态资源。"})
            return None
        expected_host = f"127.0.0.1:{self.server.server_port}"
        prefix = "/" + self.server.token + "/"
        protected = ("Host", "Origin", "Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-Dest",
                     "Sec-Fetch-User", "Content-Length", "X-Workbench-Instance")
        if any(len(self.headers.get_all(key, [])) > 1 for key in protected):
            self.reply(403, {"error": "拒绝含重复控制字段的请求。"})
            return None
        # Normal user-activated links from WorkSwarm cross ports/origins. Only
        # this entry document gets an exception, never scripts, fetches or control.
        entry_navigation = (
            self.command == "GET" and self.path == prefix + "web/index.html"
            and self.headers.get("Origin") is None
            and self.headers.get("Sec-Fetch-Site") in {"same-site", "cross-site"}
            and self.headers.get("Sec-Fetch-Mode") == "navigate"
            and self.headers.get("Sec-Fetch-Dest") == "document"
            and self.headers.get("Sec-Fetch-User") == "?1"
        )
        if (self.client_address[0] != "127.0.0.1" or self.headers.get_all("Host") != [expected_host]
                or self.headers.get("Origin") not in {None, "http://" + expected_host}
                or (self.headers.get("Sec-Fetch-Site") not in {None, "none", "same-origin"}
                    and not entry_navigation)):
            self.reply(403, {"error": "仅接受本机同源请求或用户点击的工作台入口。"})
            return None
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            parsed = None
        if (parsed is None or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
                or not parsed.path.startswith(prefix)):
            self.reply(404, {"error": "未找到插件资源。"})
            return None
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            self.reply(405, {"error": "此服务不接收轨道要素、文件内容或其他请求正文。"})
            return None
        return parsed.path[len(prefix):]

    def identity(self, running=True):
        return {"plugin": PLUGIN, "version": VERSION, "instance": self.server.instance, "running": running}

    def do_GET(self):
        route = self.route()
        if route is None:
            return
        if route == "__health":
            if self.headers.get("X-Workbench-Instance") != self.server.instance:
                self.reply(403, {"error": "会话身份不匹配。"})
                return
            self.reply(200, self.identity())
            return
        content_type = asset_type(route)
        if not content_type:
            self.reply(404, {"error": "未找到插件资源。"})
            return
        try:
            body = read_asset(route)
        except OSError:
            self.reply(404, {"error": "插件资源不可用。"})
            return
        self.server.last_activity = time.monotonic()
        self.reply(200, body, content_type)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        route = self.route()
        if route is None:
            return
        if route != "__stop":
            self.reply(405, {"error": "此服务没有轨道要素计算、上传或文件写入接口。"})
            return
        if self.headers.get("X-Workbench-Instance") != self.server.instance:
            self.reply(403, {"error": "会话身份不匹配；服务未停止。"})
            return
        self.reply(200, self.identity(running=False))
        self.server.stopping = True

    def setup(self):
        super().setup()
        self.connection.settimeout(3)


def main():
    raw = sys.stdin.buffer.read(4097)
    data = json.loads(raw)
    if (len(raw) > 4096 or not isinstance(data, dict) or set(data) != {"token", "instance"}
            or not isinstance(data.get("token"), str) or not re.fullmatch(r"[0-9a-f]{64}", data["token"])
            or not isinstance(data.get("instance"), str) or not re.fullmatch(r"[0-9a-f]{32}", data["instance"])):
        raise ValueError("运行参数无效")
    read_asset("web/index.html")
    with WorkbenchServer(("127.0.0.1", 0), Handler) as server:
        server.token, server.instance = data["token"], data["instance"]
        server.stopping, server.last_activity = False, time.monotonic()
        print(json.dumps({"port": server.server_port}), flush=True)
        sys.stdout.close()
        while not server.stopping and time.monotonic() - server.last_activity < IDLE_SECONDS:
            server.handle_request()


if __name__ == "__main__":
    main()
