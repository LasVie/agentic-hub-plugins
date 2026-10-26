# Manual testing handoff — 离线备份与恢复 1.0.0

Owner Cai Zhenze; candidate CAND-DSH-275; task AH-20261026-offline-backup-recovery; branch feat/offline-backup-recovery. These are the original Build handoff instructions. User subsequently confirmed exact1.0.0 testing passed2026-10-26; current GitHub-only delivery authority and original evidence are in USER_TEST_CONFIRMATION.md. Package bytes remain unchanged.

- Canonical delivery ZIP: `releases/agent-plugin/offline-backup-recovery/1.0.0/offline-backup-recovery-1.0.0.zip`; SHA-256 `eedd7c0ce3b3cf39a09f030d910bfbab7bcbc591a0a0d2839e069df6f741f91a`.
- WorkSwarm test ZIP: `dist/offline-backup-recovery/1.0.0/offline-backup-recovery-1.0.0-workswarm.zip` (also preserved under plugins/offline-backup-recovery/test-packages); SHA-256 `58d978fed742962d02ce450c1cba4a255370cd95e0a38ebbbd9b5ba1168d2bfd`.
- Both ZIPs have the exact same7 inner payload files. Use the native test ZIP in the older host, retain the canonical wrapper for later authorized GitHub delivery. No ZIP changes after user confirmation without renewed testing.

Open http://127.0.0.1:6283 . The plugin is already installed through backend import/install, and Extensions → My Extensions displays its1 skill/3 tools. Click **Use** to start a new task. To import elsewhere: Extensions → My Extensions → Create → Create from file → choose the native test ZIP → Confirm, then install/enable if prompted. The in-app browser upload dialog was checked; native file selection was not automated. Actual backend import/install and resulting UI were verified.

The existing model is a disabled testing placeholder. Select/configure your own approved model for the manual conversation; no model setting was changed and no paid/model call was made by the agent. Alternatively, the packaged CLI can exercise the same core without a model. Do not click Publish.

Synthetic fixtures are already prepared under `dist/offline-backup-recovery/1.0.0/manual-test/`:3 files,2 directories,4202 file bytes. Source contains Chinese/emoji text, JSON, all-byte binary content, nested/empty directories. No personal files are used. `人工测试备份.zip` and `人工测试恢复` have deliberately not been created by automated checks.

Paste this Chinese prompt into the new task:

```text
请只使用「离线备份与恢复」的实际工具，测试插件 v1.0.0。

我明确授权复制以下合成测试目录并创建备份，以及在预览后恢复到指定的新目录；不授权操作其他目录、停止服务、联网或发布。
source_dir=/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-backup-recovery/1.0.0/manual-test/示例源目录
archive_path=/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-backup-recovery/1.0.0/manual-test/人工测试备份.zip
target_dir=/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-backup-recovery/1.0.0/manual-test/人工测试恢复

1. 实际调用 create_directory_backup，confirmed=true，展示实际ok、version、归档路径、SHA-256、文件/目录数和总字节。预期是3文件、2目录、4202字节，但必须以实际返回为准。
2. 用刚才真实返回的archive_sha256作为expected_sha256，实际调用inspect_directory_backup，展示校验结果和清单。
3. 调用restore_directory_backup，先mode=preview，展示writes_performed=false与恢复计划，确认尚未写入。
4. 按上面的明确授权，用mode=restore、confirmed=true和同一实际摘要执行恢复，展示实际结果。
5. 再次向相同已存在目标执行恢复，确认被拒绝，不能删除、覆盖或自动换目标。
6. 实际校验 /Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-backup-recovery/1.0.0/manual-test/损坏示例.zip，确认如实返回失败。

如已有备份或恢复目标，不删除或覆盖，停止并告知我。工具不可用就如实报错，不编写替代工具，不根据预期值编造结果。中文报告各次真实返回，并区分预览、实际写入、自动测试和我的人工确认。不要宣称在线宿主迁移、加密或来源认证。
```

After actual recovery, independently compare restored bytes/tree without changing anything:

```sh
cd /Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins
/opt/homebrew/bin/python3.12 -B plugins/offline-backup-recovery/verify_manual_output.py
```

Expect `passed=true`, source unchanged, exact file hashes/tree,5 entries/3 files. These are expected assertions, not a result already obtained from your manual outputs. Inspect the restored Chinese text and empty directory as well.

Provide original readable screenshots showing actual current-version create/inspect/preview/recovery results, refusal/error behavior and the independent comparison. Hide keys/private configuration. Explicitly confirm whether testing of this exact1.0.0 package/hash passed or report any failures. No push, commit, PR, merge, Release, Hub operation or lead acceptance is authorized by this handoff.
