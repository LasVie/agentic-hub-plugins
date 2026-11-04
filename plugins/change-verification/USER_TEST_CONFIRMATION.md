# 变更影响与回归检查台 1.0.0 用户测试确认

- 用户/负责人：Wang Jie；任务 `AH-20261102-change-verification`；候选 `CAND-DSH-145`。
- 名称：TraceScope → **变更影响与回归检查台** → `change-verification`；内部 ID `repo:agent-plugin:change-verification`。
- 截图：当前会话 2026-11-02T06:47:06.737Z 收到十一张 PNG 原图，最后三张对应新对话复查。
- 用户确认：2026-11-02 **14:52:33.138 Asia/Singapore**，原话“ok啊，那继续吧，提交pr”。该回复紧接当前版本截图结果核对，确认采用简化步骤的当前包测试完成并授权 GitHub PR。
- 会话：`01a1627d-e063-7851-a189-e6b662469130`，没有编造公开会话链接。沿用确认报告 `RPT-20261102-change-verification-build`，不新建任务。

## 精确包核对

| 包 | SHA-256 |
| --- | --- |
| 原生 WorkSwarm 实测包 | `4d760812e23fe870e32a8fba986df5eaf332fd3bdce579f69ebc3052712dd40d` |
| 对应标准交付包 | `e1ca8c8f2ef5e27f518f950fbf62b6da041bc32db118e3d9cde058d74a31faaa` |

提交前只读核对宿主安装目录 `~/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/change-verification/`，manifest 为 1.0.0，25 个运行文件全部与源码、标准包、原生包及解压副本一致。没有更改测试后的载荷、名称、版本、wrapper 或 ZIP；仅补载荷外的确认、测试说明与交付证据。

## 当前用户实际结果

1. WorkSwarm 实际发现并调用插件工具，创建包含两个真实提交的独立演示仓库，中文展示两个直接变更和三个间接候选；保留删除接口的旧调用关系。
2. 用户采用会话中简化的操作：只将 `src/auth.ts` 保存为跳过，备注为“演示测试：本轮只检查结果保存，未验证业务功能。”其余四项保持未验证。实际报告 `e591affed5bf40e7819d980ae4adae1a` 修订 1，数量为 pending 4 / pass 0 / fail 0 / skip 1。
3. WorkSwarm 读取实际磁盘状态并导出中文报告，结果与面板一致；没有按照旧提示词把未录入的失败或第二个跳过编造出来。原文档第三步尚使用两项预期，与后来简化指导不同，现已在载荷外测试说明同步更正，不是保存故障。
4. 新对话列出唯一已有报告，再查询并打开同一报告；修订、两个提交、备注及状态保持一致，没有重建演示或覆盖历史。
5. 只读交叉核对插件现有缓存：报告修订及逐项状态/备注与截图相同。没有重新执行用户操作或修改缓存。用户未上传条目截图，五项的截图列表为空；不声称用户验证了图片上传、内嵌图片或所有状态分支。开发者对这些分支的独立测试另见 TEST_REPORT.md。

基线 `a8d46e73ad3b56a56126e1654cb94f2bc88c963e`，目标 `9e942dd53beed9f74cb5c4aa63325f1349fc830f`。演示项目的未验证状态不是插件流程测试失败，也不能反过来宣称虚构项目已通过业务回归。

十一张原图从当前用户消息直接保存，没有缩放、裁剪或格式转换；图片尺寸、字节与 SHA-256 见 evidence.json。用户明确同意“允许公开上传并提交 PR”，授权在自己的公开 fork 托管并于上游交付 PR 展示。原图已上传至 https://github.com/dashingsss/agentic-hub-plugins/issues/5 ，逐张公开下载核对字节哈希一致。画面含本地演示路径，无可见密钥或面板访问令牌；截图不进入运行 ZIP。

## 英文确认记录

User test confirmation: Wang Jie confirmed the accepted simplified WorkSwarm flow for the current Chinese 变更影响与回归检查台 1.0.0 and requested PR submission after reviewing eleven current-version screenshots; confirmed by Wang Jie; date/time 2026-11-02 14:52:33.138 Asia/Singapore; Task ID AH-20261102-change-verification; version 1.0.0; tested native ZIP SHA-256 4d760812e23fe870e32a8fba986df5eaf332fd3bdce579f69ebc3052712dd40d; canonical ZIP SHA-256 e1ca8c8f2ef5e27f518f950fbf62b6da041bc32db118e3d9cde058d74a31faaa; known runtime blocking issues: none established in the accepted scope; evidence/source: current conversation, screenshot message 2026-11-02T06:47:06.737Z, confirmation message 2026-11-02T06:52:33.138Z, unchanged installed 25-file payload and read-only persisted report cross-check. The user explicitly authorized public upload to dashingsss/agentic-hub-plugins and display in the upstream delivery PR; eleven downloaded attachments match the received original PNG hashes.

这不是 Project Lead Acceptance，也不是 Hub 提交或上架。不填写 Hub 截图或完成日期，不登记 Asset Ledger。
