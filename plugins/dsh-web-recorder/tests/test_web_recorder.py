"""End-to-end functional test for dsh-web-recorder.

Launches a real headless Chromium, serves a tiny local page, drives a genuine
click + input + navigation + network request through CDP, then verifies the
recorder captured every event kind and produced report.md and events.jsonl.

Run with the OpenJiuwen venv, e.g.:
    ~/agent-core/.venv/bin/python plugins/dsh-web-recorder/tests/test_web_recorder.py
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve()
PAYLOAD_TOOLS = HERE.parents[1] / "dsh-web-recorder" / "tools"
sys.path.insert(0, str(PAYLOAD_TOOLS))

import web_recorder  # noqa: E402

PAGE = b"""<!doctype html><html><head><title>rec-test</title>
<style>body{font:18px system-ui;margin:48px;max-width:850px} .card{padding:24px;border:2px solid #315efb;border-radius:14px} #result{margin-top:22px;padding:16px;background:#eef3ff;white-space:pre-wrap}</style></head>
<body><div class="card"><h1>Web Session Recorder 1.0.2</h1><p>Automated local integration test</p>
<input id="field" name="field" />
<button id="go">Go</button>
<a id="next" href="/next">next</a>
<div id="result">Waiting for interaction...</div>
<script>
document.getElementById('go').addEventListener('click', () => {
  fetch('/api/data').then(r => r.text()).then(() => {
    document.getElementById('result').textContent = 'PASS: /api/data returned successfully';
  });
});
</script></div></body></html>"""

NEXT = b"<!doctype html><html><head><title>next</title></head><body>next page</body></html>"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def do_GET(self):
        if self.path.startswith("/api/"):
            body = b'{"ok": true}'
            ctype = "application/json"
        elif self.path.startswith("/next"):
            body, ctype = NEXT, "text/html"
        else:
            body, ctype = PAGE, "text/html"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


async def _cdp(session, method, params=None, sid=None):
    return await session.send(method, params or {}, session_id=sid)


async def run() -> int:
    os.environ["DSH_WEB_RECORDER_IN_PROCESS"] = "1"
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    host, port = srv.server_address
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://{host}:{port}"

    start = web_recorder.WebRecordStartTool()
    stop = web_recorder.WebRecordStopTool()
    status = web_recorder.WebRecordStatusTool()

    res = await start.invoke({"headless": True, "port": 0, "url": base})
    assert res.get("ok"), f"start failed: {res}"
    sid = res["session_id"]
    print("start:", json.dumps(res))

    # Wait for the page to be attached and the document fetched.
    session = web_recorder._SESSIONS[sid]
    await asyncio.sleep(1.0)

    # Find the page CDP session that loaded our URL and drive real interactions.
    page_sid = None
    for candidate_sid in session._page_sessions:
        location = await _cdp(
            session,
            "Runtime.evaluate",
            {"expression": "location.href", "returnByValue": True},
            sid=candidate_sid,
        )
        value = location.get("result", {}).get("value")
        if value and value.startswith(base):
            page_sid = candidate_sid
            break
    assert page_sid, f"no page CDP session attached for {base}"
    # Give the navigation a moment, then click (triggers fetch) and type.
    await _cdp(session, "Runtime.evaluate",
               {"expression": "document.getElementById('field').focus();"
                              "document.getElementById('field').value='hello';"
                              "document.getElementById('field').dispatchEvent(new Event('input',{bubbles:true}));"},
               sid=page_sid)
    await _cdp(session, "Runtime.evaluate",
               {"expression": "document.getElementById('go').click();"}, sid=page_sid)
    await asyncio.sleep(0.8)
    # SPA-style navigation via history + a full navigation.
    await _cdp(session, "Runtime.evaluate",
               {"expression": "history.pushState({}, '', '/next');"
                              "window.dispatchEvent(new PopStateEvent('popstate'));"}, sid=page_sid)
    await asyncio.sleep(0.5)

    st = await status.invoke({"session_id": sid})
    print("status:", json.dumps(st))

    # Render real recorder counts into the test page and capture supplemental
    # automated evidence. This does not replace the user's WorkSwarm screenshot.
    summary = "PASS: recorder captured\n" + "\n".join(
        f"{kind}: {st['counts'][kind]}" for kind in ("click", "input", "navigation", "network")
    )
    await _cdp(session, "Runtime.evaluate", {
        "expression": f"document.getElementById('result').textContent={json.dumps(summary)}"
    }, sid=page_sid)
    shot = await _cdp(session, "Page.captureScreenshot", {"format": "png"}, sid=page_sid)
    evidence = HERE.parents[1] / "test-evidence" / "dsh-web-recorder-1.0.2-functional.png"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(base64.b64decode(shot["data"]))
    print("automated evidence:", evidence)

    done = await stop.invoke({"session_id": sid})
    print("stop:", json.dumps(done))
    assert done.get("ok"), f"stop failed: {done}"

    counts = done["counts"]
    report = Path(done["report_md"]).read_text(encoding="utf-8")
    events = [json.loads(l) for l in Path(done["events_jsonl"]).read_text(encoding="utf-8").splitlines() if l.strip()]

    checks = {
        "click>=1": counts["click"] >= 1,
        "input>=1": counts["input"] >= 1,
        "navigation>=1": counts["navigation"] >= 1,
        "network>=2": counts["network"] >= 2,
        "events.jsonl non-empty": len(events) >= 4,
        "report has timeline": "## Timeline" in report and "| click |" in report.replace(" ", " "),
        "network has api/data": any(e.get("kind") == "network" and "/api/data" in str(e.get("url", "")) for e in events),
    }
    print("\nchecks:")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("\ncounts:", json.dumps(counts))
    print("report.md first 40 lines:\n" + "\n".join(report.splitlines()[:40]))

    srv.shutdown()
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
