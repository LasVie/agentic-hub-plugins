# Functional test report

2026-10-23; actual openjiuwen native Tool/ToolCard SDK, Python3.11.17, WorkSwarm bundled Node22.11.0.

6/6 targeted tests passed, no skips. Tests exercise native invoke and bundled source, not mock tool results.

- PASS: C++ and QML findings located
- PASS: code not modified
- PASS: clean file accepts
- PASS: traversal rejected
- PASS: missing rejected
- PASS: empty rejected

Reproduce functional tests: `python -B tests/five_ports_functional.py` with the native openjiuwen SDK available. Extracted native payloads also passed the same targeted tests (48/48 total).

Host UI: imported exact native ZIP through desktop WorkSwarm My Extensions; clicked Use and ran a new model-backed session. 2 native tool result events verified in the host session history; installed file hashes match every source/native/Hub payload file. Session web_1a166b420cc_687f52ecd583. These local tests do not establish user completion or acceptance.

Native ZIP SHA-256: c14c8564d904ccc923037285f02ba82d80d95b30b8169404aefe3f1e81149ae6
Hub-wrapper ZIP SHA-256: 17c1b3d154ab42cf6f083274bba9eca0872d352f2025e2bc136d2b65455ca237

Original full-resolution screenshots and filtered native tool result events are retained in the local migration-five-20261023/evidence handoff. Assistant-operated testing is not a personal-human-test claim or explicit user completion/acceptance. No push/PR/merge/Hub submission performed.

## User completion and delivery authorization

2026-10-23, current Song Haoran conversation: after the exact Chinese1.0.0 functional and follow-up visual results were presented, the user explicitly instructed `pr合入` (submit and merge the PR). This is the current-package completion confirmation and GitHub delivery authorization; tests were assistant-operated at the user's explicit request, not claimed as manual human testing. Original full-resolution images were collected and inspected before the delivery push. Confirmation report: RPT-20261023-qt-dev-review-confirmed-100. Package hashes above remain unchanged. Lead handoff acceptance and official Hub catalog registration remain separate.

Portable delivery/evidence index: `docs/deliveries/five-chinese-plugins-20261023/README.md`. Earlier no-push/pending statements describe the historical Build stage; this authorization supersedes that boundary.
