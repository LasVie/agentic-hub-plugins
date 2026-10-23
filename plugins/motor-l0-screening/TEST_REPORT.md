# Functional test report

2026-10-23; actual openjiuwen native Tool/ToolCard SDK, Python3.11.17, WorkSwarm bundled Node22.11.0.

11/11 targeted tests passed, no skips. Tests exercise native invoke and bundled source, not mock tool results.

- PASS: matrix and validation produced
- PASS: full matrix saved
- PASS: ranking excludes failed and infeasible
- PASS: finite efficiency sorted descending
- PASS: deterministic matrix
- PASS: power_kw invalid -1 rejected
- PASS: speed_rpm invalid 0 rejected
- PASS: count invalid 121 rejected
- PASS: power_kw invalid True rejected
- PASS: motor_type invalid unsupported rejected
- PASS: explicit PMSM and 60Hz passed through

Reproduce functional tests: `python -B tests/five_ports_functional.py` with the native openjiuwen SDK available. Extracted native payloads also passed the same targeted tests (48/48 total).

Host UI: imported exact native ZIP through desktop WorkSwarm My Extensions; clicked Use and ran a new model-backed session. 2 native tool result events verified in the host session history; installed file hashes match every source/native/Hub payload file. Session web_1a166b6da77_c6eff8b23288. These local tests do not establish user completion or acceptance.

Native ZIP SHA-256: 1194cbe5aee2e5edbccd526a9bdae9b113fa027b9919b05b1513772f08c25604
Hub-wrapper ZIP SHA-256: b53f89b843c3153e16132496e4f1f09533e0dece12b8184e4773894008cbb058

Original full-resolution screenshots and filtered native tool result events are retained in the local migration-five-20261023/evidence handoff. Assistant-operated testing is not a personal-human-test claim or explicit user completion/acceptance. No push/PR/merge/Hub submission performed.

## User completion and delivery authorization

2026-10-23, current Song Haoran conversation: after the exact Chinese1.0.0 functional and follow-up visual results were presented, the user explicitly instructed `pr合入` (submit and merge the PR). This is the current-package completion confirmation and GitHub delivery authorization; tests were assistant-operated at the user's explicit request, not claimed as manual human testing. Original full-resolution images were collected and inspected before the delivery push. Confirmation report: RPT-20261023-motor-l0-screening-confirmed-100. Package hashes above remain unchanged. Lead handoff acceptance and official Hub catalog registration remain separate.

Portable delivery/evidence index: `docs/deliveries/five-chinese-plugins-20261023/README.md`. Earlier no-push/pending statements describe the historical Build stage; this authorization supersedes that boundary.
