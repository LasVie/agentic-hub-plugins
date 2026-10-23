# Test report — 星际防线 1.0.2

2026-10-23; Task AH-20261023-invaders-local; CAND-CLD-302; Cai Zhenze.
Mapping Invaders → 星际防线 → invaders-local; repo:agent-plugin:invaders-local.
Build began on feat/invaders-local at f7b0e8a; Phase3 fast-forwarded the branch to current main726e157 without changing the payload.

## Functional tests

Source:15/15 Node engine tests plus7/7 Python export tests passed, no skips.
Extracted final canonical payload: the same22/22 passed, no skips.
Environment: Node24.19.0; Python3.10.11; host checks Python3.12.14/openjiuwen0.1.19.
Cases cover deterministic seeded traces, immutable input, movement/glide/bounds,
shots/reload, collisions, shields, UFO/enemy scoring, lives/end/extra-life conditions,
wave progression and board dimensions. Strict save round-trip, wrong seed/version,
malformed/oversized/unsafe shapes and30 different actual gameplay traces passed.
Export cases cover Chinese output, version/hash, full MIT propagation, invalid inputs,
symlinks, preserving existing files and concurrent exclusive writes.

```sh
node --test tests/test_invaders_engine.mjs
python3 -B -m unittest discover -s tests -p 'test_invaders_local.py' -v
# Repeat with INVADERS_PAYLOAD=<extracted inner payload> for extracted tests.
python tools/asset_release.py check plugins/invaders-local
python tools/asset_release.py pack plugins/invaders-local
python3 plugins/invaders-local/build_test_package.py
```

## Format and package inspection

check/pack passed. All15 payload files match source, canonical ZIP, native companion
and installed payload. The canonical ZIP has16 entries: plugin.yaml plus15 inner
runtime files. CRC, UTF-8, version, wrapper layout, declared paths, original complete
MIT text/hash and absence of tests/reports/caches in the ZIP passed. Node built-in
TypeScript stripping reproduces the compiled engine without downloaded packages.

- Canonical: releases/agent-plugin/invaders-local/1.0.2/invaders-local-1.0.2.zip
- SHA-256: 70aebf34f8d40746a3a9977ad22b27be3665b5351bb2535b0852d3d748acfeef
- WorkSwarm: dist/invaders-local/1.0.2/invaders-local-1.0.2-workswarm.zip
- SHA-256: 21df39acd6244c2d9be87685d4c04fb08df1baad1defcab2ce425ebbcc199f67
- Seed12345 exported HTML SHA-256: 213d6dcff4da4a5157fc88a218cedbdf083a2c5a0d4cab674853e3d9d5a0c183

Preflight1.0.0 archives (now outside delivery in ignored dist/invaders-local/preflight-canonical/) were preserved after correcting /tmp examples (a macOS symlink
intentionally rejected by the exporter) to canonical /private/tmp. Preflight1.0.1 was
also preserved after an actual game-over/reload test found a misleading Continue
instruction. Final1.0.2 directs a restored finished game to Restart. Versions were
bumped rather than silently replacing archives. None of the preflight packages was
confirmed by the user. Initial pack correctly refused a missing report before any
archive existed; subsequent successful packs have current report/source-review hashes.

## Actual isolated WorkSwarm lifecycle

Reused frontend http://127.0.0.1:6283, backend WebSocket29110, agent28110,
gateway30110. Frontend renders; direct/proxied WebSocket ping-pong and config reads
passed. Actual running backend lifecycle RPCs import_local/install/show/list passed
for final1.0.2. Chinese Extensions card/details display1Skill and 创建星际防线网页.
Create → Create from file opens its ZIP upload dialog; OS native file picking was
not exercised. Successful import/install used actual backend RPCs, not a mock.

An initial harness expected show to return a bare package; it returns {package:...}.
The harness was corrected; no plugin fix was needed for that error. Reimports are
avoided, and only this plugin's preflight installation was replaced for new versions.

The installed payload was resolved with the host's real native SDK **in a separate
process**:1Skill/1Tool, no MCP/rails. Four actual checks passed: Chinese-path export,
existing-file refusal, invalid seed and streaming export. Host's own DeepAgent hot-load
validator additionally bound1Skill/1Tool, invoked and fully unloaded them successfully.
Network was denied in these subprocess checks, with zero attempted network/model
requests. **These are installed-SDK execution checks, not tool invocation from a
running WorkSwarm model conversation.** No model prompt/agent run was sent.
Other installed plugin file hashes and model configuration digest remained unchanged.
No host patch, service restart or model-setting change was required.

## Actual browser checks

