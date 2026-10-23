# Functional test report

2026-10-23; actual openjiuwen native Tool/ToolCard SDK, Python3.11.17, WorkSwarm bundled Node22.11.0.

17/17 targeted tests passed, no skips. Tests exercise native invoke and bundled source, not mock tool results.

- PASS: horizontal win detected
- PASS: horizontal finished game immutable
- PASS: vertical win detected
- PASS: vertical finished game immutable
- PASS: diagonal win detected
- PASS: diagonal finished game immutable
- PASS: reverse-diagonal win detected
- PASS: reverse-diagonal finished game immutable
- PASS: invalid move 0 rejected without mutation
- PASS: invalid move 1 rejected without mutation
- PASS: invalid move 2 rejected without mutation
- PASS: invalid move 3 rejected without mutation
- PASS: invalid move 4 rejected without mutation
- PASS: invalid move 5 rejected without mutation
- PASS: existing game preserved
- PASS: Chinese board snapshot exported
- PASS: overline counts as win

Reproduce functional tests: `python -B tests/five_ports_functional.py` with the native openjiuwen SDK available. Extracted native payloads also passed the same targeted tests (48/48 total).

Host UI: imported exact native ZIP through desktop WorkSwarm My Extensions; clicked Use and ran a new model-backed session. 7 native tool result events verified in the host session history; installed file hashes match every source/native/Hub payload file. Session web_1a166b9ef8a_e9bb421ed4db. These local tests do not establish user completion or acceptance.

Native ZIP SHA-256: 71a72e2c7857f139978a448b75220903d24167ccc6adae92271409cd2f3f2e36
Hub-wrapper ZIP SHA-256: 058fcbdcbd1d3b0f9600c1ad9a025b473cd08065c94031823d5df52e0f4b5c17

HTML generation and Chinese content passed. Historical initial automated file-URL preview was denied by browser policy. Superseded2026-10-23: user manually opened the exact artifact in Safari; native CUA inspected the existing page and the targeted desktop visual/UI checks below passed. Original screenshots are preserved without modification. This does not establish mobile/cross-browser coverage or user test-completion confirmation.

Original full-resolution screenshots and filtered native tool result events are retained in the local migration-five-20261023/evidence handoff. Assistant-operated testing is not a personal-human-test claim or explicit user completion/acceptance. No push/PR/merge/Hub submission performed.

## Follow-up desktop visual/UI QA (2026-10-23)

- PASS: Chinese board rendering — All15rows and15columns render with visible1-based coordinates and Chinese instructions.
- PASS: Move and status identity — Black1 appears at row8/column8; White2 at row8/column9; revision2 and next turnBlack agree with state JSON.
- PASS: Read-only behavior label — The page clearly states it is a read-only snapshot and directs further moves to the WorkSwarm conversation.

Evidence: local VISUAL_VERIFICATION.md and evidence/visual-verification.json. Native and Hub ZIPs remain byte-identical to the tested1.0.0 packages.

## User completion and delivery authorization

2026-10-23, current Song Haoran conversation: after the exact Chinese1.0.0 functional and follow-up visual results were presented, the user explicitly instructed `pr合入` (submit and merge the PR). This is the current-package completion confirmation and GitHub delivery authorization; tests were assistant-operated at the user's explicit request, not claimed as manual human testing. Original full-resolution images were collected and inspected before the delivery push. Confirmation report: RPT-20261023-gomoku-local-confirmed-100. Package hashes above remain unchanged. Lead handoff acceptance and official Hub catalog registration remain separate.

Portable delivery/evidence index: `docs/deliveries/five-chinese-plugins-20261023/README.md`. Earlier no-push/pending statements describe the historical Build stage; this authorization supersedes that boundary.
