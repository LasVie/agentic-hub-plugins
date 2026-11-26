import base64
import importlib.util
import imaplib
import json
import os
import socket
import socketserver
import ssl
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock


RUNTIME = Path(__file__).resolve().parents[1] / "src" / "icloud-mail-mcp.py"
SPEC = importlib.util.spec_from_file_location("icloud_mail", RUNTIME)
mail = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mail)

CREDS = {"ICLOUD_EMAIL": "alice@example.test", "ICLOUD_APP_PASSWORD": "synthetic-app-password"}
SUMMARY = b"From: Alice <alice@example.test>\r\nSubject: Test\r\nDate: Fri, 20 Nov 2026 02:00:00 +0000\r\n\r\n"
PLAIN = b'("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "8BIT" 6 1)'
HTML = b'("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "BASE64" 100 5)'
SEQUENCE = 3


def section_data(uid, section, data, before=b"", trailing_uid=False):
    descriptor = str(SEQUENCE).encode() + b" (" + before
    uid_attr = b"UID " + str(uid).encode()
    if not trailing_uid:
        descriptor += uid_attr + b" "
    descriptor += f"BODY[{section}]<0> {{{len(data)}}}".encode("ascii")
    continuation = b" " + uid_attr + b")" if trailing_uid else b")"
    return [(descriptor, data), continuation]


def call(name, **arguments):
    return mail.dispatch({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "icloud_mail_" + name, "arguments": arguments},
    })


