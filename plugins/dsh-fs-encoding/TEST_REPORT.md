# Final delegated WorkSwarm test: dsh-fs-encoding 1.0.4

Date: 2026-10-22 (Asia/Singapore). Task `AH-20261022-dsh-fs-encoding`; candidate `CAND-DSH-153`; unchanged responsible member **Siu Lok Yin**.

Final package: marketplace SHA-256 `00288098f906e41eec6da26e17fb8ef48b940a0d6be9de94e0329be5c8cdbb03`; native import SHA-256 `3acf387d666320ded7c08d37fc5918935769fab1d6f2e98095792f5629f5d948`. Both transports, source, final extraction and actually installed payload match file for file and byte for byte.

Authority: The human user in the current conversation explicitly asked the agent to finish import and prompt testing in the user-open local WorkSwarm, preserve original screenshots, and update the existing content through a PR if successful, while keeping responsible member names unchanged. This authorizes delegated AI-operated host tests and conditional PR preparation; it is not a statement that the human personally performed the tests.

Environment: the user-open **WorkSwarm 0.2.7**, configured **Deepseek V4 Flash**, macOS. The controlling AI operated the real UI and submitted real Chinese prompts; tool results were not replaced by fabricated output. Recorded at 2026-10-22T17:31:24+08:00.

Delivery repository base `49acfa795cb6964f06a16cd30594efb7055272d0` (latest merged Smart Download baseline); the actual host tests used unchanged package bytes prepared from `e0f6b866649e82cbf37fbd082db9891ca977ae8e`. Full latest AGENTS.md was read and verified as Git blob `78a5b51285e322b38d81381d47aa9eef672bb62f`.

## Actual results

| Flow | Observed verification | Result |
| --- | --- | --- |
| Actual host import | Imported native 1.0.4 through the user-open WorkSwarm UI; independently verified all 6 installed files against final source/native/marketplace bytes. | Passed |
| Chinese file read | Real encoding_read read the Chinese GBK fixture and reported CRLF; recorded content and SHA-256. | Passed |
| Preview and preservation | Real encoding_edit dry-run found the target match and returned written=false; a second read retained original Chinese content, GBK, CRLF and SHA-256. | Passed |
| Chinese error | Empty file_path returned INVALID_INPUT with Chinese message 必须提供 file_path. | Passed |

## Final regression and package checks

57 repository unit tests passed with actual openJiuwen/Node.js and zero skipped. The independent package audit passed for exact source/native/marketplace/repository-release/extracted contents, pinned source records, unchanged original license bytes and publisher/manifest author identities. The actual openJiuwen loader passed eight checks on the final extracted Learning package. The initial final-package audit snapshot checked 7 source assets and 26 retained release ZIPs; an intermediate repository check passed for 8 source assets and 27 retained ZIPs. Other explicitly delegated repository work may proceed concurrently; the parent agent runs the final full-repository check in the fresh PR worktree. These six-asset results do not assert the completion state of that parallel work. These automated checks supplement the actual delegated host run; they are not labelled as human-performed testing.

Evidence is retained under `workswarm-host-tests-20261022/`: `final-audit/final-package-audit.json`, `final-audit/final-unit-suite.log`, `final-audit/final-learning-loader.json`, and `final-audit/final-repo-validation.log`. Each asset also has `installed-payload-verification.json`, real UI accessibility snapshots and original PNG files.

## Original screenshots and scope

- `dsh-fs-encoding/import-list.png` — version 1.0.4; SHA-256 `91baef9f5d03eed1da8f56fa4156b64ad5760fe9f289a18a2a589b6c9c4a6471`; Original actual host/browser screenshot.
- `dsh-fs-encoding/prompt-result.png` — version 1.0.4; SHA-256 `e2c7f53dbcdbe830ea84d40e6f302096731e111adf179cf45b6c2afd9f956305`; Original actual host/browser screenshot.

The final-version screenshots are local original evidence pending attachment to a real PR discussion. No PR image URL or evidence permalink has been invented. Screenshot tracker fields must receive only verified PR evidence links after upload; existing historical evidence remains valid for its stated version.

## Limits and delivery state

- The real prompt intentionally exercised read/dry-run/error flows without writing. Actual write/undo/stale-state behavior is covered separately by deterministic Tool API integration, not claimed as exercised by this UI prompt.
- Protection applies to explicit encoding_* tools; it does not intercept every host file operation.

