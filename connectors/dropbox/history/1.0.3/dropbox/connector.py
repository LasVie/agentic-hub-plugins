"""Dropbox API file reads and local desktop OAuth with PKCE."""

import argparse
import base64
import hashlib
import html
import hmac
import json
import os
import re
import secrets
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from http_client import ConnectorError, request

VERSION = "1.0.3"
REDIRECT = "http://localhost:53682/oauth/callback"
SCOPES = "account_info.read files.metadata.read files.content.read"
TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
DATA = Path(os.environ.get("JIUWENSWARM_DATA_DIR") or Path.home() / ".jiuwenswarm")
STATE = DATA / "connector-data" / "dropbox"
TOKEN = STATE / "session.json"


def app_key():
    value = os.environ.get("WORKSWARM_DROPBOX_APP_KEY")
    if not value:
        path = STATE / "app-key.txt"
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9_-]{5,128}", value):
        raise ConnectorError(f"请将 Dropbox 应用的 App key 写入 {STATE / 'app-key.txt'}，然后重试。")
    return value


def encoded(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def save(result, previous=None):
    access = result.get("access_token")
    if not isinstance(access, str) or not access:
        raise ConnectorError("Dropbox 未返回访问令牌。")
    refresh = result.get("refresh_token") or (previous or {}).get("refresh_token")
    expires = result.get("expires_in")
    if not isinstance(expires, (int, float)) or expires <= 0 or not refresh:
        raise ConnectorError("Dropbox 未返回有效的离线授权，请重新连接。")
    value = {
        "access_token": access, "refresh_token": refresh,
        "expires_at": time.time() + expires, "app_key": app_key(),
    }
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=STATE, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(TOKEN)
    finally:
        temporary.unlink(missing_ok=True)
    return value


def load():
    try:
        value = json.loads(TOKEN.read_text(encoding="utf-8"))
        if value["app_key"] != app_key() or not value["access_token"] or not value["refresh_token"]:
            return None
        float(value["expires_at"])
        return value
    except (OSError, ValueError, KeyError, TypeError, ConnectorError):
        return None


def bearer():
    value = load()
    if not value:
        raise ConnectorError("请先在 WorkSwarm 卡片上连接 Dropbox。")
    if float(value["expires_at"]) - time.time() <= 60:
        value = save(request(TOKEN_URL, form={
            "grant_type": "refresh_token", "refresh_token": value["refresh_token"],
            "client_id": value["app_key"],
        }), value)
    return {"Authorization": "Bearer " + value["access_token"]}


def exchange_code(code, key, verifier, redirect=None):
    form = {"grant_type": "authorization_code", "code": code,
            "client_id": key, "code_verifier": verifier}
    if redirect:
        form["redirect_uri"] = redirect
    token = request(TOKEN_URL, form=form)
    scopes = token.get("scope")
    if isinstance(scopes, str) and not set(SCOPES.split()) <= set(scopes.split()):
        raise ConnectorError("Dropbox 缺少所需的文件读取权限。")
    request("https://api.dropboxapi.com/2/users/get_current_account", body=None,
            headers={"Authorization": "Bearer " + token["access_token"]}, method="POST")
    save(token)


def login():
    key = app_key()
    verifier = encoded(secrets.token_bytes(48))
    state = secrets.token_urlsafe(32)
    challenge = encoded(hashlib.sha256(verifier.encode("ascii")).digest())
    origin = "http://127.0.0.1:53682"
    route = "/" + secrets.token_urlsafe(24)
    authorization = "https://www.dropbox.com/oauth2/authorize?"
    options = {
        "client_id": key, "response_type": "code", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
        "scope": SCOPES, "token_access_type": "offline",
    }
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def setup(self):
            self.request.settimeout(5)
            super().setup()

        def log_message(self, *_args):
            pass

        def respond(self, status, body):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "same-origin")
            self.end_headers()
            self.wfile.write(('<meta charset="utf-8"><title>连接 Dropbox</title>' + body).encode())

        def complete(self, code, redirect=None):
            try:
                if not code:
                    raise ConnectorError("Dropbox 授权已取消或拒绝。")
                exchange_code(code, key, verifier, redirect)
            except (ConnectorError, KeyError, TypeError, OSError, ValueError) as error:
                result["error"] = str(error) if isinstance(error, ConnectorError) else "无法完成 Dropbox 授权。"
            result["complete"] = True
            if "error" in result:
                self.respond(400, "<p>Dropbox 授权失败，请返回 WorkSwarm。</p>")
            else:
                self.respond(200, "<p>Dropbox 授权成功。请返回 WorkSwarm。</p>")

        def do_GET(self):
            target = urlsplit(self.path)
            host = self.headers.get("Host")
            if host == "127.0.0.1:53682" and not target.query:
                if self.path == route:
                    url = html.escape(authorization + urlencode(dict(options, redirect_uri=REDIRECT)), quote=True)
                    self.respond(200, f'<p><a href="{url}" rel="noreferrer">前往 Dropbox 授权</a></p>'
                                 f'<p><a href="{route}/code">回调不可用时，改用一次性授权码</a></p>')
                    return
                if self.path == route + "/code":
                    url = html.escape(authorization + urlencode(options), quote=True)
                    self.respond(200, f'<p><a href="{url}" target="_blank" rel="noopener noreferrer">'
                                 '前往 Dropbox 获取授权码</a></p><p>授权后回到此页填写 Dropbox 显示的一次性授权码。</p>'
                                 '<form method="post"><label>一次性授权码 <input type="password" name="code" '
                                 'required autocomplete="off" maxlength="1024"></label> <button>完成连接</button></form>')
                    return
            if host == "localhost:53682" and target.path == "/oauth/callback":
                params = parse_qs(target.query)
                if hmac.compare_digest(params.get("state", [""])[0], state):
                    self.complete(params.get("code", [""])[0] if "error" not in params else "", REDIRECT)
                    return
            self.send_error(400)

        def do_POST(self):
            if (self.headers.get("Host") != "127.0.0.1:53682" or self.headers.get("Origin") != origin
                    or self.path != route + "/code"):
                self.send_error(403)
                return
            length = self.headers.get("Content-Length", "")
            if not length.isascii() or not length.isdecimal() or not 1 <= int(length) <= 3500:
                self.send_error(400)
                return
            fields = parse_qs(self.rfile.read(int(length)).decode("ascii", errors="replace"))
            code = fields.get("code", [""])[0].strip()
            if not re.fullmatch(r"[!-~]{8,1024}", code):
                self.respond(400, '<p>请填写 Dropbox 显示的一次性授权码。</p><p><a href="">重试</a></p>')
                return
            self.complete(code)

    try:
        with HTTPServer(("127.0.0.1", 53682), Callback) as server:
            server.timeout = 1
            print(origin + route, flush=True)
            deadline = time.monotonic() + 300
            while "complete" not in result and time.monotonic() < deadline:
                server.handle_request()
    except OSError as error:
        raise ConnectorError("无法监听 Dropbox 回调端口 53682，请关闭占用该端口的程序后重试。") from error
    if "error" in result:
        raise ConnectorError(result["error"])
    if "complete" not in result:
        raise ConnectorError("Dropbox 授权超时，请从卡片重新连接。")
    return {"connected": True}


