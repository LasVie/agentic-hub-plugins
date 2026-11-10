"""Bounded local engine execution and ownership-checked workbench lifecycle."""
from __future__ import annotations

import errno
import fcntl
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

VERSION = "1.0.1"
PLUGIN_ID = "queue-capacity-workbench"
ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ".queue-capacity-workbench"
MAX_INPUT = 256 * 1024
MAX_OUTPUT = 12 * 1024 * 1024
ENGINE_TIMEOUT = 15.0
_CHILDREN: dict[str, subprocess.Popen] = {}
_DIRECT_SLOT = threading.BoundedSemaphore(1)


class WorkbenchError(Exception):
    """A Chinese message safe for a user-facing tool result."""


def failure(message: str, **extra) -> dict:
    return {"ok": False, "version": VERSION, "error": message, **extra}


def encode_json(value, maximum=MAX_INPUT) -> bytes:
    try:
        data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise WorkbenchError("输入必须是有效的 UTF-8 JSON，不能含非有限数值。") from exc
    if len(data) > maximum:
        raise WorkbenchError("输入超过 256 KiB 上限，请减少排队场景大小。")
    return data


def strict_json(data: bytes):
    def reject_constant(_value):
        raise ValueError("nonfinite")

    def unique_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate key")
            value[key] = item
        return value

    return json.loads(data.decode("utf-8"), parse_constant=reject_constant, object_pairs_hook=unique_pairs)


def process_env() -> dict[str, str]:
    # No NODE_OPTIONS/NODE_PATH, proxy settings, model keys, Python path hooks,
    # or inherited package-manager configuration reach the calculation process.
    allowed = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "WINDIR")
    result = {key: os.environ[key] for key in allowed if key in os.environ}
    result.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"})
    return result


def _stop_child(process: subprocess.Popen) -> None:
    """Signal only the process object created by this invocation, never disk PIDs."""
    if process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=0.6)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        except ProcessLookupError:
            pass


def run_engine(project: dict, cancelled: threading.Event | None = None) -> dict:
    if not isinstance(project, dict):
        return failure("project 必须是排队容量项目对象。")
    try:
        payload = encode_json(project)
    except WorkbenchError as exc:
        return failure(str(exc))
    if cancelled is not None and cancelled.is_set():
        return failure("计算已取消。", cancelled=True)
    command = [sys.executable, "-I", "-B", str(ROOT / "runtime" / "worker.py")]
    try:
        process = subprocess.Popen(command, cwd=ROOT, env=process_env(), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError:
        return failure("无法启动本地排队场景引擎，请检查 Python 3.11+ 和插件文件。")
    output = bytearray()
    overflow = threading.Event()

    def feed():
        try:
            process.stdin.write(payload)
            process.stdin.close()
        except (OSError, ValueError):
            pass

    def drain(stream, destination, limit):
        size = 0
        try:
            while block := stream.read(65536):
                size += len(block)
                if size > limit:
                    overflow.set()
                    return
                if destination is not None:
                    destination.extend(block)
        except (OSError, ValueError):
            pass

    threads = [threading.Thread(target=feed, daemon=True),
               threading.Thread(target=drain, args=(process.stdout, output, MAX_OUTPUT), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, None, 65536), daemon=True)]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + ENGINE_TIMEOUT
    reason = None
    try:
        while process.poll() is None:
            if cancelled is not None and cancelled.is_set():
                reason = failure("计算已取消。", cancelled=True)
                break
            if overflow.is_set():
                reason = failure("引擎输出超过上限，本次计算已停止。")
                break
            if time.monotonic() >= deadline:
                reason = failure("计算超过 15 秒上限，请简化排队场景后重试。", timed_out=True)
                break
            time.sleep(0.02)
        if reason:
            _stop_child(process)
        else:
            process.wait(timeout=1)
        for thread in threads:
            thread.join(timeout=1)
        if reason:
            return reason
        if overflow.is_set():
            return failure("引擎输出超过上限，本次计算已停止。")
        if cancelled is not None and cancelled.is_set():
            return failure("计算已取消。", cancelled=True)
        if process.returncode:
            return failure("排队场景引擎未完成计算；可能达到内存限制，请简化排队场景后重试。")
        try:
            result = strict_json(bytes(output))
        except (ValueError, UnicodeError, RecursionError):
            return failure("排队场景引擎返回了无效结果。")
        if not isinstance(result, dict) or type(result.get("ok")) is not bool:
            return failure("排队场景引擎返回了无效结果。")
        if not result["ok"] and not isinstance(result.get("error"), str):
            return failure("排队场景引擎返回了无效错误信息。")
        return {**result, "version": VERSION}
    finally:
        _stop_child(process)
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except (OSError, ValueError):
                pass


