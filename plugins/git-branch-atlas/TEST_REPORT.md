# Functional test report

Owner: Song Haoran. 2026-10-23. Chinese package 1.0.0.

26 actual native Tool/ToolCard, Node22.11 SQLite/HTTP/Git checks passed without mocks or skips on source. Tests use fresh disposable workspaces and real files/commits.

- PASS: fresh native SDK invocation
- PASS: Chinese native help
- PASS: unknown operation rejected
- PASS: real branched/merged repository scan
- PASS: merge parents and lane core preserved
- PASS: two branch refs parsed
- PASS: ahead/behind real divergence
- PASS: bounded graph retains truncation signal
- PASS: traversal rejected
- PASS: option ref rejected
- PASS: unresolvable ref rejected
- PASS: repository tracked state and index immutable
- PASS: graph export retains authoritative parent OIDs
- PASS: unborn repository reported honestly
- PASS: real loopback UI starts
- PASS: Chinese UI shell and restrictive CSP
- PASS: UI uses same authoritative SQLite revision
- PASS: missing UI token denied
- PASS: cross-origin mutation denied
- PASS: UI cannot switch workspace
- PASS: non-JSON CSRF request denied
- PASS: not an arbitrary file server
- PASS: reopening reuses current healthy version
- PASS: UI shutdown preserves state
- PASS: private SQLite permissions
- PASS: native data persists across new Tool objects

## Final-package and desktop verification

The same 26 checks passed again on the independently extracted final native ZIP, with no skips or mocks. Native SHA-256: `f6dea01503ef9ef90a29f74f1d60fe6f7b7eba4e0ec87dba22c4030aee424568`. Canonical Hub-wrapper ZIP SHA-256: `ebd09a1e5f8838aae5c079349e0429c30f5dd698f36b1f727f9a2bc24207b025`. Source, native ZIP, canonical ZIP and the actual WorkSwarm installation match for every runtime file.

WorkSwarm imported the actual native ZIP through My Extensions and ran `git_branch_atlas` in dedicated session `web_1a1675af767_dc1401a49c2b`. All observed calls and deliberate failure cases are summarized in [native host evidence](../../docs/deliveries/interactive-five-20261023/native-host-results.json). Browser actions wrote the same SQLite state; a subsequent real native `status` read verified the UI changes. UI and original full-resolution screenshots: [delivery evidence](../../docs/deliveries/interactive-five-20261023/README.md).

Actual UI checks:

- PASS: Read actual synthetic Git merge fixture
- PASS: Scan repo through UI
- PASS: Compare feature/main: 0/2 unique commits
- PASS: Select merge commit and see both full parent OIDs
- PASS: Search feature and verify only matching commit remains
- PASS: Native status reads two branches, four commits, one merge, revision 2

Song Haoran explicitly delegated autonomous selection, adaptation, testing and submission for this batch. These are assistant-operated tests, not a claim of personally performed human testing or final Project Lead acceptance. The package is ready for GitHub handoff. Hub operations remain with Song Haoran; no catalog registration is implied.

Only the current macOS desktop and in-app browser were exercised. Export downloads, narrow/mobile layouts and other operating systems/browsers were not visually tested. Functional export actions are covered by the native runner. Current runtime needs Node.js >=22.11 with built-in SQLite and the WorkSwarm native Tool SDK; it does not need another account, external model or npm installation. Follow the Chinese README for scope and limits.
