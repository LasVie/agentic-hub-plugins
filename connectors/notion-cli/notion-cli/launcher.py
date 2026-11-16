"""Run the pinned Notion CLI with connector-specific local credentials."""

from __future__ import annotations

import argparse
import hashlib
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from threading import Thread
from urllib.parse import urlsplit
from urllib.request import urlopen
from uuid import UUID, uuid4

NTN_VERSION = "0.23.30"
TARBALL_URL = f"https://registry.npmjs.org/ntn/-/ntn-{NTN_VERSION}.tgz"
TARBALL_SHA256 = "f466d18f58808d8ee58cd1f027035b14a0bdf29dffef66e83c59ce62c63b86e6"
BINARY_HASHES = {
    "darwin-arm64": "5bd2388d7d402cdf02b45e274124dcaff81c62e247930e82851b6cf46c2e43e9",
    "darwin-x64": "8e7f946c2576dab6ee95cf57859ebbf89574b7439a312e6ebb9fa49ebc738189",
    "linux-arm64": "291a4b1aae57a64a708c045a3199b326f3b93528c1c0e08e98db4f1e3afb1450",
    "linux-x64": "268d6ba68ccd01de6d319965c09dc441661af94b89956fb2230c8c5ae0dc9d71",
    "win32-x64": "b92feafa081949dc9f7521ff00fe52dc7c61e86ae3e8e0d9810e2fe492cff394",
}
API_VERSION = "2026-03-11"
MAX_DOWNLOAD = 40 * 1024 * 1024
PROFILE = re.compile(r"session-[a-f0-9]{32}\Z")
PAGE_ID = re.compile(r"(?:^|[-/])([a-fA-F0-9]{32}|[a-fA-F0-9-]{36})/?\Z")


class ConnectorError(Exception):
    """An error safe to show without exposing CLI output or credentials."""


def private_root():
    path = Path(os.environ.get("WORKSWARM_NOTION_CLI_HOME", Path.home() / ".local/share/agentic-hub/notion-cli"))
    if not path.is_absolute() or path.is_symlink():
        raise ConnectorError("连接器目录必须是本地绝对路径。")
    path = path.resolve()
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise ConnectorError("连接器目录必须位于代码仓库之外。")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt" and (path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077):
        raise ConnectorError("连接器目录必须由当前用户所有，权限须为 700。")
    return path


def binary_target():
    architecture = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64"}.get(
        platform.machine().lower(), platform.machine().lower()
    )
    target = f"{sys.platform}-{architecture}"
    if target not in BINARY_HASHES:
        raise ConnectorError("此系统或处理器尚无受支持的 Notion CLI 发行包。")
    return target


def binary_path(root):
    suffix = ".exe" if os.name == "nt" else ""
    return root / f"ntn-{NTN_VERSION}-{binary_target()}{suffix}"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def installed(root):
    path = binary_path(root)
    return path.is_file() and not path.is_symlink() and digest(path) == BINARY_HASHES[binary_target()]


def prepare(root):
    if installed(root):
        return
    target = binary_target()
    binary = binary_path(root)
    with tempfile.TemporaryDirectory(prefix="download-", dir=root) as temp:
        temp = Path(temp)
        archive = temp / "ntn.tgz"
        with urlopen(TARBALL_URL, timeout=30) as response, archive.open("wb") as output:
            remaining = MAX_DOWNLOAD
            while chunk := response.read(1024 * 1024):
                remaining -= len(chunk)
                if remaining < 0:
                    raise ConnectorError("Notion CLI 下载大小超出预期。")
                output.write(chunk)
        if digest(archive) != TARBALL_SHA256:
            raise ConnectorError("Notion CLI 发行包校验失败。")
        filename = "ntn.exe" if os.name == "nt" else "ntn"
        stage = temp / filename
        with tarfile.open(archive, "r:gz") as package:
            member = package.getmember(f"package/dist/ntn-{target}/{filename}")
            if not member.isfile():
                raise ConnectorError("Notion CLI 发行包缺少对应的可执行文件。")
            with package.extractfile(member) as source, stage.open("wb") as output:
                shutil.copyfileobj(source, output)
        if digest(stage) != BINARY_HASHES[target]:
            raise ConnectorError("Notion CLI 可执行文件校验失败。")
        stage.chmod(0o700)
        os.replace(stage, binary)


def ntn_environment(session):
    env = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith(("NOTION_", "NTN_"))
    }
    env.update(NOTION_HOME=str(session), NOTION_KEYRING="0", NOTION_ENV="prod")
    return env


