"""插件独立静态服务生命周期；只保存会话记录，不保存轨道要素输入。

沿用仓库 offline-pipe-network-workbench 1.0.0 的已维护生命周期与安装身份校验；
不更改该插件。此模块只管理本安装、本工作目录中身份已核实的服务。
"""
import contextlib
import fcntl
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import select
import stat
import subprocess
import sys
import time

VERSION = "1.0.0"
PLUGIN = "offline-satellite-orbit-workbench"
ROOT = Path(__file__).resolve().parents[1]
RUNTIME_NAME = ".offline-satellite-orbit-workbench"
_CHILDREN = {}  # Strong references only to processes launched by this module; never saved PIDs.


def reap_children():
    for identity, process in list(_CHILDREN.items()):
        if process.poll() is not None:
            _CHILDREN.pop(identity, None)


def finish_child(identity, terminate=False):
    process = _CHILDREN.pop(identity, None)
    if process:
        if terminate and process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _CHILDREN[identity] = process


class InputError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


def error(code, message):
    return {"ok": False, "version": VERSION, "error": {"code": code, "message": message}}


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise InputError("invalid_runtime", "运行记录含重复字段；原记录保留。")
        value[key] = item
    return value


def read_json_file(path, limit=4096):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_nlink != 1 or info.st_mode & 0o077):
            raise InputError("invalid_runtime", "运行记录须是当前用户所有的独立普通文件，权限为 0600；不能是链接或设备。")
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise InputError("invalid_runtime", "运行记录超过大小限制。")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError):
        raise InputError("invalid_runtime", "运行记录无效；不会覆盖或删除。")


def workspace_path(value):
    if not isinstance(value, str) or not Path(value).is_absolute() or ".." in Path(value).parts:
        raise InputError("invalid_workspace", "workspace 必须是已存在的真实目录绝对路径，不能含 .. 或符号链接。")
    path = Path(value)
    for part in [*reversed(path.parents), path]:
        if not part.is_dir() or part.is_symlink():
            raise InputError("invalid_workspace", "workspace 及其上级必须是已存在的真实目录，不能含符号链接。")
    return path


def runtime_path(workspace, create=False):
    path = workspace / RUNTIME_NAME
    if create and not os.path.lexists(path):
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass  # A concurrent launcher may have created it; validate below.
    if os.path.lexists(path):
        if path.is_symlink() or not path.is_dir():
            raise InputError("invalid_runtime", "插件运行目录不能是链接或非目录对象。")
        info = path.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise InputError("invalid_runtime", "插件运行目录须由当前用户所有，且权限为 0700；不会自动修改既有目录权限。")
    return path


def read_state(directory):
    path = directory / "server.json"
    if not os.path.lexists(path):
        return None
    data = read_json_file(path)
    if (not isinstance(data, dict) or set(data) != {"plugin", "version", "port", "token", "instance", "root"} or
            data.get("plugin") != PLUGIN or data.get("version") != VERSION or
            type(data.get("port")) is not int or not 1 <= data["port"] <= 65535 or
            not isinstance(data.get("token"), str) or not re.fullmatch(r"[0-9a-f]{64}", data["token"]) or
            not isinstance(data.get("instance"), str) or not re.fullmatch(r"[0-9a-f]{32}", data["instance"]) or
            data.get("root") != str(ROOT)):
        raise InputError("invalid_runtime", "现有运行记录不属于当前插件安装或格式无效；不会覆盖或停止未知服务。")
    return data


def contact(state, stop=False):
    connection = http.client.HTTPConnection("127.0.0.1", state["port"], timeout=2)
    try:
        connection.request("POST" if stop else "GET", f'/{state["token"]}/__stop' if stop else f'/{state["token"]}/__health',
                           headers={"Host": f'127.0.0.1:{state["port"]}', "X-Workbench-Instance": state["instance"]})
        response = connection.getresponse()
        raw = response.read(4097)
        if response.status != 200 or len(raw) > 4096:
            return False
        data = json.loads(raw)
        return (isinstance(data, dict) and data.get("instance") == state["instance"] and
                data.get("version") == VERSION and data.get("plugin") == PLUGIN and
                data.get("running") is (not stop))
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        connection.close()


