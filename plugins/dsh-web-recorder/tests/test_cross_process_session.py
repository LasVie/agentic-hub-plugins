"""Verify start/status/stop survive three separate WorkSwarm-style processes."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve()
TOOLS = HERE.parents[1] / "dsh-web-recorder" / "tools"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = b"<!doctype html><title>cross-process</title><h1>persistent recorder</h1>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def call(class_name: str, payload: dict) -> dict:
    code = """
import asyncio, json, sys
sys.path.insert(0, sys.argv[1])
import web_recorder
async def main():
    result = await getattr(web_recorder, sys.argv[2])().invoke(json.loads(sys.argv[3]))
    print('RESULT_JSON=' + json.dumps(result))
asyncio.run(main())
"""
    run = subprocess.run(
        [sys.executable, "-c", code, str(TOOLS), class_name, json.dumps(payload)],
        check=True, text=True, capture_output=True,
    )
    marker = next(line for line in reversed(run.stdout.splitlines()) if line.startswith("RESULT_JSON="))
    return json.loads(marker.removeprefix("RESULT_JSON="))


def main() -> int:
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    output = Path(tempfile.mkdtemp(prefix="web-recorder-cross-process-")) / "recording"
    start = call("WebRecordStartTool", {"url": f"http://127.0.0.1:{server.server_port}/", "headless": True, "port": 0, "output_dir": str(output)})
    assert start.get("ok"), start
    time.sleep(1)
    status = call("WebRecordStatusTool", {"session_id": start["session_id"]})
    assert status.get("ok") and status.get("active"), status
    stop = call("WebRecordStopTool", {"session_id": start["session_id"]})
    assert stop.get("ok") and not stop.get("active", True), stop
    assert Path(stop["report_md"]).is_file() and Path(stop["events_jsonl"]).is_file()
    assert stop["total_events"] >= 1 and stop["counts"]["network"] >= 1
    server.shutdown()
    print(json.dumps({"start": start, "status": status, "stop": stop}, indent=2))
    print("PASS separate-process start/status/stop persistence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
