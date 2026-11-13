"""WorkSwarm CLI bootstrap, adapted from the Gmail 1.5.1 launcher."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import venv

PAYLOAD = Path(__file__).resolve().parent
# WorkSwarm starts the launcher as a package module; load its sibling service.
sys.path.insert(0, str(PAYLOAD))
import service
VERSION = "1.0.0"


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, add_help=False, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助")

    def format_help(self):
        return super().format_help().replace("usage: ", "用法：", 1).replace("\noptions:", "\n选项：").replace("\noptional arguments:", "\n选项：")

    def error(self, message):
        self.exit(2, json.dumps({"ok": False, "error": {"code": "invalid_argument",
                         "message": "参数无效，请用 --help 查看说明。"}}, ensure_ascii=False) + "\n")


def python_executable():
    if sys.version_info[:2] in {(3, 11), (3, 12)}:
        return str(Path(sys.executable).resolve())
    for version in ("3.12", "3.11"):
        command = f"python{version}"
        if candidate := shutil.which(command):
            return str(Path(candidate).resolve())
        if sys.platform == "darwin":
            home = Path.home()
            arch = "aarch64" if platform.machine() == "arm64" else platform.machine()
            for directory in (home / ".local/bin",
                              home / f".local/share/uv/python/cpython-{version}-macos-{arch}-none/bin",
                              Path("/opt/homebrew/bin"), Path("/usr/local/bin"),
                              Path(f"/Library/Frameworks/Python.framework/Versions/{version}/bin")):
                candidate = directory / command
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return str(candidate.resolve())
    raise ValueError("请先安装 Python 3.11 或 3.12。")


def runtime_paths():
    root = Path(os.environ.get("WORKSWARM_GOOGLE_WORKSPACE_HOME", str(Path.home() / ".local/share/agentic-hub/google-workspace"))).expanduser()
    if not root.is_absolute() or root.is_symlink():
        raise ValueError("运行目录必须是非符号链接的绝对路径。")
    root = root.resolve()
    if root == PAYLOAD or PAYLOAD in root.parents or any((p / ".git").exists() for p in (root, *root.parents)):
        raise ValueError("运行目录必须位于源码仓库和安装包之外。")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = root.stat()
    if os.name != "nt" and (info.st_uid != os.getuid() or info.st_mode & 0o077):
        raise ValueError("运行目录须归当前用户所有，权限为 700。")
    requirements = PAYLOAD / "requirements.txt"
    digest = sha256(requirements.read_bytes()).hexdigest()
    runtime = root / f"runtime-{digest[:16]}"
    ready = runtime / ".ready"
    if runtime.is_symlink() or ready.is_symlink():
        raise ValueError("独立运行目录和标记不能是符号链接。")
    executable = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return requirements, runtime, ready, executable


def run_again(executable):
    os.execv(str(executable), [str(executable), "-u", "-B", str(PAYLOAD / "launcher.py"), *sys.argv[1:]])


def prepare(requirements, runtime, ready, executable):
    if ready.is_file() and executable.is_file():
        return
    interpreter = python_executable()
    if interpreter != sys.executable:
        run_again(interpreter)
    from bootstrap_lock import install_lock

    with install_lock(runtime.parent):
        if ready.is_file() and executable.is_file():
            return
        venv.EnvBuilder(with_pip=True, clear=True).create(runtime)
        subprocess.run([str(executable), "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
                        "--index-url", "https://pypi.org/simple", "--require-hashes", "-r", str(requirements)],
                       check=True, timeout=240)
        subprocess.run([str(executable), "-B", "-c", "import google_auth_oauthlib, requests"], check=True)
        ready.touch()


def parse_arguments():
    parser = Parser(prog=service.SLUG, description=service.LABEL)
    sub = parser.add_subparsers(dest="action", required=True, title="命令")
    sub.add_parser("prepare", help="准备独立 Python 依赖")
    sub.add_parser("version", help="显示连接器版本")
    sub.add_parser("runtime-version", help="检查独立依赖并显示版本")
    config = sub.add_parser("configure", help="导入共用的 Desktop OAuth 配置")
    config.add_argument("--client-file", type=Path, required=True, help="本机 Desktop OAuth JSON 路径")
    login = sub.add_parser("login", help="在系统浏览器进行 Google 授权")
    login.add_argument("--no-open-browser", action="store_true", help="将授权链接交给 WorkSwarm")
    sub.add_parser("status", help="检查本卡片的本地授权")
    sub.add_parser("logout", help="清除本卡片的本地授权")
    service.register(sub)
    return parser.parse_args()


def output(ok, values, *, stream=None):
    print(json.dumps({"ok": ok, "version": VERSION, **values}, ensure_ascii=False, allow_nan=False),
          file=stream or sys.stdout)
    return 0 if ok else 1


def main():
    args = parse_arguments()
    try:
        if args.action == "version":
            print(VERSION)
            return 0
        requirements, runtime, ready, executable = runtime_paths()
        if args.action == "prepare":
            prepare(requirements, runtime, ready, executable)
            return output(True, {"message": "独立 Python 依赖已准备。"})
        if not ready.is_file() or not executable.is_file():
            raise ValueError("请先通过卡片安装连接器，或按 README 运行 prepare。")
        if Path(sys.prefix).resolve() != runtime:
            run_again(executable)
        import oauth
        from google_api import GoogleAPI, NOTICE

        if args.action == "runtime-version":
            print(VERSION)
            return 0
        if args.action == "configure":
            return output(True, oauth.configure(args.client_file))
        if args.action == "login":
            return output(True, oauth.sign_in(service.SLUG, service.SCOPE, service.LABEL, not args.no_open_browser))
        if args.action == "logout":
            return output(True, oauth.sign_out(service.SLUG))
        if args.action == "status":
            return output(True, oauth.status(service.SLUG, service.SCOPE))
        data = args.operation(GoogleAPI(service.SLUG, service.SCOPE, service.BASE), args)
        return output(True, {"data": data, "untrusted_data_notice": NOTICE})
    except Exception as exc:
        if args.action == "runtime-version":
            print("运行依赖未就绪。", file=sys.stderr)
            return 1
        # Unexpected errors can contain provider response data or credentials.
        if type(exc).__name__ == "Error" and hasattr(exc, "code"):
            code, message = exc.code, exc.message
        else:
            code, message = "operation_failed", "操作未完成。请检查 Python、连接器安装和输入参数。"
            if isinstance(exc, ValueError) and args.action in {"prepare", "configure"}:
                message = str(exc)
        return output(False, {"signed_in_local": False, "error": {"code": code, "message": message}}, stream=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
