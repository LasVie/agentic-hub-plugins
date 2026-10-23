---
name: git-branch-atlas
description: 只读本地 Git 分支拓扑、父提交与关联工作树，比较两个引用的独有提交和共同祖先，提供可搜索、可点选的中文图谱。
---

# Git 分支全景

默认使用简体中文。先确认用户指定的现有工作目录，调用 `git_branch_atlas` 的 help/status；写入时携带最新 expected_revision。用户想操作界面时调用open_ui，展示一个带中文标签的链接，提醒仅在本机使用，不要复制短期凭据到共享记录。

- status：读取上一份已保存分支图。
- scan：expected_revision, repo_dir（工作区内相对目录，默认.）, limit（1至200）；只读分支、提交parent、泳道与关联工作树。
- compare_branches：repo_dir, base, head；引用先解析完整提交OID，再计算base_only/head_only/merge_bases，不联网取对象。
- export_graph：导出已有图数据。不支持checkout/fetch/commit/删除/文件blame。

只根据真实工具返回报告成功。不要把未观测当不存在、把保存草稿当验收、把记录证据当自动评审，也不要调用本插件未提供的宿主操作。原始工作文件或 Git 状态不可擅自改动。只读显示本地分支拓扑、提交父节点、泳道和关联工作树，比较已有提交的独有数量与共同祖先。伴随既有文件历史工具使用；不重复blame，不切换、拉取、提交或删除分支。
