"""Desktop OAuth adapted from the team-owned Gmail 1.5.1 connector."""
from __future__ import annotations

import contextlib
import json
import logging
import os
from pathlib import Path
import stat
import tempfile
import uuid

from bootstrap_lock import file_lock

from google.auth.exceptions import RefreshError, TransportError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URIS = {"https://accounts.google.com/o/oauth2/auth", "https://accounts.google.com/o/oauth2/v2/auth"}


class Error(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def root() -> Path:
    path = Path(os.environ.get("WORKSWARM_GOOGLE_WORKSPACE_HOME", str(Path.home() / ".local/share/agentic-hub/google-workspace"))).expanduser()
    if not path.is_absolute() or path.is_symlink():
        raise Error("unsafe_storage", "Google 凭据目录必须是非符号链接的绝对路径。")
    path = path.resolve()
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise Error("unsafe_storage", "凭据目录必须位于源码仓库之外。")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    mode = path.stat()
    if os.name != "nt" and (mode.st_uid != os.getuid() or mode.st_mode & 0o077):
        raise Error("unsafe_storage", "凭据目录须归当前用户所有，权限为 700。")
    return path


def lock(path):
    return file_lock(path / "credentials.lock")


def read(file):
    if file.is_symlink():
        raise Error("unsafe_storage", "凭据文件不能是符号链接。")
    try:
        with os.fdopen(os.open(file, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)), "r", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 32768:
                raise ValueError
            if os.name != "nt" and (info.st_uid != os.getuid() or info.st_mode & 0o077):
                raise ValueError
            value = json.load(stream)
            if not isinstance(value, dict):
                raise ValueError
            return value
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        raise Error("invalid_credentials", "本地凭据不可读取，请检查文件格式和访问权限。") from None


def write(file, value):
    if file.is_symlink():
        raise Error("unsafe_storage", "凭据文件不能是符号链接。")
    fd, temporary = tempfile.mkstemp(prefix=".google-", dir=file.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, file)
    finally:
        Path(temporary).unlink(missing_ok=True)


def validate_client(value):
    try:
        installed = value["installed"]
        fields = {key: installed[key] for key in ("client_id", "client_secret", "auth_uri", "token_uri")}
        if (not all(isinstance(item, str) and item for item in fields.values())
                or not fields["client_id"].endswith(".apps.googleusercontent.com")
                or fields["auth_uri"] not in AUTH_URIS or fields["token_uri"] != TOKEN_URI):
            raise ValueError
    except (KeyError, ValueError, TypeError):
        raise Error("invalid_client", "请导入 Google Cloud 创建的 Desktop app OAuth 客户端 JSON。") from None
    return {"installed": fields}


def configure(source):
    try:
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 32768:
            raise ValueError
        value = validate_client(json.loads(source.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        raise Error("invalid_client", "无法读取 Desktop OAuth 客户端 JSON。") from None
    path = root()
    with lock(path):
        current = read(path / "client.json")
        if current != value:
            if any(path.glob("google-*.token.json")):
                raise Error("sessions_exist", "请先断开此电脑上的 Google Workspace 卡片，再更换客户端。")
            write(path / "client.json", value)
    return {"message": "Desktop OAuth 配置已保存。请回到 WorkSwarm 点击相应卡片的「连接」。"}


def client(path):
    value = read(path / "client.json")
    if value is None:
        raise Error("client_config_required", "请按连接器说明导入自己的 Desktop OAuth JSON，再点「连接」。")
    return validate_client(value)


@contextlib.contextmanager
def silence_sensitive_logs():
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


class DesktopFlow(InstalledAppFlow):
    def fetch_token(self, **kwargs):
        kwargs["timeout"] = (10, 30)
        return super().fetch_token(**kwargs)


def sign_in(slug, scope, label, open_browser):
    path = root()
    token_file = path / f"{slug}.token.json"
    attempt_file = path / f"{slug}.login.json"
    attempt = {"id": uuid.uuid4().hex}
    with lock(path):
        configuration = client(path)
        write(attempt_file, attempt)
    try:
        flow = DesktopFlow.from_client_config(configuration, [scope], autogenerate_code_verifier=True)
        flow.oauth2session.trust_env = False
        with silence_sensitive_logs():
            credentials = flow.run_local_server(
                host="127.0.0.1", port=0, open_browser=open_browser, timeout_seconds=180,
                authorization_prompt_message=f"请在系统浏览器核对 {label} 所需权限。\n{{url}}",
                success_message="Google 授权已返回本机，请回到 WorkSwarm 查看状态。",
                access_type="offline", prompt="consent", include_granted_scopes="false",
            )
        if set(credentials.scopes if credentials.granted_scopes is None else credentials.granted_scopes) != {scope}:
            raise Error("scope_mismatch", "Google 返回的权限和本卡片所需权限不一致，请重新连接。")
        if not credentials.refresh_token:
            raise Error("missing_refresh", "Google 未返回刷新凭据，请重新授权。")
        with lock(path):
            if read(attempt_file) != attempt or client(path) != configuration:
                raise Error("login_cancelled", "本次登录已取消或客户端已更换，请重新连接。")
            save_credentials(token_file, credentials, scope, attempt["id"], configuration["installed"]["client_id"])
    except Error:
        raise
    except Exception:
        raise Error("authorization_failed", "Google 授权未完成。请检查测试账号、授权期限和组织访问设置。") from None
    finally:
        with lock(path):
            if read(attempt_file) == attempt:
                attempt_file.unlink()
    return {"message": f"{label} 授权已保存。请回到 WorkSwarm。"}


def save_credentials(file, credentials, scope, session_id, client_id):
    write(file, {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expiry": json.loads(credentials.to_json()).get("expiry"),
        "scopes": [scope],
        "session_id": session_id,
        "client_id": client_id,
    })


def load(path, token_file, scope):
    value = read(token_file)
    if not value:
        raise Error("not_signed_in", "尚未授权，请从对应的 WorkSwarm 卡片连接 Google。")
    configuration = client(path)["installed"]
    if value.get("scopes") != [scope] or value.get("client_id") != configuration["client_id"]:
        raise Error("scope_mismatch", "本地会话与此卡片的权限或客户端不匹配，请重新连接。")
    try:
        if not value.get("session_id") or not value.get("refresh_token"):
            raise ValueError
        credentials = Credentials.from_authorized_user_info(
            {**value, "client_secret": configuration["client_secret"]}, scopes=[scope],
        )
    except (TypeError, ValueError):
        raise Error("invalid_credentials", "本地授权记录无效，请重新连接。") from None
    return credentials, value


def access_token(slug, scope, request, rejected=None):
    path = root()
    file = path / f"{slug}.token.json"
    with lock(path):
        credentials, state = load(path, file, scope)
        if not credentials.valid or (rejected is not None and credentials.token == rejected):
            try:
                with silence_sensitive_logs():
                    credentials.refresh(request)
            except TransportError:
                raise Error("network_error", "暂时无法连接 Google 刷新令牌，请稍后重试。") from None
            except RefreshError as exc:
                details = exc.args[1] if len(exc.args) > 1 and isinstance(exc.args[1], dict) else {}
                if details.get("error") in {"invalid_grant", "invalid_client"}:
                    file.unlink()
                    raise Error("reauth_required", "Google 授权已过期或被撤销，请重新连接。") from None
                raise Error("refresh_failed", "Google 暂时无法刷新授权，请稍后重试。") from None
            if set(credentials.scopes if credentials.granted_scopes is None else credentials.granted_scopes) != {scope}:
                file.unlink()
                raise Error("scope_mismatch", "刷新后的权限与本卡片不符，请重新连接。")
            save_credentials(file, credentials, scope, state["session_id"], state["client_id"])
        return credentials.token


def status(slug, scope):
    path = root()
    with lock(path):
        credentials, _ = load(path, path / f"{slug}.token.json", scope)
    return {"signed_in_local": True, "access_token_expired": credentials.expired,
            "message": "本地 Google 会话已就绪。实际访问权限由 Google 在操作时检查。"}


def sign_out(slug):
    path = root()
    with lock(path):
        for name in (f"{slug}.token.json", f"{slug}.login.json"):
            (path / name).unlink(missing_ok=True)
    return {"message": "此卡片的本地会话已清除。可在 Google 账号设置撤销整个项目的授权。"}
