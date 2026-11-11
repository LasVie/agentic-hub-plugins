"""Explicit runtime setup, local OAuth helpers, and portable MCP launcher."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

VERSION = "1.0.0"
PAYLOAD = Path(__file__).resolve().parent


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


def prepare() -> None:
    if sys.version_info[:2] != (3, 12):
        raise ValueError("此依赖锁使用 Python 3.12；请用 python3.12 执行 prepare。")
    root = home()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt" and root.stat().st_mode & 0o077:
        raise ValueError("运行目录权限必须为 700。")
    runtime = root / "runtime"
    if runtime.is_symlink():
        raise ValueError("拒绝将依赖安装到符号链接目录。")
    if not python_path().exists():
        venv.EnvBuilder(with_pip=True).create(runtime)
    # Only this explicit command downloads dependencies. Never invoked on import,
    # server startup, tool call, sign-in or Marketplace Connect.
    subprocess.run([str(python_path()), "-m", "pip", "install", "--disable-pip-version-check",
                    "--require-hashes", "-r", str(PAYLOAD / "requirements.txt")], check=True)
    print(json.dumps({"ok": True, "version": VERSION, "message": "独立依赖已准备；未登录或访问邮箱。"}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Gmail 只读邮件连接器：独立运行环境与浏览器登录。")
    parser.add_argument("action", choices=["prepare", "configure", "login", "status", "logout", "serve", "version"], nargs="?", default="serve", help="prepare 准备依赖；configure 配置开发者客户端；login 浏览器登录；logout 移除本地凭据。")
    parser.add_argument("--client-file", type=Path, help="开发者下载的 Desktop app 客户端 JSON 路径（不是访问令牌）。")
    args = parser.parse_args()
    try:
        if args.action == "version":
            print(VERSION)
            return 0
        if args.action == "prepare":
            prepare()
            return 0
        target = python_path()
        if not target.is_file() or target.is_symlink():
            # CPython venvs normally symlink their interpreter; permit that one
            # standard venv link, but never auto-install missing software.
            if not target.is_file():
                raise ValueError("尚未准备独立运行环境。请先明确执行 launcher.py prepare。")
        if Path(sys.prefix).resolve() != (home() / "runtime").resolve():
            os.execv(str(target), [str(target), "-B", str(PAYLOAD / "launcher.py"), *sys.argv[1:]])
        if args.action == "serve":
            os.execv(str(target), [str(target), "-B", str(PAYLOAD / "server.py")])
        from auth import ConnectorError, configure, session_status, sign_in, sign_out
        if args.action == "configure":
            if args.client_file is None:
                raise ValueError("configure 需要 --client-file 指定开发者 JSON 路径。")
            result = configure(args.client_file)
        elif args.action == "login":
            result = sign_in()
        elif args.action == "logout":
            result = sign_out()
        else:
            result = session_status()
        print(json.dumps({"version": VERSION, **result}, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    except Exception as exc:
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
