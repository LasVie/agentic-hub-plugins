"""WorkSwarm port of MIT-licensed dsh-smart-download 1.4.6.

Copyright (c) 2026 dsh-smart-dl contributors. Modified to expose standalone
Python/OpenJiuwen tools; see ../licenses/dsh-smart-download/LICENSE.
"""
# 修改说明（2026-10-22）：将工具说明与可读错误中文化，保留接口、状态值和原始 MIT 署名；
# 校验错误改用专用异常保持错误码稳定，状态中的网址隐藏用户凭据与查询参数；保留既有下载目录权限。
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Mapping

from openjiuwen.core.foundation.tool import Tool, ToolCard

_STATUS_DIR = Path(tempfile.gettempdir()) / "workswarm-dsh-smart-download-status"
_LOCK = threading.RLock()
_CHUNK = 256 * 1024
_MIN_MULTI = 1024 * 1024
_MAX_REDIRECTS = 5
_USER_AGENT = "WorkSwarm-Smart-Download/1.0"


class _ChecksumMismatchError(RuntimeError):
    """校验失败的内部标记，不依赖面向用户的错误文字进行分类。"""


def _error_message(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP 请求失败（状态码 {exc.code}），请检查网址、访问权限和服务器状态"
    if isinstance(exc, urllib.error.URLError):
        return "网络连接失败，请检查网络、服务器地址和访问权限"
    if isinstance(exc, TimeoutError):
        return "网络请求超时，请检查连接后重试"
    message = str(exc)
    if any("\u4e00" <= char <= "\u9fff" for char in message):
        return message
    if isinstance(exc, OSError):
        return f"文件或网络操作失败（系统错误码 {exc.errno}），请检查路径权限、网络连接和剩余空间"
    if isinstance(exc, ValueError):
        return "参数或服务器响应格式无效，请检查网址、输出路径和下载参数"
    return f"下载操作失败（异常类型 {type(exc).__name__}），请检查网络和服务器响应后重试"


def _error(code: str, message: str, task_id: str | None = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ok": False, "error": {"code": code, "message": message}}
    if task_id:
        result["task_id"] = task_id
    return result


def _status_path(task_id: str) -> Path:
    return _STATUS_DIR / f"{task_id}.json"


def _write_json_private(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent == _STATUS_DIR:
        os.chmod(path.parent, 0o700)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def _save_status(record: Dict[str, Any]) -> None:
    record["updated_at"] = time.time()
    with _LOCK:
        _write_json_private(_status_path(str(record["task_id"])), record)


def _public_status(record: Mapping[str, Any]) -> Dict[str, Any]:
    allowed = ("task_id", "state", "url", "output_path", "bytes_downloaded", "total_bytes", "workers", "resumed", "sha256", "verified", "error", "updated_at")
    return {key: record[key] for key in allowed if key in record}


def _validate_url(raw: str, allow_private: bool) -> str:
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("只支持包含主机名的完整 HTTP(S) 网址")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("网址中不能包含用户名或密码；需要认证时请使用 headers")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme.lower() == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("无法解析服务器主机名，请检查网址和 DNS 网络连接") from exc
    if not allow_private:
        for info in addresses:
            address = ipaddress.ip_address(info[4][0].split("%")[0])
            if not address.is_global:
                raise ValueError(f"默认禁止访问私有、本地或保留地址：{address}")
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))


def _display_url(raw: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return ""
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1], parsed.path, "", ""))


class _RedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_private: bool) -> None:
        self.allow_private = allow_private
        self.count = 0

    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> urllib.request.Request:
        self.count += 1
        if self.count > _MAX_REDIRECTS:
            raise urllib.error.HTTPError(newurl, code, "重定向次数过多", headers, fp)
        safe = _validate_url(urllib.parse.urljoin(req.full_url, newurl), self.allow_private)
        return super().redirect_request(req, fp, code, msg, headers, safe)


def _opener(allow_private: bool) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_RedirectHandler(allow_private))


