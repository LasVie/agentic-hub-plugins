# User test confirmation — 会话人设切换 1.0.0

- Candidate CAND-DSH-095; task AH-20261027-persona-switcher; owner and confirming user Vannes Wijaya.
- Explicit current-conversation statement: "Testing of persona-switcher 1.0.0 (native ZIP c75f33a4…) is complete, no blocking issues".
- Recorded 2026-10-27, approximately 15:30 Asia/Singapore. No message permalink exists (Claude Code conversation); none is invented.
- Tested native ZIP SHA-256: `c75f33a45c1d0cc3f11d52e5f0e2cdbe960c5f9f53de9e045c4455e7a1b0940a`.
- Release ZIP SHA-256: `995bb3011bf17f35075d0711da17b39ad313a95800e5a0c23542d8892741791a`. Both contain the same 13 payload files, byte-identical to the source directory.
- Host test session: web_1a17c38e0c0_7d8311269a55 (desktop WorkSwarm on WSL2, deepseek/deepseek-v4-pro); installed `runtime/engine.py` hash matched the source.
- Known blocking issues: none. Round 1 defects (delete without confirmation, notice spacing, misleading none wording) fixed in this build.
- Known non-blocking issue, accepted by the user: after `default`, the model may claim the default applies to the next new session; the tool's set-default reply does not explain the rule. Corrected by the model's subsequent replies.
- User test completion is separate from later Project Lead acceptance.

## Original screenshots collected before delivery

See `evidence/originals.json` (original filename, size, SHA-256, what each shows). Eight 1920×1200 PNG originals, inspected: readable, Chinese UI, current-build session; no credential, email or key visible (localhost URL, other chat titles in the sidebar, taskbar; used as supplied by the user).