Final HTML hash agrees between extracted CLI and installed native Tool. Chrome was
operated through CUA at http://127.0.0.1:6284/game.html. This read-only loopback
preview serves only the synthetic generated HTML, with no directory/other-file access.
Browser policy disallows file:// navigation; no warning was bypassed. Direct local
file opening remains a user check, separate from the successful HTTP preview.

Actual1.0.2 checks: Chinese title/version/help, paused initial board, Start, left
movement15→13, P pause, Save, reload restoring position13/tick1 while paused, Right
movement13→15, visible Space projectile after reload cooldown, and continued ticking
with decreasing lives. Restart and finished-state restoration are checked separately
below. Engine scoring/collisions/waves were verified by automated functional tests;
no complete browser win/playthrough is claimed. Native focus switching/blur behavior
is implemented but not verified (background CUA actions do not emulate that reliably).
No external resource import/network API exists in the page; CSP connect-src none.
No packet-capture claim is made about unrelated browser extensions or the host.

Assistant-only local raw checks/screenshots: /private/tmp/invaders-build-20261023/,
with final-version checks under v1.0.2/. They are outside ZIPs and future PR staging.
Compact package-verification.json is retained beside this report. Raw host-verification.json is preserved outside the commit. Original user screenshot hashes are in evidence/originals.json; images are attached directly to the delivery PR.

## Remaining gates and cleanup

No known blocking payload failure in performed checks. The Build checkpoint had user confirmation/screenshots pending; the Phase3 record below supersedes that gate. OS file picker, native focus-loss, touch and other browsers remain unverified. The game is a
standalone page, not a WorkSwarm chat pane. See MANUAL_TESTING.md.
No paid calls, commits, pushes, PRs, merges, Releases or Hub operations.

SerialHunt cleanup was explicitly requested: removed its untracked source, tests/cache,
canonical/native packages, six agent-created temp directories, isolated installation
and empty branch. No SerialHunt-named file remains in this checkout or isolated plugin
directory. Retired Task ID/cancellation reports remain in the live tracker; original
user screenshot and shared service logs remain. Other plugins/services and parallel
message-quota work were preserved. No provider request or access bypass was attempted.

## Final browser regression result

Actual1.0.2 run reached score50/high-score50, lives0/game-over at tick780. Reload
restored all those values and displayed the corrected Restart instruction, with
Continue disabled. Restart reset score0/wave1/lives3/position15/tick0 and retained
high-score50. Final browser error/warning log was empty. Screenshots are in the
final v1.0.2 evidence directory. This is assistant-operated evidence, not user test
completion. Earlier check-repo temporarily detected stale report metadata while this
report was being updated; repacking refreshes artifact.json without changing ZIP bytes.

## Phase3 user confirmation and evidence — 2026-10-23

Cai Zhenze explicitly confirmed: “I confirm manual testing of CAND-CLD-302 — 星际防线 v1.0.2 passed. Use my attached screenshot and proceed to Phase 3 under AGENTS.md.” Source: current conversation; no message permalink available. Four full-resolution original PNGs were received and inspected before push/PR. Their dimensions, hashes and observed scope are retained in evidence/originals.json.

The user's actual exported HTML in Downloads hashes to213d6dcff4da4a5157fc88a218cedbdf083a2c5a0d4cab674853e3d9d5a0c183, identical to the installed/extracted tool output for seed12345. The screenshots show WorkSwarm at localhost6385 reporting version1.0.2/export success, a blank board in the host artifact preview, and independent local-file gameplay with score40/wave1/lives3/tick228. The same first images show a host “control input is already being delivered” error; that is retained honestly, not edited away or counted as successful tool invocation. The exact exported artifact, standalone gameplay and explicit user completion corroborate the intended workflow; no package change is needed. Host preview rendering is not the required standalone-game entry point. Screenshot text alone does not establish backend tool invocation.

Only non-payload delivery docs, evidence metadata and test harness cleanup changed after confirmation. Python test imports now suppress bytecode in the runtime directory so normal CI leaves the tested payload immutable. Node immutability assertions were tightened to compare the actual input. These test-only changes do not alter either confirmed ZIP. No additional paid/model call was made.

Phase3 verification: the user-tested localhost6385 installed payload matches every one of the15 canonical payload hashes. Existing backend log confirms create_invaders_game registration at17:33:57; screenshot/model text is not used as independent proof of invocation. No new chat/model call was made. After updating from main726e157, local full repository suite passed256 tests with1optional historical Prosody-baseline comparison skipped; the15Node game tests and7Python export tests also passed. Normal Python test import leaves no payload bytecode.