def _headers(raw: Any) -> Dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("headers 必须为键和值均为字符串的对象")
    result: Dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str) or "\n" in key + value or "\r" in key + value:
            raise ValueError("请求头名称和值必须是字符串，且不能包含换行符")
        if key.lower() in {"host", "content-length", "range"}:
            raise ValueError(f"此请求头由下载器管理，不能手动设置：{key}")
        result[key] = value
    result.setdefault("User-Agent", _USER_AGENT)
    return result


def _request(opener: urllib.request.OpenerDirector, url: str, headers: Mapping[str, str], timeout: float, method: str = "GET") -> Any:
    return opener.open(urllib.request.Request(url, headers=dict(headers), method=method), timeout=timeout)


def _total_from_content_range(value: str | None) -> int | None:
    match = re.match(r"bytes\s+\d+-\d+/(\d+|\*)", value or "", re.I)
    return int(match.group(1)) if match and match.group(1) != "*" else None


def _probe(url: str, headers: Mapping[str, str], timeout: float, allow_private: bool) -> Dict[str, Any]:
    opener = _opener(allow_private)
    total: int | None = None
    final_url = url
    accept_ranges = False
    etag = None
    modified = None
    disposition = None
    try:
        with _request(opener, url, headers, timeout, "HEAD") as response:
            final_url = _validate_url(response.geturl(), allow_private)
            total = int(response.headers["Content-Length"]) if response.headers.get("Content-Length", "").isdigit() else None
            accept_ranges = "bytes" in response.headers.get("Accept-Ranges", "").lower()
            etag = response.headers.get("ETag")
            modified = response.headers.get("Last-Modified")
            disposition = response.headers.get("Content-Disposition")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        pass
    range_headers = dict(headers)
    range_headers["Range"] = "bytes=0-0"
    try:
        with _request(_opener(allow_private), final_url, range_headers, timeout) as response:
            final_url = _validate_url(response.geturl(), allow_private)
            if response.status == 206:
                accept_ranges = True
                total = _total_from_content_range(response.headers.get("Content-Range")) or total
            elif total is None and response.headers.get("Content-Length", "").isdigit():
                total = int(response.headers["Content-Length"])
            etag = response.headers.get("ETag") or etag
            modified = response.headers.get("Last-Modified") or modified
            disposition = response.headers.get("Content-Disposition") or disposition
            response.read(1)
    except urllib.error.HTTPError as exc:
        if exc.code == 416:
            total = _total_from_content_range(exc.headers.get("Content-Range")) or total
        elif total is None:
            raise
    return {"url": final_url, "total": total, "accept_ranges": accept_ranges, "etag": etag, "modified": modified, "disposition": disposition}


def _safe_filename(url: str, disposition: str | None) -> str:
    candidate = ""
    if disposition:
        encoded = re.search(r"filename\*=UTF-8''([^;]+)", disposition, re.I)
        plain = re.search(r'filename="?([^";]+)', disposition, re.I)
        candidate = urllib.parse.unquote(encoded.group(1)) if encoded else (plain.group(1) if plain else "")
    if not candidate:
        candidate = urllib.parse.unquote(Path(urllib.parse.urlsplit(url).path).name)
    candidate = re.sub(r"[\\/\x00-\x1f\x7f]", "_", candidate).strip(" .")
    return candidate[:240] or "download.bin"


def _download_range(url: str, headers: Mapping[str, str], timeout: float, allow_private: bool, start: int, end: int, target: Path, progress: Any) -> None:
    request_headers = dict(headers)
    request_headers["Range"] = f"bytes={start}-{end}"
    with _request(_opener(allow_private), url, request_headers, timeout) as response:
        if response.status != 206:
            raise ValueError("服务器未按请求返回字节分段")
        content_range = response.headers.get("Content-Range", "")
        if not content_range.lower().startswith(f"bytes {start}-{end}/"):
            raise ValueError("服务器返回的 Content-Range 与请求范围不一致")
        written = 0
        with target.open("wb") as handle:
            while True:
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)
                progress(len(chunk))
        if written != end - start + 1:
            raise ValueError("分段响应在声明的边界前提前结束")


def _fingerprint(probe: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: probe.get(key) for key in ("url", "total", "etag", "modified")}


