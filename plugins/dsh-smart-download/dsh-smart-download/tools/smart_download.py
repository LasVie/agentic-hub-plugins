"""WorkSwarm port of MIT-licensed dsh-smart-download 1.4.6.

Copyright (c) 2026 dsh-smart-dl contributors. Modified to expose standalone
Python/OpenJiuwen tools; see ../licenses/dsh-smart-download/LICENSE.
"""
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


def _error(code: str, message: str, task_id: str | None = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ok": False, "error": {"code": code, "message": message}}
    if task_id:
        result["task_id"] = task_id
    return result


def _status_path(task_id: str) -> Path:
    return _STATUS_DIR / f"{task_id}.json"


def _write_json_private(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
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
        raise ValueError("only absolute HTTP(S) URLs are supported")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("credentials in URLs are not allowed; use headers")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme.lower() == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"host lookup failed: {exc}") from exc
    if not allow_private:
        for info in addresses:
            address = ipaddress.ip_address(info[4][0].split("%")[0])
            if not address.is_global:
                raise ValueError(f"private, local or reserved destination is blocked: {address}")
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))


def _display_url(raw: str) -> str:
    parsed = urllib.parse.urlsplit(raw)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


class _RedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_private: bool) -> None:
        self.allow_private = allow_private
        self.count = 0

    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> urllib.request.Request:
        self.count += 1
        if self.count > _MAX_REDIRECTS:
            raise urllib.error.HTTPError(newurl, code, "too many redirects", headers, fp)
        safe = _validate_url(urllib.parse.urljoin(req.full_url, newurl), self.allow_private)
        return super().redirect_request(req, fp, code, msg, headers, safe)


def _opener(allow_private: bool) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_RedirectHandler(allow_private))


def _headers(raw: Any) -> Dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("headers must be an object of string values")
    result: Dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str) or "\n" in key + value or "\r" in key + value:
            raise ValueError("header names and values must be strings without line breaks")
        if key.lower() in {"host", "content-length", "range"}:
            raise ValueError(f"header is managed by the downloader: {key}")
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
            raise ValueError("server did not honor a byte-range request")
        content_range = response.headers.get("Content-Range", "")
        if not content_range.lower().startswith(f"bytes {start}-{end}/"):
            raise ValueError("server returned an inconsistent Content-Range")
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
            raise ValueError("range response ended before its declared boundary")


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
            description="Download one HTTP(S) file with range acceleration, conservative resume and optional SHA-256 verification.",
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
                raise ValueError("sha256 must contain exactly 64 hexadecimal characters")
            requested_workers = int(inputs.get("workers", 8))
            if requested_workers not in {1, 4, 8}:
                raise ValueError("workers must be 1, 4, or 8")
            probe = _probe(url, custom_headers, timeout, allow_private)
            url = str(probe["url"])
            if inputs.get("output_path") and inputs.get("output_dir"):
                raise ValueError("use output_path or output_dir, not both")
            if inputs.get("output_path"):
                output = Path(str(inputs["output_path"])).expanduser().resolve()
            else:
                directory = Path(str(inputs.get("output_dir", "."))).expanduser().resolve()
                output = directory / _safe_filename(url, probe.get("disposition"))
            if output.exists() and not bool(inputs.get("overwrite", False)):
                raise FileExistsError(f"destination exists: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            part = output.with_name(output.name + ".part")
            meta = output.with_name(output.name + ".part.json")
            if part.is_symlink():
                raise ValueError(f"refusing symbolic-link partial path: {part}")
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
                raise ValueError(f"downloaded size {actual_size} does not match expected {total}")
            actual_hash = _sha256(part)
            record["sha256"] = actual_hash
            if expected and actual_hash != expected:
                part.unlink(missing_ok=True)
                meta.unlink(missing_ok=True)
                raise RuntimeError(f"SHA-256 mismatch: expected {expected}, got {actual_hash}")
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
                code = "CHECKSUM_MISMATCH" if "SHA-256 mismatch" in str(exc) else "DOWNLOAD_FAILED"
            record.update({"state":"failed","error":{"code":code,"message":str(exc)}})
            _save_status(record)
            return _error(code, str(exc), task_id)
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
            description="Read persisted status for a Smart Download task.",
            input_params={"type":"object","properties":{"task_id":{"type":"string","pattern":"^[a-f0-9]{32}$"}},"required":["task_id"]},
            idempotent=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        task_id = str(inputs.get("task_id", ""))
        if not re.fullmatch(r"[a-f0-9]{32}", task_id):
            return _error("INVALID_TASK_ID", "task_id must be the 32-character ID returned by smart_download")
        path = _status_path(task_id)
        if not path.is_file():
            return _error("NOT_FOUND", "download task was not found")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _error("STATUS_READ_FAILED", str(exc))
        return {"ok":True, **_public_status(record)}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)
