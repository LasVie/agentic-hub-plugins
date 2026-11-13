"""Synthetic Gmail/API tests; no account calls."""
from __future__ import annotations

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
    monkeypatch.setattr(gs, "load_credentials", lambda **kwargs: marker)
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


@pytest.mark.parametrize("path", ["labels", "messages/m1/modify", "messages/m1/attachments/a1", "drafts/d1/delete", "threads/t1/trash", "../messages", "https://evil.example/messages", "messages?x=1", "messages/m1%2Fmodify"])
def test_endpoint_allowlist_blocks_unexpected_operations(path):
    api, session, _ = service({})
    with pytest.raises(ConnectorError) as exc:
        api._get(path, {})
    assert exc.value.code == "unsupported_operation"
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


def test_empty_plain_alternative_uses_html_text():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": ""}},
            {"mimeType": "text/html", "body": {"data": encoded("<p>可见正文</p><script>skip()</script>")}},
        ],
    }
    body, warnings = gs._part_text(payload)
    assert body.strip() == "可见正文"
    assert warnings


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



class RouteSession(Session):
    """Serve exact in-memory Gmail routes and record method and payload."""
    def __init__(self, routes):
        super().__init__(None)
        self.routes = routes

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def request(self, method, url, **kwargs):
        assert url.startswith(gs.BASE_URL)
        path = url.removeprefix(gs.BASE_URL)
        self.calls.append((method, path, kwargs))
        assert kwargs["allow_redirects"] is False
        payload = self.routes[method, path]
        if isinstance(payload, Exception):
            raise payload
        return payload if isinstance(payload, Response) else Response(payload)


def test_draft_list_and_preview_use_draft_id_and_show_bcc():
    raw = message()
    raw["payload"]["headers"].append({"name": "Bcc", "value": "hidden@example.invalid"})
    session = RouteSession({
        ("GET", "drafts"): {"drafts": [{"id": "d1", "message": {"id": "m1", "threadId": "t1"}}], "nextPageToken": "p2"},
        ("GET", "drafts/d1"): {"id": "d1", "message": raw},
    })
    api = gs.GmailService(lambda: session)
    assert api.list_drafts(1)["drafts"] == [{"draft_id": "d1", "message_id": "m1", "thread_id": "t1"}]
    result = api.read_draft("d1", 2)
    assert result["headers"]["Bcc"] == "hidden@example.invalid" and result["body_truncated"]


@pytest.mark.parametrize("subject", [None, "新主题"])
def test_edit_draft_preserves_unedited_addresses_and_attachment(subject):
    from email.message import EmailMessage
    from gmail_message import decode_draft, encode_message

    draft = EmailMessage()
    draft["From"] = "self@example.invalid"
    draft["To"] = "before@example.invalid"
    draft["Cc"] = "copy@example.invalid"
    draft["Subject"] = "旧主题"
    draft.set_content("旧正文")
    draft.add_alternative("<p>旧格式</p>", subtype="html")
    draft.add_attachment(b"attachment", maintype="application", subtype="octet-stream", filename="keep.bin")
    session = RouteSession({
        ("GET", "drafts/d1"): {"id": "d1", "message": {"raw": encode_message(draft), "threadId": "t1"}},
        ("PUT", "drafts/d1"): {"id": "d1"},
    })
    api = gs.GmailService(lambda: session)
    result = api.edit_draft("d1", to=["after@example.invalid"], subject=subject, body="新正文 <内容>")
    assert result == {"draft_id": "d1"}
    sent = session.calls[1][2]["json"]["message"]
    assert sent.get("threadId") == ("t1" if subject is None else None)
    updated = decode_draft(sent["raw"])
    assert updated["Subject"] == (subject or "旧主题") and updated["To"] == "after@example.invalid"
    assert updated["Cc"] == "copy@example.invalid" and updated["From"] == "self@example.invalid"
    assert updated.get_body(("plain",)).get_content().strip() == "新正文 <内容>"
    assert "&lt;内容&gt;" in updated.get_body(("html",)).get_content()
    assert next(updated.iter_attachments()).get_content() == b"attachment"


