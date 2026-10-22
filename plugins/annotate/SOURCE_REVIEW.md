# Annotate source and scope review

Review date: 2026-10-22 (Asia/Singapore). Candidate CAND-CLD-264; Task AH-20261022-annotate. User selection and owner: Wang Jie, confirmed in the current conversation. Cloud candidate is reserved as Planned and linked to the task. Both Owner fields and the progress Reporter were saved and verified as Wang Jie without modifying the separate Members list or validation choices. The earlier temporary Unassigned reservation was synchronized after checking that the confirmed name could be entered. No other assignment was retained as an overwrite; an adjacent report accidentally touched during final synchronization was restored to its verified original reporter/status and re-read by ID.

## Functional comparison

Reuse the existing Confirmed New Capability finding and compare the current ledger entries: chrome-devtools-mcp (2f99a9222dce41f4bd5ac440bf4496f4@1.0.0) controls and diagnoses Chrome; page-acceptance (747494162b0c4725ae6ca95b9803b501@0.1.0) executes acceptance steps; frontend-design (8fd546a8a97149a08029b24e9d3cd028@e7bda4f) generates frontend designs; playground (repo:skill:playground@1.0.0) creates standalone interactive HTML explorers. The scoped increment is human-drawn notes on a running local page, with element context, screenshot delivery and per-note feedback. Different packaging alone is not the justification. Comparison uses live ledger descriptions and existing review evidence; runtime equivalence of those other assets was not tested.

## Materials and permission

Upstream: https://github.com/FinalAngel/claude-annotate at d70e57a29ed480b05ff046296572fcc5b761f25e, version 0.3.2. The complete root MIT text identifies Copyright (c) 2026 Angelo Dini. At this pinned revision there is no separate subdirectory license or NOTICE among the 20 tracked files. The copied JavaScript headers are preserved. MIT permission/notice retention is fulfilled by the complete bundled text and THIRD_PARTY_NOTICES.md; no new relicensing claim is made.

| Reused upstream material | Delivered path | Changes and coverage |
| --- | --- | --- |
| server/index.mjs | runtime/server/index.mjs | MIT; polling-only host protocol, inline images, explicit note completion, bounded waits and configurable cache |
| server/overlay.js | runtime/server/overlay.js | MIT; neutral user-facing agent wording |
| package.json | runtime/package.json | MIT; runtime identity/version and exact direct dependency versions |
| package-lock.json | runtime/package-lock.json | MIT metadata; preserve pinned resolved versions and integrity hashes, update runtime identity/root dependency pins |
| LICENSE | licenses/claude-annotate/LICENSE | Exact complete MIT text, SHA-256 560cb98de97e83fc25542efdd90e7ab60fa0f824bb9a3d0152c0141b97935da3 |

New manifest, skill, launch/setup helpers, demo and test harness are adaptation work for the authorized task. Original Claude manifests, commands, hooks and ticker script are not shipped. No upstream logo, GIF, screenshot, icon, font, third-party dataset or account credential is copied. The upstream README's inspiration credit is retained in THIRD_PARTY_NOTICES.md without asserting that a separate upstream repository was audited or copied.

## Runtime dependencies

The exact existing lock resolves @modelcontextprotocol/sdk 1.32.0 (MIT) and playwright-core 1.63.0 (Apache-2.0). Original npm ci was run with installation scripts disabled. The lock has 95 dependency packages; recorded license declarations comprise MIT, ISC, BSD-2-Clause, BSD-3-Clause and Apache-2.0. Direct dependency license/notice files are available in the installed packages and the dependency inventory records their hashes. Declarations alone are not a complete review of every dependency file. No dependency implementation or node_modules is bundled into the delivery ZIP: users install the pinned packages with their original notices. Any later decision to bundle dependencies requires a separate distribution review and renewed final-ZIP inspection.

Python, Node, installed Chrome and WorkSwarm are external prerequisites. No browser binary or model is bundled. A configured WorkSwarm model can receive the returned annotations and images; local browser operation does not promise that model inputs remain local. No service subscription or API key specific to this plugin is required by the scoped runtime.

## Host and runtime evidence

The official openJiuwen extension loader expands mcps[].file relative to the native package and uses the MCP config file's parent as the default cwd. The bundled config launches ../../scripts/launch.py from mcps/annotate/. Python resolves the actual payload location. Setup records the selected Node executable outside the payload so a GUI host need not inherit Conda's Node PATH. Runtime dependencies still need installation in the actual imported directory.

Source references inspected: openJiuwen-ai/agent-core develop/openjiuwen/harness/resources/extension_loader.py; openJiuwen-ai/jiuwenswarm develop/jiuwenswarm/server/runtime/extension_package_manager.py; skillhub Agent asset specification pinned at 0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a. Live WorkSwarm UI/model compatibility remains a user-test gate; these source reads are not a claim of host acceptance.

## Final ZIP review

The payload must include runtime implementation, native manifest/skill/MCP configuration, setup and launch helpers, demo, README, THIRD_PARTY_NOTICES.md and the complete upstream MIT text. The wrapper must contain only plugin.yaml and the same-name payload. Development tests, tracking, installed dependencies and caches stay outside it. Final extraction, file inventory and license hash results are recorded after functional tests in TEST_REPORT.md. Permission status verified applies to the specifically reused upstream materials above, not blanket clearance of logos, dependencies or service terms.

