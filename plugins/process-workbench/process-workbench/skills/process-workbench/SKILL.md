---
name: process-workbench
description: 校验多阶段流程模板，冻结每次运行快照，以实际文件 SHA-256 记录环节完成证据，提供中文交互看板。
---

# 流程执行台

默认使用简体中文。先确认用户指定的现有工作目录，调用 `process_workbench` 的 help/status；写入时携带最新 expected_revision。用户想操作界面时调用open_ui，展示一个带中文标签的链接，提醒仅在本机使用，不要复制短期凭据到共享记录。

- status：读取当前模板与运行记录。
- validate_template：template 为 JSON对象：process:{name}, phases:[{id,name,links:[{id,name,prompt,on_success}]}]；支持 next/end/break/goto:环节id。
- save_template：expected_revision, template；校验后保存，既有运行不会换用新模板。
- start_run：expected_revision, run_id；创建唯一运行编号并冻结模板。
- complete_step：expected_revision, run_id, step_id, note, evidence_files（1至10个工作区内相对文件路径）；记录真实文件SHA-256后流转，不能跳步骤。
- resume_run：expected_revision, run_id；显式恢复暂停运行。
- export_process：导出模板、快照与文件证据；不执行命令、模型或代理。

只根据真实工具返回报告成功。不要把未观测当不存在、把保存草稿当验收、把记录证据当自动评审，也不要调用本插件未提供的宿主操作。原始工作文件或 Git 状态不可擅自改动。保存用户定义的多阶段JSON模板与独立运行快照，校验环节流转，以工作目录内的真实文件哈希记录完成证据，提供交互看板。没有后台调度、自动模型评分、自动智能体或任意命令执行。
