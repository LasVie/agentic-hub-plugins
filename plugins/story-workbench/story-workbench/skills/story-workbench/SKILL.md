---
name: story-workbench
description: 管理本地小说项目、人物、章节与修订历史；在中文编辑器中添加可重新定位的原文批注，不自动生成或改写正文。
---

# 小说创作台

默认使用简体中文。先确认用户指定的现有工作目录，调用 `story_workbench` 的 help/status；写入时携带最新 expected_revision。用户想操作界面时调用open_ui，展示一个带中文标签的链接，提醒仅在本机使用，不要复制短期凭据到共享记录。

- status：读取项目、人物、章节、原文批注与修订历史。
- create_project：expected_revision, name；一个工作目录一个项目，不覆盖已有项目。
- save_character：expected_revision, id, name, role, goal；保存/修改人物设定。
- save_chapter：expected_revision, id, title, content, chapter_revision（更新已有章节时必填其hash）；保存旧版本并重新定位批注。
- annotate：expected_revision, chapter_id, chapter_revision, quote, note, start_hint/end_hint（可选，JavaScript UTF-16索引）；仅可批注已保存原文。
- resolve_annotation：expected_revision, annotation_id；标记解决并保留记录。
- export_project：导出完整项目与历史；不生成正文。

只根据真实工具返回报告成功。不要把未观测当不存在、把保存草稿当验收、把记录证据当自动评审，也不要调用本插件未提供的宿主操作。原始工作文件或 Git 状态不可擅自改动。保存小说项目、人物设定、章节正文、原文批注与旧版本。作为既有小说写作技能的本地编辑伴随工具，不重复写作语料或自动生成正文，不包含上游整套后端与智能体。
