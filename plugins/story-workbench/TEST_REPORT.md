# Functional test report

Owner: Song Haoran. 2026-10-23. Chinese package 1.0.0.

29 actual native Tool/ToolCard, Node22.11 SQLite/HTTP/Git checks passed without mocks or skips on source. Tests use fresh disposable workspaces and real files/commits.

- PASS: fresh native SDK invocation
- PASS: Chinese native help
- PASS: unknown operation rejected
- PASS: project created
- PASS: existing project never overwritten
- PASS: character saved
- PASS: Chinese chapter saved
- PASS: original marker core measures prose
- PASS: quote anchored
- PASS: UTF16 quote relocated after prefix
- PASS: prior revision immutable and hashed
- PASS: ambiguous quote detached honestly
- PASS: ambiguous new annotation rejected
- PASS: stale chapter hash rejected
- PASS: resolve preserves annotation
- PASS: stale character update rejected
- PASS: complete project history export
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

The same 29 checks passed again on the independently extracted final native ZIP, with no skips or mocks. Native SHA-256: `d2eb4ed772dfcfcf5caa34d693fc37501f67474cbf4bec3140e36d8a226d6813`. Canonical Hub-wrapper ZIP SHA-256: `6bcf455c2b2cfedc8a7a97cee4d8524bc51afea1755b1a9262544dd8f08c7efc`. Source, native ZIP, canonical ZIP and the actual WorkSwarm installation match for every runtime file.

WorkSwarm imported the actual native ZIP through My Extensions and ran `story_workbench` in dedicated session `web_1a1675a2b1e_db587ee431a7`. All observed calls and deliberate failure cases are summarized in [native host evidence](../../docs/deliveries/interactive-five-20261023/native-host-results.json). Browser actions wrote the same SQLite state; a subsequent real native `status` read verified the UI changes. UI and original full-resolution screenshots: [delivery evidence](../../docs/deliveries/interactive-five-20261023/README.md).

Actual UI checks:

- PASS: Open native-created chapter and relocated 旧书店 annotation
- PASS: Select 街道尽头 in textarea and add Chinese annotation
- PASS: Append Chinese final sentence and save chapter
- PASS: Native status reads two annotations, two historical revisions, revision 7

Song Haoran explicitly delegated autonomous selection, adaptation, testing and submission for this batch. These are assistant-operated tests, not a claim of personally performed human testing or final Project Lead acceptance. The package is ready for GitHub handoff. Hub operations remain with Song Haoran; no catalog registration is implied.

Only the current macOS desktop and in-app browser were exercised. Export downloads, narrow/mobile layouts and other operating systems/browsers were not visually tested. Functional export actions are covered by the native runner. Current runtime needs Node.js >=22.11 with built-in SQLite and the WorkSwarm native Tool SDK; it does not need another account, external model or npm installation. Follow the Chinese README for scope and limits.
