# Verification and user confirmation — 离线卫星轨道工作台 1.0.0

Date: 2026-11-12, Asia/Singapore. Owner Cai Zhenze; candidate `CAND-EXT-014`; original task `AH-20261112-offline-satellite-orbit-workbench`. Phase 2 results below are retained as dated evidence. On 2026-11-13 Cai Zhenze explicitly confirmed current-package manual testing passed and authorized Phase 3 GitHub delivery; Hub operations remain unauthorized.

## Exact packages

- Native WorkSwarm installation ZIP: `test-packages/offline-satellite-orbit-workbench-1.0.0-workswarm.zip`; SHA-256 `d554e61da463cfbf6124d776190aafbf407dc8a941396029d5e4c5a7cdb16710`.
- Canonical wrapped ZIP: `releases/agent-plugin/offline-satellite-orbit-workbench/1.0.0/offline-satellite-orbit-workbench-1.0.0.zip` (repository root relative); SHA-256 `3527dcede1c53acb0e556ba9520fb5f22d95f80a4d9be7b43d7d30fe0c923e60`.
- Both have identical 36-file inner payloads. Safe/unique paths, ZIP CRCs, source/native/canonical SHA-256 maps, Chinese UTF-8 instructions/labels, manifest version and five retained legal-text hashes verified. Runtime payload is 217,597 bytes (see the authoritative per-file artifact map for exact current sizes).
- `asset_release.py check` passed. Exact native and canonical preflight: 20 JavaScript files each, **0 known dynamic-execution signatures**. This covers the published local signatures; it does not claim Hub acceptance.
- `asset_release.py check-repo` passed: 71 source assets / 86 release ZIPs. Unrelated historical artifacts were preserved. No broad functional-test success for other assets is inferred.

## Numerical acceptance

Node 24.11.1 and 22.23.3: `node --test tests/test_engine.mjs`, **25 passed / 0 failed / 0 skipped**. Root repeated Node 24 with `--disallow-code-generation-from-strings`; 25 passed.

Actual `analyzeOrbit` results, not only the underlying propagator, match the independently inspected official CelesTrak satellite 00005 reference at epoch, +360 and +720 minutes within **1 m position / 1 mm/s velocity**. These tolerances compare implementations for the supplied model, not real satellite accuracy. Epoch microseconds, equivalent OMM, deep-space cache independence, observer/orbit separation, complete bounded sampling, refined crossings, clipped intervals, no-pass results, invalid inputs and recovery passed. The default historical example produces 1,441 samples and seven geometric intervals.

## Presentation and lifecycle

Node 24, installed test-only jsdom via `NODE_PATH`: `node --disallow-code-generation-from-strings --test tests/test_presentation.mjs`, **6 passed / 0 failed / 0 skipped**. Includes real SVG XML serialization/parse, escaping, dateline splitting in both directions, actual sample CSV completeness, BOM and units. A real serializer test found redundant namespace assignment producing duplicate `xmlns`; the final package removes that one redundant assignment and the regression passes. No dependency or host patch was used.

Lifecycle: `python -B tests/test_runtime.py`, **11 targeted tests passed** (agent execution with loopback permission). Tests cover status/confirmation without writes, own start/reuse/stop/restart, authenticated health, real user-activated cross-port navigation, foreign/corrupt/link records preserved, no signals to foreign listeners, static allowlist/MIME/CSP, concurrent launch and actual idle shutdown. These fixtures intentionally use small test web files; full payload/browser integration is separate.

Root and a second reviewer inspected owner/callers/ToolCard interface, module import closure, freshness, cancellation/recovery, units, DOM/export safety and installation identities. No further blocking code issue was identified. No host/core/frontend/backend/SDK/shared dependency/other-plugin source is modified.

## Current-host build limitation

A fresh, unchanged WorkSwarm 0.2.8 archive at `fa91394e42a7af731424222db82b02351e694de9` built its frontend, but its supported frozen dependency install failed in pinned `openjiuwen-computeruse` native macOS compilation: Swift 6.0.3 reports non-Sendable generic / `[String: Any]` values crossing actor boundaries. No newer installed toolchain or genuine prebuilt backend was found. The task-owned failed setup and logs are retained at `/private/tmp/satellite-orbit-build-9kma9kmq/host/runtime/dependency-install-retry.log`. No source patch, build bypass or stub was used. **Full WorkSwarm 0.2.8 compatibility remains unverified.**

