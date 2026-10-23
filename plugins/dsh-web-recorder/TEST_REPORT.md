# Functional Test — dsh-web-recorder 1.0.2

Test date: 2026-10-23 (Asia/Singapore). Task AH-20261023-dsh-web-recorder; candidate CAND-DSH-172.
Passing here means development functionality plus repository packaging checks only. It is **not** Hub submission/publication, host-install approval, or Project Lead acceptance.

## Environment & repeatable commands
macOS Darwin arm64; Python 3.11.15 (OpenJiuwen `~/agent-core/.venv`); aiohttp 3.13.3; Google Chrome 155.0.8059.86.
No API keys, business data, cloud deployment, or paid calls. The test serves a local `http.server` page on 127.0.0.1 and launches headless Chrome in a throwaway `--user-data-dir`.

```bash
# functional test (drives a real headless Chromium over CDP)
~/agent-core/.venv/bin/python plugins/dsh-web-recorder/tests/test_web_recorder.py

# repository format / packaging checks
python tools/asset_release.py check plugins/dsh-web-recorder
python tools/asset_release.py pack plugins/dsh-web-recorder
python tools/asset_release.py check-repo
```

Raw output of the functional test is saved to `FUNCTIONAL_TEST.log` (host connector-pool INFO lines stripped; it does not replace real user screenshots).
The previous 1.0.1 automated screenshot is retained as historical development evidence only. Version 1.0.2 changes session persistence and requires fresh WorkSwarm confirmation.

## What the test exercises
A local page with an input, a button (whose click issues `fetch('/api/data')`), and a link. Over CDP the test performs a genuine `input` event, a genuine `click` (triggering the network request), and a history `pushState` + `popstate` navigation, then stops the session.

## Actual results — PASS
All assertions passed (process exit 0):

| Check | Result |
| --- | --- |
| click captured (>=1) | PASS |
| input captured (>=1) | PASS |
| navigation captured (>=1) | PASS |
| network captured (>=2) | PASS |
| events.jsonl non-empty (>=4) | PASS |
| report.md contains timeline | PASS |
| network event includes `/api/data` | PASS |

In-process run counts: `click=1, input=1, navigation=2, network=8` (12 events total).

Representative captured timeline (from a run):

```
| 1 | network    | GET http://127.0.0.1:.../ [Document] |
| 2 | network    | ← 200 text/html http://127.0.0.1:.../ |
| 3 | navigation | load → http://127.0.0.1:.../ |
| 4 | input      | input#field[name=field] (len=5) |
| 5 | click      | button#go "Go" |
| 6 | network    | GET http://127.0.0.1:.../api/data [Fetch] |
| 7 | network    | ← 200 application/json http://127.0.0.1:.../api/data |
| 8 | navigation | popstate → http://127.0.0.1:.../next |
```

`web_record_start` → `web_record_status` → `web_record_stop` all returned `ok: true`; outputs `report.md` and `events.jsonl` were written to the session output directory.

The rerun also verified the test targets the page whose `location.href` matches the fixture URL instead of relying on unordered CDP target enumeration. A lifecycle defect was fixed so `keep_browser_open=true` no longer deletes the retained browser's temporary profile directory.

The initial-document-request race noted in 1.0.1 is resolved in 1.0.2: new targets auto-attach paused (`waitForDebuggerOnStart`) until Network/Runtime/binding/init-script are installed and then resume, and a page opened via the `url` parameter is reached by navigating the already-instrumented initial page rather than `Target.createTarget`. The first document GET/response is now captured (timeline rows 1–2 above).

Version 1.0.2 adds a detached recorder worker and file-backed registry/state/result protocol. `tests/test_cross_process_session.py` invokes start, status, and stop in three separate Python processes and verifies the active session survives, navigation/network events remain visible, and both output files are produced.

## Known issues / limitations
- The first document request of a page opened via the `url` parameter may precede per-page network instrumentation; the recommended flow (start, then browse, or `attach_url`) captures everything. Documented in README.
- Chromium-family browsers only (CDP). Firefox/WebKit unsupported.
- A browser must already be installed on the host; none is downloaded.

## Scope statement
This report covers functional behavior and repository packaging only. It is not a legal license conclusion, not Hub acceptance, and not Project Lead acceptance.
