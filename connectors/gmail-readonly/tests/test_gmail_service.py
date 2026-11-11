"""Synthetic Gmail/API and real SDK registration tests; no account calls."""
from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path

import pytest
from google.auth.exceptions import RefreshError
from requests.exceptions import ConnectionError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gmail-readonly"))
import gmail_service as gs
from auth import ConnectorError


def encoded(text: str, charset: str = "utf-8") -> str:
    return base64.urlsafe_b64encode(text.encode(charset)).decode().rstrip("=")


def message(text: str = "中文测试正文", **overrides):
    result = {"id": "m1", "threadId": "t1", "labelIds": ["INBOX", "UNREAD"], "internalDate": "123", "payload": {"mimeType": "text/plain", "headers": [{"name": "Subject", "value": "中文合成邮件"}], "body": {"data": encoded(text)}}}
    result.update(overrides)
    return result


class Response:
    def __init__(self, payload=None, *, status=200, headers=None, chunks=None):
        self.status_code = status
        self.headers = headers or {}
        self.chunks = chunks if chunks is not None else [json.dumps(payload).encode()]
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def iter_content(self, chunk_size):
        yield from self.chunks


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []
        self.trust_env = True
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def service(payload=None, **kwargs):
    response = Response(payload, **kwargs)
    session = Session(response)
    return gs.GmailService(lambda: session), session, response


def test_search_fixed_get_params_and_preserved_pagination():
    api, session, response = service({"messages": [{"id": "m1", "threadId": "t1"}], "nextPageToken": "next-1", "resultSizeEstimate": 2})
    result = api.search_messages('subject:"中文测试"', 1, "previous")
    assert result["messages"] == [{"message_id": "m1", "thread_id": "t1"}]
    assert result["next_page_token"] == "next-1" and result["truncated"]
    assert session.calls == [(gs.BASE_URL + "messages", {"params": {"q": 'subject:"中文测试"', "maxResults": 1, "includeSpamTrash": "false", "fields": "messages(id,threadId),nextPageToken,resultSizeEstimate", "pageToken": "previous"}, "timeout": (10, 30), "allow_redirects": False, "stream": True})]
    assert session.trust_env is False
    assert session.closed and response.closed


def test_both_api_and_refresh_transports_ignore_environment_and_close(monkeypatch):
    captured = {}
    class AuthTransport:
        trust_env = True
        closed = False
        def __enter__(self):
            captured["auth_session"] = self
            return self
        def __exit__(self, *args):
            self.close()
        def close(self):
            self.closed = True
    class ApiTransport(AuthTransport):
        def __init__(self, credentials, *, auth_request, max_refresh_attempts):
            captured["credentials"] = credentials
            captured["auth_request"] = auth_request
            captured["max_refresh_attempts"] = max_refresh_attempts
        def __enter__(self):
            captured["api_session"] = self
            return self
    marker = object()
    monkeypatch.setattr(gs, "Session", AuthTransport)
    monkeypatch.setattr(gs, "AuthorizedSession", ApiTransport)
    monkeypatch.setattr(gs, "load_credentials", lambda: marker)
    with gs._google_session() as session:
        assert session.trust_env is False
        assert captured["auth_request"].session is captured["auth_session"]
        assert captured["auth_request"].session.trust_env is False
        assert captured["credentials"] is marker
        assert captured["max_refresh_attempts"] == 0
    assert captured["auth_session"].closed and captured["api_session"].closed


@pytest.mark.parametrize("supplied_timeout", [None, 120, 9999])
def test_refresh_transport_forces_bounded_timeout(supplied_timeout):
    class RefreshTransport:
        def __init__(self):
            self.calls = []
        def request(self, method, url, **kwargs):
            self.calls.append({"method": method, "url": url, **kwargs})
            return type("Reply", (), {"status_code": 200, "headers": {}, "content": b"{}"})()
        def close(self):
            pass
    transport = RefreshTransport()
    request = gs._BoundedRequest(session=transport)
    reply = request("https://oauth2.googleapis.com/token", method="POST", body=b"synthetic", timeout=supplied_timeout)
    assert reply.status == 200
    assert transport.calls == [{"method": "POST", "url": "https://oauth2.googleapis.com/token", "data": b"synthetic", "headers": None, "timeout": (10, 30)}]


def test_empty_list_does_not_invent_messages():
    api, _, _ = service({"resultSizeEstimate": 0})
    result = api.search_messages()
    assert result["messages"] == [] and result["count"] == 0
    assert result["truncated"] is False


