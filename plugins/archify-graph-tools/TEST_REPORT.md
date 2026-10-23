# Functional test report

2026-10-23; actual openjiuwen native Tool/ToolCard SDK, Python3.11.17, WorkSwarm bundled Node22.11.0.

8/8 targeted tests passed, no skips. Tests exercise native invoke and bundled source, not mock tool results.

- PASS: Chinese example created
- PASS: valid source accepted
- PASS: real renderer delivered
- PASS: Chinese content and interactive controls
- PASS: broken node reference rejected
- PASS: failed delivery preserves prior output
- PASS: remote resource rejected before renderer
- PASS: unsafe path rejected

Reproduce functional tests: `python -B tests/five_ports_functional.py` with the native openjiuwen SDK available. Extracted native payloads also passed the same targeted tests (48/48 total).

Host UI: imported exact native ZIP through desktop WorkSwarm My Extensions; clicked Use and ran a new model-backed session. 3 native tool result events verified in the host session history; installed file hashes match every source/native/Hub payload file. Session web_1a166b5f704_395f922c4007. These local tests do not establish user completion or acceptance.

Native ZIP SHA-256: 30119fc51738db33f5f52c474fd73965de66ecd298e9f9cbde543e6178a9ccf7
Hub-wrapper ZIP SHA-256: a3df97a8c026b6f70ae7e045c46319e20629824ab0058db243e171f47a0c6258

HTML generation and Chinese content passed. Historical initial automated file-URL preview was denied by browser policy. Superseded2026-10-23: user manually opened the exact artifact in Safari; native CUA inspected the existing page and the targeted desktop visual/UI checks below passed. Original screenshots are preserved without modification. This does not establish mobile/cross-browser coverage or user test-completion confirmation.

Original full-resolution screenshots and filtered native tool result events are retained in the local migration-five-20261023/evidence handoff. Assistant-operated testing is not a personal-human-test claim or explicit user completion/acceptance. No push/PR/merge/Hub submission performed.

## Follow-up desktop visual/UI QA (2026-10-23)

- PASS: Chinese workflow rendering — Title/subtitle, three node labels, arrows, legend and node index render in Chinese without blocking clipping in the observed desktop view.
- PASS: Zoom and reset — Zoom changed from100% to125%; reset returned to100%; final graph view was reset.
- PASS: Theme switch — Dark-to-light switch responded; light theme screenshot captured; original dark theme restored.
- PASS: Node details — Clicking Desktop Test in node index opened its Chinese semantic passport and showed0outgoing/1incoming link.
- PASS: Upstream reachability — Toggle on displayed2upstream nodes,2connections, maximum depth2.
- PASS: Chinese node finder — Searching 中文适配 reduced3nodes to1/3matching result.
- PASS: Visual style — Classic switched to Blueprint with Chinese state label, then restored to Classic.

Evidence: local VISUAL_VERIFICATION.md and evidence/visual-verification.json. Native and Hub ZIPs remain byte-identical to the tested1.0.0 packages.

## User completion and delivery authorization

2026-10-23, current Song Haoran conversation: after the exact Chinese1.0.0 functional and follow-up visual results were presented, the user explicitly instructed `pr合入` (submit and merge the PR). This is the current-package completion confirmation and GitHub delivery authorization; tests were assistant-operated at the user's explicit request, not claimed as manual human testing. Original full-resolution images were collected and inspected before the delivery push. Confirmation report: RPT-20261023-archify-graph-tools-confirmed-100. Package hashes above remain unchanged. Lead handoff acceptance and official Hub catalog registration remain separate.

Portable delivery/evidence index: `docs/deliveries/five-chinese-plugins-20261023/README.md`. Earlier no-push/pending statements describe the historical Build stage; this authorization supersedes that boundary.
