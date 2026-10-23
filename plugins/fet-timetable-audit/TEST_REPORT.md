# 课表校验与导出 1.0.0 test report

Candidate `CAND-CLD-219`; task `AH-20261023-fet-timetable-audit`; owner Cai Zhenze; local branch `feat/fet-timetable-audit`, based on main `49eaab9`. Tested 2026-10-23 on macOS arm64, Python 3.12.14, openJiuwen 0.1.19 and PyYAML 6.0.3. The approved scope is offline inspection, supplied-timetable verification and export, without solving or repair.

## Source functionality and review

- All **43 source functional tests passed with no skips**, in 1.694 seconds, using the real openJiuwen SDK. Format validation passed separately.
- Tests cover Chinese fictional inputs, references/workload, normalized duplicate IDs, student hierarchy and inherited availability, teacher/student overlaps, unplaced and overflowing activities, explicit unsupported constraints, exact filters, CSV formula protection, UTF-8, malformed XML, DTD/entities, symlinks/FIFOs, resource bounds, read-only inputs, exclusive export creation, real SDK invocation/streaming and the model-free CLI.
- An independent read-only review found no blocking issue. It reran the then-existing 41 tests with no skips and additionally checked the pinned upstream sample: supported inspection/verification checks passed and 12 activities exported. Unsupported constraints remained explicitly disclosed. Two CLI tests were subsequently added and are included in the 43-test result above.
- Complete MIT license bytes and all three reused source hashes match pinned upstream. No solver, OR-Tools, third-party data, external service or model call is included.

## Exact package and extracted functionality

- Canonical: `releases/agent-plugin/fet-timetable-audit/1.0.0/fet-timetable-audit-1.0.0.zip`, **52,504 bytes**; SHA-256 `20ce4ca8188428a8d8abd957be6158f83d76337322cf70ba78c9b3ba1b80c911`.
- Native WorkSwarm: `dist/fet-timetable-audit/1.0.0/fet-timetable-audit-1.0.0-workswarm.zip`, **51,390 bytes**; SHA-256 `1340355e0dd10218bf0853b23f2323895661f793f3fc3bf321675e4de455cfbf`.
- `asset_release.py check` and `pack` passed. The canonical ZIP has one marketplace wrapper plus eight regular runtime files. The native ZIP contains the same eight files unchanged. CRC, safe unique paths, UTF-8 decoding, declared files and matching 1.0.0 identity/version passed.
- Full source/canonical/native byte equality and original MIT license equality passed. No tests, fixtures, caches, screenshots or development records are in either runtime package.
- All **43 tests passed against the extracted canonical payload**, no skips, in **1.722 seconds**, including Chinese input/results/errors/help and real SDK invocation/streaming.
- Local evidence: `/private/tmp/fet-package-audit.json`, `/private/tmp/fet-source-tests.log`, `/private/tmp/fet-extracted-tests.log`. The independently authored Chinese fixtures are copied to `dist/fet-timetable-audit/1.0.0/test-inputs/` for manual use.
- Repository structural check passed for **14 source assets and 22 release ZIPs**. Existing assets' unchanged functional evidence was reused; no unrelated test suite or runtime was modified. Report/source-review metadata was refreshed in `artifact.json` without changing either runtime ZIP hash.

## Installed host and interface

The existing isolated WorkSwarm instance at `http://127.0.0.1:6283/` (backend/WebSocket 29110, runtime `/private/tmp/deckaura-workswarm-20261022`) passed frontend HTTP, backend RPC, direct/proxied WebSocket ping/pong, configuration and plugin-catalog checks. No restart or unrelated code change was needed.

The actual backend import/install RPCs installed 1.0.0. All eight installed files match source, canonical and native payloads byte-for-byte. The host loader resolved one Skill and three native Tools using openJiuwen 0.1.19. Direct invocation/streaming passed:

