# Functional test report

Owner: Song Haoran. 2026-10-23. Chinese package 1.0.0.

31 actual native Tool/ToolCard, Node22.11 SQLite/HTTP/Git checks passed without mocks or skips on source. Tests use fresh disposable workspaces and real files/commits.

- PASS: fresh native SDK invocation
- PASS: Chinese native help
- PASS: unknown operation rejected
- PASS: real template metadata validation
- PASS: duplicate step id rejected
- PASS: dangling transition rejected
- PASS: template saved
- PASS: run freezes template
- PASS: existing run unaffected by template edits
- PASS: skipping rejected without advancement
- PASS: missing proof rejected without advancement
- PASS: traversal rejected without advancement
- PASS: draft completion recorded
- PASS: verify completion recorded
- PASS: run completes with real evidence hash
- PASS: finished run cannot double-complete
- PASS: break pauses instead of pretending done
- PASS: explicit resume works
- PASS: full run export
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

The same 31 checks passed again on the independently extracted final native ZIP, with no skips or mocks. Native SHA-256: `40053cbac5f8bca1773c9c2bbfcbe521213f2eb05063c238ee621b7203f8db54`. Canonical Hub-wrapper ZIP SHA-256: `a5a9d8bac54603f0d891aadbde350f9dbd7a5cc050f8b3aa1513d967c9765c43`. Source, native ZIP, canonical ZIP and the actual WorkSwarm installation match for every runtime file.

WorkSwarm imported the actual native ZIP through My Extensions and ran `process_workbench` in dedicated session `web_1a1675ab4ed_70622f242643`. All observed calls and deliberate failure cases are summarized in [native host evidence](../../docs/deliveries/interactive-five-20261023/native-host-results.json). Browser actions wrote the same SQLite state; a subsequent real native `status` read verified the UI changes. UI and original full-resolution screenshots: [delivery evidence](../../docs/deliveries/interactive-five-20261023/README.md).

Actual UI checks:

- PASS: Read native-created frozen run at check step
- PASS: Reject missing.txt without finishing run
- PASS: Complete check with actual verification.txt file
- PASS: See done board and SHA-256 evidence table
- PASS: Native status reads done and two trail entries, revision 4

Song Haoran explicitly delegated autonomous selection, adaptation, testing and submission for this batch. These are assistant-operated tests, not a claim of personally performed human testing or final Project Lead acceptance. The package is ready for GitHub handoff. Hub operations remain with Song Haoran; no catalog registration is implied.

Only the current macOS desktop and in-app browser were exercised. Export downloads, narrow/mobile layouts and other operating systems/browsers were not visually tested. Functional export actions are covered by the native runner. Current runtime needs Node.js >=22.11 with built-in SQLite and the WorkSwarm native Tool SDK; it does not need another account, external model or npm installation. Follow the Chinese README for scope and limits.
