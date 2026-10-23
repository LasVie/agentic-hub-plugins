# Web Session Recorder

Recording runs in a detached local worker with file-backed session state, so `web_record_status` and `web_record_stop` continue to work when the host executes tool calls in separate plugin processes.

Record a **user-guided** browser session and export a Markdown timeline (`report.md`) plus a structured event log (`events.jsonl`). The intended use is reverse-engineering a web flow — including the network/API calls behind it — so you can build an API-level skill from a real session.

This is an independent OpenJiuwen/Agentic Hub implementation inspired by the public functional description of the DSH `dsh-web-recorder` plugin. It does **not** reuse the upstream DSH/Cordis code (that runtime is not portable to this host). Capture is implemented directly over the Chrome DevTools Protocol.

## Tools

| Tool | Purpose |
| --- | --- |
| `web_record_start` | Launch (or `attach_url` to) a browser and begin capturing. Returns a `session_id`. |
| `web_record_stop` | Stop a session and write `report.md` + `events.jsonl`. |
| `web_record_status` | List active sessions and live event counts. |

### `web_record_start` inputs
- `url` (string, optional) — page to open when recording starts.
- `attach_url` (string, optional) — attach to a browser already started with `--remote-debugging-port`, e.g. `http://127.0.0.1:9222`.
- `headless` (bool, default `false`) — headless launch, mainly for automated tests.
- `port` (int, default `9222`) — remote-debugging port when launching.
- `browser_path` (string, optional) — explicit browser executable.
- `output_dir` (string, optional) — where `report.md`/`events.jsonl` are written. Defaults to `./dsh-web-recorder-sessions/<session_id>`.

## What is captured
Clicks, `input`/`change`/`submit`, same-document navigation (popstate/hashchange) and full navigations, and network requests/responses (method, URL, resource type, status, MIME type).

## Requirements
- An installed **Chrome / Edge / Chromium** (none is downloaded; auto-detected, or set `browser_path` / `DSH_WEB_RECORDER_BROWSER`).
- The host's `aiohttp` (a declared dependency). No Node, no Playwright install, no MCP.

## Privacy
Only the **length** of input values is recorded, never their content; network bodies are not captured. Recordings can still include sensitive URLs or query strings — review the outputs before sharing.

## Known limitations
- Chromium-family browsers only (CDP). Firefox/WebKit are not supported.
- When using `attach_url` to a browser you control, pages already loaded before you attach are instrumented in place, but requests that completed before attaching cannot be recovered. A page opened via the `url` parameter, or any navigation after start, is captured in full (including its first document request).
