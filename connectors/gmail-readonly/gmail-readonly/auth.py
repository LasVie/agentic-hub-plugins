"""Google-library OAuth and private local state; never log provider responses."""
from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import stat
import tempfile
import time
import uuid
import webbrowser

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow as _GoogleInstalledAppFlow

import workspace_oauth

SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
SCOPES = [SCOPE, COMPOSE_SCOPE]
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"


class InstalledAppFlow(_GoogleInstalledAppFlow):
    """Public flow extension: callback timeout does not bound token HTTP I/O."""
    def fetch_token(self, **kwargs):
        kwargs["timeout"] = (10, 30)
        return super().fetch_token(**kwargs)


class ConnectorError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


@contextlib.contextmanager
def _sensitive_exchange():
    # OAuth libraries can log complete token request/response bodies at DEBUG.
    # This runs only inside the connector/helper subprocess, never in the host.
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


def state_root() -> Path:
    root = Path(os.environ.get("GMAIL_READONLY_HOME", str(Path.home() / ".local/share/agentic-hub/gmail-readonly"))).expanduser()
    if not root.is_absolute() or root.is_symlink():
        raise ConnectorError("unsafe_storage", "凭据目录必须是非符号链接的绝对路径。")
    resolved = root.resolve()
    payload = Path(__file__).resolve().parent
    # Runtime state must never become distributable package/repository content.
    if resolved == payload or payload in resolved.parents or any((p / ".git").exists() for p in [resolved, *resolved.parents]):
        raise ConnectorError("unsafe_storage", "请将凭据目录放在源码仓库和安装包之外。")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt" and (root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode) & 0o077):
        raise ConnectorError("unsafe_storage", "凭据目录必须由当前用户拥有，权限应为 700。")
    return root


def _read(path: Path) -> dict:
    try:
        # NOFOLLOW also closes the final-component symlink race on Unix.
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "r", encoding="utf-8") as f:
            st = os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_size > 32768:
                raise ValueError()
            if os.name != "nt" and (st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) & 0o077):
                raise ValueError()
            value = json.load(f)
            if not isinstance(value, dict):
                raise ValueError()
            return value
    except FileNotFoundError:
        raise ConnectorError("not_signed_in", "尚未配置或登录；请按 README 完成开发者配置与浏览器登录。") from None
    except (OSError, ValueError, UnicodeError):
        raise ConnectorError("unsafe_credentials", "本地凭据无效或权限不安全；请检查私有目录，不要粘贴令牌。") from None


