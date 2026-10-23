# Independent Implementation Spec — dsh-web-recorder

## Material-exposure record (honesty requirement)
Before writing this plugin I read **only public, non-code material**: the candidate catalog row (CAND-DSH-172), the npm metadata for `dsh-web-recorder@0.6.0` (name, version, declared MIT license, dependency list such as `playwright-core` and `@deepseek-ai/cordis`), and the GitHub repository's rendered README (functional description and the note that it requires a locally installed browser and treats Playwright MCP as optional). I did **not** read, copy, translate, or paraphrase the upstream implementation source, prompts, or assets. The upstream DSH/Cordis runtime (`dsh.bundle.patch` → `cordis.patch.yml`, `@deepseek-ai/cordis`, `@deepseek-ai/dsh-tools`) is not portable to this host, so this is a clean-room functional reimplementation, not a port.

## Public functional requirement
Record a **user-guided** (human-driven) browser session — real clicks, inputs, navigation, and network traffic — and produce a Markdown timeline report (`report.md`) plus a structured event log (`events.jsonl`) that can be used to reverse-engineer a site's flow and build API-level skills. The tool observes; it does not drive the browser for the user.

## Component boundaries
- **Target host:** OpenJiuwen / Agentic Hub `agent-plugin`. Tools are Python `Tool` subclasses declared in `manifest.json`.
- **Engine strategy:** Capture directly over the Chrome DevTools Protocol (CDP). This reuses the host's existing browser-automation substrate assumption (the host's `browser_move` runtime also drives an installed Chrome via CDP and does not bundle a browser). No Playwright, no Node, no MCP server. Transport is the host's declared `aiohttp` dependency (HTTP discovery + WebSocket client).
- **Browser:** An installed Chrome/Edge/Chromium, auto-detected or set via `browser_path` / `DSH_WEB_RECORDER_BROWSER`. Never downloaded — matching both the upstream behaviour and the host's assumption.

## Inputs / outputs
- `web_record_start(url?, attach_url?, headless?, port?, browser_path?, output_dir?) -> {session_id, endpoint, ...}`
- `web_record_stop(session_id, keep_browser_open?) -> {counts, report_md, events_jsonl, ...}`
- `web_record_status(session_id?) -> {active sessions + counts}`
- Outputs: `report.md` (chronological `| # | +ms | kind | detail |` timeline with a breakdown header) and `events.jsonl` (one JSON object per event: `seq`, `ts`, `rel_ms`, `kind`, and kind-specific fields).

## Independent design
1. Launch Chrome with a throwaway `--user-data-dir` and `--remote-debugging-port` (resolving `port=0` via the `DevToolsActivePort` file), or attach to an existing endpoint via `/json/version`.
2. Open the browser-level CDP WebSocket; `Target.setAutoAttach(flatten)` to receive a flat session per page.
3. Per page session: enable `Page`, `Runtime`, `Network`; `Runtime.addBinding("__dshRecord")`; inject a capture script via `Page.addScriptToEvaluateOnNewDocument` (and once into the current document). The injected script adds capturing listeners for click/input/change/submit and popstate/hashchange and forwards them through the binding.
4. A background reader task maps CDP responses to awaited futures and routes events: `Runtime.bindingCalled` → UI events; `Network.requestWillBeSent`/`responseReceived` → network; top-frame `Page.frameNavigated` → navigation.
5. On stop, render `report.md` and write `events.jsonl`, close the socket, and terminate the launched browser (unless `keep_browser_open`).

## Privacy decisions
Input **contents are never recorded** — only value length. Network **bodies are not captured** — only request/response metadata. Documented so users review URLs/query strings before sharing.

## Tests
`tests/test_web_recorder.py` launches a real headless Chromium, serves a local page, drives a genuine click (which triggers a `fetch`), an input event, and a history navigation over CDP, then asserts that click/input/navigation/network were all captured and that `report.md` + `events.jsonl` were produced. See `TEST_REPORT.md` and `FUNCTIONAL_TEST.log`.

## Unresolved / honest notes
- The first-document-request race (1.0.1) is resolved in 1.0.2: new targets auto-attach paused (`waitForDebuggerOnStart`) until instrumentation is installed, then resume; a `url` page is reached by navigating the already-instrumented initial page instead of `Target.createTarget`. Only requests that completed *before* an `attach_url` attach are unrecoverable (documented in README).
- Host lifecycle (1.0.2): WorkSwarm may run each tool call in a fresh plugin process, so sessions cannot live only in memory. Recording runs in a detached worker; `web_record_start/status/stop` coordinate through a file-backed registry (shared tmp dir), per-session `state.json`, `stop.request.json` and `result.json`. The in-memory path is retained only for the in-process test harness (`DSH_WEB_RECORDER_IN_PROCESS=1`).
- Independent implementation addresses copyright of the *code only*; it is not a blanket exemption from any upstream trademark or service-term considerations. No DSH branding or assets are reused.
