"""Small HTTPS JSON transport for the connector's fixed provider endpoints."""

import json
import socket
import urllib.error
import urllib.request


class ConnectorError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(url, *, body=None, headers=None, form=None, raw=False, method=None):
    req_headers = {"Accept": "application/json", **(headers or {})}
    if form is not None:
        from urllib.parse import urlencode

        data = urlencode(form).encode("ascii")
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=25) as response:
            limit = 1048576 if raw else 4194304
            content = response.read(limit + 1)
    except urllib.error.HTTPError as error:
        messages = {
            401: "授权无效或已过期，请检查连接。",
            403: "当前账号没有所需权限。",
            404: "指定资源不存在或当前账号无法访问。",
            429: "请求超出服务限制，请稍后再试。",
        }
        raise ConnectorError(messages.get(error.code, f"服务返回 HTTP {error.code}。")) from None
    except (urllib.error.URLError, socket.timeout) as error:
        raise ConnectorError("无法访问服务，请检查网络并重试。") from error
    if len(content) > limit:
        raise ConnectorError("返回内容超过此连接器的大小限制。")
    if raw:
        return content
    try:
        return json.loads(content) if content else {}
    except (ValueError, UnicodeError) as error:
        raise ConnectorError("服务返回了无法解析的内容。") from error
