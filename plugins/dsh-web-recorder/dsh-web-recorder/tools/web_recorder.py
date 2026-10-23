"""Independent WorkSwarm/OpenJiuwen implementation of a user-guided web session recorder.

Native design (see ../NATIVE_DESIGN.md). Written from the public functional
description of the DSH ``dsh-web-recorder`` candidate (record real clicks, inputs,
navigation and network traffic in a user-guided browser session, then emit a
Markdown timeline report plus an events.jsonl log). No upstream DSH/Cordis code,
prompts or assets were copied; the DSH bundle/Cordis runtime is not portable to
this host. Capture is implemented directly over the Chrome DevTools Protocol
(CDP) using ``aiohttp`` (a declared host dependency) and an installed
Chrome/Edge/Chromium browser, which the host already assumes for browser tooling.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from openjiuwen.core.foundation.tool import Tool, ToolCard

# In-process sessions are retained for the integration harness. Normal host
# calls use a detached worker plus file-backed state because WorkSwarm may load
# each tool invocation in a fresh process.
_SESSIONS: "dict[str, RecordingSession]" = {}
_REGISTRY = Path(tempfile.gettempdir()) / "dsh-web-recorder-registry"

# Page-side capture hook. Added before every document so early interactions are
# not missed. Only the *length* of input values is reported, never their content.
_INJECT_JS = r"""
(() => {
  if (window.__dshHooked) return; window.__dshHooked = true;
  const send = (o) => { try { window.__dshRecord(JSON.stringify(o)); } catch (e) {} };
  const desc = (el) => {
    if (!el || !el.tagName) return '';
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    const nm = el.getAttribute && el.getAttribute('name');
    if (nm) s += '[name=' + nm + ']';
    const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40);
    if (t) s += ' "' + t + '"';
    return s;
  };
  document.addEventListener('click', (e) => send({kind: 'click', target: desc(e.target), x: e.clientX, y: e.clientY, url: location.href}), true);
  document.addEventListener('input', (e) => send({kind: 'input', target: desc(e.target), value_len: (e.target && e.target.value != null) ? String(e.target.value).length : 0, url: location.href}), true);
  document.addEventListener('change', (e) => send({kind: 'change', target: desc(e.target), url: location.href}), true);
  document.addEventListener('submit', (e) => send({kind: 'submit', target: desc(e.target), url: location.href}), true);
  window.addEventListener('popstate', () => send({kind: 'navigation', via: 'popstate', url: location.href}));
  window.addEventListener('hashchange', () => send({kind: 'navigation', via: 'hashchange', url: location.href}));
})();
"""


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _registry_path(session_id: str) -> Path:
    return _REGISTRY / f"{session_id}.json"


def _session_paths(session_id: str) -> Optional[Dict[str, Path]]:
    entry = _read_json(_registry_path(session_id))
    if not entry or not isinstance(entry.get("output_dir"), str):
        return None
    root = Path(entry["output_dir"])
    return {"root": root, "state": root / "state.json", "stop": root / "stop.request.json", "result": root / "result.json"}


def _find_browser(explicit: Optional[str] = None) -> Optional[str]:
    """Locate an installed Chromium-family browser without downloading one."""
    if explicit:
        return explicit if Path(explicit).exists() else None
    env = os.getenv("DSH_WEB_RECORDER_BROWSER") or os.getenv("CHROME_PATH")
    if env and Path(env).exists():
        return env
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    if sys.platform == "darwin":
        mac = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif os.name == "nt":
        mac = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
    else:
        mac = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/opt/google/chrome/chrome"]
    return next((p for p in mac if Path(p).exists()), None)


class RecordingSession:
    """Owns a CDP connection, the captured events and (optionally) a launched browser."""

    def __init__(self, session_id: str, output_dir: Path) -> None:
        self.id = session_id
        self.output_dir = output_dir
        self.events: List[Dict[str, Any]] = []
        self.started_ms = _now_ms()
        self.stopped_ms: Optional[int] = None
        self.endpoint = ""
        self._seq = 0
        self._proc: Optional[subprocess.Popen] = None
        self._user_data_dir: Optional[str] = None
        self._http: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._reader: Optional[asyncio.Task] = None
        self._cmd_id = 0
        self._pending: "dict[int, asyncio.Future]" = {}
        self._page_sessions: set[str] = set()
        self._page_session_order: List[str] = []
        self._first_page = asyncio.Event()
        self._state_path: Optional[Path] = None

    # -- event recording ----------------------------------------------------
    def record(self, event: Dict[str, Any]) -> None:
        self._seq += 1
        self.events.append({"seq": self._seq, "ts": _now_ms(), "rel_ms": _now_ms() - self.started_ms, **event})
        self.write_state(active=True)

    def write_state(self, active: bool, **extra: Any) -> None:
        if self._state_path:
            _write_json(self._state_path, {
                "ok": True, "session_id": self.id, "active": active,
                "total_events": len(self.events), "counts": self.counts(),
                "output_dir": str(self.output_dir), "endpoint": self.endpoint,
                "pid": os.getpid(), **extra,
            })

    # -- CDP transport ------------------------------------------------------
    async def send(self, method: str, params: Optional[dict] = None, session_id: Optional[str] = None, timeout: float = 10.0) -> dict:
        assert self._ws is not None
        self._cmd_id += 1
        cid = self._cmd_id
        payload: Dict[str, Any] = {"id": cid, "method": method, "params": params or {}}
        if session_id:
            payload["sessionId"] = session_id
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[cid] = fut
        await self._ws.send_str(json.dumps(payload))
        try:
            return await asyncio.wait_for(fut, timeout)
        finally:
            self._pending.pop(cid, None)

    async def _reader_loop(self) -> None:
        assert self._ws is not None
        try:
            async for msg in self._ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue
                data = json.loads(msg.data)
                if "id" in data and data["id"] in self._pending:
                    fut = self._pending.get(data["id"])
                    if fut and not fut.done():
                        fut.set_result(data.get("result", {}))
                    continue
                method = data.get("method")
                if method:
                    await self._on_event(method, data.get("params", {}), data.get("sessionId"))
        except (aiohttp.ClientError, asyncio.CancelledError):
            pass
        except Exception:  # noqa: BLE001 - never let the reader kill the plugin process
            pass

    async def _on_event(self, method: str, params: dict, session_id: Optional[str]) -> None:
        if method == "Target.attachedToTarget":
            info = params.get("targetInfo", {})
            sid = params.get("sessionId")
            if sid and info.get("type") == "page":
                asyncio.ensure_future(self._init_page(sid))
            elif sid:
                # Non-page sub-targets attach paused too; resume them so they
                # never block the page we are instrumenting.
                asyncio.ensure_future(self._resume(sid))
            return
        if method == "Runtime.bindingCalled" and params.get("name") == "__dshRecord":
            try:
                payload = json.loads(params.get("payload", "{}"))
            except json.JSONDecodeError:
                return
            if isinstance(payload, dict) and payload.get("kind"):
                self.record(payload)
            return
        if method == "Network.requestWillBeSent":
            req = params.get("request", {})
            self.record({"kind": "network", "phase": "request", "method": req.get("method"),
                         "url": req.get("url"), "resource_type": params.get("type"),
                         "request_id": params.get("requestId")})
            return
        if method == "Network.responseReceived":
            resp = params.get("response", {})
            self.record({"kind": "network", "phase": "response", "status": resp.get("status"),
                         "mime_type": resp.get("mimeType"), "url": resp.get("url"),
                         "request_id": params.get("requestId")})
            return
        if method == "Page.frameNavigated":
            frame = params.get("frame", {})
            if not frame.get("parentId"):
                self.record({"kind": "navigation", "via": "load", "url": frame.get("url")})
            return

    async def _resume(self, session_id: str) -> None:
        try:
            await self.send("Runtime.runIfWaitingForDebugger", session_id=session_id)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            pass

    async def _init_page(self, session_id: str) -> None:
        if session_id in self._page_sessions:
            return
        self._page_sessions.add(session_id)
        self._page_session_order.append(session_id)
        try:
            await self.send("Page.enable", session_id=session_id)
            await self.send("Runtime.enable", session_id=session_id)
            await self.send("Network.enable", session_id=session_id)
            await self.send("Runtime.addBinding", {"name": "__dshRecord"}, session_id=session_id)
            await self.send("Page.addScriptToEvaluateOnNewDocument", {"source": _INJECT_JS}, session_id=session_id)
            # Attach to an already-loaded document too (e.g. attach_url to a
            # running browser, where the target is not paused on start).
            await self.send("Runtime.evaluate", {"expression": _INJECT_JS}, session_id=session_id)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            pass
        finally:
            # Resume the paused target now that instrumentation is installed.
            await self._resume(session_id)
            self._first_page.set()

    # -- lifecycle ----------------------------------------------------------
    async def connect(self, ws_url: str) -> None:
        self.endpoint = ws_url
        self._http = aiohttp.ClientSession()
        self._ws = await self._http.ws_connect(ws_url, max_msg_size=0, heartbeat=None)
        self._reader = asyncio.ensure_future(self._reader_loop())
        await self.send("Target.setDiscoverTargets", {"discover": True})
        # waitForDebuggerOnStart pauses each new target until we have installed
        # Network/Runtime/binding/init-script, so the first document request and
        # early interactions on a freshly opened page are not missed.
        await self.send("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": True, "flatten": True})

    async def wait_first_page(self, timeout: float = 8.0) -> bool:
        try:
            await asyncio.wait_for(self._first_page.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def open_url(self, url: str) -> None:
        # Navigate the already-instrumented initial page so Network/Page are
        # active before the document request. Target.createTarget with a URL is
        # not reliably paused by waitForDebuggerOnStart, which loses the first
        # request; a blank page we already hooked avoids that race.
        target_sid = self._page_session_order[0] if self._page_session_order else None
        if target_sid:
            await self.send("Page.navigate", {"url": url}, session_id=target_sid)
        else:
            await self.send("Target.createTarget", {"url": url})

    async def close(self, kill_browser: bool) -> None:
        if self._reader:
            self._reader.cancel()
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._http and not self._http.closed:
            await self._http.close()
        if kill_browser and self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        # A retained browser still needs its profile directory.  Only remove
        # the temporary profile when this recorder also stops the process.
        if kill_browser and self._user_data_dir:
            shutil.rmtree(self._user_data_dir, ignore_errors=True)

    # -- counts / rendering -------------------------------------------------
    def counts(self) -> Dict[str, int]:
        c = {"click": 0, "input": 0, "change": 0, "submit": 0, "navigation": 0, "network": 0}
        for e in self.events:
            k = e.get("kind")
            if k in c:
                c[k] += 1
        return c

    def render_report(self) -> str:
        counts = self.counts()
        started = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.started_ms / 1000))
        stopped = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime((self.stopped_ms or _now_ms()) / 1000))
        lines = [
            f"# Web Session Recording — {self.id}",
            "",
            f"- Started: {started}",
            f"- Stopped: {stopped}",
            f"- Endpoint: {self.endpoint}",
            f"- Total events: {len(self.events)}",
            "- Breakdown: " + ", ".join(f"{k}={v}" for k, v in counts.items()),
            "",
            "## Timeline",
            "",
            "| # | +ms | kind | detail |",
            "| --- | --- | --- | --- |",
        ]
        for e in self.events:
            kind = e.get("kind", "")
            if kind == "navigation":
                detail = f"{e.get('via', '')} → {e.get('url', '')}"
            elif kind == "network":
                if e.get("phase") == "request":
                    detail = f"{e.get('method', '')} {e.get('url', '')} [{e.get('resource_type', '')}]"
                else:
                    detail = f"← {e.get('status', '')} {e.get('mime_type', '')} {e.get('url', '')}"
            elif kind in ("click", "change", "submit"):
                detail = e.get("target", "")
            elif kind == "input":
                detail = f"{e.get('target', '')} (len={e.get('value_len', 0)})"
            else:
                detail = ""
            detail = str(detail).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {e.get('seq')} | {e.get('rel_ms')} | {kind} | {detail} |")
        lines.append("")
        return "\n".join(lines)

    def write_outputs(self) -> Dict[str, str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        jsonl = self.output_dir / "events.jsonl"
        with jsonl.open("w", encoding="utf-8") as fh:
            for e in self.events:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        report = self.output_dir / "report.md"
        report.write_text(self.render_report(), encoding="utf-8")
        return {"report_md": str(report), "events_jsonl": str(jsonl)}


async def _discover_ws(http: aiohttp.ClientSession, base: str) -> Optional[str]:
    try:
        async with http.get(base.rstrip("/") + "/json/version", timeout=aiohttp.ClientTimeout(total=3)) as r:
            if r.status == 200:
                data = await r.json()
                return data.get("webSocketDebuggerUrl")
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
    return None


async def _launch_browser(session: RecordingSession, browser_path: str, port: int, headless: bool) -> str:
    user_data_dir = tempfile.mkdtemp(prefix="dsh-web-recorder-")
    session._user_data_dir = user_data_dir
    args = [
        browser_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        "about:blank",
    ]
    if headless:
        args.insert(1, "--headless=new")
        args.insert(2, "--disable-gpu")
    session._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    active_port_file = Path(user_data_dir) / "DevToolsActivePort"
    discover = aiohttp.ClientSession()
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            if session._proc.poll() is not None:
                raise RuntimeError("browser process exited before the debug endpoint was ready")
            # Chrome writes the actual port to DevToolsActivePort (required when port=0).
            real_port = port
            if active_port_file.exists():
                try:
                    real_port = int(active_port_file.read_text().splitlines()[0].strip())
                except (ValueError, IndexError):
                    real_port = port
            if real_port:
                ws = await _discover_ws(discover, f"http://127.0.0.1:{real_port}")
                if ws:
                    return ws
            await asyncio.sleep(0.25)
        raise RuntimeError("timed out waiting for the browser remote-debugging endpoint")
    finally:
        await discover.close()


async def _connect_session(session: RecordingSession, config: Dict[str, Any]) -> None:
    attach_url = config.get("attach_url")
    if attach_url:
        http = aiohttp.ClientSession()
        try:
            ws_url = await _discover_ws(http, str(attach_url))
        finally:
            await http.close()
        if not ws_url:
            raise RuntimeError(f"no DevTools endpoint at {attach_url}; launch Chrome with --remote-debugging-port")
    else:
        browser = _find_browser(config.get("browser_path"))
        if not browser:
            raise RuntimeError("no Chrome/Edge/Chromium found; install one or pass browser_path/DSH_WEB_RECORDER_BROWSER")
        ws_url = await _launch_browser(session, browser, int(config.get("port", 9222)), bool(config.get("headless", False)))
    await session.connect(ws_url)
    await session.wait_first_page(timeout=8.0)
    if config.get("url"):
        # open_url navigates the already-instrumented initial page, so there is
        # no new target to wait for; just let the navigation begin.
        await session.open_url(str(config["url"]))
        await asyncio.sleep(0.8)


async def _daemon_run(config_path: Path) -> int:
    config = _read_json(config_path)
    if not config:
        return 2
    session_id = str(config["session_id"])
    output_dir = Path(str(config["output_dir"]))
    session = RecordingSession(session_id, output_dir)
    session._state_path = output_dir / "state.json"
    stop_path = output_dir / "stop.request.json"
    result_path = output_dir / "result.json"
    try:
        session.write_state(active=False, phase="starting")
        await _connect_session(session, config)
        session.write_state(active=True, phase="recording")
        while not stop_path.exists():
            if session._ws is None or session._ws.closed:
                raise RuntimeError("browser debugging connection closed before stop")
            await asyncio.sleep(0.2)
        stop_request = _read_json(stop_path) or {}
        session.stopped_ms = _now_ms()
        paths = session.write_outputs()
        await session.close(kill_browser=not bool(stop_request.get("keep_browser_open", False)))
        result = {"ok": True, "session_id": session_id, "active": False,
                  "total_events": len(session.events), "counts": session.counts(),
                  "output_dir": str(output_dir), **paths}
        _write_json(result_path, result)
        session.write_state(active=False, phase="completed", result=result)
        return 0
    except Exception as exc:  # noqa: BLE001 - persist worker failures for later calls
        try:
            await session.close(kill_browser=True)
        except Exception:
            pass
        result = _error("RECORDER_FAILED", str(exc))
        result.update({"session_id": session_id, "active": False, "output_dir": str(output_dir)})
        _write_json(result_path, result)
        session.write_state(active=False, phase="failed", error=result["error"])
        return 1


async def _start_in_process(session_id: str, output_dir: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
    session = RecordingSession(session_id, output_dir)
    try:
        await _connect_session(session, inputs)
    except (RuntimeError, aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
        await session.close(kill_browser=True)
        return _error("START_FAILED", str(exc))
    _SESSIONS[session_id] = session
    return {"ok": True, "session_id": session_id, "endpoint": session.endpoint,
            "attached": bool(inputs.get("attach_url")), "headless": bool(inputs.get("headless", False)),
            "output_dir": str(output_dir),
            "note": "Interact with the browser now, then call web_record_stop with this session_id."}


class WebRecordStartTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="web_record_start",
            name="web_record_start",
            description="Start recording a user-guided browser session (clicks, inputs, navigation and network).",
            input_params={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Optional page to open when recording starts."},
                    "attach_url": {"type": "string", "description": "Attach to an already-running browser DevTools endpoint, e.g. http://127.0.0.1:9222, instead of launching one."},
                    "headless": {"type": "boolean", "default": False, "description": "Launch the browser headless (used for automated tests)."},
                    "port": {"type": "integer", "default": 9222, "description": "Remote debugging port used when launching a browser."},
                    "browser_path": {"type": "string", "description": "Explicit browser executable path; otherwise an installed Chrome/Edge/Chromium is auto-detected."},
                    "output_dir": {"type": "string", "description": "Directory for report.md and events.jsonl; defaults to ./dsh-web-recorder-sessions/<id>."},
                },
            },
            parallel_safe=False,
        ))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        session_id = uuid.uuid4().hex[:12]
        output_dir = Path(inputs.get("output_dir") or (Path.cwd() / "dsh-web-recorder-sessions" / session_id)).expanduser().resolve()
        if os.getenv("DSH_WEB_RECORDER_IN_PROCESS") == "1":
            return await _start_in_process(session_id, output_dir, inputs)

        output_dir.mkdir(parents=True, exist_ok=True)
        config = {"session_id": session_id, "output_dir": str(output_dir),
                  "url": inputs.get("url"), "attach_url": inputs.get("attach_url"),
                  "headless": bool(inputs.get("headless", False)),
                  "port": int(inputs.get("port", 9222)), "browser_path": inputs.get("browser_path")}
        config_path = output_dir / "worker-config.json"
        _write_json(config_path, config)
        _write_json(_registry_path(session_id), {"session_id": session_id, "output_dir": str(output_dir)})
        try:
            subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--daemon", str(config_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True, close_fds=True,
            )
        except OSError as exc:
            _registry_path(session_id).unlink(missing_ok=True)
            return _error("START_FAILED", f"could not start recorder worker: {exc}")

        deadline = time.time() + 30
        state_path = output_dir / "state.json"
        result_path = output_dir / "result.json"
        while time.time() < deadline:
            result = _read_json(result_path)
            if result and not result.get("ok"):
                _registry_path(session_id).unlink(missing_ok=True)
                return result
            state = _read_json(state_path)
            if state and state.get("active"):
                return {"ok": True, "session_id": session_id, "endpoint": state.get("endpoint"),
                        "attached": bool(inputs.get("attach_url")), "headless": bool(inputs.get("headless", False)),
                        "output_dir": str(output_dir), "worker_pid": state.get("pid"),
                        "note": "Recording runs in a persistent worker. Interact with the browser, then call web_record_stop with this session_id."}
            await asyncio.sleep(0.1)
        return _error("START_FAILED", "recorder worker did not become ready within 30 seconds")

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class WebRecordStopTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="web_record_stop",
            name="web_record_stop",
            description="Stop a recording session and write report.md plus events.jsonl.",
            input_params={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "keep_browser_open": {"type": "boolean", "default": False, "description": "Leave an attached/launched browser running after stopping."},
                },
                "required": ["session_id"],
            },
            parallel_safe=False,
        ))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        session_id = inputs.get("session_id")
        if not session_id:
            return _error("INVALID_INPUT", "session_id is required")
        session = _SESSIONS.get(str(session_id))
        if session:
            session.stopped_ms = _now_ms()
            paths = session.write_outputs()
            await session.close(kill_browser=not bool(inputs.get("keep_browser_open", False)))
            _SESSIONS.pop(str(session_id), None)
            return {"ok": True, "session_id": session_id, "total_events": len(session.events),
                    "counts": session.counts(), "output_dir": str(session.output_dir), **paths}

        paths = _session_paths(str(session_id))
        if not paths:
            return _error("NOT_FOUND", f"no active session {session_id}")
        existing = _read_json(paths["result"])
        if existing:
            return existing
        state = _read_json(paths["state"])
        if not state or not state.get("active"):
            return _error("NOT_FOUND", f"no active session {session_id}")
        _write_json(paths["stop"], {"keep_browser_open": bool(inputs.get("keep_browser_open", False)), "requested_ms": _now_ms()})
        deadline = time.time() + 30
        while time.time() < deadline:
            result = _read_json(paths["result"])
            if result:
                _registry_path(str(session_id)).unlink(missing_ok=True)
                return result
            await asyncio.sleep(0.1)
        return _error("STOP_TIMEOUT", f"recorder worker did not stop session {session_id} within 30 seconds")

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class WebRecordStatusTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="web_record_status",
            name="web_record_status",
            description="List active recording sessions and their current event counts.",
            input_params={"type": "object", "properties": {"session_id": {"type": "string"}}},
            idempotent=True,
        ))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        sid = inputs.get("session_id")
        if sid:
            session = _SESSIONS.get(str(sid))
            if session:
                return {"ok": True, "session_id": sid, "active": True, "total_events": len(session.events),
                        "counts": session.counts(), "output_dir": str(session.output_dir)}
            paths = _session_paths(str(sid))
            if not paths:
                return _error("NOT_FOUND", f"no active session {sid}")
            result = _read_json(paths["result"])
            if result:
                return result
            state = _read_json(paths["state"])
            return state or _error("NOT_FOUND", f"no active session {sid}")
        active = [{"session_id": s.id, "total_events": len(s.events), "counts": s.counts()}
                  for s in _SESSIONS.values()]
        if _REGISTRY.exists():
            for entry_path in _REGISTRY.glob("*.json"):
                entry = _read_json(entry_path)
                if not entry or not isinstance(entry.get("session_id"), str):
                    continue
                paths = _session_paths(entry["session_id"])
                state = _read_json(paths["state"]) if paths else None
                if state and state.get("active"):
                    active.append(state)
        return {"ok": True, "active_sessions": active}

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--daemon":
    raise SystemExit(asyncio.run(_daemon_run(Path(sys.argv[2]))))