def _write(path: Path, value: dict) -> None:
    if path.is_symlink():
        raise ConnectorError("unsafe_storage", "拒绝写入符号链接。")
    fd, tmp = tempfile.mkstemp(prefix=".credential-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            os.chmod(tmp, 0o600)
            json.dump(value, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def state_lock():
    path = state_root() / "state.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "r+b") as f:
        if os.name == "nt":
            import msvcrt
            f.seek(0); f.write(b"0"); f.flush(); f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def validate_client(value: dict) -> dict:
    cfg = value.get("installed")
    if not isinstance(cfg, dict) or not cfg.get("client_id") or not cfg.get("client_secret"):
        raise ConnectorError("invalid_client", "需要开发者下载的 Desktop app OAuth 客户端 JSON，而非网页客户端或令牌。")
    if cfg.get("auth_uri") not in (AUTH_URI, "https://accounts.google.com/o/oauth2/v2/auth") or cfg.get("token_uri") != TOKEN_URI:
        raise ConnectorError("invalid_client", "仅允许 Google 官方授权与令牌端点。")
    return {"installed": {k: cfg[k] for k in ("client_id", "client_secret", "auth_uri", "token_uri")}}


def configure(client_file: Path) -> dict:
    try:
        if client_file.is_symlink() or client_file.stat().st_size > 32768:
            raise ValueError()
        value = validate_client(json.loads(client_file.read_text(encoding="utf-8")))
    except (OSError, ValueError, UnicodeError):
        raise ConnectorError("invalid_client", "无法读取 Desktop OAuth 客户端 JSON。") from None
    with state_lock():
        root = state_root()
        if (root / "token.json").exists():
            raise ConnectorError("session_exists", "已有登录会话；请先退出登录，再更换开发者客户端。")
        # Invalidate an outstanding browser attempt using the previous client.
        (root / "login.json").unlink(missing_ok=True)
        _write(root / "client.json", value)
    return {"ok": True, "message": "开发者客户端已保存到私有目录；尚未登录或访问邮箱。"}


def _scope_set(scopes) -> set[str]:
    if isinstance(scopes, str):
        scopes = scopes.split()
    if not isinstance(scopes, (list, tuple)) or any(not isinstance(scope, str) for scope in scopes):
        return set()
    return set(scopes)


def _check_scopes(scopes, expected) -> None:
    if _scope_set(scopes) != _scope_set(expected):
        raise ConnectorError("scope_mismatch", "Google 返回的授权范围与请求不一致，请重新连接并核对同意页权限。")


def _granted_scopes(creds: Credentials):
    if creds.granted_scopes is not None:
        return creds.granted_scopes
    return creds.scopes


def _managed_call(operation, *args):
    try:
        return operation(*args)
    except workspace_oauth.ServiceError as exc:
        messages = {
            "reauth_required": "Google 授权已失效。请重新连接 Gmail。",
            "authorization_denied": "你未允许 Gmail 访问。可随时重新发起连接。",
            "scope_or_grant_incomplete": "Google 未授予所需的邮件读取权限，或返回了不适用的权限。",
            "service_configuration": "Google 授权服务配置无效，请联系管理员。",
        }
        raise ConnectorError(exc.code, messages.get(exc.code, "暂时无法完成 Google 授权，请稍后重试。")) from None


def _managed_grant(value):
    scopes = _scope_set(value.get("scopes"))
    if scopes not in ({SCOPE}, set(SCOPES)):
        raise ConnectorError("scope_mismatch", "Google 返回的授权范围不适用于 Gmail，请重新连接。")
    return sorted(scopes)


def _managed_expiry(value):
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=value["expires_in"])


def _managed_sign_in(base: str, *, open_browser: bool) -> dict:
    root = state_root()
    attempt = uuid.uuid4().hex
    with state_lock():
        previous = _read(root / "token.json") if (root / "token.json").exists() else {}
        if _scope_set(previous.get("scopes")) == set(SCOPES):
            raise ConnectorError("session_exists", "已有 Gmail 登录会话。请先断开连接，再重新登录。")
        _write(root / "login.json", {"attempt": attempt})
    proof = None
    committed = False
    try:
        proof, url = _managed_call(workspace_oauth.start, base, SCOPES)
        print(f"请在浏览器核对 Gmail 权限并授权。\n{url}", flush=True)
        if open_browser:
            webbrowser.open(url)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            value = _managed_call(workspace_oauth.token, base, proof)
            if value is not None:
                break
            time.sleep(2)
        else:
            raise ConnectorError("authorization_timeout", "等待 Google 授权超时，请重新连接。")
        scopes = _managed_grant(value)
        with state_lock():
            if _read(root / "login.json").get("attempt") != attempt:
                raise ConnectorError("login_cancelled", "本次登录已取消，请重新发起。")
            if previous.get("method") == "workspace" and previous.get("service_origin") == base:
                _managed_call(workspace_oauth.disconnect, base, previous["proof"])
            _write(root / "token.json", {"method": "workspace", "service_origin": base,
                       "proof": proof, "scopes": scopes, "session_id": attempt,
                       "expiry": _managed_expiry(value).isoformat()})
            committed = True
    finally:
        if proof is not None and not committed:
            with contextlib.suppress(workspace_oauth.ServiceError):
                workspace_oauth.disconnect(base, proof)
        with state_lock():
            try:
                if _read(root / "login.json").get("attempt") == attempt:
                    (root / "login.json").unlink()
            except ConnectorError:
                pass
    message = "Gmail 授权完成。请返回 WorkSwarm。"
    if COMPOSE_SCOPE not in scopes:
        message = "Gmail 已连接，当前仅可读取。需要草稿或发送功能时，请重新授权。"
    return {"ok": True, "message": message}


def sign_in(*, open_browser: bool = True) -> dict:
    base = _managed_call(workspace_oauth.origin)
    if base:
        return _managed_sign_in(base, open_browser=open_browser)
    root = state_root()
    # No lock while the browser is open. A generation reservation prevents a
    # cancelled login from restoring credentials after sign_out/configure.
    attempt = uuid.uuid4().hex
    with state_lock():
        try:
            client = validate_client(_read(root / "client.json"))
        except ConnectorError as exc:
            if exc.code != "not_signed_in":
                raise
            raise ConnectorError("client_config_required", "请先在自己的 Google Cloud 项目创建 Desktop app 客户端，按连接器说明导入 JSON，再点连接。") from None
        token = root / "token.json"
        if token.exists() or token.is_symlink():
            if _scope_set(_read(token).get("scopes")) != {SCOPE}:
                raise ConnectorError("session_exists", "已有本地登录会话；需要重新登录时请先退出登录。")
        _write(root / "login.json", {"attempt": attempt})
    try:
        flow = InstalledAppFlow.from_client_config(client, SCOPES, autogenerate_code_verifier=True)
        # Match the API and refresh transports: direct Google only, no inherited
        # proxy / .netrc / CA override. No host network settings are changed.
        flow.oauth2session.trust_env = False
        with _sensitive_exchange():
            creds = flow.run_local_server(
                host="127.0.0.1", port=0, open_browser=open_browser, timeout_seconds=180,
                authorization_prompt_message="请在系统浏览器核对并授予 Gmail 读取、草稿与发送权限。\n{url}",
                success_message="Gmail 授权已返回本机。可关闭此页并回到 WorkSwarm。",
                access_type="offline", prompt="consent", include_granted_scopes="false",
            )
        _check_scopes(_granted_scopes(creds), SCOPES)
        if not creds.refresh_token:
            raise ConnectorError("missing_refresh", "未获得刷新凭据；请撤销旧授权后重新登录。")
        value = json.loads(creds.to_json())
        value["scopes"] = SCOPES
        value["session_id"] = uuid.uuid4().hex
        with state_lock():
            if _read(root / "login.json").get("attempt") != attempt:
                raise ConnectorError("login_cancelled", "本次登录已取消，请重新发起。")
            _write(root / "token.json", value)
            (root / "login.json").unlink()
    except ConnectorError:
        raise
    except Exception:
        # OAuth exceptions can contain callback codes and provider responses.
        raise ConnectorError("authorization_failed", "Google 授权未完成、被拒绝或已超时；未访问邮箱。请检查客户端、测试用户与账号策略。") from None
    finally:
        with state_lock():
            try:
                if _read(root / "login.json").get("attempt") == attempt:
                    (root / "login.json").unlink()
            except ConnectorError:
                pass
    return {"ok": True, "message": "Gmail 读取、草稿与发送授权已保存。请回到 WorkSwarm 查看连接状态。"}


class StoredCredentials(Credentials):
    """Persist refresh only while this exact local login is still active."""
    session_id: str

    def refresh(self, request):
        with state_lock():
            path = state_root() / "token.json"
            current = _read(path)
            if current.get("session_id") != self.session_id:
                raise ConnectorError("signed_out", "该登录会话已退出，请重新登录。")
            try:
                with _sensitive_exchange():
                    super().refresh(request)
            except Exception:
                raise ConnectorError("reauth_required", "授权已过期、被撤销或刷新失败；请重新登录。") from None
            _check_scopes(_granted_scopes(self), current.get("scopes"))
            value = json.loads(self.to_json())
            value["session_id"] = self.session_id
            _write(path, value)


class WorkspaceCredentials(Credentials):
    """Fetch a short-lived Google token without persisting it on the client."""

    def __init__(self, session, require_compose):
        super().__init__(None, scopes=session["scopes"], expiry=datetime.fromisoformat(session["expiry"]))
        self.session_id = session["session_id"]
        self.require_compose = require_compose

    def refresh(self, _request):
        with state_lock():
            path = state_root() / "token.json"
            session = _read(path)
            if session.get("session_id") != self.session_id:
                raise ConnectorError("signed_out", "该登录会话已退出，请重新登录。")
            base = _managed_call(workspace_oauth.origin)
            if not base or session["service_origin"] != base:
                raise ConnectorError("reauth_required", "授权服务已更改，请断开连接后重新授权。")
            try:
                for _ in range(3):
                    value = _managed_call(workspace_oauth.token, base, session["proof"])
                    if value is not None:
                        break
                    time.sleep(1)
                else:
                    raise ConnectorError("service_unavailable", "正在刷新 Google 授权，请稍后重试。")
            except ConnectorError as exc:
                if exc.code == "reauth_required":
                    path.unlink()
                raise
            scopes = _managed_grant(value)
            if not set(scopes) <= set(session["scopes"]):
                raise ConnectorError("scope_mismatch", "刷新后的 Google 权限与原连接不一致，请重新授权。")
            self.expiry = _managed_expiry(value)
            _write(path, {**session, "scopes": scopes, "expiry": self.expiry.isoformat()})
            if self.require_compose and COMPOSE_SCOPE not in scopes:
                raise ConnectorError("compose_required", "当前仅有读取权限，请重新连接并授予 Gmail 草稿和发送权限。")
            self.token = value["access_token"]


def load_credentials(*, require_compose: bool = False) -> Credentials:
    with state_lock():
        value = _read(state_root() / "token.json")
        granted = _scope_set(value.get("scopes"))
        if granted not in ({SCOPE}, set(SCOPES)):
            raise ConnectorError("scope_mismatch", "本地 Gmail 授权范围不受支持，请重新连接。")
        if require_compose and COMPOSE_SCOPE not in granted:
            raise ConnectorError("compose_required", "当前仅有读取权限，请重新连接并授予 Gmail 草稿和发送权限。")
        try:
            if value.get("method") == "workspace":
                if (not value.get("session_id") or not isinstance(value.get("proof"), str)
                        or not workspace_oauth.KEY.fullmatch(value["proof"])
                        or not isinstance(value.get("service_origin"), str)):
                    raise ValueError()
                return WorkspaceCredentials(value, require_compose)
            if value.get("token_uri") != TOKEN_URI or not value.get("session_id") or not value.get("refresh_token"):
                raise ConnectorError("unsafe_credentials", "本地凭据格式不受支持；请重新登录。")
            scopes = [scope for scope in SCOPES if scope in granted]
            creds = StoredCredentials.from_authorized_user_info(value, scopes=scopes)
            creds.session_id = value["session_id"]
            return creds
        except (KeyError, ValueError, TypeError):
            raise ConnectorError("unsafe_credentials", "本地凭据无法加载；请重新登录。") from None


def session_status() -> dict:
    try:
        creds = load_credentials()
        return {"ok": True, "signed_in_local": True, "write_enabled": creds.has_scopes([COMPOSE_SCOPE]),
                "access_token_expired": creds.expired,
                "provider_access_verified": False, "message": "仅检查本地凭据，未联系 Google 或读取邮箱。"}
    except ConnectorError as e:
        return {"ok": False, "signed_in_local": False, "write_enabled": False,
                "error": {"code": e.code, "message": e.message}}


def sign_out() -> dict:
    with state_lock():
        root = state_root()
        path = root / "token.json"
        if path.exists() and not path.is_symlink():
            session = _read(path)
            if session.get("method") == "workspace":
                base = _managed_call(workspace_oauth.origin)
                if base and session.get("service_origin") == base and workspace_oauth.KEY.fullmatch(session.get("proof", "")):
                    _managed_call(workspace_oauth.disconnect, base, session["proof"])
        for name in ("token.json", "login.json"):
            path = root / name
            if path.is_symlink():
                raise ConnectorError("unsafe_storage", "拒绝删除符号链接凭据。")
            path.unlink(missing_ok=True)
    return {"ok": True, "message": "本地会话已清除。Google 端的授权可在 Google 账号设置中管理。"}
