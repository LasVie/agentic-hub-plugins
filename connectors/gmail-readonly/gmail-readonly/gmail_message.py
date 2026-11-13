"""Build MIME for Gmail sends and preserve untouched draft parts."""
from __future__ import annotations

import base64
from email import policy
from email.errors import MessageError
from email.headerregistry import Address
from email.message import EmailMessage
from email.parser import BytesParser
from html import escape
import re

from auth import ConnectorError

_MESSAGE_ID = re.compile(r"<[^<>\s@]+@[^<>\s@]+>")


def header_text(value: str, name: str, limit: int = 998) -> str:
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ConnectorError("invalid_argument", f"{name} 必须是最多 {limit} 个字符的单行文本。")
    return value


def mailbox(value: str) -> Address:
    try:
        address = Address(addr_spec=header_text(value, "邮箱地址", 254))
    except (ValueError, IndexError, MessageError):
        raise ConnectorError("invalid_address", "请提供完整的邮箱地址，每个地址使用一个参数。") from None
    if not address.username or not address.domain:
        raise ConnectorError("invalid_address", "请提供完整的邮箱地址，每个地址使用一个参数。")
    return address


def recipients(values: list[str]) -> tuple[Address, ...]:
    if not values or len(values) > 20:
        raise ConnectorError("invalid_address", "请提供 1 至 20 个收件人地址。")
    return tuple(mailbox(value) for value in values)


def body_text(value: str) -> str:
    if not isinstance(value, str) or len(value) > 30000 or "\x00" in value:
        raise ConnectorError("invalid_argument", "正文必须是最多 30000 个字符的文本。")
    return value


def reply_recipient(value: str) -> Address:
    header = policy.default.header_factory("To", header_text(value, "回复地址"))
    if header.defects or len(header.addresses) != 1:
        raise ConnectorError("invalid_reply_target", "原邮件的回复地址不明确，请检查邮件头。")
    return mailbox(header.addresses[0].addr_spec)


def reply_references(message_id: str, references: str, in_reply_to: str) -> str:
    if not _MESSAGE_ID.fullmatch(header_text(message_id, "Message-ID")):
        raise ConnectorError("invalid_reply_target", "原邮件缺少有效 Message-ID，无法建立会话回复。")
    chain = header_text(references, "References", 8192).split()
    if not chain and _MESSAGE_ID.fullmatch(header_text(in_reply_to, "In-Reply-To")):
        chain.append(in_reply_to)
    if any(not _MESSAGE_ID.fullmatch(item) for item in chain):
        raise ConnectorError("invalid_reply_target", "原邮件的会话引用格式无效。")
    return " ".join([*chain, message_id])


def new_message(sender: Address, to: tuple[Address, ...], subject: str, body: str) -> EmailMessage:
    mail = EmailMessage(policy=policy.SMTP)
    mail["From"] = sender
    mail["To"] = to
    mail["Subject"] = header_text(subject, "主题")
    mail.set_content(body_text(body))
    return mail


def decode_draft(raw: str) -> EmailMessage:
    try:
        if not isinstance(raw, str) or not raw:
            raise ValueError()
        decoded = base64.b64decode(raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True)
        message = BytesParser(policy=policy.SMTP).parsebytes(decoded)
    except (ValueError, UnicodeError, RecursionError, MessageError):
        raise ConnectorError("invalid_draft", "草稿的 MIME 数据无效，无法安全更新。") from None
    stack = [message]
    for _ in range(200):
        if not stack:
            return message
        part = stack.pop()
        if part.defects or part.get_content_type() in {"multipart/signed", "multipart/encrypted"}:
            raise ConnectorError("invalid_draft", "草稿结构异常、已签名或已加密，无法安全更新。")
        if part.is_multipart():
            stack.extend(part.iter_parts())
    if stack:
        raise ConnectorError("invalid_draft", "草稿结构过于复杂，无法安全更新。")
    return message


def edit_draft_message(
    message: EmailMessage,
    *,
    to: tuple[Address, ...] | None,
    subject: str | None,
    body: str | None,
) -> None:
    if to is not None:
        del message["To"]
        message["To"] = to
    if subject is not None:
        del message["Subject"]
        message["Subject"] = subject
    if body is None:
        return
    plain = message.get_body(preferencelist=("plain",))
    html = message.get_body(preferencelist=("html",))
    if not any(part is not None and not part.get_filename() for part in (plain, html)):
        raise ConnectorError("invalid_draft", "草稿没有可编辑的文本正文。")
    if plain is not None and not plain.get_filename():
        _replace_body(plain, body, "plain")
    if html is not None and not html.get_filename():
        _replace_body(html, f"<pre>{escape(body)}</pre>", "html")


def _replace_body(part: EmailMessage, value: str, subtype: str) -> None:
    headers = [
        (name, part[name])
        for name in ("Content-ID", "Content-Disposition", "Content-Language", "Content-Location")
        if part[name] is not None
    ]
    part.set_content(value, subtype=subtype, charset="utf-8")
    for name, value in headers:
        part[name] = value


def encode_message(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
