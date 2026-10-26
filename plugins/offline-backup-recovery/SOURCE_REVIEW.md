# Source review — 离线备份与恢复 1.0.0

Task `AH-20261026-offline-backup-recovery`; candidate `CAND-DSH-275`; owner Cai Zhenze. Reviewed 2026-10-26. User approved only manual offline directory backup, verification, recovery preview and recovery into a new directory. User confirmed unchanged1.0.0 manual testing passed2026-10-26 and authorized GitHub-only delivery; see USER_TEST_CONFIRMATION.md. No Release/Hub operation or Project Lead acceptance is inferred.

## Pinned source and permission

- Upstream: https://github.com/xiaoyuyu6420/dsh-backup , version0.13.4, commit `608ed261adcbfde11acab00207f76912fa207c1b` (matches catalog npm gitHead and pinned package.json).
- Downloaded fixed GitHub source archive SHA-256: `9b5aae930984d3277e0f7aa204065f83b4fdc495ac13a2cb32d8524067fbb81f`. Research source stays outside the deliverable in `/private/tmp/dsh-backup-608ed261-source/`.
- Read complete root LICENSE, package.json, README.en.md, lib/index.js and recursive file inventory. Root LICENSE is MIT, Copyright (c) 2026 xiaoyuyu6420; SHA-256 `cd82853c068839eb0f8fbb2e09efe527ab2ebdab629ac21a5069ffc13220b9cf`. No nested LICENSE or NOTICE exists in the pinned tree. The MIT grant covers the reviewed authored code/documentation; it does not license separately provided services or imply endorsement.
- Mode: **ported**, permission_status **verified** for the reviewed backup/verification/preview/recovery workflow. Python host adapter rewrites the implementation and archive format; it is not represented as a clean-room or unchanged upstream port. Full MIT text and attribution travel inside both packages.

## Reuse and exclusions

| Source | Delivered path / treatment | Permission and changes |
|---|---|---|
| lib/index.js: doBackup, sha256File, verifyOne, safeArchiveEntries, restoreArchive | runtime/backup.py | MIT workflow adaptation; Python standard library, explicit user paths, bounded structured ZIP+manifest, stream hashes, exclusive output creation, no symlinks/hardlinks and new-target-only recovery. Upstream textual tar listing parser and in-place restore are replaced. |
| README.en.md backup/verify/dry-run workflow | README.md and skills/directory-backup/SKILL.md | MIT workflow concepts rewritten in Simplified Chinese for actual supported behavior. |
| LICENSE | licenses/dsh-backup/LICENSE | Complete original text/notice, unchanged. |
| Upstream React client/lib/client.js, icons/screenshots, rescue console, dependencies, other code | Excluded | No third-party JS/media/runtime is copied or bundled. No additional permission conclusion is made for unused assets. |

The original lib/index.js header has no separate copyright/license notice; retain its attribution through the Python header and full upstream MIT notice. THIRD_PARTY_NOTICES.md identifies pinned source, original rightsholder, actual covered paths and modifications. Repository-owned additions are not assigned a new unified license by this task.

Upstream needs Node>=20, system tar and DSH/Cordis peers. None is used by the bounded adapter: runtime is POSIX Python>=3.11 plus the host's existing openJiuwen SDK. No pip/npm dependency, account, network, paid model, scheduled task or shell command is used by the plugin. Existing host SDK is not bundled or relicensed.

## Identity and capability comparison

`xiaoyuyu6420/dsh-backup` → **离线备份与恢复** → `offline-backup-recovery`; internal ID `repo:agent-plugin:offline-backup-recovery`.

This is multi-file/binary directory backup and new-directory recovery. Python distribution archive comparison `850431fa7351409f922e0fbd510d1b8a@1.0.0` only compares existing packages. 文件编码守护 `repo:agent-plugin:dsh-fs-encoding@1.0.4` undoes one explicit text edit. 桌面指挥官 `7202ba29df594ed39b2ac7f42b062c6b@1.0.0` offers generic file/terminal operations. CWC `d1d82ce9aa974435b5ec1d4fa4f15716@1.0.0` backs up device firmware. Newly merged 原文快照与精简预览1.0.1 (PR46, CAND-DSH-121) preserves individual UTF-8 texts for compact views/range retrieval, not directory recovery. No equivalent dedicated workflow was found in the Phase1 live625-asset ledger/34-task review; kickoff checked new main341277d and preserved all claims.

## Safety and testing contract

No full/live WorkSwarm migration, application-consistency claim, overwrite/in-place restore, retention deletion, update/install, session repair, GitHub sync, credential discovery or encryption. Explicitly selected files can contain private information; archives remain local and are not automatically redacted. Checksums detect inconsistency, not authenticity. Restrict size/count/depth and reject unsupported archive entries. Source must be quiescent; same-user malicious concurrent filesystem changes are outside the protection boundary. Functional tests and final extracted-license/package verification will be recorded after execution in TEST_REPORT.md.

## Final distribution inspection — 2026-10-26

Canonical `releases/agent-plugin/offline-backup-recovery/1.0.0/offline-backup-recovery-1.0.0.zip`, SHA-256 `eedd7c0ce3b3cf39a09f030d910bfbab7bcbc591a0a0d2839e069df6f741f91a`; native compatibility ZIP `plugins/offline-backup-recovery/test-packages/offline-backup-recovery-1.0.0-workswarm.zip`, SHA-256 `58d978fed742962d02ce450c1cba4a255370cd95e0a38ebbbd9b5ba1168d2bfd`. Extracted and compared all7 payload files against source, native ZIP and actual installed package. Original complete MIT license bytes/hash match provenance; THIRD_PARTY_NOTICES.md and Python adaptation header retain actual author/license attribution. No applicable upstream NOTICE, media, React client or additional dependency is bundled. Declared paths exist; wrapper/manifest/asset IDs and versions agree. All translatable payload descriptions, instructions, help and errors are Chinese. No tests, screenshots, runtime state, research source or logs enter the payload. Source/extracted functional checks and separate installed-SDK/website checks passed as recorded in TEST_REPORT.md. User subsequently confirmed this exact unchanged package passed, with applicable originals received. No legal/platform or lead acceptance is inferred from automated checks or the user's manual pass.
