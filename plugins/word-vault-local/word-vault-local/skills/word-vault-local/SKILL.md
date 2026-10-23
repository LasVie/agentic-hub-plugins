---
name: word-vault-local
description: 按学习者保存英文词条、出现次数与连对掌握状态；在中文交互界面完成四选一、错词复习和导出，无需额外账号。
---

# 词汇练习室

默认使用简体中文。先确认用户指定的现有工作目录，调用 `word_vault_local` 的 help/status；写入时携带最新 expected_revision。用户想操作界面时调用open_ui，展示一个带中文标签的链接，提醒仅在本机使用，不要复制短期凭据到共享记录。

- status：learner（默认 learner-1）；返回该学习者词库、统计与最近练习，不公开未答题目的答案索引。
- add_words：expected_revision, learner, entries:[{term,meaning}]，每次1至50条；重复词元计次，释义修改会重置掌握状态。
- start_quiz：expected_revision, learner, size（1至10，默认4）, wrong_only（可选）；四个不同释义才可出题。
- answer：expected_revision, learner, quiz_id, question_id, option_index（0至3）；答案按本地保存的题目核对，三次连对掌握。
- export_bank：learner；导出该学习者词库。

只根据真实工具返回报告成功。不要把未观测当不存在、把保存草稿当验收、把记录证据当自动评审，也不要调用本插件未提供的宿主操作。原始工作文件或 Git 状态不可擅自改动。按学习者分开保存词条、出现次数与连续答对次数，提供真实计分的四选一和错词复习。释义由用户或当前会话提供，不包含拍照识词、借用的记忆卡设计、第三方词表、自动查词或语音服务。
