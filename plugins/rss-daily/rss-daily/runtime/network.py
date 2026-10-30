import email.utils
import html.parser
import http.client
import ipaddress
import re
import socket
import ssl
import urllib.parse
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone


MAX_BYTES = 524288


class FeedError(ValueError):
    pass


def public_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise FeedError("地址必须是不超过 2048 字符的 HTTPS 地址")
    parsed = urllib.parse.urlsplit(value)
    try:
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise FeedError("仅支持不含账号密码的公开 HTTPS 地址")
        if parsed.port not in (None, 443):
            raise FeedError("仅支持 HTTPS 默认端口 443")
        hostname = parsed.hostname.encode("idna").decode("ascii")
        if hostname.lower() == "localhost" or "." not in hostname or any(char.isspace() for char in value):
            raise FeedError("不允许本地或无效地址")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise FeedError("不允许访问非公网地址")
    except (ValueError, UnicodeError) as error:
        raise FeedError("地址格式无效：" + str(error)) from error
    return parsed, hostname


def download(url):
    for redirect_count in range(4):
        parsed, hostname = public_url(url)
        addresses = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(result[4][0]).is_global for result in addresses):
            raise FeedError("域名解析包含非公网地址，已拒绝访问")
        connection = http.client.HTTPSConnection(hostname, timeout=7, context=ssl.create_default_context())
        try:
            raw_socket = socket.create_connection((addresses[0][4][0], 443), timeout=7)
            try:
                connection.sock = ssl.create_default_context().wrap_socket(raw_socket, server_hostname=hostname)
            except BaseException:
                raw_socket.close()
                raise
            target = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
            connection.request("GET", target, headers={
                "User-Agent": "RSSDaily/1.0.0 (+public-feed-reader)",
                "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
                "Accept-Encoding": "identity",
                "Connection": "close",
            })
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                if redirect_count == 3 or not response.getheader("Location"):
                    raise FeedError("订阅源重定向次数过多或缺少目标地址")
                url = urllib.parse.urljoin(url, response.getheader("Location"))
                continue
            if response.status != 200:
                raise FeedError("订阅源返回 HTTP " + str(response.status))
            if response.getheader("Content-Encoding", "identity") != "identity":
                raise FeedError("订阅源未遵守不压缩请求，已停止读取")
            content = response.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise FeedError("订阅源超过 512 KiB 大小限制")
            return content
        finally:
            connection.close()
    raise FeedError("订阅源重定向失败")


class PlainText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(value, limit=1000):
    parser = PlainText()
    parser.feed(value or "")
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()[:limit]


def canonical_url(value):
    parsed, hostname = public_url(value)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(key, item) for key, item in query if not key.lower().startswith("utm_") and key not in ("fbclid", "gclid")]
    return urllib.parse.urlunsplit(("https", hostname, parsed.path or "/", urllib.parse.urlencode(query), ""))


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            parsed = email.utils.parsedate_to_datetime(value)
        except (ValueError, TypeError, IndexError):
            return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).timestamp()


def parse_feed(content, source, now, hours):
    if len(content) > MAX_BYTES or re.search(br"<!\s*(DOCTYPE|ENTITY)\b", content.replace(b"\x00", b""), re.I):
        raise FeedError("订阅源过大或包含不允许的 XML 声明")
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise FeedError("订阅源 XML 解析失败") from error
    local_name = lambda tag: tag.rsplit("}", 1)[-1]
    if local_name(root.tag) not in ("rss", "feed", "RDF"):
        raise FeedError("内容不是受支持的 RSS 或 Atom 订阅源")
    items = []
    skipped = 0
    entries = [node for node in root.iter() if local_name(node.tag) in ("item", "entry")][:200]
    for entry in entries:
        fields = {}
        link = ""
        for child in entry:
            name = local_name(child.tag)
            fields.setdefault(name, "".join(child.itertext()))
            if name == "link" and child.get("rel", "alternate") == "alternate":
                link = child.get("href") or fields[name]
        published = timestamp(fields.get("pubDate") or fields.get("published") or fields.get("updated") or fields.get("date") or "")
        title = plain(fields.get("title"), 240)
        try:
            link = canonical_url(link.strip())
        except FeedError:
            skipped += 1
            continue
        if not title or published is None or published < now - hours * 3600 or published > now + 900:
            skipped += 1
            continue
        items.append({
            "title": title, "url": link, "published_at": datetime.fromtimestamp(published, timezone.utc).isoformat(),
            "timestamp": published, "source": source["name"],
            "excerpt": plain(fields.get("description") or fields.get("summary") or fields.get("content") or ""),
        })
    return items, {"name": source["name"], "url": source["url"], "entries": len(entries), "eligible": len(items), "skipped": skipped}


def fetch_source(source, now, hours):
    try:
        return parse_feed(download(source["url"]), source, now, hours)
    except (OSError, ValueError, http.client.HTTPException) as error:
        return [], {"name": source["name"], "url": source["url"], "error": "订阅源读取失败：" + str(error)[:250]}