def content(response):
    return json.loads(response["result"]["content"][0]["text"])


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        env = mock.patch.dict(os.environ, CREDS, clear=True)
        env.start()
        self.addCleanup(env.stop)
        patcher = mock.patch.object(mail, "BoundedIMAP")
        self.connect = patcher.start()
        self.addCleanup(patcher.stop)
        self.client = self.connect.return_value
        self.client.login.return_value = ("OK", [b"login ok"])
        self.client.select.return_value = ("OK", [b"250"])
        self.client.response.return_value = ("UIDVALIDITY", [b"51"])

    def test_status_uses_verified_tls_examining_inbox_and_closes(self):
        result = content(call("status"))
        self.assertEqual(result, {
            "connected": True, "mailbox": "INBOX", "message_count": 250, "uidvalidity": 51,
        })
        self.assertEqual(self.connect.call_args.args, ("imap.mail.me.com", 993))
        options = self.connect.call_args.kwargs
        self.assertEqual(options["timeout"], 10)
        self.assertTrue(options["ssl_context"].check_hostname)
        self.assertEqual(options["ssl_context"].verify_mode, ssl.CERT_REQUIRED)
        self.client.login.assert_called_once_with('"alice"', CREDS["ICLOUD_APP_PASSWORD"])
        self.client.select.assert_called_once_with("INBOX", readonly=True)
        self.client.shutdown.assert_called_once_with()
        self.client.uid.assert_not_called()

    def test_missing_credentials_does_not_connect(self):
        with mock.patch.dict(os.environ, {"ICLOUD_EMAIL": "${ICLOUD_EMAIL}"}, clear=False):
            result = call("status")
        self.assertTrue(result["result"]["isError"])
        self.assertEqual(content(result)["error"], "missing_credentials")
        self.connect.assert_not_called()

    def test_username_fallback_and_sanitized_auth_failure(self):
        rejection = imaplib.IMAP4.error(b"private login rejection synthetic-app-password")
        self.client.login.side_effect = [rejection, rejection]
        result = call("status")
        self.assertEqual(content(result)["error"], "authentication_failed")
        self.assertNotIn("private login rejection", str(result))
        self.assertNotIn(CREDS["ICLOUD_APP_PASSWORD"], str(result))
        self.assertEqual(self.client.login.call_args_list, [
            mock.call('"alice"', CREDS["ICLOUD_APP_PASSWORD"]),
            mock.call('"alice@example.test"', CREDS["ICLOUD_APP_PASSWORD"]),
        ])
        self.client.shutdown.assert_called_once()

    def test_timeout_and_tls_errors_are_sanitized(self):
        for failure, code in [
            (socket.timeout("synthetic-private"), "timeout"),
            (ssl.SSLCertVerificationError("synthetic-private"), "tls_failed"),
            (imaplib.IMAP4.abort("synthetic-private"), "connection_failed"),
        ]:
            self.connect.side_effect = failure
            result = call("status")
            self.assertEqual(content(result)["error"], code)
            self.assertNotIn("synthetic-private", str(result))

    def test_ascii_search_quotes_criteria_and_fetches_only_matching_uids(self):
        self.client.uid.side_effect = [
            ("OK", [b"301 422"]),
            ("OK", section_data(422, "HEADER.FIELDS (DATE FROM SUBJECT)", SUMMARY, trailing_uid=True)),
        ]
        result = content(call("search", subject='quote " then \\ still literal', **{"from": "example.test", "limit": 1}))
        self.assertEqual(result["messages"][0]["uid"], 422)
        self.assertEqual(result["search_window"], 100)
        self.assertEqual(result["returned_count"], 1)
        self.assertEqual(self.client.uid.call_args_list, [
            mock.call("SEARCH", "151:250", "SUBJECT", '"quote \\" then \\\\ still literal"', "FROM", '"example.test"'),
            mock.call("FETCH", "422", "(UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)]<0.8192>)"),
        ])

    def test_unicode_subject_and_sender_are_decoded_and_matched(self):
        subject = base64.b64encode("项目进度 Café".encode()).decode()
        sender = base64.b64encode("王小明".encode()).decode()
        encoded = (
            f"Subject: =?UTF-8?B?{subject}?=\r\n"
            f"From: =?UTF-8?B?{sender}?= <alice@example.test>\r\n\r\n"
        ).encode()
        self.client.uid.side_effect = [
            ("OK", [b"301 422 512"]),
            ("OK", section_data(301, mail.SUMMARY_SECTION, encoded)
             + section_data(512, mail.SUMMARY_SECTION, SUMMARY)
             + section_data(422, mail.SUMMARY_SECTION, encoded)),
        ]
        result = content(call("search", subject="项目进度 CAFE\u0301", **{"from": "王小明"}))
        self.assertEqual([entry["uid"] for entry in result["messages"]], [422, 301])
        self.assertEqual(result["messages"][0]["subject"], "项目进度 Café")
        self.assertEqual(result["messages"][0]["from"], "王小明 <alice@example.test>")
        self.assertEqual(self.client.uid.call_args_list[0], mock.call("SEARCH", "151:250"))

    def test_empty_mailbox_and_no_server_search_match_skip_fetch(self):
        self.client.select.return_value = ("OK", [b"0"])
        self.assertEqual(content(call("search", subject="Unique"))["messages"], [])
        self.client.uid.assert_not_called()
        self.client.select.return_value = ("OK", [b"1"])
        self.client.uid.return_value = ("OK", [b""])
        self.assertEqual(content(call("search", subject="Unique"))["messages"], [])
        self.client.uid.assert_called_once_with("SEARCH", "1:1", "SUBJECT", '"Unique"')

    def test_invalid_inputs_fail_before_network_access(self):
        bad_requests = [
            call("search"),
            call("search", subject=" "),
            call("search", subject="literal\r\nNOOP"),
            call("search", subject="x", limit=True),
            call("search", subject="x", limit=21),
            call("status", unexpected=True),
            call("read", uid=2),
            call("read", uid=2, uidvalidity=0),
        ]
        self.assertTrue(all(request["error"]["code"] == -32602 for request in bad_requests))
        self.connect.assert_not_called()

    def test_read_checks_validity_and_missing_uid(self):
        result = call("read", uid=422, uidvalidity=99)
        self.assertEqual(content(result)["error"], "uidvalidity_changed")
        self.client.uid.assert_not_called()
        self.client.uid.return_value = ("OK", [None])
        result = call("read", uid=422, uidvalidity=51)
        self.assertEqual(content(result)["error"], "message_not_found")

    def test_multipart_read_selects_plain_and_skips_text_attachment(self):
        root = SUMMARY[:-2] + b"Content-Type: multipart/mixed; boundary=one\r\n\r\n"
        structure = b"(" + PLAIN + b"(" + HTML + PLAIN + b' "ALTERNATIVE") "MIXED")'
        plain_mime = b"Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n"
        attachment_mime = b"Content-Type: text/plain\r\nContent-Disposition: attachment; filename=notes.txt\r\n\r\n"
        nested_mime = b"Content-Type: multipart/alternative; boundary=two\r\n\r\n"
        self.client.uid.side_effect = [
            ("OK", section_data(422, mail.MESSAGE_SECTION, root, before=b"BODYSTRUCTURE " + structure + b" ")),
            ("OK", section_data(422, "1.MIME", attachment_mime)),
            ("OK", section_data(422, "2.MIME", nested_mime)),
            ("OK", section_data(422, "2.2.MIME", plain_mime)),
            ("OK", section_data(422, "2.2", b"=E4=BD=A0=E5=A5=BD world")),
        ]
        result = content(call("read", uid=422, uidvalidity=51, max_chars=4))
        self.assertEqual(result["body"], "你好 w")
        self.assertEqual(result["body_format"], "plain_text")
        self.assertTrue(result["truncated"])
        self.assertEqual([item.args[2] for item in self.client.uid.call_args_list], [
            "(UID BODYSTRUCTURE " + mail.peek(mail.MESSAGE_SECTION, 8192) + ")",
            "(UID BODY.PEEK[1.MIME]<0.8192>)",
            "(UID BODY.PEEK[2.MIME]<0.8192>)",
            "(UID BODY.PEEK[2.2.MIME]<0.8192>)",
            "(UID BODY.PEEK[2.2]<0.65536>)",
        ])

    def test_top_level_attachment_never_fetches_text(self):
        root = SUMMARY[:-2] + b"Content-Type: text/plain; name=secret.txt\r\n\r\n"
        self.client.uid.return_value = (
            "OK", section_data(422, mail.MESSAGE_SECTION, root, before=b"BODYSTRUCTURE " + PLAIN + b" ")
        )
        result = content(call("read", uid=422, uidvalidity=51))
        self.assertEqual(result["body"], "")
        self.assertIsNone(result["body_format"])
        self.client.uid.assert_called_once()

    def test_html_text_fallback_skips_scripts_and_urls_in_attributes(self):
        root = (SUMMARY[:-2] + b"Content-Type: text/html; charset=UTF-8\r\n"
                b"Content-Transfer-Encoding: base64\r\n\r\n")
        html = '<p>你好 &amp; hello</p><style>.private</style><script>private</script>' \
               '<a href="https://example.test/private">see message</a><img src="https://example.test/t">'
        self.client.uid.side_effect = [
            ("OK", section_data(422, mail.MESSAGE_SECTION, root, before=b"BODYSTRUCTURE " + HTML + b" ")),
            ("OK", section_data(422, "TEXT", base64.b64encode(html.encode()))),
        ]
        result = content(call("read", uid=422, uidvalidity=51))
        self.assertEqual(result["body"], "你好 & hello\nsee message")
        self.assertEqual(result["body_format"], "html_text")
        self.assertFalse(result["truncated"])

    def test_partial_text_marks_truncated_even_if_requested_characters_are_shorter(self):
        root = SUMMARY[:-2] + b"Content-Type: text/plain; charset=UTF-8\r\n\r\n"
        self.client.uid.side_effect = [
            ("OK", section_data(422, mail.MESSAGE_SECTION, root, before=b"BODYSTRUCTURE " + PLAIN + b" ")),
            ("OK", section_data(422, "TEXT", b"a" * mail.BODY_BYTES)),
        ]
        result = content(call("read", uid=422, uidvalidity=51))
        self.assertEqual(len(result["body"]), 4000)
        self.assertTrue(result["truncated"])

    def test_literal_boundary_does_not_interpret_labeled_header_text_as_uid(self):
        root = b"Subject: Test UID 999) (FLAGS \\Seen)\r\n\r\n"
        items = section_data(422, mail.SUMMARY_SECTION, root, trailing_uid=True)
        parsed = mail.parse_fetch(next(mail.fetch_records(items)))
        self.assertEqual(parsed[b"UID"], b"422")
        self.assertEqual(mail.section_bytes(parsed, mail.SUMMARY_SECTION, 8192), root)

    def test_bodystructure_literals_are_parsed_as_single_values(self):
        records = [
            (b'3 (BODYSTRUCTURE ("TEXT" "PLAIN" ("CHARSET" {5}', b"utf-8"),
            b') NIL NIL "8BIT" 6 1) UID 422)',
        ]
        parsed = mail.parse_fetch(next(mail.fetch_records(records)))
        self.assertEqual(parsed[b"BODYSTRUCTURE"][2], [b"CHARSET", b"utf-8"])
        self.assertEqual(parsed[b"UID"], b"422")


