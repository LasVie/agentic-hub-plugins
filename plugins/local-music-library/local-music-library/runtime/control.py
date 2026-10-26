"""本地服务生命周期；只连接本插件的127.0.0.1会话。"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time
from urllib.request import build_opener, ProxyHandler, Request
from urllib.parse import urlsplit

if __package__:
    from .library import VERSION, LibraryError, canonical_directory, fail, read_json
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from library import VERSION, LibraryError, canonical_directory, fail, read_json


def request(info, endpoint, body=None):
    url = info.get("url", "")
    p = urlsplit(url)
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}/[A-Za-z0-9_-]{43}/", url) or not p.port:
        fail("invalid_session", "本地会话地址损坏；未连接。")
    data = None if body is None else json.dumps(body).encode()
    req = Request(url + "api/" + endpoint, data=data, headers={"Content-Type": "application/json"})
    with build_opener(ProxyHandler({})).open(req, timeout=3) as response:
        value = json.loads(response.read(512 * 1024))
    return value


def state_directory(workspace, root, create=True):
    base = canonical_directory(workspace)
    if base == root or base.is_relative_to(root):
        fail("state_in_library", "工作目录必须位于音频目录之外，以免向曲库写入状态。")
    folder = base / ".local-music-library"
    target = folder / hashlib.sha256(str(root).encode()).hexdigest()[:24]
    if not create and not target.exists():
        return target
    for directory in (folder, target):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        if directory.is_symlink() or not directory.is_dir() or directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
            fail("unsafe_state", "状态目录必须为当前用户私有目录，且不能是符号链接。")
    return directory


def execute(inputs):
    if not isinstance(inputs, dict) or set(inputs) - {"action", "library_dir", "workspace", "confirmed"}:
        fail("invalid_input", "仅接受 action、library_dir、workspace 和 confirmed。")
    action = inputs.get("action")
    if action not in ("start", "status", "stop"):
        fail("invalid_action", "action 必须为 start、status 或 stop。")
    if action in ("start", "stop") and inputs.get("confirmed") is not True:
        fail("confirmation_required", "启动或关闭本地服务需要用户明确授权，并提供 confirmed=true。")
    root = canonical_directory(inputs.get("library_dir"))
    folder = state_directory(inputs.get("workspace"), root, create=action == "start")
    if not folder.exists():
        return {"ok": True, "version": VERSION, "running": False, "message": "当前曲库没有运行会话。"}
    root_key = hashlib.sha256(str(root).encode()).hexdigest()
    fd = os.open(folder / "control.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        session_path = folder / "session.json"
        info = None
        if session_path.exists() or session_path.is_symlink():
            try:
                info = read_json(session_path)
                if not isinstance(info, dict) or info.get("root_key") != root_key or info.get("version") != VERSION:
                    fail("invalid_session", "状态版本或曲库身份不一致；未自动修改。")
            except (ValueError, OSError):
                fail("invalid_session", "会话状态无效；请检查状态文件，不要根据 PID 手动终止其他进程。")
        alive = False
        if info and info.get("status") == "running":
            try:
                health = request(info, "health")
                alive = health.get("plugin") == "local-music-library" and health.get("session_id") == info.get("session_id") and health.get("root_key") == root_key and health.get("version") == VERSION
            except Exception:
                alive = False
        if action == "status":
            if not alive:
                return {"ok": True, "version": VERSION, "running": False, "message": "当前曲库没有可验证的运行会话。"}
        elif action == "stop":
            if not alive:
                return {"ok": True, "version": VERSION, "running": False, "message": "没有可验证的服务，未终止任何进程。"}
            request(info, "stop", {})
            for _ in range(30):
                time.sleep(.1)
                if read_json(session_path).get("status") == "stopped":
                    break
            else:
                fail("stop_pending", "已请求关闭，但尚未确认完成；请稍后查询。")
            return {"ok": True, "version": VERSION, "running": False, "message": "已关闭本插件的本地服务，音频和歌单均已保留。"}
        elif not alive:
            # A lifetime file lock prevents simultaneous writers, even after an
            # unresponsive server; never terminate a process by a saved PID.
            sid = secrets.token_hex(12)
            log = folder / ("startup-" + sid + ".log")
            log_fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(log_fd, "wb") as output:
                process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).with_name("server.py"))],
                    stdin=subprocess.PIPE, stdout=output, stderr=output, start_new_session=True,
                    cwd=str(Path(__file__).parent), env={"PATH": "/usr/bin:/bin", "LANG": "zh_CN.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"})
            config = {"root": str(root), "state_dir": str(folder), "session_id": sid, "root_key": root_key}
            process.stdin.write((json.dumps(config) + "\n").encode())
            process.stdin.close()
            for _ in range(80):
                if process.poll() is not None:
                    fail("start_failed", "本地服务未启动；请检查私有启动日志，或先关闭已有会话。")
                try:
                    candidate = read_json(session_path)
                    if candidate.get("session_id") == sid and request(candidate, "health").get("session_id") == sid:
                        info = candidate
                        alive = True
                        break
                except Exception:
                    pass
                time.sleep(.1)
            if not alive:
                # This process was created here; no unrelated process is touched.
                process.terminate()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=2)
                fail("start_timeout", "本次服务启动超时，未确认成功。")
            threading.Thread(target=process.wait, daemon=True).start()
        manifest = request(info, "library")
        return {"ok": True, "version": VERSION, "display_name": "本地音乐库", "running": True,
                "url": info["url"], "session_id": info["session_id"], "scan": manifest["scan"],
                "playlist_count": len(manifest["playlists"]),
                "message": "本地播放器已就绪；请在桌面浏览器打开返回地址并点击播放。链接含本地会话凭据，请勿公开分享。30分钟无请求会关闭服务，可重新启动。列出曲目不等于已验证解码或听感。"}
    finally:
        os.close(fd)


def safe_execute(inputs):
    try:
        return execute(inputs)
    except LibraryError as e:
        return {"ok": False, "version": VERSION, "code": e.code, "message": str(e)}
    except BlockingIOError:
        return {"ok": False, "version": VERSION, "code": "busy", "message": "同一工作目录正在处理操作，请稍后重试。"}
    except Exception:
        return {"ok": False, "version": VERSION, "code": "operation_failed", "message": "操作失败；请检查目录、权限和状态，未确认成功。"}


if __name__ == "__main__":
    if sys.argv[1:] in (["--help"], ["-h"]):
        print('本地音乐库：python control.py \'{"action":"start","library_dir":"/音频目录","workspace":"/独立工作目录","confirmed":true}\'\n操作：start 启动、status 查询、stop 关闭。仅回环；无模型或外网调用。')
        raise SystemExit(0)
    try:
        value = json.loads(sys.argv[1]) if len(sys.argv) == 2 else None
        result = safe_execute(value)
    except (ValueError, TypeError):
        result = {"ok": False, "version": VERSION, "message": "请提供一个 JSON 对象参数，使用 --help 查看中文帮助。"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 2)