Final extraction review completed: the complete MIT file has the recorded original hash, THIRD_PARTY_NOTICES.md is present, all declared paths exist, and no node_modules, tests, tracking data, hidden cache or upstream media occurs in the payload. The canonical archive and WorkSwarm native companion contain identical native payload inventories and SHA-256 values. The exact extracted canonical payload passed the real-browser integration harness. The host UI/model round trip, user confirmation and screenshot evidence remain pending.

## Version 1.0.2 first-use initialization update

The preceding manual-setup findings describe the 1.0.1 baseline. The user explicitly requested automatic dependency preparation on first use and authorized this update in the current conversation. Preserve task AH-20261022-annotate and owner Wang Jie; no new candidate or duplicate task is created. The current user delivery scope is GitHub PR only, not Hub web submission, and no submission is performed during this update.

Version 1.0.2 changes repository-owned launch/setup helpers, manifest timeout, instructions, package identity and tests. Reused server/overlay code and dependency versions are unchanged. No additional third-party implementation is bundled, so the pinned upstream license evidence and 95-package dependency inventory remain applicable. Manual setup is no longer required: a macOS Python launcher discovers Node from configured locations or the WorkSwarm application, runs locked npm ci with scripts disabled, serializes concurrent initialization, validates installed package versions and records readiness only after success. All installation output is diagnostic stderr, not MCP stdout. First use requires network and writable local installation/cache directories; import-time code execution is not claimed.

The 1.0.2 package remains subject to fresh extracted-ZIP inspection and functional tests. Prior user-provided 1.0.1 screenshots/reports show host loading and annotation work after manual setup, but do not confirm first-use initialization or image delivery for 1.0.2. Real WorkSwarm model/image handling and explicit user completion for this new version remain pending. Automatic initialization does not bypass the plugin-creator validator or modify application security controls.

Final 1.0.2 archive inspection and extracted-payload tests subsequently passed: native/canonical payload hashes match; upstream MIT text is unchanged; no dependencies, development caches or tests were bundled. The final extracted runtime automatically installed from an initially empty npm cache, retried an expected offline failure, handled simultaneous real MCP starts with a single installation, completed real-browser annotation/image/progress tests and reused dependencies on warm start. This is development evidence only; actual 1.0.2 desktop/model acceptance still awaits the user.

## Version 1.0.3 Chinese localization

Naming map: upstream/candidate Annotate (claude-annotate) → Chinese display name 网页圈选与批注 → unchanged internal slug annotate. Candidate CAND-CLD-264, task AH-20261022-annotate and owner Wang Jie are preserved. Current main be479b1 requires Chinese-language packages. The user explicitly selected Chinese localization and subsequently instructed not to repeat their manual test round.

Version 1.0.3 translates repository-owned Skill instructions, default agent instructions, metadata, tool descriptions, batch text, human-readable errors, bootstrap diagnostics, toolbar/notes/toasts and documentation. The edited upstream server/overlay remain MIT-covered; original headers and the complete upstream license are unchanged. Package/API identifiers, schema keys, delivery and progress enum values, HTTP error codes and DOM hooks are preserved; human-facing display text and simple textual acknowledgements are localized. All 95 dependency versions, resolved URLs and integrity entries remain identical to the reviewed inventory; a regression test checks the inventory against the lock. No new upstream code, media or service is introduced.

The previously confirmed 1.0.2 archive is retained with its original hash. Its user confirmation and screenshots are historical evidence, not user acceptance of the changed Chinese package. The new version is subject to developer-side Chinese UTF-8/UI/function checks and final extracted-ZIP review. No additional manual user tests are requested, and no 1.0.3 user completion is fabricated. Direct GitHub delivery remains gated; no push, PR or Hub publication is performed during localization. Original clipboard-only screenshots cannot be exported by the current CLI toolchain, so no fake original-file hashes or attachment links are created.

Final 1.0.3 extraction review passed. Native and canonical payloads are identical; required notices and exact original MIT text remain bundled. All 95 dependency records match the reviewed original lock except root package identity, and no dependency implementation is redistributed. The actual extracted package passes Chinese instruction/tool/UI/batch/error checks plus cold initialization, concurrency, retry, screenshot/progress and warm-reuse automation. The user is not asked to repeat their manual round, and developer screenshots are not substituted for user evidence.

## Current submission instruction

Wang Jie subsequently accepted proceeding with version 1.0.3 and explicitly requested immediate PR creation, superseding the historical local-only hold above. USER_TEST_CONFIRMATION.md records the actual statements and exact package hashes. Runtime payloads are unchanged by this submission preparation. The seven actual user screenshots were subsequently recovered without further image processing from the current conversation and attached at https://github.com/LasVie/agentic-hub-plugins/pull/28#issuecomment-6338983543. All seven hosted PNG hashes match the recovered files. Historical unavailability statements above are resolved; the screenshot test version remains 1.0.2 and is not relabeled. Do not merge automatically or perform Hub operations.