def test_send_message_uses_authenticated_sender_and_explicit_recipients():
    from gmail_message import decode_draft

    session = RouteSession({
        ("GET", "profile"): {"emailAddress": "self@example.invalid"},
        ("POST", "messages/send"): {"id": "sent1", "threadId": "thread1"},
    })
    api = gs.GmailService(lambda: session)
    assert api.send_message(["alice@example.invalid", "bob@example.invalid"], "中文主题", "正文") == {
        "message_id": "sent1", "thread_id": "thread1",
    }
    raw = session.calls[1][2]["json"]["raw"]
    message = decode_draft(raw)
    assert message["From"] == "self@example.invalid"
    assert [address.addr_spec for address in message["To"].addresses] == ["alice@example.invalid", "bob@example.invalid"]
    assert message["Subject"] == "中文主题" and message.get_content().strip() == "正文"


def test_send_draft_only_posts_the_draft_id():
    session = RouteSession({("POST", "drafts/send"): {"id": "sent1", "threadId": "t1"}})
    result = gs.GmailService(lambda: session).send_draft("d1")
    assert result["message_id"] == "sent1"
    assert session.calls[0][2]["json"] == {"id": "d1"}


def test_reply_matches_thread_headers_and_uses_reply_to():
    from gmail_message import decode_draft

    headers = {
        "Subject": "中文原主题",
        "From": "Original <from@example.invalid>",
        "Reply-To": "Alice <reply@example.invalid>",
        "Message-ID": "<message@example.invalid>",
        "References": "<root@example.invalid>",
    }
    session = RouteSession({
        ("GET", "messages/m1"): {"id": "m1", "threadId": "t1", "payload": {"headers": [
            {"name": name, "value": value} for name, value in headers.items()
        ]}},
        ("GET", "profile"): {"emailAddress": "self@example.invalid"},
        ("POST", "messages/send"): {"id": "sent1", "threadId": "t1"},
    })
    assert gs.GmailService(lambda: session).reply("m1", "测试回复")["thread_id"] == "t1"
    assert session.calls[0][2]["params"]["format"] == "metadata"
    payload = session.calls[-1][2]["json"]
    message = decode_draft(payload["raw"])
    assert payload["threadId"] == "t1"
    assert message["To"] == "reply@example.invalid" and message["Subject"] == headers["Subject"]
    assert message["In-Reply-To"] == "<message@example.invalid>"
    assert message["References"] == "<root@example.invalid> <message@example.invalid>"


@pytest.mark.parametrize("address, subject", [
    ("alice@example.invalid\r\nBcc: intruder@example.invalid", "测试"),
    ("alice@example.invalid", "测试\nBcc: intruder@example.invalid"),
    ("missing-address", "测试"),
])
def test_invalid_outbound_header_is_rejected_before_network(address, subject):
    session = RouteSession({})
    with pytest.raises(ConnectorError):
        gs.GmailService(lambda: session).send_message([address], subject, "正文")
    assert not session.calls


@pytest.mark.parametrize("response", [ConnectionError("private-provider-details"), Response({}, status=503), Response({})])
def test_uncertain_send_never_automatically_retries(response):
    session = RouteSession({("POST", "drafts/send"): response})
    with pytest.raises(ConnectorError) as failure:
        gs.GmailService(lambda: session).send_draft("d1")
    assert failure.value.code == "write_outcome_unknown"
    assert "private-provider-details" not in str(failure.value)
    assert len(session.calls) == 1


@pytest.mark.parametrize("method, path", [("DELETE", "drafts/d1"), ("POST", "messages/m1/trash"), ("PUT", "messages/m1")])
def test_write_allowlist_rejects_other_mailbox_changes(method, path):
    session = RouteSession({})
    with pytest.raises(ConnectorError) as error:
        gs.GmailService(lambda: session)._request(session, method, path, payload={})
    assert error.value.code == "unsupported_operation"
    assert not session.calls