The delegated test scope passed. Current status is `Awaiting Acceptance` with the delivery PR pending creation. `current_version_user_test_confirmation` remains null because the agent ran the tests under explicit human delegation; the separate `delegated_ai_test_confirmation` records that authority and the exact tested hashes. No current-version PR merge, Hub submission, Hub approval/publication, human-performed test completion or final Project Lead acceptance is claimed. Owners, stable IDs and historical PR/evidence records are preserved.

## Historical reports (preserved; prior versions and pending snapshots are not current results)

# WorkSwarm Chinese runtime test candidate dsh-fs-encoding 1.0.4

2026-10-22. Final native import/prompt tests delegated by the Project Lead; results pending. Previous version 1.0.3 and prior reports/hashes are historical only. No current-version user-performed testing, merge or Hub submission is claimed.

## Historical reports

# WorkSwarm Chinese runtime test candidate dsh-fs-encoding 1.0.3

2026-10-22. Final native import/prompt tests delegated by the Project Lead; results pending. Previous version 1.0.2 and prior reports/hashes are historical only. No current-version user-performed testing, merge or Hub submission is claimed.

## Historical reports

# Chinese package verification: dsh-fs-encoding 1.0.2

Date: 2026-10-22. Current package is a local Build candidate, not merged or submitted. All current-version user testing and screenshot confirmation are pending. Original owner, stable task/candidate IDs, prior PR #16 and historical evidence remain intact. Earlier confirmation below covers only its original bytes.

Source validation: 50 repository unit/functional tests passed with actual openJiuwen SDK and Node.js (zero skipped); file encoding and LaTeX real Tool API integrations passed. Final archive source/market/native/extracted equality and original-license checks passed; details are in LOCALIZATION_TEST.json and package-verification.json. Six Plugins passed actual isolated import/install/load/Chinese-card/uninstall checks; Playground passed actual relocated Skill resolver checks through a temporary test harness (not target-host Skill import). No paid model call is made. Crossref fill integration uses a deterministic mock, not a live service assertion.

Localization covers Chinese marketplace/native display fields, tags, README and user instructions. Playground SKILL body is Chinese; its six pinned templates remain unchanged. Original license texts, technical IDs and functional algorithms are preserved; MCP generator changes only its version literal and Skill version references.

Actual Tool API integration passed, including byte-preserving read/edit/write, shared-module undo, stale undo refusal, BOM cases and unrepresentable characters. Functional source bytes match the final extracted ZIP.

## Historical report (original version only)

# Functional Test Report

Date: 2026-10-22

Version 1.0.1 fixes a host-test finding from 1.0.0: WorkSwarm can load separate tool classes in isolated module contexts, so an in-memory undo dictionary was not shared and `encoding_undo` returned `NO_UNDO`. Undo records now use an owner-only host temporary directory. The regression suite deliberately reloads the module between edit and undo, verifies byte restoration, and verifies `STALE_UNDO` after an external change.

Upstream 1.5.2 was pinned at commit `a4d31cc33bd6f0fab2bf6752f6e50e8301885b94` and checked under Node 24. `npm run build` passed. The upstream `npm test` result was 601 passed and 4 failed out of 605 tests; all four failures were in `test/grep-tool.test.ts`, where current ripgrep output included directory-prefixed paths rather than the basename-only keys expected by the tests. These upstream grep failures do not exercise code copied into this Python port. `npm ci` also reported five vulnerabilities in the upstream development/dependency tree (one moderate, two high and two critical); those Node packages are not bundled or used by this standard-library-only port.

The native port integration test covers UTF-8 BOM, UTF-16, GBK and CRLF preservation; explicit decoding and remembered encoding for a later full-file write; preview-only mutation; rejection of an unrepresentable emoji without byte changes; decoded search; successful undo; and byte-for-byte restoration.

The direct integration suite passed. WorkSwarm 0.2.7 L0/L1/L2 validation passed with one bound Skill, five bound Tools, and zero errors or warnings. Repository format validation and a repeat deterministic pack comparison also passed.

The user subsequently confirmed the full version 1.0.1 host test for ZIP SHA-256 `9572f21c28380903c389ec9aa2ab49c329edc0d69843c382a87a954b5f78d194`. All documented GBK, strict-write, grep, successful undo, stale-undo, UTF-8 BOM, UTF-16LE BOM and CRLF cases passed. A real test screenshot, PR merge, Hub submission and Project Lead acceptance remain pending.
