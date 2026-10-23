---
name: web-recorder
description: Record a user-guided browser session (clicks, inputs, navigation, network) and export a Markdown timeline and events.jsonl for reverse-engineering web flows and building API-level skills.
---

# Web Session Recorder

Capture what a human actually does in a browser, then turn it into evidence.

## When to use
Use when the user wants to observe a real, human-driven browsing session — not script one — so they can understand a site's flow or the network/API calls behind it, then build a skill from that. This records; it does not drive the browser for the user.

## Tools
- `web_record_start` — launch a fresh Chrome/Edge/Chromium (or `attach_url` to one already started with `--remote-debugging-port`), then begin capturing. Returns a `session_id`. Optional `url` opens a page; `headless: true` is for automated tests; `output_dir` overrides where results go.
- `web_record_stop` — end the session by `session_id`; writes `report.md` (chronological timeline) and `events.jsonl` (one JSON event per line) and returns counts and paths.
- `web_record_status` — list active sessions and live event counts.

## Workflow
1. Call `web_record_start`. For the most complete capture, start first, then let the user browse — instrumentation is installed before they act.
2. Tell the user to perform the actions they want recorded in the opened browser window.
3. When they are done, call `web_record_stop` with the same `session_id` and summarize the timeline and captured network/API calls from `report.md`.

## What is captured
Clicks, `input`/`change`/`submit` events, same-document navigation (popstate/hashchange) and full navigations, and network requests/responses (method, URL, resource type, status, MIME type).

## Privacy and honesty
Only the **length** of input values is recorded, never their contents. Network bodies are not captured — only request/response metadata. Recordings can still contain sensitive URLs or query strings; review `report.md`/`events.jsonl` before sharing. Report only what was actually captured; if an event kind is absent, say so rather than inferring it.

## Requirements
An installed Chrome/Edge/Chromium on the host (none is downloaded). Auto-detected, or set `browser_path` / the `DSH_WEB_RECORDER_BROWSER` env var. Uses the host's `aiohttp`; no extra install, no Node, no MCP required.