def run_ntn(root, session, *args, body=None, timeout=35):
    return subprocess.run(
        [str(binary_path(root)), *args], cwd=session, env=ntn_environment(session),
        input=json.dumps(body, ensure_ascii=False) if body is not None else "",
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def active_session(root):
    marker = root / "active"
    if not marker.is_file():
        return None
    name = marker.read_text(encoding="utf-8").strip()
    if not PROFILE.fullmatch(name):
        raise ConnectorError("本地授权记录无效，请断开后重新连接。")
    session = root / name
    if session.is_symlink():
        raise ConnectorError("本地授权目录无效，请断开后重新连接。")
    return session if (session / "auth.json").is_file() else None


def login_details(output):
    match = re.search(r"https://[^\s<>]+", output)
    code = re.search(r"(?m)^[ \t]+([A-Z0-9]{3}-[A-Z0-9]{3})[ \t]*$", output)
    if not match or not code:
        raise ConnectorError("没有取得 Notion 授权链接和验证码。")
    url = match[0]
    parts = urlsplit(url)
    if parts.netloc != "app.notion.com" or parts.path != "/workers/cli-login":
        raise ConnectorError("Notion 授权链接的来源与预期不符。")
    return url, code[1]


def login(root):
    session = root / f"session-{uuid4().hex}"
    session.mkdir(mode=0o700)
    promoted = False
    try:
        start = run_ntn(root, session, "login", "--no-browser", timeout=25)
        if start.returncode:
            raise ConnectorError("Notion 未能创建登录会话，请检查网络后重试。")
        url, code = login_details(start.stdout)
        route = f"/{uuid4().hex}"
        page = (
            '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>连接 Notion</title><main><h1>连接 Notion</h1>'
            '<p>请核对 Notion 网页显示的验证码与下方一致，再确认授权。</p>'
            f'<p><strong><code>{html.escape(code)}</code></strong></p>'
            f'<p><a rel="noreferrer" href="{html.escape(url, quote=True)}">前往 Notion 授权</a></p>'
            '<p>完成后回到 WorkSwarm。</p></main></html>'
        ).encode()

        class LoginPage(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                if self.path != route:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)

        with HTTPServer(("127.0.0.1", 0), LoginPage) as entry:
            thread = Thread(target=entry.serve_forever, daemon=True)
            thread.start()
            try:
                print(f"http://127.0.0.1:{entry.server_port}{route}", flush=True)
                poll = run_ntn(root, session, "login", "poll", timeout=300)
                credentials = session / "auth.json"
                if poll.returncode or not credentials.is_file() or credentials.is_symlink():
                    raise ConnectorError("Notion 登录未完成。请重新连接并核对验证码。")
                credentials.chmod(0o600)
                api(root, session, "GET", "v1/users/me")
                previous = active_session(root)
                marker = session / "active.new"
                marker.write_text(session.name, encoding="utf-8")
                os.replace(marker, root / "active")
                promoted = True
                if previous and previous != session:
                    shutil.rmtree(previous, ignore_errors=True)
            finally:
                entry.shutdown()
    finally:
        if not promoted:
            shutil.rmtree(session, ignore_errors=True)


def api(root, session, method, path, body=None):
    options = [path, "--notion-version", API_VERSION, "-X", method]
    if body is not None:
        options += ["--data", "@-"]
    result = run_ntn(root, session, "api", *options, body=body)
    if result.returncode:
        # The CLI can include the requested page or body in failure output.
        status = re.search(r"\b(401|403|404|429)\b", result.stderr)
        message = {
            "401": "Notion 授权已失效，请重新连接。",
            "403": "当前账号对指定页面没有所需权限。",
            "404": "找不到指定页面，或当前账号没有访问权限。",
            "429": "Notion 请求受限，请稍后再试。",
        }.get(status[1] if status else "", "Notion 请求失败，请检查网络、页面和账号权限。")
        raise ConnectorError(message)
    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise ConnectorError("Notion CLI 未返回有效结果。") from exc
    if not isinstance(data, dict):
        raise ConnectorError("Notion CLI 返回了非预期结果。")
    return data


def page_id(value):
    parts = urlsplit(value)
    if parts.scheme:
        host = parts.hostname or ""
        allowed = host in {"notion.so", "www.notion.so", "app.notion.com", "notion.site"} or host.endswith(".notion.site")
        if parts.scheme != "https" or not allowed or parts.netloc != host:
            raise ConnectorError("请提供 Notion 页面链接或页面 ID。")
        value = parts.path
    match = PAGE_ID.search(value)
    if match:
        try:
            return str(UUID(match[1]))
        except ValueError:
            pass
    raise ConnectorError("无法从输入识别 Notion 页面 ID。")


def search(root, session, query, limit):
    if not query.strip() or len(query) > 200 or not 1 <= limit <= 20:
        raise ConnectorError("请输入 1 至 200 字的标题关键词，结果数须为 1 至 20。")
    result = api(root, session, "POST", "v1/search", {
        "query": query, "filter": {"property": "object", "value": "page"}, "page_size": limit,
    })
    pages = []
    for page in result["results"]:
        title = next((v.get("title", []) for v in page["properties"].values() if v.get("type") == "title"), [])
        pages.append({"id": page["id"], "url": page["url"], "title": "".join(t.get("plain_text", "") for t in title)})
    return {"pages": pages, "has_more": result.get("has_more", False)}


def read(root, session, identifier):
    data = api(root, session, "GET", f"v1/pages/{identifier}/markdown")
    markdown = data["markdown"]
    return {
        "page_id": identifier, "markdown": markdown[:20000],
        "truncated": len(markdown) > 20000 or data.get("truncated", False),
    }


def append(root, session, identifier, content):
    if not content.strip() or len(content) > 1500 or len(content.encode("utf-16-le")) > 4000:
        raise ConnectorError("追加内容须为 1 至 1500 字的文本段落。")
    data = api(root, session, "PATCH", f"v1/blocks/{identifier}/children", {
        "children": [{"type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": content}}],
        }}],
    })
    results = data.get("results", [])
    if len(results) != 1 or not results[0].get("id"):
        raise ConnectorError("Notion 未返回明确的写入结果，请先回读页面确认。")
    return {"page_id": identifier, "block_id": results[0]["id"]}


