# 第三方来源与修改声明

本插件包含对 Document Vault 有界元数据/有效期流程的移植与改写。

- 原始项目：https://github.com/cudjo21/document-vault
- 固定版本：0.5.3；提交 `1afd4e52feda695406898fafba0577106aebc7a3`。
- 上游原有权利人声明：**Copyright (c) 2026 Ilya**。完整原文见 `licenses/document-vault/LICENSE`，保留 MIT 许可及免责声明。
- 原始路径：`scripts/create_vault.py`、`scripts/find_docs.py`、`scripts/vault_check.py`、`scripts/make_pack.py`；`skills/vault-check-up/SKILL.md`、`skills/prepare-pack/SKILL.md` 及 README 的元数据流程。
- 实际改写路径：`runtime/registry.py`、`skills/family-documents/SKILL.md`、`README.md`。所查原始 Python 文件没有独立版权/许可头；完整根许可保留，运行核心首部列明来源与修改。
- 修改日期：2026-10-26。新建中文 openJiuwen 工具与界面声明；仅移植持续人员/文档台账、有效期/新近程度检查及经批准的副本流程；重新实现严格 JSON、精确月末、未知日期、显式替换关系、修订历史、预览摘要和文件边界。
- 不包含上游 OCR、图片处理、PDF 合并、云盘/手机快捷指令、自动归档/整理或任何真实家庭资料。无第三方图标、字体或数据；未发现适用的上游 NOTICE 文件，不编造额外 NOTICE。
- 核心仅使用 Python 标准库。外部已安装的 openJiuwen SDK 属于宿主运行依赖，不随包重新分发。模板与新工具包装未据此改变整个仓库的许可。

本产品不是上游官方出品；本地台账未加密，也不构成文档真实性、法律资格或安全保证。
