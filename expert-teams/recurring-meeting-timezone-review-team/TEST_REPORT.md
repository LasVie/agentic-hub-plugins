# Recurring Meeting Time-Zone Review Team 1.0.0 test report

Executed 2026-11-19 for Cai Zhenze. Task `AH-20261119-recurring-meeting-timezone-review-team`. Display name 跨时区例会时间核验专家团. Manual package testing passed on 2026-11-20.

| Package | SHA-256 |
| --- | --- |
| Native ZIP | `7fd40e9c9121331ddb268c77434fc522f59074b3fe1ac9ec9cced78bc4a951d9` |
| Wrapped agent-group ZIP | `b3439f95f0d6c6f19cb36015968ce737b70d624fe06b82bac1f4ef7701ee055a` |

## Package and deterministic checks

The pinned official agentichub CLI 0.0.1 ran `init`, `validate` and `pack` with exit code zero. The repository wrapper and dynamic signature preflights passed. Both archive layouts, the source, the native extraction and both actual host installations were compared by path and SHA-256. All 23 payload files match. See [final verification](tests/records/final-verification.json) and [CLI source checks](tests/records/official-cli-sources.json).

All 16 functional tests passed on Python 3.10.11 from the [source](tests/records/source-tests.txt) and the [exact extracted native ZIP](tests/records/extracted-tests.txt). The cases exercise the Chinese command-line workflow and outputs, staggered clock changes, a nonexistent time, a repeated time, local-date rollover, meetings ending at or after closing, actual elapsed duration across an offset change, fractional offsets, explicit closures, invalid and missing data, stale or tampered handoffs, unchanged existing outputs, spreadsheet-safe CSV and the supported size limit.

The actual WorkSwarm group creator accepted the exact native extraction. SDK 0.1.20 loaded the Leader entry and all four agents with each agent’s private skill and the shared skill. It rejected a wrong member package type, a missing Leader entry and a missing verifier. See [loader record](tests/records/host-loader.json).

## Actual WorkSwarm execution

On a loopback WorkSwarm instance with its own data directory, task registry, artifacts and ports, real task, messaging, skill and shell tools ran with a deterministic local model fixture. Both runs verified all four role sessions and commands, including the verifier's independent original-input baseline before planning. Each captured 258 host events and 28 fixture model requests. The March run correctly gave 09:00 2/4 and 08:00 4/4 available weeks. The gap run classified the nonexistent New York start without moving it to another time. In both runs the Leader produced Chinese `review.md`, `meetings.csv` and `audit.json` after checking the real input, TZif and handoff hashes. See the [March run](tests/records/host-clock-change.json) and [gap run](tests/records/host-gap.json).

The planner and verifier use different algorithms over the same system time-zone data. Agreement confirms the results for that input and time-zone data. The fixture tests host integration and deterministic outputs. The separate user run is recorded below.

## Manual instance

An isolated WorkSwarm instance at http://127.0.0.1:6675/ serves the team. The browser reached **专家 → 我的专家 → 专家团 → 创建 → 上传文件创建**, where the host's file selector returned no file. The exact native ZIP was installed through the host's local Expert Team import entry point, which is also used by the upload dialog. The UI displayed 1.0.0 and the four members. The [manual host record](tests/records/manual-host-import.json) confirms the installed payload. Desktop file-picker import remains a manual check. The isolated instance's scripted provider requires the tester to select their own authorized model, or to use a compatible instance with an authorized model already configured. See the [manual instructions](MANUAL_TESTING.md).

## Manual package confirmation

On 2026-11-20 Cai Zhenze explicitly confirmed in the Main 4.0 Codex conversation that manual testing of the exact 1.0.0 native ZIP was complete and passed. Four original PNGs show the Chinese report, native Expert Team participation, independent review and task handoffs, and the per-participant CSV. The [evidence index](evidence/1.0.0/index.json) records their full-resolution dimensions and hashes and links the result to confirmation report `RPT-20261120-recurring-meeting-timezone-review-team-confirmed`.

Manual execution used the bundled scripts from the source directory, whose bytes match the tested ZIP. The verifier ran the original-input baseline before planning and compared all eight scheduled occurrences. The analyst ran the packaged delivery script under a Leader-assigned handoff. All four handoff hashes matched the audited output, and the 24 participant rows agreed with the Chinese report. New York 09:00 fit two weeks, and 08:00 fit all four. The sample exceeded Singapore's window by 30 minutes in week one and Berlin's by 10 minutes in week three. WorkSwarm's local Expert Team import had already passed. The screenshot run used an installed team and adds no desktop-picker evidence.

Before submission, all 16 source and 16 exact-native functional tests and all three dynamic JavaScript preflights passed again. The 23-file payload, two ZIP hashes, and official wrapper identity were rechecked without repackaging.