@contextlib.contextmanager
def runtime_lock(directory):
    descriptor = os.open(directory / "server.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                info.st_nlink != 1 or info.st_mode & 0o077):
            raise InputError("invalid_runtime", "运行锁不是当前用户的独立普通文件。")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def service_result(state, running, message, reused=False):
    return {"ok": True, "version": VERSION, "running": running,
            "reused": reused,
            "url": f'http://127.0.0.1:{state["port"]}/{state["token"]}/web/index.html' if running else None,
            "message": message, "idle_timeout_seconds": 1800,
            "boundary": "只向本机浏览器提供插件自带网页和示例；轨道要素在浏览器本地校验和轨道计算，导出由浏览器下载，不修改宿主或原件。"}


def workbench(inputs):
    try:
        reap_children()
        if not isinstance(inputs, dict) or set(inputs) - {"workspace", "action", "confirmed"}:
            raise InputError("invalid_input", "只接受 workspace、action 和可选的 confirmed 参数。")
        if "confirmed" in inputs and type(inputs["confirmed"]) is not bool:
            raise InputError("invalid_input", "confirmed 必须是布尔值，不能使用字符串或数字代替。")
        action = inputs.get("action")
        if not isinstance(action, str) or action not in {"start", "status", "stop"}:
            raise InputError("invalid_action", "action 必须为 start、status 或 stop。")
        if action in {"start", "stop"} and inputs.get("confirmed") is not True:
            raise InputError("confirmation_required", "启动或停止本插件服务需要用户明确确认；仅 status 为只读。")
        workspace = workspace_path(inputs.get("workspace"))
        directory = runtime_path(workspace, create=action == "start")
        if not directory.exists():
            return service_result(None, False, "此工作目录尚无本插件运行记录。")
        if action == "status":
            state = read_state(directory)
            running = bool(state and contact(state))
            return service_result(state, running, "本插件服务正在运行。" if running else "没有可验证的本插件运行服务。")
        read_state(directory)  # Reject foreign/corrupt records before even creating the lock.
        with runtime_lock(directory):
            state = read_state(directory)
            running = bool(state and contact(state))
            if action == "stop":
                if running and not contact(state, stop=True):
                    raise InputError("stop_failed", "未能验证停止响应；未向任何进程发送信号。")
                if running:
                    finish_child(state["instance"])
                    for _ in range(30):
                        if not contact(state):
                            break
                        time.sleep(.05)
                    else:
                        raise InputError("stop_pending", "已请求停止，但服务仍有响应；请稍后查询。未向未知进程发送信号。")
                return service_result(state, False, "已向已验证的本插件服务发送停止请求。" if running else "没有可验证的本插件运行服务；未操作其他进程。")
            if running:
                return service_result(state, True, "复用此工作目录中已验证的本插件服务。", reused=True)
            previous_state = state
            token, instance = secrets.token_hex(32), secrets.token_hex(16)
            process = subprocess.Popen([sys.executable, "-I", "-B", str(ROOT / "tools/server.py")],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                       cwd=ROOT, env={}, start_new_session=True)
            _CHILDREN[instance] = process
            try:
                process.stdin.write(json.dumps({"token": token, "instance": instance}).encode())
                process.stdin.close()
                # Read the bounded handshake without waiting for the long-lived server to exit.
                if not select.select([process.stdout], [], [], 5)[0]:
                    raise subprocess.TimeoutExpired(process.args, 5)
                output = process.stdout.readline(4097)
            except subprocess.TimeoutExpired:
                finish_child(instance, terminate=True)
                raise InputError("server_failed", "本插件服务未能及时启动，已停止刚创建的进程。")
            except OSError:
                finish_child(instance, terminate=True)
                raise InputError("server_failed", "新服务启动握手失败；已清理刚创建的进程。")
            finally:
                if not process.stdin.closed:
                    process.stdin.close()
                process.stdout.close()
            try:
                ready = json.loads(output)
                port = ready["port"]
                if type(port) is not int or not 1 <= port <= 65535:
                    raise ValueError()
                state = {"plugin": PLUGIN, "version": VERSION, "port": port, "token": token, "instance": instance, "root": str(ROOT)}
                if not contact(state):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                finish_child(instance, terminate=True)
                raise InputError("server_failed", "无法核实新服务的身份；没有修改已有服务记录。")
            temporary = directory / (".server-" + secrets.token_hex(8) + ".json")
            try:
                if read_state(directory) != previous_state:
                    raise InputError("runtime_changed", "启动过程中运行记录已变化；保留新记录，不覆盖其他会话。")
                descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(state, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, directory / "server.json")
            except (OSError, InputError):
                contact(state, stop=True)
                finish_child(instance)
                raise
            finally:
                if temporary.exists():
                    temporary.unlink()
            return service_result(state, True, "已启动本插件独立工作台；请用本机正常浏览器打开地址。")
    except InputError as exc:
        return error(exc.code, exc.message)
    except BlockingIOError:
        return error("busy", "此工作目录正在处理另一项服务操作，请稍后重试。")
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return error("runtime_failed", "无法安全读取或创建插件运行记录；未修改宿主或其他服务。")


if __name__ == "__main__":
    # Manual launcher uses exactly the same validation and lifecycle as the native tool.
    raw = sys.stdin.buffer.read(10001)
    try:
        request = json.loads(raw)
        result = workbench(request) if len(raw) <= 10000 else error("invalid_input", "输入过大。")
    except ValueError:
        result = error("invalid_input", "请输入有效 JSON 参数。")
    print(json.dumps(result, ensure_ascii=False))