class LocalizedParser(argparse.ArgumentParser):
    def error(self, _):
        raise ConnectorError("命令或参数无效，请运行 --help 查看用法。")


def main():
    parser = LocalizedParser(description="Notion 工作区连接器")
    commands = parser.add_subparsers(dest="command", required=True, title="命令")
    commands.add_parser("prepare", help="安装校验过的 Notion CLI")
    commands.add_parser("version", help="检查已准备的 CLI 版本")
    commands.add_parser("login", help="开始浏览器授权")
    commands.add_parser("status", help="检查登录状态")
    commands.add_parser("logout", help="清除本连接器的本地授权")
    find = commands.add_parser("search", help="按标题搜索页面")
    find.add_argument("--query", required=True, help="页面标题关键词")
    find.add_argument("--limit", type=int, default=10, help="最多返回的页面数")
    for name, hint in (("read", "读取页面正文"), ("append", "在指定页面末尾追加段落")):
        command = commands.add_parser(name, help=hint)
        command.add_argument("--page", required=True, help="Notion 页面链接或 ID")
        if name == "append":
            command.add_argument("--text", required=True, help="要追加的文本")
    try:
        args = parser.parse_args()
        root = private_root()
        if args.command == "prepare":
            prepare(root)
            return print(json.dumps({"ready": True}, ensure_ascii=False))
        if args.command == "logout":
            session = active_session(root)
            (root / "active").unlink(missing_ok=True)
            if session:
                shutil.rmtree(session)
            return print(json.dumps({"connected": False}))
        if args.command == "status":
            session = active_session(root)
            connected = False
            if session and installed(root):
                try:
                    api(root, session, "GET", "v1/users/me")
                    connected = True
                except ConnectorError:
                    pass
            return print(json.dumps({"connected": connected}))
        if not installed(root):
            raise ConnectorError("尚未准备 Notion CLI，请从连接器卡片安装。")
        if args.command == "version":
            return print(NTN_VERSION)
        if args.command == "login":
            return login(root)
        session = active_session(root)
        if not session:
            raise ConnectorError("请先用 WorkSwarm 的连接器卡片登录 Notion。")
        if args.command == "search":
            data = search(root, session, args.query, args.limit)
        elif args.command == "read":
            data = read(root, session, page_id(args.page))
        else:
            data = append(root, session, page_id(args.page), args.text)
        print(json.dumps({"ok": True, "data": data}, ensure_ascii=False))
    except ConnectorError as exc:
        print(json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired, tarfile.TarError):
        print(json.dumps({"ok": False, "message": "连接器操作未完成。请检查运行环境、网络或授权状态。"}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
