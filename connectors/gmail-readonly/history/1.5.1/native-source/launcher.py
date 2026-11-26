"""Install and run the Gmail CLI in a private Python environment."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import venv

VERSION = "1.5.1"
PAYLOAD = Path(__file__).resolve().parent


class CliParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, add_help=False, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示此帮助")

    def format_help(self) -> str:
        return super().format_help().replace("usage: ", "用法：", 1).replace("\noptions:", "\n选项：")

    def error(self, message: str) -> None:
        self.exit(2, json.dumps({
            "ok": False,
            "version": VERSION,
            "error": {"code": "invalid_argument", "message": "参数无效，请运行 gmail-readonly --help 查看用法。"},
        }, ensure_ascii=False) + "\n")


def home() -> Path:
    path = Path(os.environ.get("GMAIL_READONLY_HOME", str(Path.home() / ".local/share/agentic-hub/gmail-readonly"))).expanduser()
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("运行目录必须为非符号链接的绝对路径。")
    path = path.resolve()
    if path == PAYLOAD or PAYLOAD in path.parents or any((p / ".git").exists() for p in [path, *path.parents]):
        raise ValueError("运行目录必须位于源码仓库和安装包之外。")
    return path


def python_path() -> Path:
    return home() / "runtime" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def install_command(bin_dir: Path) -> None:
    bin_dir = bin_dir.expanduser().resolve()
    bin_dir.mkdir(parents=True, exist_ok=True)
    interpreter = str(Path(sys.executable).absolute())
    launcher = str(PAYLOAD / "launcher.py")
    private_dir = str(home())
    if os.name == "nt":
        target = bin_dir / "gmail-readonly.cmd"
        argv = [item.replace("%", "%%") for item in (interpreter, launcher, private_dir)]
        wrapper = f'@echo off\nset "GMAIL_READONLY_HOME={argv[2]}"\n@"{argv[0]}" -B "{argv[1]}" %*\n'
    else:
        target = bin_dir / "gmail-readonly"
        wrapper = (
            f'#!/bin/sh\nexport GMAIL_READONLY_HOME={shlex.quote(private_dir)}\n'
            f'exec {shlex.quote(interpreter)} -B {shlex.quote(launcher)} "$@"\n'
        )
    if target.is_symlink() or (
        target.exists() and (
            not target.is_file()
            or target.stat().st_size > 8192
            or target.read_text(encoding="utf-8") != wrapper
        )
    ):
        raise ValueError("目标目录已有其他 Gmail CLI 入口，请先核对来源或选择另一个目录。")
    if not target.exists():
        with target.open("x", encoding="utf-8") as command:
            command.write(wrapper)
    target.chmod(0o700)


def runtime_python() -> str:
    if sys.version_info[:2] in {(3, 11), (3, 12)}:
        return sys.executable
    for version in ("3.12", "3.11"):
        command = f"python{version}"
        candidate = shutil.which(command)
        if candidate:
            return str(Path(candidate).resolve())
        if sys.platform != "darwin":
            continue
        user_home = Path.home()
        machine = platform.machine()
        uv_arch = "aarch64" if machine == "arm64" else machine
        for path in (
            user_home / ".local/bin" / command,
            user_home / f".local/share/uv/python/cpython-{version}-macos-{uv_arch}-none/bin/{command}",
            Path(f"/opt/homebrew/bin/{command}"),
            Path(f"/usr/local/bin/{command}"),
            Path(f"/Library/Frameworks/Python.framework/Versions/{version}/bin/{command}"),
        ):
            if path.is_file() and os.access(path, os.X_OK):
                return str(path.resolve())
    raise ValueError("未找到 Python 3.11 或 3.12。请安装其中一个版本后重新连接。")


def prepare(bin_dir: Path | None) -> None:
    interpreter = runtime_python()
    if interpreter != sys.executable:
        os.execv(interpreter, [interpreter, "-u", "-B", str(PAYLOAD / "launcher.py"), *sys.argv[1:]])
    root = home()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt" and root.stat().st_mode & 0o077:
        raise ValueError("运行目录权限必须为 700。")
    runtime = root / "runtime"
    if runtime.is_symlink():
        raise ValueError("拒绝将依赖安装到符号链接目录。")
    if not python_path().exists():
        venv.EnvBuilder(with_pip=True).create(runtime)
    # Keep dependency downloads in prepare, which is also the host's init step.
    subprocess.run([str(python_path()), "-m", "pip", "install", "--disable-pip-version-check",
                    "--require-hashes", "-r", str(PAYLOAD / "requirements.txt")], check=True)
    if bin_dir is not None:
        install_command(bin_dir)
    print(json.dumps({"ok": True, "version": VERSION, "message": "独立依赖已准备；未登录或访问邮箱。"}, ensure_ascii=False))


def main() -> int:
    parser = CliParser(prog="gmail-readonly", description="Gmail 邮件连接器")
    commands = parser.add_subparsers(dest="action", required=True, title="命令")
    setup = commands.add_parser("prepare", help="准备独立依赖")
    setup.add_argument("--bin-dir", type=Path, help="在指定目录安装 gmail-readonly 命令")
    configure_cmd = commands.add_parser("configure", help="配置开发者 Desktop OAuth 客户端")
    configure_cmd.add_argument("--client-file", type=Path, required=True, help="Desktop OAuth 客户端 JSON 路径")
    login = commands.add_parser("login", help="发起浏览器授权")
    login.add_argument("--no-open-browser", action="store_true", help="将授权链接交给宿主")
    commands.add_parser("status", help="检查本地会话")
    commands.add_parser("logout", help="移除本地会话")
    commands.add_parser("version", help="显示 CLI 版本")
    commands.add_parser("runtime-version", help="检查独立依赖与版本")
    search = commands.add_parser("search", help="搜索邮件标识")
    search.set_defaults(operation="search_messages")
    search.add_argument("--query", default="", help="Gmail 查询语句")
    search.add_argument("--max-results", type=int, default=5, help="本页邮件数，最多 20")
    search.add_argument("--page-token", default="", help="上一次搜索返回的分页令牌")
    message = commands.add_parser("read-message", help="读取一封邮件")
    message.set_defaults(operation="read_message")
    message.add_argument("--message-id", required=True, help="搜索结果中的邮件标识")
    message.add_argument("--max-chars", type=int, default=3000, help="正文字符上限，最多 20000")
    thread = commands.add_parser("read-thread", help="读取一个邮件会话")
    thread.set_defaults(operation="read_thread")
    thread.add_argument("--thread-id", required=True, help="搜索结果中的会话标识")
    thread.add_argument("--max-messages", type=int, default=5, help="返回邮件数，最多 20")
    thread.add_argument("--max-chars", type=int, default=6000, help="正文总字符上限，最多 30000")
    drafts = commands.add_parser("list-drafts", help="列出草稿标识")
    drafts.set_defaults(operation="list_drafts")
    drafts.add_argument("--max-results", type=int, default=5, help="本页草稿数，最多 20")
    drafts.add_argument("--page-token", default="", help="上一次列表返回的分页令牌")
    draft = commands.add_parser("read-draft", help="读取草稿及其收件人")
    draft.set_defaults(operation="read_draft")
    draft.add_argument("--draft-id", required=True, help="Gmail 草稿标识")
    draft.add_argument("--max-chars", type=int, default=3000, help="正文字符上限，最多 20000")
    edit = commands.add_parser("edit-draft", help="更新现有草稿")
    edit.set_defaults(operation="edit_draft")
    edit.add_argument("--draft-id", required=True, help="Gmail 草稿标识")
    edit.add_argument("--to", action="append", help="新的收件人，可重复传入")
    edit.add_argument("--subject", help="新主题")
    edit.add_argument("--body", help="新正文，最多 30000 个字符")
    send = commands.add_parser("send", help="发送一封新邮件")
    send.set_defaults(operation="send_message")
    send.add_argument("--to", required=True, action="append", help="收件人邮箱，可重复传入")
    send.add_argument("--subject", required=True, help="邮件主题")
    send.add_argument("--body", required=True, help="邮件正文，最多 30000 个字符")
    send_draft = commands.add_parser("send-draft", help="发送指定的现有草稿")
    send_draft.set_defaults(operation="send_draft")
    send_draft.add_argument("--draft-id", required=True, help="Gmail 草稿标识")
    reply = commands.add_parser("reply", help="在原 Gmail 会话中回复一封邮件")
    reply.set_defaults(operation="reply")
    reply.add_argument("--message-id", required=True, help="要回复的 Gmail 邮件标识")
    reply.add_argument("--body", required=True, help="回复正文，最多 30000 个字符")
    args = parser.parse_args()
    try:
        if args.action == "version":
            print(VERSION)
            return 0
        if args.action == "prepare":
            prepare(args.bin_dir)
            return 0
        target = python_path()
        if not target.is_file() or target.is_symlink():
            # CPython venvs normally symlink their interpreter; permit that one
            # standard venv link, but never auto-install missing software.
            if not target.is_file():
                raise ValueError("尚未准备独立运行环境。请先明确执行 launcher.py prepare。")
        if Path(sys.prefix).resolve() != (home() / "runtime").resolve():
            os.execv(str(target), [str(target), "-u", "-B", str(PAYLOAD / "launcher.py"), *sys.argv[1:]])
        if args.action == "runtime-version":
            # Import the CLI's service so a partial setup is not reported as ready.
            from gmail_service import VERSION as service_version

            print(service_version)
            return 0
        from auth import ConnectorError, configure, session_status, sign_in, sign_out
        from gmail_service import GmailService, UNTRUSTED_NOTICE

        if args.action == "configure":
            result = configure(args.client_file)
        elif args.action == "login":
            result = sign_in(open_browser=not args.no_open_browser)
        elif args.action == "logout":
            result = sign_out()
        elif args.action == "status":
            result = session_status()
        else:
            service = GmailService()
            arguments = vars(args).copy()
            arguments.pop("action")
            operation = arguments.pop("operation")
            try:
                data = getattr(service, operation)(**arguments)
            except ConnectorError:
                raise
            except Exception:
                result = {"ok": False, "error": {"code": "internal_error", "message": "操作未完成，请检查参数或当前会话。"}}
            else:
                result = {"ok": True, "data": data, "untrusted_data_notice": UNTRUSTED_NOTICE}
        print(json.dumps({"version": VERSION, **result}, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    except Exception as exc:
        if args.action == "runtime-version":
            # WorkSwarm 0.2.8 extracts version strings even on a failed exit.
            # A missing runtime must report no version so the host runs init.
            print("Gmail 运行依赖未就绪。", file=sys.stderr)
            return 1
        # Never serialize OAuth / request exceptions, token JSON or private data.
        if type(exc).__name__ == "ConnectorError":
            code, message = exc.code, exc.message
        elif isinstance(exc, ValueError):
            code, message = "setup_required", str(exc)
        else:
            code, message = "setup_failed", "本地操作未完成；请检查独立依赖与目录权限。未输出敏感错误详情。"
        print(json.dumps({"ok": False, "version": VERSION, "error": {"code": code, "message": message}}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
