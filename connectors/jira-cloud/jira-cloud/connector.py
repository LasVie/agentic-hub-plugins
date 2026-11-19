"""Run a small set of trusted Atlassian CLI commands with scoped arguments."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from browser_gate import JiraLoginError, browser_login
from vendor_runtime import install

PRODUCT = "jira"
BINARY = "acli"
VERSION = "1.0.4"
DATA = Path(os.environ.get("JIUWENSWARM_DATA_DIR") or Path.home() / ".jiuwenswarm")
STATE = DATA / "connector-data" / PRODUCT
DOC = "https://developer.atlassian.com/cloud/acli/guides/install/"


class ConnectorError(Exception):
    pass


def binary(*, install_if_missing=False):
    system_paths = [
        str(STATE / "bin"), os.environ.get("PATH", ""),
        str(Path.home() / ".local" / "bin"),
        *(("/opt/homebrew/bin", "/usr/local/bin") if os.name != "nt" else ()),
    ]
    found = shutil.which(BINARY, path=os.pathsep.join(filter(None, system_paths)))
    if not found and install_if_missing:
        install(STATE / "bin")
        return binary()
    if not found:
        raise ConnectorError(f"未找到官方 {BINARY}，请按说明安装后重试。{DOC}")
    return found


def env():
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    scoped = dict(os.environ)
    scoped["ACLI_CONFIG_DIR"] = str(STATE / "acli")
    scoped["XDG_CONFIG_HOME"] = str(STATE)
    return scoped


def run(args, *, require=True, timeout=40):
    proc = subprocess.run(
        [binary(), *args], stdin=subprocess.DEVNULL, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env(), timeout=timeout,
    )
    if proc.returncode and require:
        raise ConnectorError(f"{BINARY} 操作失败（退出码 {proc.returncode}）。请核对登录、站点、目标和权限。")
    return proc


def status():
    return run(["jira", "auth", "status"], require=False).returncode == 0


def select_command(args):
    prefix = ["jira", "workitem"]
    if args.command == "search":
        return prefix + ["search", "--jql", args.query, "--limit", "25", "--json"]
    if args.command == "read":
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,40}-[1-9][0-9]*", args.id):
            raise ConnectorError("请输入 Jira 工单键，例如 DEMO-123。")
        return prefix + ["view", "--json", args.id]
    return prefix + ["create", "--project", args.container, "--type", args.type,
                     "--summary", args.title, "--description", args.body]


def main():
    parser = argparse.ArgumentParser(description=f"读取和创建 {PRODUCT} 记录")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "version", "status", "login", "logout"):
        commands.add_parser(name)
    query = commands.add_parser("search")
    query.add_argument("--query", required=True)
    read = commands.add_parser("read")
    read.add_argument("--id", required=True)
    create = commands.add_parser("create")
    create.add_argument("--container", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--body", default="")
    create.add_argument("--type", default="Task")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            binary(install_if_missing=True)
            result = {"ready": True}
        elif args.command == "version":
            result = {"version": VERSION, "provider_cli": run(["--version"]).stdout.strip()}
        elif args.command == "status":
            try:
                connected = status()
            except (ConnectorError, ValueError):
                connected = False
            result = {"connected": connected}
        elif args.command == "login":
            if browser_login([binary(), "jira", "auth", "login", "--web"], env(), status):
                raise ConnectorError("服务登录未完成，请核对授权及站点权限。")
            result = {"connected": True}
        elif args.command == "logout":
            run(["jira", "auth", "logout"], require=False)
            result = {"connected": status()}
            if result["connected"]:
                raise ConnectorError("官方 CLI 仍显示已登录，请检查账号状态。")
        else:
            output = run(select_command(args)).stdout.strip()
            try:
                result = json.loads(output)
            except ValueError:
                result = {"provider_output": output}
    except (ConnectorError, JiraLoginError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(str(error) if isinstance(error, (ConnectorError, JiraLoginError, ValueError)) else f"{BINARY} 无法完成操作。", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
