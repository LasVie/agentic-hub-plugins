"""Present an official OAuth link in the browser opened by the connector card."""

import html
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

SITE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.atlassian\.net)?")


class LoginPage:
    def __init__(self, service, hosts, *, needs_site=False):
        self.service = service
        self.hosts = hosts
        self.needs_site = needs_site
        self.site = ""
        self.url = ""
        self.result = None
        self.started = threading.Event()
        self.seen = threading.Event()
        self.route = "/" + secrets.token_urlsafe(24)

    def publish(self, value):
        try:
            parsed = urlsplit(value)
        except ValueError:
            return
        if (parsed.scheme == "https" and parsed.netloc in self.hosts
                and parsed.query and not any(char.isspace() for char in value)):
            self.url = value

    def __enter__(self):
        page = self

        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                self.request.settimeout(4)
                super().setup()

            def log_message(self, *_args):
                pass

            def valid(self):
                if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                    self.send_error(400)
                    return False
                if self.path != page.route:
                    self.send_error(404)
                    return False
                return True

            def respond(self, body):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "same-origin")
                self.end_headers()
                self.wfile.write((f'<meta charset="utf-8"><title>连接 {page.service}</title>' + body).encode())

            def do_GET(self):
                if not self.valid():
                    return
                if page.result is not None:
                    self.respond("<p>连接成功，请返回 WorkSwarm。</p>" if page.result
                                 else "<p>授权未完成。请返回 WorkSwarm 重试。</p>")
                    page.seen.set()
                elif page.url:
                    url = html.escape(page.url, quote=True)
                    codes = parse_qs(urlsplit(page.url).query).get("user_code", [])
                    code = f"<p>核对服务页面上的设备验证码为 <strong>{html.escape(codes[0])}</strong>。</p>" if codes else ""
                    self.respond(code + f'<p><a href="{url}" rel="noreferrer">前往 {page.service} 授权</a></p>')
                elif page.started.is_set():
                    self.respond('<meta http-equiv="refresh" content="2"><p>正在准备服务授权，请稍候。</p>')
                else:
                    site_input = ('<label>Atlassian 站点 <input name="site" placeholder="示例：example.atlassian.net" required></label> '
                                  if page.needs_site else '')
                    self.respond(f'<form method="post">{site_input}<button>开始连接 {page.service}</button></form>')

            def do_POST(self):
                if not self.valid():
                    return
                host = f"http://127.0.0.1:{self.server.server_port}"
                if self.headers.get("Origin") != host or page.started.is_set():
                    self.send_error(403)
                    return
                length = self.headers.get("Content-Length", "")
                if not length.isdecimal() or not 0 <= int(length) <= 160:
                    self.send_error(400)
                    return
                fields = parse_qs(self.rfile.read(int(length)).decode("ascii", errors="replace"))
                site = fields.get("site", [""])[0].strip().lower()
                if page.needs_site and not SITE.fullmatch(site):
                    self.respond('<p>请输入 Atlassian Cloud 站点名称或 atlassian.net 域名。</p><a href="">重试</a>')
                    return
                page.site = site.removesuffix(".atlassian.net")
                page.started.set()
                self.send_response(303)
                self.send_header("Location", page.route)
                self.end_headers()

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"http://127.0.0.1:{self.server.server_port}{self.route}", flush=True)
        return self

    def finish(self, result):
        self.result = result
        if not result:
            self.seen.wait(timeout=3)

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
