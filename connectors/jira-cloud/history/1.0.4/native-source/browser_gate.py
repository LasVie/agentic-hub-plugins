"""Route the official Jira CLI's authorization page to the active browser."""

import html
import os
import re
import secrets
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


class JiraLoginError(Exception):
    pass


def is_atlassian_authorization(value):
    try:
        url = urlsplit(value)
        return (
            not any(char in value for char in "\r\n\t")
            and url.scheme == "https"
            and url.netloc == "auth.atlassian.com"
            and url.path == "/authorize"
            and bool(url.query)
        )
    except ValueError:
        return False


def write_browser_helper(folder):
    # This private PATH entry applies only to the official ACLI subprocess.
    # The vendor continues to generate OAuth state and handle all callbacks.
    script = """#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

for value in sys.argv[1:]:
    url = urlsplit(value)
    if url.scheme == 'https' and url.netloc == 'auth.atlassian.com' and url.path == '/authorize' and url.query:
        target = Path(__file__).with_name('authorization-url')
        temporary = target.with_suffix('.pending')
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            output.write(value)
        temporary.replace(target)
        sys.exit(0)
sys.exit(1)
"""
    for name in ("open", "xdg-open"):
        helper = folder / name
        helper.write_text(script, encoding="utf-8")
        helper.chmod(0o700)


def site_options(output):
    text = re.sub(rb"\x1b\[[0-?]*[ -/]*[@-~]", b"", output).decode("utf-8", errors="replace")
    _, found, prompt = text.rpartition("Select the site to login")
    if not found or not re.search(r"Enter a number between|There is only one option available", prompt):
        return {}
    return dict(re.findall(
        r"^\s*([1-9][0-9]*)\. (?:https://)?([a-z0-9][a-z0-9-]*\.atlassian\.net)/?\s*$",
        prompt, flags=re.MULTILINE,
    ))


class VendorLogin:
    def __init__(self, command, env):
        self.process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.output = b""
        self.selected = False
        self.reader = threading.Thread(target=self.read_output, daemon=True)
        self.reader.start()

    def read_output(self):
        with self.process.stdout as output:
            while chunk := output.read1(4096):
                self.output = (self.output + chunk)[-128 * 1024:]

    def select(self, number):
        if self.selected or number not in site_options(self.output) or self.process.poll() is not None:
            return False
        self.process.stdin.write((number + "\n").encode("ascii"))
        self.process.stdin.flush()
        self.selected = True
        return True

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.reader.join(timeout=1)


def browser_login(command, environment, connected):
    route = "/" + secrets.token_urlsafe(24)
    login = None
    result = None
    result_seen = False

    with tempfile.TemporaryDirectory(prefix="workswarm-jira-oauth-") as directory:
        folder = Path(directory)
        link = folder / "authorization-url"
        env = dict(environment, ACLI_ACCESSIBLE="true")
        if os.name != "nt":
            write_browser_helper(folder)
            env["PATH"] = str(folder) + os.pathsep + env.get("PATH", "")

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, status, body):
                self.send_response(status)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(("<meta charset=utf-8><title>连接 Jira Cloud</title>" + body).encode())

            def valid_request(self):
                if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                    self.send_error(400)
                    return False
                if self.path != route:
                    self.send_error(404)
                    return False
                return True

            def render(self):
                nonlocal result_seen
                pending = '<meta http-equiv="refresh" content="2">'
                if result is not None:
                    result_seen = True
                    self.respond(200, "<p>Jira 已连接。请返回 WorkSwarm。</p>" if result == 0 else
                                 "<p>Jira 授权未完成。请返回 WorkSwarm 重新连接。</p>")
                    return
                choices = {} if login.selected else site_options(login.output)
                if choices:
                    options = "".join(f'<option value="{number}">{site}</option>' for number, site in choices.items())
                    self.respond(200, f'<p>选择要连接的 Jira Cloud 站点。</p><form method="post">'
                                 f'<select name="site" aria-label="Jira Cloud 站点">{options}</select> '
                                 '<button type="submit">连接所选站点</button></form>')
                    return
                if os.name != "nt" and not login.selected and link.is_file():
                    value = link.read_text(encoding="utf-8")
                    if is_atlassian_authorization(value):
                        url = html.escape(value, quote=True)
                        self.respond(200, pending + f'<p><a href="{url}" target="_blank" rel="noopener noreferrer">'
                                     '前往 Atlassian 授权</a></p><p>授权后回到此页选择 Jira 站点。</p>')
                        return
                message = "正在完成连接。" if login.selected else "正在等待 Atlassian 授权。"
                if os.name == "nt" and not login.selected:
                    message = "请在系统打开的 Atlassian 页面完成授权，然后回到此页。"
                self.respond(200, pending + f"<p>{message}</p>")

            def do_GET(self):
                nonlocal login
                if not self.valid_request():
                    return
                if login is None:
                    login = VendorLogin(command, env)
                self.render()

            def do_POST(self):
                if not self.valid_request():
                    return
                if self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
                    self.send_error(403)
                    return
                length = self.headers.get("Content-Length", "")
                if not length.isascii() or not length.isdecimal() or not 1 <= int(length) <= 64:
                    self.send_error(400)
                    return
                fields = parse_qs(self.rfile.read(int(length)).decode("ascii", errors="replace"))
                if login is None or not login.select(fields.get("site", [""])[0]):
                    self.send_error(409)
                    return
                self.send_response(303)
                self.send_header("Location", route)
                self.end_headers()

        try:
            with HTTPServer(("127.0.0.1", 0), Handler) as server:
                server.timeout = 0.5
                print(f"http://127.0.0.1:{server.server_port}{route}", flush=True)
                deadline = time.monotonic() + 165
                while (login is None or login.process.poll() is None) and time.monotonic() < deadline:
                    server.handle_request()
                if login is None or login.process.poll() is None:
                    raise JiraLoginError("等待 Jira 授权或选择站点超时，请在 WorkSwarm 重新连接。")
                result = 0 if login.process.returncode == 0 and connected() else 1
                display_deadline = time.monotonic() + 3
                while not result_seen and time.monotonic() < display_deadline:
                    server.handle_request()
                return result
        finally:
            if login is not None:
                login.close()