@pytest.mark.parametrize("kwargs", [{"max_results": 0}, {"max_results": 21}, {"max_results": True}, {"query": "a" * 2049}, {"query": "a\nb"}, {"page_token": "a" * 2049}])
def test_search_argument_bounds_precede_auth_or_network(kwargs):
    api, session, _ = service({})
    with pytest.raises(ConnectorError) as exc:
        api.search_messages(**kwargs)
    assert exc.value.code == "invalid_argument"
    assert not session.calls


@pytest.mark.parametrize("path", ["profile", "labels", "messages/m1/modify", "messages/m1/attachments/a1", "drafts", "threads/t1/trash", "../messages", "https://evil.example/messages", "messages?x=1", "messages/m1%2Fmodify"])
def test_endpoint_allowlist_blocks_unexpected_operations(path):
    api, session, _ = service({})
    with pytest.raises(ConnectorError) as exc:
        api._get(path, {})
    assert exc.value.code == "read_only_violation"
    assert not session.calls


@pytest.mark.parametrize("bad_id", ["", "../m1", "https://evil.example", "m1/modify", "m1%2fmodify", "m1\n", "x" * 257, "邮件"])
def test_ids_cannot_be_paths(bad_id):
    api, session, _ = service({})
    with pytest.raises(ConnectorError):
        api.read_message(bad_id)
    with pytest.raises(ConnectorError):
        api.read_thread(bad_id)
    assert not session.calls


def test_read_message_preserves_original_plaintext_unread_label_and_reports_truncation():
    api, session, _ = service(message("中文测试"))
    result = api.read_message("m1", 2)
    assert result["body_text"] == "中文"
    assert result["body_chars_available"] == 4 and result["body_truncated"]
    assert result["label_ids"] == ["INBOX", "UNREAD"]
    assert session.calls[0][0] == gs.BASE_URL + "messages/m1"
    assert session.calls[0][1]["params"]["format"] == "full"
    assert len(session.calls) == 1


def test_plain_alternative_preferred_and_attachment_not_fetched():
    payload = {"mimeType": "multipart/mixed", "parts": [
        {"mimeType": "multipart/alternative", "parts": [
            {"mimeType": "text/html", "body": {"data": encoded("<p>HTML替代</p>")}},
            {"mimeType": "text/plain", "body": {"data": encoded("原始纯文本")}},
        ]},
        {"mimeType": "text/plain", "filename": "私密.txt", "body": {"attachmentId": "a1", "data": encoded("附件内容")}},
    ]}
    api, session, _ = service(message(payload=payload))
    result = api.read_message("m1")
    assert result["body_text"] == "原始纯文本"
    assert any("附件未下载" in s for s in result["warnings"])
    assert len(session.calls) == 1


def test_html_becomes_text_without_scripts_styles_or_remote_resources():
    payload = {"mimeType": "text/html", "body": {"data": encoded('<head><title>隐藏</title><style>body{}</style></head><p>你好 &amp; 朋友</p><script>steal()</script><img src="https://evil.example/x"><a href="https://evil.example/">文字</a>')}}
    api, session, _ = service(message(payload=payload))
    result = api.read_message("m1")
    assert "你好 & 朋友" in result["body_text"] and "文字" in result["body_text"]
    for excluded in ["steal", "evil.example", "隐藏", "body{}", "<"]:
        assert excluded not in result["body_text"]
    assert any("HTML" in s for s in result["warnings"])
    assert len(session.calls) == 1


def test_legacy_charset_and_invalid_charset_warning():
    payload = {"mimeType": "text/plain", "headers": [{"name": "Content-Type", "value": "text/plain; charset=gb18030"}], "body": {"data": encoded("中文旧编码", "gb18030")}}
    api, _, _ = service(message(payload=payload))
    assert api.read_message("m1")["body_text"] == "中文旧编码"
    payload["headers"][0]["value"] = "text/plain; charset=nonexistent"
    api, _, _ = service(message(payload=payload))
    assert api.read_message("m1")["warnings"]


def test_thread_message_limit_and_total_body_budget():
    api, session, _ = service({"id": "t1", "messages": [message("abcd"), message("efgh"), message("ijkl")]})
    result = api.read_thread("t1", max_messages=2, max_chars=6)
    assert [m["body_text"] for m in result["messages"]] == ["abcd", "ef"]
    assert result["count"] == 2 and result["messages_available"] == 3 and result["truncated"]
    assert len(session.calls) == 1


def test_thread_budget_does_not_return_later_empty_bodies():
    api, _, _ = service({"id": "t1", "messages": [message("abcd"), message("efgh")]})
    result = api.read_thread("t1", max_chars=4)
    assert result["count"] == 1 and result["truncated"]