## Installed host and SDK results

The exact native ZIP was imported/installed through the supported `plugin_packages.import_local/install/list/show` WebSocket APIs in a fresh task-owned **WorkSwarm 0.2.5.beta1**, source `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`, SDK 0.1.19. Frontend HTTP 200, proxy/direct WebSocket ping-pong, all 36 installed file hashes, package catalog/card and native Tool/Chinese Skill loading passed. Chrome independently displayed the installed plugin under Extensions → My Extensions and the manual upload control. Frontend: `http://127.0.0.1:6461/`; backend WebSocket 29461, agent 28461, gateway 30461. The fresh instance's model configuration is disabled and unchanged.

The installed public SDK passed no-write status, missing-confirmation rejection, start/reuse/stream/stop and fresh browser-QA status/start/reuse/status. Current **SDK 0.1.20**, exact `f3f8f576164cc405c046e43079c8ad00ee17f0c4`, also passed public plugin loading and the same lifecycle independently. It does not establish a complete running WorkSwarm 0.2.8 host. Host source/model configuration, unrelated catalog entries and installed package files remained unchanged. See `host-verification.json`.

A browser automation download wait stalled past the normal 1,800-second service idle limit. The cached page then honestly reported `worker_failed` on a new computation. Installed Tool status confirmed the service was no longer running; its own supported start safely restarted only the task's expired QA service, repeated start reused it, and status returned the same new URL. No foreign record/service was touched. This is an actual idle-expiry/restart observation, not a packaged-code change. Latest SDK-returned URL:

`http://127.0.0.1:60310/ed271aba78664bb9ed7e87aabc38d69f4a66c9116f53212e8ff8767b8c93ab7a/web/index.html`

Its developer QA workspace is `/private/tmp/satellite-orbit-build-9kma9kmq/host-025/runtime/installed-workbench-qa`; **do not reuse it after a separate manual installation**. On 2026-11-12, before manual testing, a fresh empty user workspace was prepared at `/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/offline-satellite-orbit-workbench/1.0.0/manual-workspace-user-20261112`, with no runtime record. That directory was subsequently used in the successful 2026-11-13 user test below. For another installation or test round, create a new dedicated empty directory and invoke the real chat Tool there; never overwrite the historical record.

A direct installed-SDK call is not running-chat tool dispatch. No paid/model calls were made by the development agent. The subsequent original user chat screenshot supplies running-chat status/start/reuse/status evidence, as recorded below.

## Actual Chrome checks

On the exact installed payload and tool-returned URL, the browser worker rendered the default TLE's genuine 1,441 samples / seven geometric intervals, date-line-separated ground track, elevation curve, sample slider and paginated numerical table. Selecting the final sample changed its timestamp, readout and table page to 49/49. Observer latitude change altered azimuth/range while engine tests independently establish unchanged TEME coordinates. Root visually inspected the Chinese interface; console errors/warnings were empty at the initial result.

Actual browser JSON/CSV/SVG downloads were found in the normal Downloads directory and independently parsed/read. JSON has version 1.0.0 and all 1,441 samples/seven intervals, the CSV has 1,442 rows including headers and agrees with the raw TEME first sample, and the SVG is well-formed with real paths. Exact downloaded-file sizes/hashes are retained in `browser-verification.json`. A duplicate JSON download caused by automation recovery is preserved; it is not a second result claim. The internal browser download-manager page was blocked by browser URL policy and was not accessed; verification used only these specific generated local files.

Browser input edits (text, observer and step) immediately cleared charts and disabled exports. Invalid UTC calendar date returned `invalid_utc`; bad TLE checksum returned `tle_checksum`; duplicate OMM field returned `duplicate_json_key`. Each recovered through a valid example. Actual file-picker import of `tests/fixtures/00005.omm.json` selected OMM, invalidated exports and calculated successfully. Equivalent OMM example also calculated 1,441 samples. No standalone harness was represented as browser computation.