class WireFixture(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"* OK local synthetic IMAP fixture\r\n")
        for data in self.rfile:
            tag, command = data.rstrip(b"\r\n").split(b" ", 1)
            self.server.commands.append(command)
            if command == b"CAPABILITY":
                self.wfile.write(b"* CAPABILITY IMAP4rev1\r\n")
            elif command == b'LOGIN "alice" "synthetic-app-password"':
                pass
            elif command == b"EXAMINE INBOX":
                self.wfile.write(b"* 1 EXISTS\r\n* 0 RECENT\r\n* OK [UIDVALIDITY 51] fixed\r\n")
            elif command == b'UID SEARCH 1:1 SUBJECT "Test"':
                self.wfile.write(b"* SEARCH 422\r\n")
            elif command.startswith(b"UID FETCH 422 (UID BODYSTRUCTURE "):
                header = SUMMARY[:-2] + b"Content-Type: text/plain; charset=UTF-8\r\n\r\n"
                self.literal(422, mail.MESSAGE_SECTION, header, before=b"BODYSTRUCTURE " + PLAIN + b" ")
            elif command == b"UID FETCH 422 (UID BODY.PEEK[TEXT]<0.65536>)":
                self.literal(422, "TEXT", "你好".encode())
            elif command == b"UID FETCH 422 (UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)]<0.8192>)":
                self.literal(422, mail.SUMMARY_SECTION, SUMMARY)
            else:
                self.wfile.write(tag + b" BAD unexpected fixture command\r\n")
                continue
            read_only = b"[READ-ONLY] " if command == b"EXAMINE INBOX" else b""
            self.wfile.write(tag + b" OK " + read_only + b"fixture command complete\r\n")

    def literal(self, uid, section, raw, before=b""):
        (descriptor, data), trailer = section_data(uid, section, raw, before, trailing_uid=True)
        sequence, attributes = descriptor.split(b" ", 1)
        self.wfile.write(b"* " + sequence + b" FETCH " + attributes + b"\r\n" + data + trailer + b"\r\n")


