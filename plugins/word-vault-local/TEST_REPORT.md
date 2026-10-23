# Functional test report

Owner: Song Haoran. 2026-10-23. Chinese package 1.0.0.

50 actual native Tool/ToolCard, Node22.11 SQLite/HTTP/Git checks passed without mocks or skips on source. Tests use fresh disposable workspaces and real files/commits.

- PASS: fresh native SDK invocation
- PASS: Chinese native help
- PASS: unknown operation rejected
- PASS: five local words saved
- PASS: upstream protected plural stays distinct
- PASS: upstream conservative morphology used
- PASS: stale write is immutable
- PASS: repeat counts without duplicate row
- PASS: learner isolation
- PASS: quiz 0 generated real options
- PASS: quiz 0 hides answer indices
- PASS: quiz 0 scores question 0
- PASS: quiz 0 scores question 1
- PASS: quiz 0 scores question 2
- PASS: quiz 0 scores question 3
- PASS: quiz 0 scores question 4
- PASS: quiz 1 generated real options
- PASS: quiz 1 hides answer indices
- PASS: quiz 1 scores question 0
- PASS: quiz 1 scores question 1
- PASS: quiz 1 scores question 2
- PASS: quiz 1 scores question 3
- PASS: quiz 1 scores question 4
- PASS: quiz 2 generated real options
- PASS: quiz 2 hides answer indices
- PASS: quiz 2 scores question 0
- PASS: quiz 2 scores question 1
- PASS: quiz 2 scores question 2
- PASS: quiz 2 scores question 3
- PASS: quiz 2 scores question 4
- PASS: three-consecutive mastery persisted
- PASS: duplicate answer does not double score
- PASS: client cannot self-award a correct answer
- PASS: wrong-answer review selects wrong word
- PASS: boolean revision rejected
- PASS: unsafe learner rejected
- PASS: invalid term rejected
- PASS: learner export excludes other banks
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

The same 50 checks passed again on the independently extracted final native ZIP, with no skips or mocks. Native SHA-256: `861f1042194ac12db09f35df190d37d690b115cfb934f1167904db640fa471e1`. Canonical Hub-wrapper ZIP SHA-256: `9769327de19ef7413ec4d6f1571c9fa618adbed089e377ad358217f4739d69c0`. Source, native ZIP, canonical ZIP and the actual WorkSwarm installation match for every runtime file.

WorkSwarm imported the actual native ZIP through My Extensions and ran `word_vault_local` in dedicated session `web_1a167599bdc_a5b557027c88`. All observed calls and deliberate failure cases are summarized in [native host evidence](../../docs/deliveries/interactive-five-20261023/native-host-results.json). Browser actions wrote the same SQLite state; a subsequent real native `status` read verified the UI changes. UI and original full-resolution screenshots: [delivery evidence](../../docs/deliveries/interactive-five-20261023/README.md).

Actual UI checks:

- PASS: Read native-created five-word bank and graded quiz
- PASS: Add lighthouse / 灯塔 through form
- PASS: Submit wrong choice for glasses and see correct meaning
- PASS: Search 灯塔 and verify only lighthouse remains
- PASS: Native status reads six words, one wrong word, revision 5

Song Haoran explicitly delegated autonomous selection, adaptation, testing and submission for this batch. These are assistant-operated tests, not a claim of personally performed human testing or final Project Lead acceptance. The package is ready for GitHub handoff. Hub operations remain with Song Haoran; no catalog registration is implied.

Only the current macOS desktop and in-app browser were exercised. Export downloads, narrow/mobile layouts and other operating systems/browsers were not visually tested. Functional export actions are covered by the native runner. Current runtime needs Node.js >=22.11 with built-in SQLite and the WorkSwarm native Tool SDK; it does not need another account, external model or npm installation. Follow the Chinese README for scope and limits.