Cancellation could not be exercised through the actual page because even the largest admitted 8,641-sample calculation finished before the Cancel click; **browser cancellation and timeout remain unverified**, with code-level generation/termination review only. Full network interception/offline-browser mode and exported-SVG reopening were not exercised; static module audit found no external requests, and the UI plots and downloaded SVG XML were separately checked. No reality-accuracy, optical visibility, Doppler, collision or navigation claim is made.

Developer screenshot preview: `/private/tmp/satellite-orbit-browser-evidence/orbit-final.png`. It is developer QA evidence, **not an original user manual-test screenshot**. Main/other chats' environments were not modified. No commits, pushes, PRs, merges, Releases or Hub actions occurred during Phase 2. The subsequent Phase 3 authorization is recorded below.


## User manual confirmation and original evidence — 2026-11-13

User test confirmation: “I confirm manual testing of 离线卫星轨道工作台 1.0.0 is complete and passed.” Confirmed by Cai Zhenze in this conversation on 2026-11-13, Asia/Singapore; exact message timestamp unavailable. Original task `AH-20261112-offline-satellite-orbit-workbench`, candidate `CAND-EXT-014`. Confirmation report: `RPT-20261113-offline-satellite-orbit-workbench-confirmed`. Native ZIP SHA-256 `d554e61da463cfbf6124d776190aafbf407dc8a941396029d5e4c5a7cdb16710`; canonical ZIP SHA-256 `3527dcede1c53acb0e556ba9520fb5f22d95f80a4d9be7b43d7d30fe0c923e60`. Both exact tested ZIPs and all runtime files remain unchanged. No known functional blocking issue was reported.

Five original PNG attachments were received before delivery push/PR, inspected for version, readability and public-repository suitability, and preserved byte for byte. Their dimensions and SHA-256 hashes are recorded in `evidence/user-testing-1.0.0/originals.json`. Originals are reserved for attachment to the delivery PR before merge; they are excluded from both plugin ZIPs. They contain public historical test elements, observer coordinates and a temporary loopback-only static-resource URL; no account keys, remote credentials or private document contents were observed.

The four workbench originals show plugin 1.0.0 / Satellite.js 7.2.0, OMM input, 1,441 computed samples, ground tracks, elevation intervals, sample/table navigation and observer/threshold changes (five to four intervals). The fifth original shows actual WorkSwarm `satellite_orbit_workbench` calls: initial status not running, confirmed start, repeated start with `reused=true`, and final running status; all report version 1.0.0 and the same actual tool-returned URL. The fresh workspace is `dist/offline-satellite-orbit-workbench/1.0.0/manual-workspace-user-20261112` under this worktree. The chat screenshot visibly dates the successful sequence 2026-11-13 17:07. No new model call was made by the development agent to produce this evidence.

User confirmation establishes manual completion; individual screenshots corroborate only their visible operations, not every possible test or an independent download audit. The developer test limitations above remain disclosed, including unverified full fresh WorkSwarm 0.2.8 compatibility, browser cancellation/timeout and full network interception. They do not become claimed passes. The supported manually tested installation succeeded without host changes. Phase 3 is authorized for GitHub delivery only; Song Haoran acceptance and any Hub operations remain separate.


## Pre-delivery recheck — 2026-11-13

Integrated latest origin/main `c854943808565463328cac353b99bc9cf603820d` into only this task feature worktree while preserving the owned attributes append and all unrelated untracked files. Exact native/canonical hashes are unchanged. Repeated format/pack, both exact-ZIP preflights (20 scripts / zero signatures), 25 engine tests and six presentation tests with Node 24.11.1 and string-code generation disabled; all passed. Reused unaffected 11 lifecycle tests and installed host/browser evidence above. Repository structural check after integration passed: 75 source assets / 90 release ZIPs; this does not claim functional tests for unrelated assets. Final file review excludes Finder metadata, runtime/log/download scratch, duplicate original PNG repository copies and unrelated historical artifacts from the commit. Five original PNGs are reserved for PR attachment; only their identity manifest is a repository delivery record. The instance-specific developer host helper is retained locally as intermediate verification material, outside the commit; maintained runtime/numerical/presentation regressions and actual host evidence are included. MANUAL_TEST.md now explicitly dates the already-used manual directory and requires a new empty directory for another installation/test round; this external documentation correction does not change either tested ZIP.
