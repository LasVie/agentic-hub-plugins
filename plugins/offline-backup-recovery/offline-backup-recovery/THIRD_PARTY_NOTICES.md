# 第三方来源与许可

本插件“离线备份与恢复”适配 xiaoyuyu6420/dsh-backup 0.13.4 的手动备份、摘要校验、预览与恢复流程。

- 固定来源：https://github.com/xiaoyuyu6420/dsh-backup/tree/608ed261adcbfde11acab00207f76912fa207c1b
- Original rightsholder notice: Copyright (c) 2026 xiaoyuyu6420
- License: MIT；完整原文保存在 `licenses/dsh-backup/LICENSE`，包括版权、许可条件及免责声明。
- 适配路径：`runtime/backup.py`、`README.md`、`skills/directory-backup/SKILL.md`。
- 修改（2026-10-26）：Python 标准库实现与 WorkSwarm 工具；中文说明与错误；有界结构化 ZIP/清单；显式目录；排他创建；仅恢复到新目录。替换文本 tar 清单解析，移除 DSH 服务、自动任务、清理、同步、会话修复、凭据库及原地恢复。
- 未打包上游 React 客户端、图片、救援控制台或 npm/DSH 依赖。未发现适用上游 NOTICE 文件。

没有上游或平台官方背书。仓库自有新增材料的统一许可由项目负责人另行决定；此说明不替换原始许可。
