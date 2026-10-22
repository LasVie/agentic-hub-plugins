#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import socket
import sys
import tempfile
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import openjiuwen.core.foundation.tool as tool_api  # type: ignore[import-not-found]
    USING_ACTUAL_SDK = True
except ModuleNotFoundError:
    USING_ACTUAL_SDK = False
    tool_module = types.ModuleType("openjiuwen.core.foundation.tool")

    class ToolCard:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Tool:
        def __init__(self, card):
            self.card = card

    tool_module.Tool = Tool
    tool_module.ToolCard = ToolCard
    for name in ("openjiuwen", "openjiuwen.core", "openjiuwen.core.foundation"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["openjiuwen.core.foundation.tool"] = tool_module

if os.environ.get("REQUIRE_OPENJIUWEN") == "1" and not USING_ACTUAL_SDK:
    raise SystemExit("Actual OpenJiuwen SDK is required for this integration run")

FILE = Path(os.environ["SMART_DOWNLOAD_PAYLOAD"]) / "tools/smart_download.py" if os.environ.get("SMART_DOWNLOAD_PAYLOAD") else Path(__file__).parents[1] / "plugins/dsh-smart-download/dsh-smart-download/tools/smart_download.py"
spec = importlib.util.spec_from_file_location("smart_download", FILE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

DATA = (b"smart-download-range-test\n" * 70000) + b"done"
ETAG = '"smart-download-test-v1"'


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    fail_single_once = False

    def log_message(self, *_args):
        pass

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            # Probe requests intentionally read one byte then close; fallback
            # deliberately cancels servers that ignore range requests.
            pass

    def _common(self, length):
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", ETAG)
        self.send_header("Content-Disposition", 'attachment; filename="payload.bin"')

    def do_HEAD(self):
        self.send_response(200)
        self._common(len(DATA))
        self.end_headers()

    def do_GET(self):
        value = None if self.path.startswith("/no-range") else self.headers.get("Range")
        if value:
            start_text, end_text = value.removeprefix("bytes=").split("-", 1)
            start = int(start_text)
            end = int(end_text) if end_text else len(DATA) - 1
            body = DATA[start:end + 1]
            self.send_response(206)
            self._common(len(body))
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(DATA)}")
            self.end_headers()
            self.wfile.write(body)
            return
        if type(self).fail_single_once:
            type(self).fail_single_once = False
            body = DATA[:300000]
            self.send_response(200)
            self._common(len(DATA))
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            self.close_connection = True
            return
        self.send_response(200)
        self._common(len(DATA))
        self.end_headers()
        self.wfile.write(DATA)


async def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}/payload?secret=redacted"
    expected = hashlib.sha256(DATA).hexdigest()
    try:
        with tempfile.TemporaryDirectory(prefix="smart-download-test-") as raw:
            root = Path(raw)
            root.chmod(0o750)
            blocked = await mod.SmartDownloadTool().invoke({"url": base, "output_path": str(root / "blocked.bin")})
            assert blocked["error"]["code"] == "DOWNLOAD_FAILED" and not (root / "blocked.bin").exists()
            assert "默认禁止访问" in blocked["error"]["message"]

            credential_url = base.replace("http://", "http://测试用户:不能泄露@")
            rejected_credentials = await mod.SmartDownloadTool().invoke({"url": credential_url})
            rejected_status = await mod.DownloadStatusTool().invoke({"task_id": rejected_credentials["task_id"]})
            assert rejected_credentials["error"]["code"] == "DOWNLOAD_FAILED"
            assert "网址中不能包含" in rejected_credentials["error"]["message"]
            assert "不能泄露" not in json.dumps(rejected_credentials, ensure_ascii=False)
            assert "测试用户" not in json.dumps(rejected_status, ensure_ascii=False)
            assert "secret" not in rejected_status["url"]

            malformed = await mod.SmartDownloadTool().invoke({"url": "http://["})
            assert malformed["error"]["code"] == "DOWNLOAD_FAILED" and "参数" in malformed["error"]["message"]

            result = await mod.SmartDownloadTool().invoke({
                "url": base, "output_dir": str(root), "workers": 4,
                "sha256": expected, "allow_private_network": True,
            })
            assert result["ok"] and result["workers"] == 4 and result["verified"]
            assert result["url"].endswith("/payload") and "secret" not in result["url"]
            output = Path(result["output_path"])
            assert output.name == "payload.bin" and output.read_bytes() == DATA
            status = await mod.DownloadStatusTool().invoke({"task_id": result["task_id"]})
            assert status["ok"] and status["state"] == "completed" and status["sha256"] == expected

            protected = await mod.SmartDownloadTool().invoke({
                "url": base, "output_path": str(output), "allow_private_network": True,
            })
            assert protected["error"]["code"] == "OUTPUT_EXISTS" and "目标文件已存在" in protected["error"]["message"]
            assert output.read_bytes() == DATA

            fallback = await mod.SmartDownloadTool().invoke({
                "url": base.replace("/payload", "/no-range"), "output_path": str(root / "中文回退.bin"),
                "workers": 8, "sha256": expected, "allow_private_network": True,
            })
            assert fallback["ok"] and fallback["workers"] == 1 and fallback["verified"]
            assert Path(fallback["output_path"]).read_bytes() == DATA

            mismatch_path = root / "mismatch.bin"
            mismatch = await mod.SmartDownloadTool().invoke({
                "url": base, "output_path": str(mismatch_path), "workers": 1,
                "sha256": "0" * 64, "allow_private_network": True,
            })
            assert mismatch["error"]["code"] == "CHECKSUM_MISMATCH" and not mismatch_path.exists()
            assert "SHA-256 校验失败" in mismatch["error"]["message"]
            mismatch_status = await mod.DownloadStatusTool().invoke({"task_id": mismatch["task_id"]})
            assert mismatch_status["error"]["code"] == "CHECKSUM_MISMATCH"
            assert "SHA-256 校验失败" in mismatch_status["error"]["message"]

            resume_path = root / "resume.bin"
            Handler.fail_single_once = True
            interrupted = await mod.SmartDownloadTool().invoke({
                "url": base, "output_path": str(resume_path), "workers": 1,
                "allow_private_network": True,
            })
            assert not interrupted["ok"] and resume_path.with_name("resume.bin.part").is_file()
            resumed = await mod.SmartDownloadTool().invoke({
                "url": base, "output_path": str(resume_path), "workers": 1,
                "sha256": expected, "allow_private_network": True,
            })
            assert resumed["ok"] and resumed["resumed"] and resume_path.read_bytes() == DATA
            assert (root.stat().st_mode & 0o777) == 0o750
            assert (mod._status_path(resumed["task_id"]).stat().st_mode & 0o777) == 0o600
            assert (mod._STATUS_DIR.stat().st_mode & 0o777) == 0o700

            invalid = await mod.DownloadStatusTool().invoke({"task_id": "../bad"})
            assert invalid["error"]["code"] == "INVALID_TASK_ID"
            assert "32 个字符" in invalid["error"]["message"]
            absent = await mod.DownloadStatusTool().invoke({"task_id": "0" * 32})
            assert absent["error"]["code"] == "NOT_FOUND" and "未找到" in absent["error"]["message"]
    finally:
        server.shutdown()
        server.server_close()
    print("Tool API backend:", getattr(tool_api, "__file__", "unknown") if USING_ACTUAL_SDK else "synthetic fallback")
    print("dsh-smart-download integration: PASS")


if __name__ == "__main__":
    asyncio.run(main())
