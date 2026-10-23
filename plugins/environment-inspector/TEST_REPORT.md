# Functional test report

Owner: Song Haoran. 2026-10-23. Chinese package 1.0.0.

26 actual native Tool/ToolCard, Node22.11 SQLite/HTTP/Git checks passed without mocks or skips on source. Tests use fresh disposable workspaces and real files/commits.

- PASS: fresh native SDK invocation
- PASS: Chinese native help
- PASS: unknown operation rejected
- PASS: real local environment probe
- PASS: actual Node version observed
- PASS: port failure not represented as no service
- PASS: identity and key fields absent
- PASS: stale probe cannot overwrite snapshot
- PASS: second observation retained
- PASS: actual snapshots compared
- PASS: unknown snapshot rejected
- PASS: same snapshot comparison rejected
- PASS: snapshot export preserves two observations
- PASS: upstream lsof parser real fixture
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

The same 26 checks passed again on the independently extracted final native ZIP, with no skips or mocks. Native SHA-256: `486cff543f0880fa40f4a151a8cc53c32cf0f9021dd96632b6fb293e3c1ddf33`. Canonical Hub-wrapper ZIP SHA-256: `2202ce83a7fc1a13174b5b1d635f71e60864a816c1a36a62e939de058f440557`. Source, native ZIP, canonical ZIP and the actual WorkSwarm installation match for every runtime file.

WorkSwarm imported the actual native ZIP through My Extensions and ran `environment_inspector` in dedicated session `web_1a1675ac492_3eb318eb583a`. All observed calls and deliberate failure cases are summarized in [native host evidence](../../docs/deliveries/interactive-five-20261023/native-host-results.json). Browser actions wrote the same SQLite state; a subsequent real native `status` read verified the UI changes. UI and original full-resolution screenshots: [delivery evidence](../../docs/deliveries/interactive-five-20261023/README.md).

Actual UI checks:

- PASS: Read two native-created snapshots and actual tools/ports
- PASS: Trigger third actual read-only probe
- PASS: Select snap-1 and snap-3 and compare actual opened ports
- PASS: Filter ports to workswarm
- PASS: Native status reads three snapshots, revision 3

Song Haoran explicitly delegated autonomous selection, adaptation, testing and submission for this batch. These are assistant-operated tests, not a claim of personally performed human testing or final Project Lead acceptance. The package is ready for GitHub handoff. Hub operations remain with Song Haoran; no catalog registration is implied.

Only the current macOS desktop and in-app browser were exercised. Export downloads, narrow/mobile layouts and other operating systems/browsers were not visually tested. Functional export actions are covered by the native runner. Current runtime needs Node.js >=22.11 with built-in SQLite and the WorkSwarm native Tool SDK; it does not need another account, external model or npm installation. Follow the Chinese README for scope and limits.
