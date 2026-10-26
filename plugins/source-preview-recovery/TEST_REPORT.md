# Functional test report

Task AH-20261023-source-preview-recovery; CAND-DSH-121; Cai Zhenze.
Mapping vibe-any/dsh-plugin-save-token → 原文快照与精简预览 → source-preview-recovery.
Final Chinese package1.0.1; Python3.12.14/macOS arm64, standard library and host SDK. Minimum Python3.11; Linux host unverified, Windows unsupported.

## Actual final checks on2026-10-23

- `python -B -m unittest discover -s tests -p test_source_preview_recovery.py -q`:43/43 source tests passed.
- Same command with SOURCE_PREVIEW_PAYLOAD=/private/tmp/source-preview-recovery-package-test-101/canonical/source-preview-recovery/source-preview-recovery:43/43 extracted tests passed.
- `PYTHONDONTWRITEBYTECODE=1 PATH=<available Node22.23.3>:$PATH python -B -m unittest discover -s tests -q`:292 tests OK,1skip; final log /private/tmp/source-preview-recovery-final-101-suite.log.
- `python tools/asset_release.py check plugins/source-preview-recovery`:format passed; `pack` produced canonical ZIP. `check-repo`:32source assets/41releaseZIPs passed. These structural checks are distinct from the asset functional tests.
- Eight payload files match source, canonical/native ZIPs and real installed plugin. Extracted wrapper contains only plugin.yaml plus one inner directory. Full license hash/original three headers/declared files checked. All8 UTF-8 files decode successfully; Chinese manifests/descriptions/Skill/README/help/messages and real browser labels inspected.

Functional tests use real temporary files and independent processes: Chinese/emoji, CR/LF/CRLF/BOM and Unicode separators; accurate blank/repeat/error coordinates; mixed JSON scalar types, large integers/decimals, duplicate keys, escaped-surrogate fallback and huge headers; exact large-file export beyond the old262144-character cache; unchanged/changed/deleted sources; new-process durable-ID recovery; damaged/missing snapshots; source/store/parent symlinks, hardlinks and traversal; confirmation, size/line/range/store quotas; unknown state files; concurrent processes and writer conflicts; source modification during read; disk-write failure; export refusal. Negative tests assert actual errors and Chinese messages, never expected-output-only success.

## Real isolated host integration

Fresh instance /private/tmp/source-preview-recovery-workswarm-20261023, source3ef1de9bf0b4813e2a0e8674dedc499c78e53df2 copied from this task's previously verified pinned archive (cache/node_modules/.env excluded); independent physical COW frontend dependencies, source, config, state, caches, working directory and tasks. No credentials copied. Frontend127.0.0.1:6387, backend29260, agent28260, gateway30260; ports checked before launch; Main and other instances preserved. Fresh language zh; prewarm/image probes disabled; model is a loopback disabled placeholder.

Actual frontendHTTP200; backend and proxied WebSocket ping/pong, config.get and plugin_packages.list passed. Real Extensions import_local/install succeeded without force-overwrite; final replacement removed only hash-verified own unhanded preflight1.0.0. Installed loader resolved1Skill/3native Tool instances,13 invoke/stream calls passed, plus a new independent CLI process verified recovery. Tool tests covered unauthorized refusal, CRLF/range coordinates, repeated-byte reuse, source change, exact export/overwrite refusal, typed JSON,1000000-byte file export and range limit; all outputs1.0.1. Network audit observed0connections during installed Tool tests;0model requests. Browser after final reimport verified Chinese name, descriptions and all3Tool labels. This agent UI image is not user test evidence.

## Corrections and package identity

Preflight1.0.0 exposed a macOS concurrent lock-file initialization issue; corrected exclusive creation/fail-closed retry and reran tests. Added bounded JSON header/surrogate handling and200000-line bound before packaging. Final header audit retained all3upstream headers and bumped the unhanded package to1.0.1; earlier1.0.0 ZIPs/evidence moved outside deliverables to /private/tmp/source-preview-recovery-preflight-100. Only1.0.1 is the manual-test handoff.

Canonical ZIP SHA-256:183bc30c69074c0748d07e399a0664478200152699fd91e97bd86b5a521a2d14.
Native test ZIP SHA-256:99d19c3d678c8c6a64fa269375362a71345bb8bf9335a39553f320af2da168b5.

Evidence: package-verification.json and host-verification.json; tests/test_source_preview_recovery.py; SOURCE_REVIEW.md and provenance.json. Manual instructions MANUAL_TESTING.md and reproducible prepare_manual_testing.py; dist/source-preview-recovery/1.0.1/manual-workspace is public fictional input only and initially has no snapshots/outputs.

## Limits and next gate

As of the2026-10-23 handoff, no model conversation or native OS upload picker had been tested by this agent; real import/install RPC and SDK Tool flows passed. Previews are lossy views, raw snapshot/export bytes exact; no token/billing/quality guarantee. Files<=8MiB/200000lines; range<=1000lines/64KiB; store<=128snapshots/64MiB; no automatic deletion. User completion was pending at that handoff; current confirmation is recorded below.

## Current-package manual completion and Phase3 checks2026-10-26

Cai Zhenze explicitly confirmed manual testing of 原文快照与精简预览1.0.1 complete/passed and requested Phase3. USER_TEST_CONFIRMATION.md retains the actual quote and version/hash association. Five original PNGs received and validated at1854x1968,1726x1958,1712x1942,1652x1950,1610x1960, without recompression; evidence/originals.json stores exact byte counts/hashes. Images1–3 are instructions;4–5 show returned-result summaries with1.0.1 and expected positive/negative outcomes. Screenshot-described host/process restart was NOT executed manually; neither real billed savings nor answer quality was verified. These are readable original conversation/tool-result summaries, not raw backend-event logs. Existing automatic new-process recovery tests are separate evidence.

This agent's read-only independent crosscheck verified all five original input/snapshot byte pairs and the actual1000000-byte export (SHA8674ef6d79761164654c47bdf828a340813349c5e440a60e439030af8945a3b7); source lines32–34 retain CRLF and61bytes. evidence/manual-byte-crosscheck.json records this check; user input/snapshot/output files were not changed. Eight source/native/canonical/installed payload files and both exact testedZIP hashes remain unchanged.

Fast-forwarded only this feature branch to current main e6769f6, including existing Invaders/music work. Initial current-main test attempt used an old shared runtime missing PyYAML and sandbox-denied localhost integration; no source-preview failure was identified. A new task-private Python3.12.14 environment with locked PyYAML6.0.3 and permitted ephemeral localhost servers then passed313tests with64optional SDK/Pillow skips; all43source-preview tests executed. check and check-repo passed34sourceassets/43ZIPs. The prior SDK-enabled292tests/1skip,43extracted tests and13installed Tool calls remain valid unchanged-payload evidence; no model call was made by this agent in Phase3.

No known current-package test/material/license blocker found. Five originals, explicit completion, Chinese source/instructions, final hashes, source audit and actual functional evidence are available before push/PR. CI and actual attached-image/permalink verification remain mandatory before merge. Project Lead acceptance is not implied. No Hub operation, Asset Ledger update or Release is authorized; actual PR/merge/check links will be recorded in the original task/report and PR.