def engine_call(inputs: dict) -> dict:
    if not isinstance(inputs, dict) or set(inputs) - {"project"}:
        return failure("仅接受 project 参数。")
    if not _DIRECT_SLOT.acquire(blocking=False):
        return failure("已有计算正在运行，请稍后重试。", busy=True)
    try:
        return run_engine(inputs.get("project"))
    except WorkbenchError as exc:
        return failure(str(exc))
    finally:
        _DIRECT_SLOT.release()


def workspace_path(value) -> Path:
    if not isinstance(value, str) or not value or not Path(value).is_absolute() or ".." in Path(value).parts:
        raise WorkbenchError("workspace 必须是已有工作目录的绝对路径，不能包含 .. 或符号链接。")
    path = Path(value)
    try:
        for item in (path, *path.parents):
            if item.is_symlink():
                raise WorkbenchError("工作目录及其父目录不能是符号链接。")
        if not path.is_dir():
            raise WorkbenchError("工作目录不存在，请先创建专用目录。")
        return path.resolve(strict=True)
    except OSError as exc:
        raise WorkbenchError("无法访问工作目录。") from exc


def runtime_dir(workspace: Path, *, create=False) -> Path | None:
    path = workspace / STATE_DIR
    if create:
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise WorkbenchError("插件状态目录必须是当前用户拥有的私有真实目录（权限 0700）；未修改现有目录。")
    return path


def _read_private(path: Path, limit=8192) -> bytes | None:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise WorkbenchError("状态文件不能是链接或不可访问的文件。") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise WorkbenchError("状态文件的类型、所有者或权限无效；未修改现有状态。")
        data = os.read(descriptor, limit + 1)
        if len(data) > limit:
            raise WorkbenchError("状态文件过大；未修改现有状态。")
        return data
    finally:
        os.close(descriptor)


def read_state(directory: Path) -> dict | None:
    data = _read_private(directory / "server.json")
    if data is None:
        return None
    try:
        state = strict_json(data)
        valid = (isinstance(state, dict) and set(state) == {"version", "root", "port", "token", "session_id"}
                 and state["version"] == VERSION and state["root"] == str(ROOT)
                 and type(state["port"]) is int and 1 <= state["port"] <= 65535
                 and isinstance(state["token"], str) and re.fullmatch(r"[0-9a-f]{64}", state["token"])
                 and isinstance(state["session_id"], str) and re.fullmatch(r"[0-9a-f]{32}", state["session_id"]))
        if not valid:
            raise ValueError("state")
        return state
    except (ValueError, UnicodeError, RecursionError):
        raise WorkbenchError("插件状态无效或属于另一安装路径；请保留原文件并使用原安装停止服务。") from None


@contextmanager
def state_lock(directory: Path):
    path = directory / "server.lock"
    try:
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except OSError as exc:
        raise WorkbenchError("无法安全打开插件状态锁。") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise WorkbenchError("插件状态锁的类型或权限无效。")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WorkbenchError("工作台状态正在更新，请稍后重试。") from exc
        yield
    finally:
        os.close(descriptor)


def contact(state: dict, action="health") -> dict | None:
    connection = http.client.HTTPConnection("127.0.0.1", state["port"], timeout=2)
    try:
        method = "POST" if action == "stop" else "GET"
        connection.request(method, f"/{state['token']}/api/{action}", body=b"{}" if action == "stop" else None,
                           headers={"Content-Type": "application/json"} if action == "stop" else {})
        response = connection.getresponse()
        body = response.read(8193)
        if response.status != 200 or len(body) > 8192:
            raise WorkbenchError("端口响应不属于本工作台；未停止或覆盖任何服务。")
        result = strict_json(body)
        if (not isinstance(result, dict) or result.get("ok") is not True
                or result.get("plugin_id") != PLUGIN_ID or result.get("version") != VERSION
                or result.get("session_id") != state["session_id"]):
            raise WorkbenchError("工作台身份核验失败；未停止或覆盖任何服务。")
        return result
    except ConnectionRefusedError:
        return None
    except OSError as exc:
        if exc.errno == errno.ECONNREFUSED:
            return None
        raise WorkbenchError("无法确认已有工作台状态；请稍后重试，未覆盖原状态。") from exc
    except (http.client.HTTPException, ValueError, UnicodeError, RecursionError) as exc:
        raise WorkbenchError("工作台响应无效；未停止或覆盖任何服务。") from exc
    finally:
        connection.close()