@pytest.mark.parametrize("method,kwargs", [("read_message", {"message_id": "m1", "max_chars": 20001}), ("read_thread", {"thread_id": "t1", "max_messages": 21}), ("read_thread", {"thread_id": "t1", "max_chars": 30001})])
def test_read_output_bound_arguments(method, kwargs):
    api, session, _ = service({})
    with pytest.raises(ConnectorError):
        getattr(api, method)(**kwargs)
    assert not session.calls


@pytest.mark.parametrize("status,code", [(301, "service_unavailable"), (401, "auth_required"), (403, "access_denied"), (404, "not_found"), (429, "rate_limited"), (500, "service_unavailable")])
def test_provider_errors_are_sanitized_and_not_retried(status, code):
    api, session, response = service({"error": "secret-token/private-mail"}, status=status)
    with pytest.raises(ConnectorError) as exc:
        api.read_message("m1")
    assert exc.value.code == code
    assert "secret-token" not in str(exc.value)
    assert len(session.calls) == 1 and response.closed


@pytest.mark.parametrize("exception,code", [(ConnectionError("secret-token/private-mail"), "network_error"), (RefreshError("secret-token/private-mail"), "auth_required")])
def test_transport_and_refresh_errors_do_not_leak_details(exception, code):
    session = Session(exception)
    api = gs.GmailService(lambda: session)
    with pytest.raises(ConnectorError) as exc:
        api.search_messages()
    assert exc.value.code == code and "secret-token" not in str(exc.value)
    assert len(session.calls) == 1 and session.closed


@pytest.mark.parametrize("headers,chunks", [({"Content-Length": str(gs.MAX_RESPONSE_BYTES + 1)}, []), ({}, [b" " * gs.MAX_RESPONSE_BYTES, b"x"])])
def test_response_cap_is_checked_before_materializing_complete_payload(headers, chunks):
    api, _, response = service(headers=headers, chunks=chunks)
    with pytest.raises(ConnectorError) as exc:
        api.search_messages()
    assert exc.value.code == "response_too_large" and response.closed


@pytest.mark.parametrize("payload", [[], "secret", 1, None])
def test_invalid_json_top_level_is_rejected(payload):
    api, _, _ = service(payload)
    with pytest.raises(ConnectorError) as exc:
        api.search_messages()
    assert exc.value.code == "invalid_response"


def test_malformed_body_is_not_presented_as_original_text():
    api, _, _ = service(message(payload={"mimeType": "text/plain", "body": {"data": "$$$"}}))
    with pytest.raises(ConnectorError) as exc:
        api.read_message("m1")
    assert exc.value.code == "invalid_response"


def test_nested_and_many_mime_parts_are_bounded():
    payload = {"mimeType": "text/plain", "body": {"data": encoded("正文")}}
    for _ in range(27):
        payload = {"mimeType": "multipart/mixed", "parts": [payload]}
    api, _, _ = service(message(payload=payload))
    with pytest.raises(ConnectorError) as exc:
        api.read_message("m1")
    assert exc.value.code == "content_too_complex"
    payload = {"mimeType": "multipart/mixed", "parts": [{"mimeType": "text/plain", "body": {"data": ""}}] * 201}
    api, _, _ = service(message(payload=payload))
    with pytest.raises(ConnectorError) as exc:
        api.read_message("m1")
    assert exc.value.code == "content_too_complex"


def test_attached_message_not_expanded():
    payload = {"mimeType": "message/rfc822", "parts": [{"mimeType": "text/plain", "body": {"data": encoded("附加私密邮件")}}]}
    api, session, _ = service(message(payload=payload))
    result = api.read_message("m1")
    assert result["body_text"] == "" and any("附加邮件未展开" in w for w in result["warnings"])
    assert len(session.calls) == 1


def test_exact_mcp_tools_and_read_only_annotations():
    import server
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {"gmail_search_messages", "gmail_read_message", "gmail_read_thread"}
    assert all(t.annotations.readOnlyHint and not t.annotations.destructiveHint for t in tools)
    assert all(t.description and any("\u4e00" <= c <= "\u9fff" for c in t.description) for t in tools)


def test_mcp_result_marks_mail_untrusted_and_uses_sanitized_errors(monkeypatch):
    import server
    class FakeService:
        def search_messages(self, **kwargs):
            return {"messages": []}
    monkeypatch.setattr(server, "GmailService", FakeService)
    result = server.gmail_search_messages("中文测试")
    assert result["ok"] and result["version"] == "1.0.0"
    assert "不可信" in result["untrusted_data_notice"]
    class FailedService:
        def search_messages(self, **kwargs):
            raise ValueError("secret-token/private-mail")
    monkeypatch.setattr(server, "GmailService", FailedService)
    result = server.gmail_search_messages()
    assert result["ok"] is False and result["error"]["code"] == "internal_error"
    assert "secret-token" not in json.dumps(result)
