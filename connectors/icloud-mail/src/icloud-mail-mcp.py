"""Read-only iCloud Mail connector using MCP stdio and the Python standard library."""

import base64
import binascii
import imaplib
import json
import os
import quopri
import re
import socket
import ssl
import sys
import unicodedata
from contextlib import contextmanager, suppress
from email import policy
from email.parser import BytesHeaderParser
from html.parser import HTMLParser


VERSION = "1.0.0"
PROTOCOLS = ("2025-11-25", "2025-06-18", "2024-11-05")
IMAP_HOST = "imap.mail.me.com"
IMAP_PORT = 993
INBOX = "INBOX"
SEARCH_WINDOW = 100
SEARCH_BATCH = 20
HEADER_BYTES = 8192
BODY_BYTES = 65536
UINT32_MAX = 4294967295
RPC_BYTES = 65536
SUMMARY_HEADERS = "FROM SUBJECT DATE"
MIME_HEADERS = "CONTENT-TYPE CONTENT-DISPOSITION CONTENT-TRANSFER-ENCODING"
SUMMARY_SECTION = "HEADER.FIELDS (" + SUMMARY_HEADERS + ")"
MESSAGE_SECTION = "HEADER.FIELDS (" + SUMMARY_HEADERS + " " + MIME_HEADERS + ")"
TEXT_TYPES = ("text/plain", "text/html")

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}
PHRASE_SCHEMA = {"type": "string", "minLength": 1, "maxLength": 200}
UID_SCHEMA = {"type": "integer", "minimum": 1, "maximum": UINT32_MAX}


def tool_schema(name, description, properties, required=()):
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": list(required),
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
    }


