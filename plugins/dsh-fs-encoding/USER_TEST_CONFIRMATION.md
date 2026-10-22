# User Test Confirmation

- Date: 2026-10-22
- Task: `AH-20261022-dsh-fs-encoding`
- Candidate: `CAND-DSH-153`
- Version: `1.0.1`
- WorkSwarm ZIP SHA-256: `9572f21c28380903c389ec9aa2ab49c329edc0d69843c382a87a954b5f78d194`
- Source: current Codex conversation; no message URL available

The user explicitly reported completion of the replacement package tests. Verified host behavior included GBK creation and reading, Chinese text, CRLF preservation, preview without mutation, successful replacement, rejection of an unrepresentable emoji without mutation, decoded grep, successful byte restoration through `encoding_undo`, and `STALE_UNDO` refusal after an external change. UTF-8 BOM and UTF-16LE BOM detection, editing, BOM preservation, and CRLF preservation also passed.

The user-created outputs were reported under `/Users/kodisiu/Documents/JiuwenSwarm/2026-10-22/chat-4/outputs/`. No screenshot link was supplied, so screenshot evidence remains pending.