class BoundaryTests(unittest.TestCase):
    def test_imap_wire_format_on_loopback_with_synthetic_mail(self):
        with socketserver.ThreadingTCPServer(("127.0.0.1", 0), WireFixture) as server:
            server.commands = []
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with mock.patch.dict(os.environ, CREDS, clear=True), mock.patch.object(
                    mail, "BoundedIMAP",
                    side_effect=lambda *args, **kwargs: imaplib.IMAP4(*server.server_address, timeout=2),
                ):
                    match = content(call("search", subject="Test"))["messages"][0]
                    self.assertEqual(match["uid"], 422)
                    result = content(call("read", uid=match["uid"], uidvalidity=51))
                    self.assertEqual(result["body"], "你好")
            finally:
                server.shutdown()
                thread.join(2)
            self.assertEqual(len(server.commands), 10)
            self.assertEqual(sum(command == b"EXAMINE INBOX" for command in server.commands), 2)

    def test_exact_inline_source_as_mcp_stdio_subprocess(self):
        lines = [
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "ping"},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "icloud_mail_status"}},
            {"jsonrpc": "2.0", "id": 5, "method": "initialize", "params": {"protocolVersion": "unknown"}},
            {"jsonrpc": "2.0", "id": 6, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        ]
        mcp_input = "\n".join(map(json.dumps, lines)) + "\n{invalid\n"
        env = os.environ.copy()
        for key in CREDS:
            env.pop(key, None)
        process = subprocess.run(
            [sys.executable, "-c", RUNTIME.read_text(encoding="utf-8")],
            text=True, input=mcp_input, capture_output=True, env=env, timeout=10, check=True,
        )
        self.assertEqual(process.stderr, "")
        messages = list(map(json.loads, process.stdout.splitlines()))
        self.assertEqual([message["id"] for message in messages], [1, 2, 3, 4, 5, 6, None])
        self.assertEqual(messages[0]["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(len(messages[1]["result"]["tools"]), 3)
        self.assertEqual(messages[2]["result"], {})
        self.assertEqual(content(messages[3])["error"], "missing_credentials")
        self.assertEqual(messages[4]["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(messages[5]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(messages[6]["error"]["code"], -32700)


if __name__ == "__main__":
    unittest.main()
