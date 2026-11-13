"""Private-state and OAuth lifecycle regressions using only synthetic credentials.

All Google HTTP calls and the browser are replaced. The loopback tests exercise
the installed Google OAuth library's real local callback server and state/PKCE
handling; their synthetic token exchange is not a live Google integration test.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import base64
import hashlib
import http.client
import json
import logging
import os
from pathlib import Path
import stat
import sys
import threading
from types import SimpleNamespace
from urllib.parse import parse_qs, urlencode, urlsplit
import webbrowser

import pytest
import requests
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gmail-readonly"))
import auth


def client(client_id="synthetic-client.apps.googleusercontent.com"):
    return {"installed": {"client_id": client_id, "client_secret": "synthetic-client-secret",
                          "auth_uri": auth.AUTH_URI, "token_uri": auth.TOKEN_URI}}


def credentials(*, scopes=None, refresh_token="synthetic-refresh", token="synthetic-access"):
    return Credentials(token, refresh_token=refresh_token, token_uri=auth.TOKEN_URI,
                       client_id=client()["installed"]["client_id"], client_secret="synthetic-client-secret",
                       scopes=auth.SCOPES if scopes is None else scopes,
                       expiry=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1))


def store_token(root, *, session_id="session-one", **kwargs):
    value = json.loads(credentials(**kwargs).to_json())
    value["session_id"] = session_id
    auth._write(root / "token.json", value)
    return value


@pytest.fixture(autouse=True)
def block_external_io(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("A test attempted unmocked network or browser I/O")
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    monkeypatch.setattr(webbrowser, "get", forbidden)
    monkeypatch.setenv("GMAIL_WORKSPACE_OAUTH_URL", "")


@pytest.fixture
def private_state(tmp_path, monkeypatch):
    root = tmp_path / "private-state"
    monkeypatch.setenv("GMAIL_READONLY_HOME", str(root))
    assert auth.state_root() == root
    auth._write(root / "client.json", client())
    return root


def test_card_login_can_use_explicit_managed_origin_without_local_client(tmp_path, monkeypatch):
    root = tmp_path / "private-state"
    monkeypatch.setenv("GMAIL_READONLY_HOME", str(root))
    monkeypatch.setenv("GMAIL_WORKSPACE_OAUTH_URL", "https://oauth.example.invalid")
    calls = []

    def managed_sign_in(base, *, open_browser):
        assert not (root / "client.json").exists()
        calls.append((base, open_browser))
        return {"ok": True}

    monkeypatch.setattr(auth, "_managed_sign_in", managed_sign_in)
    assert auth.sign_in(open_browser=False) == {"ok": True}
    assert calls == [("https://oauth.example.invalid", False)]


def test_card_login_defaults_to_user_supplied_desktop_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("GMAIL_READONLY_HOME", str(tmp_path / "private-state"))
    monkeypatch.delenv("GMAIL_WORKSPACE_OAUTH_URL", raising=False)
    with pytest.raises(auth.ConnectorError) as error:
        auth.sign_in(open_browser=False)
    assert error.value.code == "client_config_required"


def mock_flow(monkeypatch, *, creds=None, effect=None):
    captured = {}
    flow = SimpleNamespace(oauth2session=SimpleNamespace(trust_env=True))
    def run(**kwargs):
        captured["run"] = kwargs
        if effect:
            effect()
        return credentials() if creds is None else creds
    flow.run_local_server = run
    def factory(config, scopes, **kwargs):
        captured.update(config=config, scopes=scopes, constructor=kwargs)
        return flow
    monkeypatch.setattr(auth.InstalledAppFlow, "from_client_config", staticmethod(factory))
    return captured, flow


def test_login_uses_loopback_pkce_exact_scope_and_private_persistence(private_state, monkeypatch, capsys):
    captured, flow = mock_flow(monkeypatch)
    assert auth.sign_in()["ok"]
    assert captured["scopes"] == auth.SCOPES
    assert captured["constructor"]["autogenerate_code_verifier"] is True
    assert captured["run"]["host"] == "127.0.0.1"
    assert captured["run"]["port"] == 0
    assert captured["run"]["open_browser"] is True
    assert captured["run"]["timeout_seconds"] == 180
    assert captured["run"]["access_type"] == "offline"
    assert captured["run"]["include_granted_scopes"] == "false"
    assert flow.oauth2session.trust_env is False
    value = auth._read(private_state / "token.json")
    assert value["scopes"] == auth.SCOPES and value["session_id"]
    assert value["refresh_token"] == "synthetic-refresh"
    assert not (private_state / "login.json").exists()
    if os.name != "nt":
        assert stat.S_IMODE(private_state.stat().st_mode) == 0o700
        assert stat.S_IMODE((private_state / "token.json").stat().st_mode) == 0o600
    assert "synthetic-refresh" not in capsys.readouterr().out


@pytest.mark.parametrize("scopes", [[auth.SCOPE, "https://mail.google.com/"], [], ["openid"]])
def test_scope_escalation_or_missing_scope_never_persists(private_state, monkeypatch, scopes):
    mock_flow(monkeypatch, creds=credentials(scopes=scopes))
    with pytest.raises(auth.ConnectorError) as error:
        auth.sign_in()
    assert error.value.code == "scope_mismatch"
    assert not (private_state / "token.json").exists()
    assert not (private_state / "login.json").exists()


def test_missing_refresh_token_never_persists(private_state, monkeypatch):
    mock_flow(monkeypatch, creds=credentials(refresh_token=None))
    with pytest.raises(auth.ConnectorError) as error:
        auth.sign_in()
    assert error.value.code == "missing_refresh"
    assert not (private_state / "token.json").exists()


def test_denied_or_timed_out_login_sanitizes_error_and_clears_reservation(private_state, monkeypatch):
    def fail():
        raise RuntimeError("private-code=synthetic-private-code token=synthetic-refresh")
    mock_flow(monkeypatch, effect=fail)
    with pytest.raises(auth.ConnectorError) as error:
        auth.sign_in()
    assert error.value.code == "authorization_failed"
    assert "synthetic" not in str(error.value)
    assert not (private_state / "token.json").exists()
    assert not (private_state / "login.json").exists()


@pytest.mark.parametrize("fail", [False, True])
def test_login_restores_existing_logging_policy_on_success_and_failure(private_state, monkeypatch, fail):
    previous = logging.root.manager.disable
    logging.disable(logging.ERROR)
    def inspect_exchange():
        assert logging.root.manager.disable >= logging.CRITICAL
        if fail:
            raise RuntimeError("synthetic-private-provider-error")
    mock_flow(monkeypatch, effect=inspect_exchange)
    try:
        if fail:
            with pytest.raises(auth.ConnectorError):
                auth.sign_in()
        else:
            assert auth.sign_in()["ok"]
        assert logging.root.manager.disable == logging.ERROR
    finally:
        logging.disable(previous)


def test_logout_while_browser_pending_cannot_resurrect_login(private_state, monkeypatch):
    mock_flow(monkeypatch, effect=auth.sign_out)
    with pytest.raises(auth.ConnectorError):
        auth.sign_in()
    assert not (private_state / "token.json").exists()
    assert not (private_state / "login.json").exists()


def test_reconfigure_while_browser_pending_cannot_save_old_client_token(private_state, tmp_path, monkeypatch):
    replacement = tmp_path / "new-client.json"
    replacement.write_text(json.dumps(client("replacement.apps.googleusercontent.com")))
    mock_flow(monkeypatch, effect=lambda: auth.configure(replacement))
    with pytest.raises(auth.ConnectorError):
        auth.sign_in()
    assert auth._read(private_state / "client.json")["installed"]["client_id"].startswith("replacement.")
    assert not (private_state / "token.json").exists()


def test_existing_login_is_not_overwritten_by_login_or_reconfigure(private_state, tmp_path):
    original = store_token(private_state)
    source = tmp_path / "client.json"
    source.write_text(json.dumps(client("replacement.apps.googleusercontent.com")))
    for operation in (auth.sign_in, lambda: auth.configure(source)):
        with pytest.raises(auth.ConnectorError) as error:
            operation()
        assert error.value.code == "session_exists"
    assert auth._read(private_state / "token.json") == original


def test_status_is_local_only_and_does_not_expose_identity_or_tokens(private_state):
    store_token(private_state)
    result = auth.session_status()
    assert result["ok"] and result["signed_in_local"]
    assert result["provider_access_verified"] is False
    assert "synthetic" not in json.dumps(result)
    auth.sign_out()
    result = auth.session_status()
    assert not result["ok"] and not result["signed_in_local"]
    assert (private_state / "client.json").exists()


def test_refresh_persists_new_token_without_changing_session(private_state, monkeypatch):
    store_token(private_state)
    loaded = auth.load_credentials()
    calls = []
    def refresh(self, request):
        calls.append(request)
        self.token = "synthetic-refreshed-access"
        self.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    monkeypatch.setattr(Credentials, "refresh", refresh)
    loaded.refresh("synthetic-request")
    saved = auth._read(private_state / "token.json")
    assert calls == ["synthetic-request"]
    assert saved["token"] == "synthetic-refreshed-access"
    assert saved["refresh_token"] == "synthetic-refresh"
    assert saved["session_id"] == "session-one"


@pytest.mark.parametrize("replace_session", [False, True])
def test_stale_refresh_cannot_restore_signed_out_or_replaced_login(private_state, monkeypatch, replace_session):
    store_token(private_state)
    loaded = auth.load_credentials()
    auth.sign_out()
    if replace_session:
        store_token(private_state, session_id="session-two", token="new-login-token")
    def forbidden_refresh(*args):
        raise AssertionError("A stale session must not reach the provider")
    monkeypatch.setattr(Credentials, "refresh", forbidden_refresh)
    with pytest.raises(auth.ConnectorError):
        loaded.refresh("unused")
    if replace_session:
        assert auth._read(private_state / "token.json")["session_id"] == "session-two"
    else:
        assert not (private_state / "token.json").exists()


def test_revoked_refresh_is_sanitized_and_does_not_overwrite_token(private_state, monkeypatch):
    original = store_token(private_state)
    loaded = auth.load_credentials()
    def revoked(*args):
        raise RefreshError("invalid_grant synthetic-refresh private-account@example.invalid")
    monkeypatch.setattr(Credentials, "refresh", revoked)
    with pytest.raises(auth.ConnectorError) as error:
        loaded.refresh("unused")
    assert error.value.code == "reauth_required"
    assert "synthetic" not in str(error.value) and "example.invalid" not in str(error.value)
    assert auth._read(private_state / "token.json") == original


def test_refresh_scope_change_is_not_persisted(private_state, monkeypatch):
    original = store_token(private_state)
    loaded = auth.load_credentials()
    def excessive_scope(self, request):
        self.token = "unexpected-token"
        self._granted_scopes = [auth.SCOPE, "https://mail.google.com/"]
    monkeypatch.setattr(Credentials, "refresh", excessive_scope)
    with pytest.raises(auth.ConnectorError) as error:
        loaded.refresh("unused")
    assert error.value.code == "scope_mismatch"
    assert auth._read(private_state / "token.json") == original


@pytest.mark.parametrize("field,value", [("scopes", ["https://mail.google.com/"]), ("token_uri", "https://evil.example/token"), ("session_id", ""), ("refresh_token", "")])
def test_unsafe_stored_credentials_rejected_before_network(private_state, field, value):
    stored = store_token(private_state)
    stored[field] = value
    auth._write(private_state / "token.json", stored)
    with pytest.raises(auth.ConnectorError):
        auth.load_credentials()


def test_missing_or_malformed_state_does_not_trigger_sign_in(private_state):
    assert auth.session_status()["error"]["code"] == "not_signed_in"
    auth._write(private_state / "token.json", {"token": "private-synthetic-token"})
    result = auth.session_status()
    assert not result["ok"] and "private-synthetic-token" not in json.dumps(result)


def test_storage_refuses_repository_payload_relative_and_symlink_roots(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    for candidate in (Path("relative-state"), link, repository / "state", Path(auth.__file__).parent / "state"):
        monkeypatch.setenv("GMAIL_READONLY_HOME", str(candidate))
        with pytest.raises(auth.ConnectorError) as error:
            auth.state_root()
        assert error.value.code == "unsafe_storage"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission checks")
def test_public_directory_or_token_permissions_are_rejected(private_state, monkeypatch):
    private_state.chmod(0o755)
    with pytest.raises(auth.ConnectorError):
        auth.state_root()
    private_state.chmod(0o700)
    store_token(private_state)
    (private_state / "token.json").chmod(0o644)
    with pytest.raises(auth.ConnectorError) as error:
        auth.load_credentials()
    assert error.value.code == "unsafe_credentials"


def test_symlink_credential_read_write_and_logout_preserve_external_file(private_state, tmp_path):
    target = tmp_path / "protected.json"
    target.write_text('{"synthetic":"preserve"}')
    target.chmod(0o600)
    link = private_state / "token.json"
    link.symlink_to(target)
    for operation in (lambda: auth._read(link), lambda: auth._write(link, {}), auth.sign_out):
        with pytest.raises(auth.ConnectorError):
            operation()
    assert target.read_text() == '{"synthetic":"preserve"}' and link.is_symlink()


@pytest.mark.parametrize("bad", [{"web": client()["installed"]}, {"installed": {}}, {"installed": {**client()["installed"], "token_uri": "https://evil.example/token"}}, {"installed": {**client()["installed"], "auth_uri": "https://evil.example/auth"}}])
def test_developer_config_is_desktop_and_google_endpoint_only(private_state, tmp_path, bad):
    path = tmp_path / "invalid-client.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(auth.ConnectorError) as error:
        auth.configure(path)
    assert error.value.code == "invalid_client"
    assert auth._read(private_state / "client.json") == client()


@pytest.mark.parametrize("wrong_state", [False, True])
def test_real_library_loopback_callback_and_state_pkce_without_google(private_state, monkeypatch, wrong_state, capsys, caplog):
    """Real loopback HTTP only; intercept every outbound token HTTP request."""
    captured = {"token_requests": [], "callback_errors": []}
    workers = []
    caplog.set_level(logging.DEBUG)
    def token_response(session, method, url, **kwargs):
        assert method.upper() == "POST" and url == auth.TOKEN_URI
        captured["token_requests"].append(kwargs)
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps({"access_token": "synthetic-loopback-access", "refresh_token": "synthetic-loopback-refresh", "token_type": "Bearer", "expires_in": 3600, "scope": " ".join(auth.SCOPES)}).encode()
        response.headers["Content-Type"] = "application/json"
        response.request = requests.Request(method, url, data=kwargs.get("data")).prepare()
        return response
    monkeypatch.setattr(requests.sessions.Session, "request", token_response)
    class Browser:
        def open(self, url, **kwargs):
            query = parse_qs(urlsplit(url).query)
            captured["authorization"] = query
            callback = urlsplit(query["redirect_uri"][0])
            assert callback.hostname == "127.0.0.1" and callback.scheme == "http"
            def return_callback():
                try:
                    connection = http.client.HTTPConnection(callback.hostname, callback.port, timeout=5)
                    suffix = urlencode({"code": "synthetic-callback-code", "state": "wrong-state" if wrong_state else query["state"][0]})
                    connection.request("GET", (callback.path or "/") + "?" + suffix)
                    response = connection.getresponse()
                    captured["callback_status"] = response.status
                    response.read()
                    connection.close()
                except Exception as error:
                    captured["callback_errors"].append(type(error).__name__)
            worker = threading.Thread(target=return_callback, daemon=True)
            workers.append(worker)
            worker.start()
            return True
    monkeypatch.setattr(webbrowser, "get", lambda *args: Browser())
    if wrong_state:
        with pytest.raises(auth.ConnectorError) as error:
            auth.sign_in()
        assert error.value.code == "authorization_failed"
        assert not captured["token_requests"]
        assert not (private_state / "token.json").exists()
    else:
        assert auth.sign_in()["ok"]
        assert len(captured["token_requests"]) == 1
        request_data = captured["token_requests"][0]["data"]
        assert "code_verifier" in request_data
        assert captured["token_requests"][0]["timeout"] == (10, 30)
        expected_challenge = base64.urlsafe_b64encode(hashlib.sha256(request_data["code_verifier"].encode("ascii")).digest()).decode("ascii").rstrip("=")
        assert captured["authorization"]["code_challenge"] == [expected_challenge]
        assert auth._read(private_state / "token.json")["refresh_token"] == "synthetic-loopback-refresh"
    for worker in workers:
        worker.join(timeout=6)
        assert not worker.is_alive()
    assert not captured["callback_errors"] and captured["callback_status"] == 200
    assert captured["authorization"]["scope"] == [" ".join(auth.SCOPES)]
    assert captured["authorization"]["code_challenge_method"] == ["S256"]
    assert len(captured["authorization"]["code_challenge"][0]) >= 43
    output = capsys.readouterr()
    for sensitive in ("synthetic-loopback-refresh", "synthetic-loopback-access", "synthetic-callback-code", "synthetic-client-secret"):
        assert sensitive not in output.out + output.err + caplog.text


def test_readonly_upgrade_preserves_session_until_full_consent(private_state, monkeypatch):
    legacy = store_token(private_state, scopes=[auth.SCOPE])
    assert auth.load_credentials().scopes == [auth.SCOPE]
    assert auth.session_status()["write_enabled"] is False
    with pytest.raises(auth.ConnectorError) as error:
        auth.load_credentials(require_compose=True)
    assert error.value.code == "compose_required"

    partially_granted = credentials(scopes=auth.SCOPES)
    partially_granted._granted_scopes = [auth.SCOPE]
    mock_flow(monkeypatch, creds=partially_granted)
    with pytest.raises(auth.ConnectorError) as error:
        auth.sign_in()
    assert error.value.code == "scope_mismatch"
    assert auth._read(private_state / "token.json") == legacy

    def verify_old_session():
        assert auth._read(private_state / "token.json") == legacy

    mock_flow(monkeypatch, effect=verify_old_session)
    assert auth.sign_in()["ok"]
    assert auth.load_credentials(require_compose=True).scopes == auth.SCOPES
    assert auth.session_status()["write_enabled"] is True
    assert auth._read(private_state / "token.json")["session_id"] != legacy["session_id"]