def _status(state: dict | None, running=False, **extra) -> dict:
    result = {"ok": True, "version": VERSION, "running": running, **extra}
    if state and running:
        result.update({"session_id": state["session_id"],
                       "url": f"http://127.0.0.1:{state['port']}/{state['token']}/index.html"})
    return result


def _save_state(directory: Path, state: dict) -> None:
    path = directory / (".server-" + secrets.token_hex(12) + ".json")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encode_json(state))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(path, directory / "server.json")
    finally:
        if path.exists():
            path.unlink()


def _start(directory: Path) -> dict:
    state = {"version": VERSION, "root": str(ROOT), "port": 0,
             "token": secrets.token_hex(32), "session_id": secrets.token_hex(16)}
    process = subprocess.Popen([sys.executable, "-B", str(ROOT / "runtime" / "server.py")], cwd=ROOT,
                               env=process_env(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    handshake = []
    ready = threading.Event()

    def read_handshake():
        try:
            handshake.append(process.stdout.readline(4097))
        finally:
            ready.set()

    try:
        process.stdin.write(encode_json({"token": state["token"], "session_id": state["session_id"]}))
        process.stdin.close()
        reader = threading.Thread(target=read_handshake, daemon=True)
        reader.start()
        if not ready.wait(5) or not handshake or len(handshake[0]) > 4096:
            raise WorkbenchError("工作台启动超时；已停止本次创建的进程。")
        message = strict_json(handshake[0])
        if (not isinstance(message, dict) or message.get("ok") is not True or type(message.get("port")) is not int
                or not 1 <= message["port"] <= 65535):
            raise WorkbenchError("工作台启动失败。")
        state["port"] = message["port"]
        if contact(state) is None:
            raise WorkbenchError("工作台启动后未通过身份核验。")
        _save_state(directory, state)
        _CHILDREN[state["session_id"]] = process
        return _status(state, True, started=True)
    except BaseException:
        _stop_child(process)
        raise
    finally:
        process.stdout.close()


def lifecycle(inputs: dict) -> dict:
    try:
        if not isinstance(inputs, dict) or set(inputs) - {"action", "workspace", "confirmed"}:
            raise WorkbenchError("仅接受 action、workspace、confirmed 参数。")
        action = inputs.get("action")
        if not isinstance(action, str) or action not in {"start", "status", "stop"}:
            raise WorkbenchError("action 必须是 start、status 或 stop。")
        if action in {"start", "stop"} and inputs.get("confirmed") is not True:
            raise WorkbenchError("启动或停止前需要用户明确授权，并设置 confirmed=true。")
        workspace = workspace_path(inputs.get("workspace"))
        directory = runtime_dir(workspace, create=action == "start")
        for identity, child in tuple(_CHILDREN.items()):
            if child.poll() is not None:
                _CHILDREN.pop(identity, None)
        if directory is None:
            return _status(None, stopped=False) if action == "stop" else _status(None)
        if action == "status":
            state = read_state(directory)
            health = contact(state) if state else None
            return _status(state, health is not None, busy=bool(health and health.get("busy")))
        with state_lock(directory):
            state = read_state(directory)
            health = contact(state) if state else None
            if action == "start":
                if health:
                    return _status(state, True, started=False, busy=bool(health.get("busy")))
                return _start(directory)
            if health:
                contact(state, "stop")
                deadline = time.monotonic() + 4
                while time.monotonic() < deadline:
                    try:
                        if contact(state) is None:
                            break
                    except WorkbenchError:
                        # The verified service may close a concurrent health
                        # socket while shutting down. Only refusal establishes
                        # that the port is closed; retain state otherwise.
                        pass
                    time.sleep(0.05)
                else:
                    raise WorkbenchError("工作台仍在关闭，请稍后查询状态。")
            if state:
                # Re-read under the lock so a changed/invalid record is preserved.
                if read_state(directory) != state:
                    raise WorkbenchError("工作台状态已变化；保留原文件，请重新查询。")
                (directory / "server.json").unlink()
                child = _CHILDREN.pop(state["session_id"], None)
                if child:
                    child.wait(timeout=2)
            return _status(None, stopped=bool(health))
    except WorkbenchError as exc:
        return failure(str(exc))
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        return failure("工作台操作失败；请检查专用目录权限和插件文件，原有服务不会被强制终止。")
