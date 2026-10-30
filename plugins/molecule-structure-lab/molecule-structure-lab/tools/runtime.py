"""离线工具运行边界；不修改宿主、不安装依赖、不保存分子输入。"""
import contextlib
import fcntl
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import select
import shutil
import stat
import subprocess
import sys
import threading

VERSION = "1.0.1"
ROOT = Path(__file__).resolve().parents[1]
RUNTIME_NAME = ".molecule-structure-lab"
ENGINE_SLOTS = threading.BoundedSemaphore(2)
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


def read_json_file(path, limit=4096):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise InputError("invalid_file", "配置和运行记录必须是普通文件，不能是链接或设备。")
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise InputError("invalid_file", "配置或运行记录超过大小限制。")
    return json.loads(raw.decode("utf-8"))


def node_executable():
    config = ROOT / "settings.json"
    configured = None
    if os.path.lexists(config):
        value = read_json_file(config)
        if not isinstance(value, dict) or set(value) != {"node_executable"}:
            raise InputError("invalid_configuration", "settings.json 只能包含 node_executable 字段。")
        configured = value["node_executable"]
    path = configured if configured is not None else os.environ.get("MOLECULE_WORKBENCH_NODE") or shutil.which("node")
    if not isinstance(path, str) or not Path(path).is_absolute() or not Path(path).is_file() or not os.access(path, os.X_OK):
        raise InputError("node_unavailable", "代理计算需要 Node.js 18 或更新版本；请配置插件 settings.json 的 node_executable 绝对路径。浏览器工作台不需要 Node.js。")
    result = subprocess.run([path, "--version"], capture_output=True, timeout=3, check=False,
                            env={k: v for k, v in os.environ.items() if k not in {"NODE_OPTIONS", "NODE_PATH"}})
    match = re.fullmatch(rb"v(\d+)\.\d+\.\d+\s*", result.stdout)
    if result.returncode or not match or int(match[1]) < 18:
        raise InputError("node_unavailable", "已配置的可执行文件未通过 Node.js 18 或更新版本检查。")
    return path


def analyze(inputs):
    if not isinstance(inputs, dict) or set(inputs) - {"smiles", "smarts"} or not isinstance(inputs.get("smiles"), str) or not isinstance(inputs.get("smarts", ""), str):
        return error("invalid_input", "参数只能包含字符串 smiles 和可选的字符串 smarts。")
    if len(inputs["smiles"]) > 1024 or len(inputs.get("smarts", "")) > 512:
        return error("input_too_large", "SMILES 最多 1024 个字符，SMARTS 最多 512 个字符。")
    if not ENGINE_SLOTS.acquire(blocking=False):
        return error("busy", "已有两个本地计算正在运行，请稍后重试。")
    try:
        node = node_executable()
        env = {k: v for k, v in os.environ.items() if k not in {"NODE_OPTIONS", "NODE_PATH"}}
        result = subprocess.run([node, "--max-old-space-size=128", "--wasm-max-mem-pages=4096",
                                 str(ROOT / "engine/node_bridge.cjs")],
                                input=json.dumps(inputs, ensure_ascii=True).encode(), capture_output=True,
                                timeout=12, check=False, cwd=ROOT, env=env)
        if len(result.stdout) > 1500000:
            return error("output_too_large", "引擎输出超过限制，未返回不完整结果。")
        data = json.loads(result.stdout)
        if not isinstance(data, dict) or data.get("version") != VERSION or type(data.get("ok")) is not bool:
            return error("engine_failed", "引擎返回格式或版本不符，未使用其结果。")
        return data
    except InputError as exc:
        return error(exc.code, exc.message)
    except subprocess.TimeoutExpired:
        return error("calculation_timeout", "本地计算超过 12 秒已终止；请缩小分子或查询，不把超时当作未匹配。")
    except (OSError, ValueError, TypeError):
        return error("engine_failed", "无法运行离线引擎；请检查 Node.js 配置及随包 JS/WASM 文件。")
    finally:
        ENGINE_SLOTS.release()


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
        path.mkdir(mode=0o700)
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
    if (not isinstance(data, dict) or set(data) != {"version", "port", "token", "instance", "root"} or
            data.get("version") != VERSION or type(data.get("port")) is not int or not 1 <= data["port"] <= 65535 or
            not isinstance(data.get("token"), str) or not re.fullmatch(r"[0-9a-f]{64}", data["token"]) or
            not isinstance(data.get("instance"), str) or not re.fullmatch(r"[0-9a-f]{32}", data["instance"]) or
            data.get("root") != str(ROOT)):
        raise InputError("invalid_runtime", "现有运行记录不属于当前插件安装或格式无效；不会覆盖或停止未知服务。")
    return data


def contact(state, stop=False):
    connection = http.client.HTTPConnection("127.0.0.1", state["port"], timeout=2)
    try:
        connection.request("POST" if stop else "GET", f'/{state["token"]}/__stop' if stop else f'/{state["token"]}/__health',
                           headers={"Host": f'127.0.0.1:{state["port"]}'})
        response = connection.getresponse()
        raw = response.read(4097)
        if response.status != 200 or len(raw) > 4096:
            return False
        data = json.loads(raw)
        return data.get("instance") == state["instance"] and data.get("version") == VERSION
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        connection.close()


@contextlib.contextmanager
def runtime_lock(directory):
    descriptor = os.open(directory / "server.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise InputError("invalid_runtime", "运行锁不是当前用户的独立普通文件。")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def service_result(state, running, message):
    return {"ok": True, "version": VERSION, "running": running,
            "url": f'http://127.0.0.1:{state["port"]}/{state["token"]}/web/index.html' if running else None,
            "message": message, "idle_timeout_seconds": 1800,
            "boundary": "只向本机浏览器提供插件自带静态文件；分子在浏览器本地计算，导出由浏览器下载，不修改宿主。"}


def workbench(inputs):
    try:
        reap_children()
        if not isinstance(inputs, dict) or set(inputs) - {"workspace", "action", "confirmed"}:
            raise InputError("invalid_input", "只接受 workspace、action 和可选的 confirmed 参数。")
        action = inputs.get("action")
        if action not in {"start", "status", "stop"}:
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
        with runtime_lock(directory):
            state = read_state(directory)
            running = bool(state and contact(state))
            if action == "stop":
                if running and not contact(state, stop=True):
                    raise InputError("stop_failed", "未能验证停止响应；未向任何进程发送信号。")
                if running:
                    finish_child(state["instance"])
                return service_result(state, False, "已向已验证的本插件服务发送停止请求。" if running else "没有可验证的本插件运行服务；未操作其他进程。")
            if running:
                return service_result(state, True, "复用此工作目录中已验证的本插件服务。")
            token, instance = secrets.token_hex(32), secrets.token_hex(16)
            process = subprocess.Popen([sys.executable, "-B", str(ROOT / "tools/server.py")],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                       cwd=ROOT, start_new_session=True)
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
                state = {"version": VERSION, "port": port, "token": token, "instance": instance, "root": str(ROOT)}
                if not contact(state):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                finish_child(instance, terminate=True)
                raise InputError("server_failed", "无法核实新服务的身份；没有修改已有服务记录。")
            temporary = directory / (".server-" + secrets.token_hex(8) + ".json")
            try:
                descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(state, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, directory / "server.json")
            except OSError:
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