def api(path, body, headers):
    return request("https://api.dropboxapi.com/2/" + path, body=body, headers=headers)


def execute(args):
    if args.command == "prepare":
        return {"ready": True}
    if args.command == "version":
        return {"version": VERSION}
    if args.command == "status":
        token = load()
        if token:
            try:
                bearer()
            except ConnectorError:
                return {"connected": False}
        return {"connected": bool(token)}
    if args.command == "login":
        return login()
    if args.command == "logout":
        TOKEN.unlink(missing_ok=True)
        return {"connected": False}
    headers = bearer()
    if args.command == "list":
        if args.cursor:
            return api("files/list_folder/continue", {"cursor": args.cursor}, headers)
        if args.path and not args.path.startswith("/"):
            raise ConnectorError("文件夹路径必须以 / 开头。")
        return api("files/list_folder", {"path": args.path}, headers)
    if args.command == "search":
        if args.cursor:
            return api("files/search/continue_v2", {"cursor": args.cursor}, headers)
        if not args.query:
            raise ConnectorError("请输入要搜索的文件名关键字。")
        return api("files/search_v2", {"query": args.query, "options": {"filename_only": True, "max_results": 30}}, headers)
    if not (args.path.startswith("/") or args.path.startswith("id:")):
        raise ConnectorError("文件路径必须以 / 开头，也可使用 Dropbox 文件 ID。")
    if args.command == "metadata":
        return api("files/get_metadata", {"path": args.path}, headers)
    try:
        raw = request("https://content.dropboxapi.com/2/files/download", headers={
            **headers, "Dropbox-API-Arg": json.dumps({"path": args.path}, ensure_ascii=True),
        }, method="POST", raw=True)
        return {"path": args.path, "text": raw.decode("utf-8")}
    except UnicodeError as error:
        raise ConnectorError("此操作只读取 UTF-8 文本文件。") from error


def main():
    parser = argparse.ArgumentParser(description="读取 Dropbox 文件")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "version", "status", "login", "logout"):
        commands.add_parser(name)
    listing = commands.add_parser("list", help="列出文件夹")
    listing.add_argument("--path", default="")
    listing.add_argument("--cursor")
    search = commands.add_parser("search", help="搜索文件名")
    search.add_argument("--query")
    search.add_argument("--cursor")
    for name in ("read", "metadata"):
        commands.add_parser(name).add_argument("--path", required=True)
    try:
        result = execute(parser.parse_args())
    except (ConnectorError, OSError) as error:
        print(str(error) if isinstance(error, ConnectorError) else "无法读取或保存本地 Dropbox 配置。", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