- Chinese input: three activities/four grid slots; teacher workloads 3 and 1.
- Valid schedule: zero findings in supported checks; conflicting schedule: exactly three findings (`teacher_unavailable`, `teacher_overlap`, `students_overlap`).
- Teacher-filtered CSV: two rows; student-filtered JSON: one row; correct UTF-8 files/hashes. Repeated writes return `output_exists` without altering files.
- URL, relative path, missing file and unexpected arguments return Chinese errors. All inputs and all 22 pre-existing Tarot/prosody payload files remained unchanged. Instrumented tool execution recorded zero network attempts; no agent/model was invoked.

Browser inspection verified Extensions → My Extensions → Create → Create from file, the Chinese plugin card/description/tags/three tool labels, and enabled selection in a fresh unsent `/chat/new` session. Native operating-system file-picker completion was not tested; actual installation used the corresponding import/install RPCs. The currently selected model provider is `local-testing-disabled`; no conversational response is claimed. User manual testing can select their own provider, or use the documented model-free CLI for deterministic checks.

Local evidence: `/private/tmp/fet-workswarm-20261023/installed-plugin-test-result.json`, `payload-comparison.json`, `health-result.json`, `extensions-details.png`, `extensions-selected.png` and accompanying scripts/logs. These automated screenshots are separate from the original user screenshot subsequently supplied at test completion. Evidence summaries are maintained here outside the runtime ZIP.

## Reproduce

Use Python 3.11+ with the actual openJiuwen SDK and PyYAML:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B tools/asset_release.py check plugins/fet-timetable-audit
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p test_fet_timetable_audit.py -v
PYTHONDONTWRITEBYTECODE=1 python -B tools/asset_release.py pack plugins/fet-timetable-audit
python plugins/fet-timetable-audit/build_local_test_package.py
python tests/test_fet_timetable_audit.py --write-demo-dir dist/fet-timetable-audit/1.0.0/test-inputs
```

Set `FET_AUDIT_PAYLOAD` to an extracted inner payload directory to exercise release bytes. Missing host SDK causes explicit skips in a generic environment and does not establish the complete evidence above. The CLI `scripts/audit_cli.py inspect/verify` runs with the Python standard library alone.

## Limits and remaining gates

Only supported deterministic checks are performed. Unknown/soft/space constraints are disclosed, not validated; no room-conflict check, solver, optimizer, repair or complete FET feasibility proof. Duration means grid slots. Input limits and export behavior are documented in the Chinese bundled README.

Automated functionality, packaging and host checks do not establish user acceptance. On 2026-10-23 the user explicitly confirmed manual testing of this exact Chinese 1.0.0 package complete/passed and supplied the original 568 × 1596 PNG. `USER_TEST_CONFIRMATION.md` preserves the actual statement, package hashes, screenshot hash and attribution limits. The screenshot shows matching version, workload, valid/conflicting schedule results and two-row CSV/hash. No blocking issue is known.

Submission preflight updated main and this feature branch to `459b25b`; only maintenance rules/tracker mapping changed, with no runtime/checker/test changes. Valid source/extracted/host functional evidence is reused. Repository-only confirmation/report updates refresh artifact metadata without changing the confirmed ZIP or runtime payload. GitHub delivery and final Project Lead acceptance are separate; no Release, Hub operation or additional paid model call is authorized. Song Haoran handles Hub operations.

The first PR CI run (`39893932616`) passed 154 repository tests with 31 documented environment/historical skips, then correctly rejected a Python cache created by the new test loader inside the source payload. The test helper now suppresses bytecode only during its imports and preloads the adapter's lazy core under that same guard; runtime source and both ZIPs are unchanged. All 43 actual-SDK tests then passed in 1.816 seconds **without** `-B` or `PYTHONDONTWRITEBYTECODE`, left no payload cache, and were followed by a successful `check-repo` (14 assets/22 ZIPs). Log: `/private/tmp/fet-phase3-tests-no-bytecode-flag.log`. The follow-up PR CI must still pass before merge; generic CI SDK skips do not replace the complete local SDK evidence.