TOOLS = [
    tool_schema("icloud_mail_status", "检查 iCloud 邮箱连接和收件箱读取权限。", {}),
    tool_schema(
        "icloud_mail_search",
        "查询最近 100 封收件箱邮件。至少提供一个主题或发件人关键词。"
        "按字面包含匹配，忽略大小写。两个条件同时提供时需同时满足。按 UID 从新到旧返回摘要。",
        {
            "subject": {**PHRASE_SCHEMA, "description": "邮件主题关键词"},
            "from": {**PHRASE_SCHEMA, "description": "发件人姓名或邮箱中的关键词"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
        },
    ),
    tool_schema(
        "icloud_mail_read",
        "使用查询结果中的 UID 和 UIDVALIDITY 读取指定邮件。优先返回纯文本，也可提取 HTML 中的文字。",
        {
            "uid": {**UID_SCHEMA, "description": "查询结果中的邮件 UID"},
            "uidvalidity": {**UID_SCHEMA, "description": "查询结果中的收件箱 UIDVALIDITY"},
            "max_chars": {"type": "integer", "minimum": 1, "maximum": 12000, "default": 4000},
        },
        ("uid", "uidvalidity"),
    ),
]


class MailError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def response_error():
    return MailError("invalid_imap_response", "iCloud 邮箱返回了无法读取的响应。请稍后重试。")


def message_missing():
    return MailError("message_not_found", "找不到这封收件箱邮件。请重新查询后再读取。")


class BoundedIMAP(imaplib.IMAP4_SSL):
    def read(self, size):
        if size > BODY_BYTES:
            raise response_error()
        return super().read(size)


def credentials():
    address = os.environ.get("ICLOUD_EMAIL", "").strip()
    password = os.environ.get("ICLOUD_APP_PASSWORD", "").strip()
    placeholder_start = "$" + "{"
    if not address or not password or address.startswith(placeholder_start) or password.startswith(placeholder_start):
        raise MailError("missing_credentials", "请在连接器设置中填写 iCloud 邮箱地址和 App 专用密码。")
    if (
        not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", address)
        or not re.fullmatch(r"[!-~]{1,254}", address)
        or not re.fullmatch(r"[ -~]{1,128}", password)
    ):
        raise MailError("invalid_credentials", "请检查 iCloud 邮箱地址和 App 专用密码的格式。")
    return address, password


def number(value, minimum=1):
    if not isinstance(value, bytes) or not re.fullmatch(rb"[0-9]{1,10}", value):
        raise response_error()
    result = int(value)
    if not minimum <= result <= UINT32_MAX:
        raise response_error()
    return result


def imap_quote(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def login(client, address, password):
    for username in (address.split("@", 1)[0], address):
        # imaplib quotes the password itself, but expects an IMAP astring for the username.
        try:
            status, _ = client.login(imap_quote(username), password)
        except imaplib.IMAP4.abort:
            raise
        except imaplib.IMAP4.error:
            continue
        if status == "OK":
            return
    raise MailError(
        "authentication_failed",
        "iCloud 邮箱登录失败。请核对邮箱地址，以及 App 专用密码是否正确、是否已被撤销。",
    )


@contextmanager
def mailbox():
    address, password = credentials()
    client = None
    try:
        client = BoundedIMAP(IMAP_HOST, IMAP_PORT, ssl_context=ssl.create_default_context(), timeout=10)
        login(client, address, password)
        status, counts = client.select(INBOX, readonly=True)
        if status != "OK":
            raise MailError("inbox_unavailable", "无法以只读方式打开 iCloud 收件箱。")
        _, validity = client.response("UIDVALIDITY")
        if not counts or not validity:
            raise response_error()
        yield client, number(counts[-1], minimum=0), number(validity[-1])
    except (socket.timeout, TimeoutError):
        raise MailError("timeout", "连接 iCloud 邮箱超时。请检查网络后重试。") from None
    except ssl.SSLError:
        raise MailError("tls_failed", "无法验证或建立 iCloud 邮箱的安全连接。") from None
    except (imaplib.IMAP4.abort, OSError):
        raise MailError("connection_failed", "无法连接 iCloud 邮箱，或连接已中断。请稍后重试。") from None
    except imaplib.IMAP4.error:
        raise MailError("imap_error", "iCloud 邮箱未能完成请求。请稍后重试。") from None
    finally:
        if client is not None:
            # End the session without CLOSE or another network round trip.
            with suppress(OSError, imaplib.IMAP4.error):
                client.shutdown()


# imaplib separates a FETCH response at each literal. Recombine the wire data
# before parsing so bytes inside a literal cannot be mistaken for an attribute.
FETCH_START = re.compile(rb"^[0-9]+ \(")
FETCH_TOKEN = re.compile(
    rb' *(BODY\[[^\]\r\n]*\](?:<[0-9]+>)?|\(|\)|"(?:\\["\\]|[^"\\\r\n])*"'
    rb'|\{[0-9]{1,10}\}\r\n|[^ ()"{}\r\n]+)',
    re.IGNORECASE,
)
QUOTED_ESCAPE = re.compile(rb'\\(["\\])')


def fetch_records(items):
    fragments = []
    for item in items:
        if item is None:
            continue
        prefix, literal = item if isinstance(item, tuple) else (item, None)
        if FETCH_START.match(prefix) and fragments:
            yield b"".join(fragments)
            fragments = []
        fragments.append(prefix)
        if literal is not None:
            fragments.extend((b"\r\n", literal))
    if fragments:
        yield b"".join(fragments)


def parse_fetch(record):
    start = FETCH_START.match(record)
    if not start or len(record) > 2 * BODY_BYTES:
        raise response_error()

    def read_value(offset, depth):
        match = FETCH_TOKEN.match(record, offset)
        if match is None or depth > 32:
            raise response_error()
        value, offset = match[1], match.end()
        if value == b"(":
            values = []
            while True:
                if record[offset:offset + 1] == b")":
                    return values, offset + 1
                child, offset = read_value(offset, depth + 1)
                values.append(child)
        if value.startswith(b"{"):
            size = int(value[1:-3])
            end = offset + size
            if end > len(record):
                raise response_error()
            return record[offset:end], end
        if value.startswith(b'"'):
            return QUOTED_ESCAPE.sub(rb"\1", value[1:-1]), offset
        if value == b")":
            raise response_error()
        return (None if value.upper() == b"NIL" else value), offset

    values, end = read_value(start.end() - 1, 0)
    if record[end:].strip() or len(values) % 2:
        raise response_error()
    fields = {}
    for name, value in zip(values[::2], values[1::2]):
        if not isinstance(name, bytes):
            raise response_error()
        fields[name.upper()] = value
    return fields


def fetch(client, uids, *attributes):
    uid_set = ",".join(map(str, uids))
    status, items = client.uid("FETCH", uid_set, "(UID " + " ".join(attributes) + ")")
    if status != "OK":
        raise MailError("fetch_failed", "iCloud 邮箱暂时无法读取请求的邮件。")
    requested = set(uids)
    results = {}
    for record in fetch_records(items):
        fields = parse_fetch(record)
        if b"UID" in fields:
            uid = number(fields[b"UID"])
            if uid in requested:
                results.setdefault(uid, {}).update(fields)
    return results


def peek(section, size):
    return f"BODY.PEEK[{section}]<0.{size}>"


def section_bytes(fields, section, size):
    expected = f"BODY[{section}]".encode("ascii")
    header_prefix = b"BODY[HEADER.FIELDS ("
    for key, value in fields.items():
        # A server may echo field names in a different order.
        equivalent = key in (expected, expected + b"<0>")
        if expected.startswith(header_prefix) and key.startswith(header_prefix):
            match = re.fullmatch(rb"BODY\[HEADER\.FIELDS \(([^)]+)\)\](?:<0>)?", key)
            requested_names = set(expected[len(header_prefix):-2].split())
            equivalent = bool(match and {name.strip(b'"') for name in match[1].split()} == requested_names)
        if equivalent:
            if not isinstance(value, bytes) or len(value) > size:
                raise response_error()
            return value
    return None


CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def clean_text(value):
    return CONTROL.sub("", value.replace("\r\n", "\n").replace("\r", "\n"))


def parse_headers(raw):
    return BytesHeaderParser(policy=policy.default).parsebytes(raw)


def summary(uid, headers):
    fields = {"uid": uid}
    for name in ("subject", "from", "date"):
        try:
            header_value = headers.get(name, "")
            fields[name] = clean_text(str(header_value)).replace("\n", " ")
        except (ValueError, IndexError, UnicodeError):
            fields[name] = ""
    return fields


def folded(value):
    return unicodedata.normalize("NFC", value.casefold())


def status_tool():
    with mailbox() as (_, count, validity):
        return {"connected": True, "mailbox": INBOX, "message_count": count, "uidvalidity": validity}


def search_tool(args):
    criteria = {name: args[name] for name in ("subject", "from") if name in args}
    remote = []
    local = {}
    for name, term in criteria.items():
        if term.isascii():
            remote.extend((name.upper(), imap_quote(term)))
        else:
            local[name] = folded(term)
    limit = args.get("limit", 10)
    with mailbox() as (client, count, validity):
        messages = []
        if count:
            first = max(1, count - SEARCH_WINDOW + 1)
            status, data = client.uid("SEARCH", f"{first}:{count}", *remote)
            if status != "OK":
                raise MailError("search_failed", "iCloud 邮箱暂时无法查询收件箱。")
            uids = sorted(
                {number(word) for line in data if line for word in line.split()},
                reverse=True,
            )[:SEARCH_WINDOW]
            batch_size = SEARCH_BATCH if local else limit
            for start in range(0, len(uids), batch_size):
                batch = uids[start:start + batch_size]
                fetched = fetch(client, batch, peek(SUMMARY_SECTION, HEADER_BYTES))
                for uid in batch:
                    raw = section_bytes(fetched.get(uid, {}), SUMMARY_SECTION, HEADER_BYTES)
                    if raw is None:
                        continue
                    metadata = summary(uid, parse_headers(raw))
                    if all(term in folded(metadata[name]) for name, term in local.items()):
                        messages.append(metadata)
                if len(messages) >= limit:
                    break
    return {
        "mailbox": INBOX,
        "uidvalidity": validity,
        "search_window": min(count, SEARCH_WINDOW),
        "returned_count": len(messages[:limit]),
        "messages": messages[:limit],
    }


def allows_body(headers):
    return headers.get_content_disposition() in (None, "inline") and headers.get_filename() is None


def body_candidates(structure, path="", depth=0):
    if not isinstance(structure, list) or not structure or depth > 8:
        return []
    if not isinstance(structure[0], list):
        media = b"/".join(
            attribute.lower() for attribute in structure[:2] if isinstance(attribute, bytes)
        ).decode("ascii", "replace")
        return [(path or "1", media)] if media in TEXT_TYPES else []

    containers = []
    for part in structure:
        if not isinstance(part, list):
            break
        containers.append(part)
    subtype = structure[len(containers):len(containers) + 1]
    kind = subtype[0].lower() if subtype and isinstance(subtype[0], bytes) else b""
    if kind not in (b"mixed", b"alternative", b"related", b"signed", b"report"):
        return []
    if kind in (b"signed", b"report"):
        containers = containers[:1]
    if kind == b"related":
        # The START parameter points to the root by Content-ID. The first part
        # is the default root when START is omitted.
        params_at = len(containers) + 1
        params = structure[params_at] if len(structure) > params_at else None
        start = next(
            (value for key, value in zip(params[::2], params[1::2]) if isinstance(key, bytes) and key.upper() == b"START"),
            None,
        ) if isinstance(params, list) else None
        for index, child in enumerate(containers, 1):
            if start is None or (len(child) > 3 and child[3] == start):
                return body_candidates(child, f"{path}.{index}" if path else str(index), depth + 1)
        return []

    candidates = []
    for index, part in enumerate(containers, 1):
        child_path = f"{path}.{index}" if path else str(index)
        candidates.extend(body_candidates(part, child_path, depth + 1))
    if kind == b"alternative":
        candidates.sort(key=lambda candidate: TEXT_TYPES.index(candidate[1]))
    return candidates


class VisibleHtml(HTMLParser):
    hidden_elements = {"head", "script", "style", "template", "title"}
    blocks = {"address", "article", "br", "div", "h1", "h2", "h3", "h4", "li", "p", "section", "tr"}

    def __init__(self):
        super().__init__()
        self.hidden = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.hidden_elements:
            self.hidden.append(tag)
        elif not self.hidden and tag in self.blocks:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden and tag == self.hidden[-1]:
            self.hidden.pop()
        elif not self.hidden and tag in self.blocks:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(re.sub(r"\s+", " ", data))

    def text(self):
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def decode_body(raw, headers, media, partial):
    encoding = str(headers.get("Content-Transfer-Encoding", "7bit")).strip().lower()
    if encoding == "base64":
        raw = re.sub(rb"\s+", b"", raw)
        if partial:
            raw = raw[:len(raw) // 4 * 4]
        else:
            raw += b"=" * (-len(raw) % 4)
        raw = base64.b64decode(raw, validate=True)
    elif encoding == "quoted-printable":
        if partial:
            raw = re.sub(rb"=[0-9a-fA-F]?\r?$", b"", raw)
        raw = quopri.decodestring(raw)
    elif encoding not in ("7bit", "8bit", "binary"):
        raise MailError("unsupported_encoding", "此邮件正文采用当前连接器无法读取的编码。")

    charset = headers.get_content_charset() or "utf-8"
    try:
        text = raw.decode(charset, "replace")
    except LookupError:
        text = raw.decode("utf-8", "replace")
    if media == "text/html":
        parser = VisibleHtml()
        parser.feed(text)
        parser.close()
        text = parser.text()
    return clean_text(text)


def header_complete(raw):
    return len(raw) < HEADER_BYTES or raw.endswith((b"\r\n\r\n", b"\n\n"))


def read_body(client, uid, fields, root_headers, max_chars):
    structure = fields.get(b"BODYSTRUCTURE")
    if not isinstance(structure, list) or not structure:
        raise response_error()
    if not allows_body(root_headers):
        return {}
    multipart = isinstance(structure[0], list)
    if multipart != (root_headers.get_content_maintype() == "multipart"):
        raise response_error()
    seen_headers = {}
    for path, media in body_candidates(structure)[:10]:
        headers = root_headers
        if multipart:
            parts = path.split(".")
            for index in range(len(parts)):
                ancestor = ".".join(parts[:index + 1])
                if ancestor not in seen_headers:
                    section = ancestor + ".MIME"
                    fetched = fetch(client, [uid], peek(section, HEADER_BYTES))
                    mime = section_bytes(fetched.get(uid, {}), section, HEADER_BYTES)
                    if mime is None:
                        raise message_missing()
                    seen_headers[ancestor] = parse_headers(mime) if header_complete(mime) else None
                headers = seen_headers[ancestor]
                if headers is None or not allows_body(headers):
                    break
        if headers is None or not allows_body(headers) or headers.get_content_type() != media:
            continue
        section = path if multipart else "TEXT"
        fetched = fetch(client, [uid], peek(section, BODY_BYTES))
        raw = section_bytes(fetched.get(uid, {}), section, BODY_BYTES)
        if raw is None:
            raise message_missing()
        partial = len(raw) == BODY_BYTES
        try:
            text = decode_body(raw, headers, media, partial)
        except (binascii.Error, ValueError):
            raise MailError("body_decode_failed", "此邮件的正文编码无法解析。") from None
        return {
            "body": text[:max_chars],
            "body_format": "html_text" if media == "text/html" else "plain_text",
            "truncated": partial or len(text) > max_chars,
        }
    return {}


def read_tool(args):
    uid, expected = args["uid"], args["uidvalidity"]
    with mailbox() as (client, _, validity):
        if validity != expected:
            raise MailError("uidvalidity_changed", "收件箱标识已变化。请重新查询后再读取邮件。")
        fetched = fetch(client, [uid], "BODYSTRUCTURE", peek(MESSAGE_SECTION, HEADER_BYTES))
        fields = fetched.get(uid, {})
        header = section_bytes(fields, MESSAGE_SECTION, HEADER_BYTES)
        if header is None:
            raise message_missing()
        if not header_complete(header):
            raise MailError("headers_too_large", "这封邮件的标头超出读取上限。")
        root_headers = parse_headers(header)
        body = read_body(client, uid, fields, root_headers, args.get("max_chars", 4000))
        result = {"mailbox": INBOX, "uidvalidity": validity, **summary(uid, root_headers)}
        if body:
            return {**result, **body}
        return {
            **result, "body": "", "body_format": None, "truncated": False,
            "message": "这封邮件没有可读取的纯文本或 HTML 正文。",
        }


HANDLERS = {
    "icloud_mail_status": lambda args: status_tool(),
    "icloud_mail_search": search_tool,
    "icloud_mail_read": read_tool,
}
SCHEMAS = {tool["name"]: tool["inputSchema"] for tool in TOOLS}


def valid_arguments(args, schema):
    if not isinstance(args, dict) or any(key not in args for key in schema["required"]):
        return False
    for key, value in args.items():
        spec = schema["properties"].get(key)
        if spec is None:
            return False
        if spec["type"] == "integer":
            if type(value) is not int or not spec["minimum"] <= value <= spec["maximum"]:
                return False
        elif (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > spec["maxLength"]
            or CONTROL.search(value)
            or any(character in value for character in "\r\n\t")
        ):
            return False
    return True


def rpc_error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def transcript(value, is_error=False):
    return {
        "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


def dispatch(request):
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        return rpc_error(None, -32600, "无效的 JSON-RPC 请求。")
    method = request.get("method")
    request_id = request.get("id")
    if not isinstance(method, str) or ("id" in request and type(request_id) not in (str, int)):
        return rpc_error(None, -32600, "无效的 JSON-RPC 请求。")
    if "id" not in request:
        return None
    params = request.get("params", {})
    if not isinstance(params, dict):
        return rpc_error(request_id, -32602, "请求参数必须是对象。")
    if method == "initialize":
        protocol = params.get("protocolVersion")
        if not isinstance(protocol, str) or not protocol:
            return rpc_error(request_id, -32602, "请提供 MCP 协议版本。")
        result = {
            "protocolVersion": protocol if protocol in PROTOCOLS else PROTOCOLS[0],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "icloud-mail", "version": VERSION},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        if not isinstance(name, str) or name not in HANDLERS:
            return rpc_error(request_id, -32602, "未知的 iCloud 邮箱工具。")
        if not valid_arguments(args, SCHEMAS[name]):
            return rpc_error(request_id, -32602, "工具参数不符合要求。请检查输入字段和范围。")
        if name == "icloud_mail_search" and "subject" not in args and "from" not in args:
            return rpc_error(request_id, -32602, "请至少提供一个邮件主题或发件人关键词。")
        try:
            result = transcript(HANDLERS[name](args))
        except MailError as error:
            result = transcript({"error": error.code, "message": str(error)}, is_error=True)
        except Exception:
            return rpc_error(request_id, -32603, "iCloud 邮箱连接器处理请求时发生错误。")
    else:
        return rpc_error(request_id, -32601, "不支持此 MCP 方法。")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def reject_constant(_):
    raise ValueError("Invalid JSON constant")


def main():
    for_line = sys.stdin.buffer
    while True:
        line = for_line.readline(RPC_BYTES + 1)
        if not line:
            break
        if len(line) > RPC_BYTES:
            while line and not line.endswith(b"\n"):
                line = for_line.readline(RPC_BYTES + 1)
            response = rpc_error(None, -32700, "MCP 请求超出读取上限。")
        else:
            try:
                request = json.loads(line.decode("utf-8"), parse_constant=reject_constant)
            except (ValueError, RecursionError):
                response = rpc_error(None, -32700, "无法解析 JSON 请求。")
            else:
                response = dispatch(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
