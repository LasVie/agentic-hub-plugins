# Functional test report — F1 赛事数据助手 1.0.0

Owner Nguyen Trung Dung; Task AH-20261106-pitwall-f1; Candidate CAND-CLD-299.
Test date 2026-11-06 Asia/Singapore. Local branch feat/pitwall-f1 from main 4776f2a.

## Exact package identity

- Stable ID repo:agent-plugin:pitwall-f1; upstream Pitwall F1 -> F1 赛事数据助手 -> pitwall-f1.
- Native import: test-packages/pitwall-f1-1.0.0-native.zip; 63131 bytes; SHA-256 8d5c293156423fba68f1ae5e2c7bf554fe33d3d62e65f39f188a6f2b06cb1178.
- Canonical marketplace archive: releases/agent-plugin/pitwall-f1/1.0.0/pitwall-f1-1.0.0.zip; SHA-256 f3567f21daf21b317f4059457a804a874ef6ffd9b718f80d080a587f29e5225a; 63948 bytes.
- Six runtime files (README.md, THIRD_PARTY_NOTICES.md, licenses/pitwall-f1/LICENSE, manifest.json, skills/pitwall-f1/SKILL.md, tools/pitwall_tools.py) are shared unchanged by source, native and canonical formats. Bundled MIT license SHA-256 44a481b6b6a342037e8f4071f32df9515db040afbc987d1c17436f8a9bf82b7c equals the pinned upstream LICENSE. No data, image, icon, binary, dependency package, credential or cache is included.

## Scope actually delivered

Twelve native read-only tools. Four port the Jolpica-F1 behaviour of upstream Pitwall F1 1.0.0 @04d65d386d96b85362e2eec37f39ca9018b13ee3; eight OpenF1 tools are original. The other 71 upstream tools need the F1 official timing feed, which returned HTTP 403/401 from two networks on 2026-11-06 and now requires an F1 TV account; they are deliberately absent. No telemetry, live timing or plots. See SOURCE_REVIEW.md.

## Environment and executed checks

Windows 11, CPython 3.11.9, openjiuwen 0.1.20.post1 from PyPI in an isolated venv outside the repository; the plugin itself uses only the Python standard library. PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1, -B. Logs, venv, extracted payload and raw evidence live under D:/jiuwen_repos/outputs/pitwall-build, outside the payload. Zero model calls.

1. `python tools/asset_release.py check plugins/pitwall-f1`: format_ok true.
2. `python -B plugins/pitwall-f1/tests/test_adapter.py`: 33/33 offline checks pass against source and, separately, the exact extracted native payload. Covers: twelve real ToolCards with closed schemas and Chinese descriptions; stream equals invoke; argument rejection (non-object, unknown field, string/bool/out-of-range numbers, bad driver id, missing required, null values) before any network request; Ergast path order and the four historical-result modes; empty/truncated results; circuit alias, fallback, ambiguity and not-found; standings aliases/round/empty; winners history using one request and the latest seasons; fastest-lap default year and the not-a-record warning; malformed Jolpica shape; OpenF1 selector conflicts, pre-2023 rejection, Chinese session types, ambiguous country (意大利, usa), unknown session key; driver resolution; result status/order/empty; lap range, fastest, pit-out-lap average and 120-lap truncation; missing pit durations kept null; weather statistics and absent rainfall; race-control category/limit and the data-not-instruction note; HTTP 401/403/429/500 mapping with Retry-After and exactly one attempt; OpenF1 404 "No results found." as empty versus other 404s as errors; timeout/connection/bad-JSON/oversized body; cache and copies; per-minute limiter without waiting or retrying; request spacing; real limiter settings below the documented OpenF1 free tier; internal errors without leaking details; no credential, environment, subprocess, eval or local-file access in the code.
3. `tests/live_checks.py` against the real services through each tool's real `invoke`: 16/16 recorded checks pass from source and from the extracted native ZIP, covering all twelve tools. Observations: 2024 Monaco winner Charles Leclerc; 2024 driver champion Max Verstappen 437 points; 2024 constructor champion McLaren 666 points; Monaco history includes 2024 Leclerc; Italy has Imola and Monza 2024 races; Monza 2024 winner LEC; VER and LEC on the grid; five timed VER laps; Leclerc has a stop and contiguous MEDIUM/HARD stints; weather statistics ordered; flag messages only; ambiguous country and pre-2023 year rejected with distinct codes. These are dated observations of public services, not promises about future data. Chinese inputs exercised: 摩纳哥, 蒙扎, 车队, 意大利, 正赛, 旗语.
4. `tests/host_checks.py --live` loads the extracted native payload in a real DeepAgent with SkillUseRail, ability manager and Runner: all twelve names are visible with DIRECT exposure and Chinese descriptions; registered invalid input and an unknown field are rejected; standings, session results and tyre stints return real data through the Runner; all tools and the Skill unload; payload hashes are unchanged. This is real SDK execution, not a stub agent, a frontend conversation or a model-planned tool-choice test.
5. Chinese check of the extracted payload: every file decodes as UTF-8 with no BOM or replacement character; manifest display name/description/tags/quick inputs are Chinese; SKILL.md, README and notices are Chinese; tool descriptions, parameter descriptions, errors, warnings and summaries are Chinese. Data keys and upstream field values (driver names, team names, race-control message text) keep their source form by design.
6. `tools/asset_release.py preflight` on the payload and the native ZIP: 0 JavaScript files, 0 dynamic-execution signatures.
7. `tests/test_pitwall_f1.py` is the repository discovery entrypoint: native/canonical/source byte contract, license evidence, and the 33-test suite in a fresh process when the SDK exists; without the SDK that case explicitly skips and claims no success. Result: 3/3 pass with the SDK; 2 pass and 1 explicit skip with system Python lacking the SDK (the CI-like case).
8. `asset_release.py pack` writes the deterministic canonical ZIP; repacking after this report was finalized reproduces the same ZIP bytes. `asset_release.py check-repo` passes in a clean LF clone of main (core.autocrlf=false) with this asset added: 67 source assets, 80 release ZIPs. In the developer's own working tree `check-repo` fails with "license evidence hash mismatch: LICENSE" for 47 pre-existing assets because `core.autocrlf=true` checks their LICENSE files out with CRLF; this asset's LICENSE is stored with LF and passes. `tests.test_asset_release` has one Windows-only symlink-privilege error (WinError 1314) that also occurs on a pristine clone of main; it is unrelated to this change.

## Real limitations and observed behaviour

- Free OpenF1 data starts in 2023; earlier sessions have only Jolpica results and standings.
- Jolpica may lag the current season by several rounds; the plugin says so rather than inferring absence.
- OpenF1 labels the free tier "personal use". The plugin limits itself to 28 requests/minute with 0.4 s spacing, never retries, and restates this in every OpenF1 result. Whether this affects public distribution is a Project Lead question recorded in SOURCE_REVIEW.md.
- Some OpenF1 sessions have null pit durations; the plugin keeps null and warns. `f1_session_results` returns an empty list with a warning if OpenF1 has no result record.
- `f1_circuit_fastest_lap` is the fastest lap of that year's race, not an all-time record (the upstream tool presented it as one).
- No frontend conversation and no model-planned tool choice were exercised; no GitHub CI run exists before an allowed PR.
