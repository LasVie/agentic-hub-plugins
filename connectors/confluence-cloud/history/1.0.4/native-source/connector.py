"""Run a small set of trusted Atlassian CLI commands with scoped arguments."""

import argparse
import errno
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from browser_gate import LoginPage
from vendor_runtime import install

PRODUCT = "confluence"
BINARY = "twg"
DATA = Path(os.environ.get("JIUWENSWARM_DATA_DIR") or Path.home() / ".jiuwenswarm")
STATE = DATA / "connector-data" / PRODUCT
DOC = "https://developer.atlassian.com/cloud/twg-cli/getting-started/installation/"


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
    scoped["TWG_CONFIG_DIR"] = str(STATE / "twg")
    return scoped


def run(args, *, require=True, timeout=40):
    proc = subprocess.run(
        [binary(), *args], stdin=subprocess.DEVNULL, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env(), timeout=timeout,
    )
    if proc.returncode and require:
        raise ConnectorError(f"{BINARY} 操作失败（退出码 {proc.returncode}）。请核对登录、站点、目标和权限。")
    return proc


def browser_auth(page):
    if os.name == "nt":
        raise ConnectorError("Windows 请先在终端运行官方 TWG CLI 并完成设备授权。")
    import fcntl
    import pty
    import struct
    import termios

    argv = [binary(), "login", "--site", page.site]
    environment = env()
    environment.pop("TWG_AGENT_DEFAULTS", None)
    pid, master = pty.fork()
    if pid == 0:
        try:
            os.execve(argv[0], argv, environment)
        finally:
            os._exit(127)
    end = time.monotonic() + 300
    waited = False
    selected_no = False
    confirmed_no = False
    output = b""
    try:
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
        while time.monotonic() < end:
            ready, _, _ = select.select([master], [], [], 0.25)
            if ready:
                try:
                    output = (output + os.read(master, 8192))[-32768:]
                    if not page.url and b"Waiting for authentication in browser" in output:
                        match = re.search(rb"Visit: (https://auth\.atlassian\.com/oauth/activate\?[^\s]+)", output)
                        if match:
                            page.publish(match.group(1).decode("ascii"))
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
            if not confirmed_no and b"Open in browser?" in output:
                if not selected_no and not (termios.tcgetattr(master)[3] & termios.ICANON):
                    os.write(master, b"\x1b[C")
                    selected_no = True
                if selected_no and "○ Y / ● n".encode() in output:
                    os.write(master, b"\r")
                    confirmed_no = True
            child, status = os.waitpid(pid, os.WNOHANG)
            if child:
                waited = True
                return os.waitstatus_to_exitcode(status)
        raise ConnectorError(f"{BINARY} 授权超时。若 CLI 要求终端输入，可按说明在终端完成授权。")
    finally:
        os.close(master)
        if not waited:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)


def status():
    result = run(["doctor", "--basic", "-o", "json"], require=False)
    if result.returncode != 0:
        return False
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        return False
    return data.get("data", {}).get("auth", {}).get("resolved", {}).get("tokenPresent") is True


def select_command(args):
    prefix = ["confluence", "content"]
    if args.command == "search":
        return ["confluence", "search", "query", "--cql", args.query, "--limit", "20", "-o", "json"]
    if args.command == "read":
        if not args.id.isdigit():
            raise ConnectorError("请输入 Confluence 页面的数字 ID。")
        return prefix + ["get", args.id, "-o", "json"]
    return prefix + ["create", "--content-type", "page", "--space-id", args.container,
                     "--title", args.title, "--body", args.body, "--format", "markdown",
                     "--ack-body-formats", "--yes", "-o", "json"]


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
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            binary(install_if_missing=True)
            result = {"ready": True}
        elif args.command == "version":
            result = {"version": "1.0.4", "provider_cli": run(["--version"]).stdout.strip()}
        elif args.command == "status":
            try:
                connected = status()
            except (ConnectorError, ValueError):
                connected = False
            result = {"connected": connected}
        elif args.command == "login":
            binary()
            with LoginPage("Confluence", {"auth.atlassian.com"}, needs_site=True) as page:
                if not page.started.wait(timeout=155):
                    raise ConnectorError("等待打开授权入口超时，请重新点击连接。")
                try:
                    if browser_auth(page) or not status():
                        raise ConnectorError("服务登录未完成，请核对授权及站点权限。")
                except (ConnectorError, OSError):
                    page.finish(False)
                    raise
            result = {"connected": True}
        elif args.command == "logout":
            run(["logout"], require=False)
            result = {"connected": status()}
            if result["connected"]:
                raise ConnectorError("官方 CLI 仍显示已登录，请检查账号状态。")
        else:
            output = run(select_command(args)).stdout.strip()
            try:
                result = json.loads(output)
            except ValueError:
                result = {"provider_output": output}
    except (ConnectorError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(str(error) if isinstance(error, (ConnectorError, ValueError)) else f"{BINARY} 无法完成操作。", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