def _single_download(url: str, headers: Mapping[str, str], timeout: float, allow_private: bool, part: Path, meta: Path, probe: Mapping[str, Any], progress: Any) -> bool:
    resumed = False
    start = 0
    if part.is_file() and meta.is_file() and probe.get("accept_ranges"):
        try:
            prior = json.loads(meta.read_text(encoding="utf-8"))
            if prior == _fingerprint(probe) and part.stat().st_size < int(probe.get("total") or 0):
                start = part.stat().st_size
                resumed = start > 0
        except (OSError, ValueError, json.JSONDecodeError):
            start = 0
    if not resumed:
        part.unlink(missing_ok=True)
        _write_json_private(meta, _fingerprint(probe))
    request_headers = dict(headers)
    if resumed:
        request_headers["Range"] = f"bytes={start}-"
        if probe.get("etag"):
            request_headers["If-Range"] = str(probe["etag"])
        elif probe.get("modified"):
            request_headers["If-Range"] = str(probe["modified"])
    with _request(_opener(allow_private), url, request_headers, timeout) as response:
        if resumed and response.status != 206:
            start = 0
            resumed = False
            part.unlink(missing_ok=True)
            return _single_download(url, headers, timeout, allow_private, part, meta, {**probe, "accept_ranges": False}, progress)
        mode = "ab" if resumed else "wb"
        with part.open(mode) as handle:
            while True:
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                handle.write(chunk)
                progress(len(chunk))
    return resumed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SmartDownloadTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="smart_download", name="smart_download",
            description="下载一个 HTTP(S) 文件，支持分段加速、安全续传及可选的 SHA-256 校验。",
            input_params={"type":"object","properties":{
                "url":{"type":"string"}, "output_path":{"type":"string"}, "output_dir":{"type":"string"},
                "sha256":{"type":"string","pattern":"^[A-Fa-f0-9]{64}$"},
                "headers":{"type":"object","additionalProperties":{"type":"string"}},
                "workers":{"type":"integer","enum":[1,4,8],"default":8},
                "timeout_seconds":{"type":"number","minimum":1,"maximum":600,"default":60},
                "overwrite":{"type":"boolean","default":False},
                "allow_private_network":{"type":"boolean","default":False}
            },"required":["url"]}, parallel_safe=False))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        task_id = uuid.uuid4().hex
        record: Dict[str, Any] = {"task_id":task_id,"state":"starting","url":_display_url(str(inputs.get("url", ""))),"bytes_downloaded":0,"total_bytes":None,"workers":1,"resumed":False,"verified":False}
        _save_status(record)
        part: Path | None = None
        meta: Path | None = None
        segment_dir: Path | None = None
        try:
            allow_private = bool(inputs.get("allow_private_network", False))
            url = _validate_url(str(inputs.get("url", "")), allow_private)
            custom_headers = _headers(inputs.get("headers"))
            timeout = float(inputs.get("timeout_seconds", 60))
            expected = str(inputs.get("sha256", "")).lower() or None
            if expected and not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise ValueError("sha256 必须恰好包含 64 个十六进制字符")
            requested_workers = int(inputs.get("workers", 8))
            if requested_workers not in {1, 4, 8}:
                raise ValueError("workers 只能为 1、4 或 8")
            probe = _probe(url, custom_headers, timeout, allow_private)
            url = str(probe["url"])
            if inputs.get("output_path") and inputs.get("output_dir"):
                raise ValueError("output_path 与 output_dir 只能选择其中一个")
            if inputs.get("output_path"):
                output = Path(str(inputs["output_path"])).expanduser().resolve()
            else:
                directory = Path(str(inputs.get("output_dir", "."))).expanduser().resolve()
                output = directory / _safe_filename(url, probe.get("disposition"))
            if output.exists() and not bool(inputs.get("overwrite", False)):
                raise FileExistsError(f"目标文件已存在，未执行覆盖：{output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            part = output.with_name(output.name + ".part")
            meta = output.with_name(output.name + ".part.json")
            if part.is_symlink():
                raise ValueError(f"拒绝使用符号链接作为下载临时文件：{part}")
            total = probe.get("total")
            workers = requested_workers if probe.get("accept_ranges") and isinstance(total, int) and total >= _MIN_MULTI else 1
            record.update({"state":"downloading","url":_display_url(url),"output_path":str(output),"total_bytes":total,"workers":workers})
            _save_status(record)

            def progress(amount: int) -> None:
                with _LOCK:
                    record["bytes_downloaded"] = int(record.get("bytes_downloaded", 0)) + amount
                _save_status(record)

            if workers > 1:
                part.unlink(missing_ok=True)
                meta.unlink(missing_ok=True)
                segment_dir = Path(tempfile.mkdtemp(prefix="smart-download-", dir=str(output.parent)))
                os.chmod(segment_dir, 0o700)
                ranges = []
                for index in range(workers):
                    start = index * total // workers
                    end = ((index + 1) * total // workers) - 1
                    ranges.append((index, start, end, segment_dir / f"{index}.part"))
                try:
                    with ThreadPoolExecutor(max_workers=workers) as pool:
                        futures = [pool.submit(_download_range, url, custom_headers, timeout, allow_private, start, end, path, progress) for _index,start,end,path in ranges]
                        for future in as_completed(futures):
                            future.result()
                    with part.open("wb") as combined:
                        for _index, _start, _end, path in ranges:
                            with path.open("rb") as source:
                                for chunk in iter(lambda: source.read(_CHUNK), b""):
                                    combined.write(chunk)
                except Exception:
                    record["bytes_downloaded"] = 0
                    record["workers"] = 1
                    _save_status(record)
                    part.unlink(missing_ok=True)
                    record["resumed"] = _single_download(url, custom_headers, timeout, allow_private, part, meta, probe, progress)
            else:
                record["resumed"] = _single_download(url, custom_headers, timeout, allow_private, part, meta, probe, progress)
            actual_size = part.stat().st_size
            if isinstance(total, int) and actual_size != total:
                raise ValueError(f"实际下载大小 {actual_size} 字节与预期 {total} 字节不一致")
            actual_hash = _sha256(part)
            record["sha256"] = actual_hash
            if expected and actual_hash != expected:
                part.unlink(missing_ok=True)
                meta.unlink(missing_ok=True)
                raise _ChecksumMismatchError(f"SHA-256 校验失败：预期 {expected}，实际 {actual_hash}")
            record["verified"] = bool(expected)
            os.replace(part, output)
            meta.unlink(missing_ok=True)
            record.update({"state":"completed","bytes_downloaded":actual_size,"total_bytes":actual_size})
            _save_status(record)
            return {"ok":True, **_public_status(record)}
        except Exception as exc:
            if isinstance(exc, FileExistsError):
                code = "OUTPUT_EXISTS"
            else:
                code = "CHECKSUM_MISMATCH" if isinstance(exc, _ChecksumMismatchError) else "DOWNLOAD_FAILED"
            message = _error_message(exc)
            record.update({"state":"failed","error":{"code":code,"message":message}})
            _save_status(record)
            return _error(code, message, task_id)
        finally:
            if segment_dir and segment_dir.is_dir():
                for child in segment_dir.iterdir():
                    child.unlink(missing_ok=True)
                segment_dir.rmdir()

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class DownloadStatusTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="download_status", name="download_status",
            description="读取智能下载任务已保存的状态和进度。",
            input_params={"type":"object","properties":{"task_id":{"type":"string","pattern":"^[a-f0-9]{32}$"}},"required":["task_id"]},
            idempotent=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        task_id = str(inputs.get("task_id", ""))
        if not re.fullmatch(r"[a-f0-9]{32}", task_id):
            return _error("INVALID_TASK_ID", "task_id 必须为 smart_download 返回的 32 个字符任务标识")
        path = _status_path(task_id)
        if not path.is_file():
            return _error("NOT_FOUND", "未找到该下载任务")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _error("STATUS_READ_FAILED", "无法读取任务状态：" + _error_message(exc))
        return {"ok":True, **_public_status(record)}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)
