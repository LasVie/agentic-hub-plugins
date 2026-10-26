"""仅回环的离线播放器；不调用外部服务或模型。"""
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import threading
import time
from urllib.parse import urlsplit

from library import Library, LibraryError, VERSION, atomic_json

PAYLOAD = Path(__file__).resolve().parents[1]


class Server(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    request_queue_size = 16


def run(config):
    root, state_dir = Path(config["root"]), Path(config["state_dir"])
    lock_fd = os.open(state_dir / "library.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    library = Library(root, state_dir / "playlists.json")
    token = secrets.token_urlsafe(32)
    prefix = "/" + token + "/"
    last = [time.monotonic()]
    slots = threading.BoundedSemaphore(8)
    page = (PAYLOAD / "assets/page.html").read_bytes()
    app = (PAYLOAD / "assets/app.js").read_bytes()
    license_text = (PAYLOAD / "licenses/dsh-music-player/LICENSE").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        server_version = "LocalMusic"
        sys_version = ""

        def log_message(self, *args):
            pass  # Never log capability URLs or file names.

        def send_error(self, code, message=None, explain=None):
            self.output({"ok": False, "version": VERSION, "message": "HTTP请求方法或格式无效。"}, code)

        def send_headers(self, status, mime, length, extra=None):
            self.send_response(status)
            for k, v in {"Content-Type": mime, "Content-Length": str(length),
                         "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                         "Referrer-Policy": "no-referrer", "Cross-Origin-Resource-Policy": "same-origin",
                         "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'unsafe-inline'; media-src 'self'; connect-src 'self'; img-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'", **(extra or {})}.items():
                self.send_header(k, v)
            self.end_headers()

        def output(self, value, status=200):
            data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.send_headers(status, "application/json; charset=utf-8", len(data))
            if self.command != "HEAD":
                self.wfile.write(data)

        def do_GET(self):
            self.handle_request()

        def do_HEAD(self):
            self.handle_request()

        def do_POST(self):
            self.handle_request()

        def handle_request(self):
            if not slots.acquire(blocking=False):
                self.output({"ok": False, "message": "请求过多，请稍后重试。"}, 429)
                return
            try:
                self.connection.settimeout(10)
                self.route()
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            except LibraryError as e:
                self.output({"ok": False, "version": VERSION, "code": e.code, "message": str(e)}, 400)
            except Exception:
                self.output({"ok": False, "version": VERSION, "message": "请求失败；未确认操作成功。"}, 500)
            finally:
                slots.release()

        def route(self):
            host = "127.0.0.1:" + str(self.server.server_port)
            origin = "http://" + host
            parsed = urlsplit(self.path)
            if parsed.query or not parsed.path.startswith(prefix):
                self.output({"ok": False, "message": "本地会话地址无效。"}, 404)
                return
            name = parsed.path[len(prefix):]
            navigation = (self.command == "GET" and name in ("", "license")
                          and self.headers_in("Sec-Fetch-Mode") == "navigate"
                          and self.headers_in("Sec-Fetch-Dest") == "document"
                          and self.headers_in("Origin") is None)
            if (self.headers_in("Host") != host or self.headers_in("Origin") not in (None, origin)
                    or (self.headers_in("Sec-Fetch-Site") == "cross-site" and not navigation)):
                self.output({"ok": False, "message": "拒绝跨站或非回环主机请求。"}, 403)
                return
            last[0] = time.monotonic()
            if self.command in ("GET", "HEAD"):
                static = {"": (page, "text/html; charset=utf-8"), "app.js": (app, "text/javascript; charset=utf-8"), "license": (license_text, "text/plain; charset=utf-8")}
                if name in static:
                    data, mime = static[name]
                    self.send_headers(200, mime, len(data))
                    if self.command != "HEAD":
                        self.wfile.write(data)
                elif name == "api/library":
                    self.output(library.manifest())
                elif name == "api/health":
                    self.output({"ok": True, "version": VERSION, "plugin": "local-music-library", "session_id": config["session_id"], "root_key": config["root_key"]})
                elif name.startswith("audio/"):
                    self.audio(name[6:])
                else:
                    self.output({"ok": False, "message": "没有这个本地资源。"}, 404)
                return
            if not self.headers_in("Content-Type", "").startswith("application/json") or self.headers_in("Transfer-Encoding"):
                self.output({"ok": False, "message": "仅接受有限长度的 JSON 请求。"}, 415)
                return
            try:
                length = int(self.headers_in("Content-Length", "-1"))
                if not 0 <= length <= 65536:
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError()
            except (ValueError, UnicodeError):
                self.output({"ok": False, "message": "JSON 内容无效或过大。"}, 400)
                return
            if name == "api/playlist" and set(body) == {"name", "tracks"}:
                self.output(library.save_playlist(body["name"], body["tracks"]))
            elif name == "api/remove-playlist" and set(body) == {"name"}:
                self.output(library.remove_playlist(body["name"]))
            elif name == "api/resume":
                self.output(library.save_resume(body))
            elif name == "api/rescan" and not body:
                self.output(library.scan())
            elif name == "api/stop" and not body:
                self.output({"ok": True, "version": VERSION, "message": "本地服务正在关闭，歌单已保留。"})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.output({"ok": False, "message": "操作或参数无效。"}, 400)

        def headers_in(self, key, default=None):
            # BaseHTTPRequestHandler stores incoming headers on the instance.
            return self.__dict__["headers"].get(key, default)

        def audio(self, tid):
            from library import parse_range
            fd, size, mime = library.open_track(tid)
            with os.fdopen(fd, "rb") as f:
                try:
                    start, end, status = parse_range(self.headers_in("Range"), size)
                except LibraryError:
                    self.send_headers(416, "text/plain; charset=utf-8", 0, {"Content-Range": "bytes */" + str(size)})
                    return
                extra = {"Accept-Ranges": "bytes"}
                if status == 206:
                    extra["Content-Range"] = f"bytes {start}-{end}/{size}"
                length = end - start + 1
                self.send_headers(status, mime, length, extra)
                if self.command == "HEAD":
                    return
                f.seek(start)
                while length:
                    block = f.read(min(length, 64 * 1024))
                    if not block:
                        break
                    self.wfile.write(block)
                    length -= len(block)

    server = Server(("127.0.0.1", 0), Handler)
    info = {"version": VERSION, "session_id": config["session_id"], "root_key": config["root_key"],
            "status": "running", "url": f"http://127.0.0.1:{server.server_port}{prefix}", "pid": os.getpid()}
    atomic_json(state_dir / "session.json", info)

    def watchdog():
        while not finished.wait(15):
            if time.monotonic() - last[0] > 1800:
                server.shutdown()
                break

    finished = threading.Event()
    threading.Thread(target=watchdog, daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        finished.set()
        server.server_close()
        library.close()
        atomic_json(state_dir / "session.json", {**info, "status": "stopped"})
        os.close(lock_fd)


if __name__ == "__main__":
    try:
        config = json.loads(sys.stdin.readline(16384))
        run(config)
    except Exception:
        print("本地音乐库服务未启动；请检查目录、状态或是否已有会话。", file=sys.stderr)
        raise SystemExit(2)
