# 家庭文档台账：来源和授权审查

- Candidate ID：CAND-CLD-247；Task ID：AH-20261026-family-document-registry。
- 负责人：Cai Zhenze；审查日期：2026-10-26。
- 名称对应：Document Vault → 家庭文档台账 → `family-document-registry`；内部身份 `repo:agent-plugin:family-document-registry`。
- 上游固定到 https://github.com/cudjo21/document-vault/tree/1afd4e52feda695406898fafba0577106aebc7a3 ，manifest 版本0.5.3。源码在独立 `/private/tmp/family-document-registry-upstream-20261026` 中只作静态审查，未运行上游脚本。
- `audit-upstream` 使用已存在的 Python3.12.14 测试环境；自动检测仅发现根 MIT 文本，人工另行审查其覆盖范围、实际代码/文档路径和依赖。默认系统 Python 缺 PyYAML，未修改系统环境，改用现有测试环境。

## 实际许可和复用

完整根 LICENSE 是 MIT，原有声明 `Copyright (c) 2026 Ilya`。允许本次有界移植和分发，条件为保留版权、完整许可和免责声明。递归树未发现子目录 LICENSE 或 NOTICE，所选 Python 文件没有独立版权/许可头。未复制品牌、媒体、字体、手机快捷指令、OCR语言模型或真实数据。根许可并不被用来授权外部平台、数据或用户文档。

实际模式 `ported / verified`，不是宣称原创。`runtime/registry.py` 改写上述四个脚本的人员/文档元数据、查找、日期检查、按确认计划复制与摘要核对；Skill/README 改写相应流程和确认要求。完整 MIT 位于内层 `licenses/document-vault/LICENSE`，原文件 SHA-256 `f0a46556162fa59b55fc18b145c3e58e499018693fa76b9bd4a0a9c66c1a4e88`；内层 THIRD_PARTY_NOTICES.md 记录来源、作者、版本、路径和修改。源码核心有显著来源/修改头。其余工具包装、封闭结构和测试为本次适配，不为仓库选择统一许可证。

核心仅用 Python3.11+标准库；保留 POSIX目录描述符、fcntl和O_NOFOLLOW约束，因此此版仅支持 macOS/Linux。openJiuwen SDK由宿主已有环境提供，不随ZIP打包。未使用上游完整工作流的 Pillow/NumPy/OpenCV/img2pdf、Tesseract、Poppler、OCR下载、paid Claude计划或其他API。

## 边界与缺陷处理

核心是持续人员/文档登记、参考日有效期和明确续办/替换状态，材料副本是辅助输出。区别于材料齐备与数据范围预检 `a789d92d40df427a948a5cfe8f7fd50e@1.0.0` 的单次输入预检、办公文档能力包 `58423394089843bcb863654f02ab937a@1.0.3` 的格式转换，以及凭据保险库 `2c760446a88c433aaff1bf94f046701a@1.0.0` 的加密/TOTP。最近 PR46源文快照、PR49状态机及Main PR50字节备份不管理个人文档生命周期。

替换上游不一致的日期算法：只在真实目标月末截断，不能把每月日期都裁为28或月初。缺失/月份精度保持未知，非法日期拒绝，不凭未知到期推断有效替换。替换关系必须显式、同人/类型/国家且无环。登记需完整预览和真实摘要确认，修订冲突拒绝，不删除历史ID。副本由明确ID计划决定，固定计划/台账/文件摘要；排他输出、核对字节，不自动移除失败现场。

没有OCR、自动正文/身份提取、自动脱敏、自动归档/删改原件、PDF合并、法律/旅行规则推断、云同步、后台任务或模型/网络调用。用户文件只按字节读取核对摘要；姓名/路径/日期仍是明文，不提供加密或来源认证。

## 固定审查文件

| 上游路径 | SHA-256 |
|---|---|
| `LICENSE` | `f0a46556162fa59b55fc18b145c3e58e499018693fa76b9bd4a0a9c66c1a4e88` |
| `.claude-plugin/plugin.json` | `b9940bc8a9a1d5bd6a507b1cf15c1337c57974f65432b6887522f119c15ee8be` |
| `README.md` | `511610820f0d6e9e9c00e9ac5643ad94e9adc1a43f0b89725faf6d17aa55d722` |
| `scripts/create_vault.py` | `7a352599c81578ceffd83b3d25108d208cdccb4805de5dd80042181162ba3b09` |
| `scripts/find_docs.py` | `2b344600c6db723bd3658f1c6913704bdbf40a102cf9bbabff227ae92d83b385` |
| `scripts/vault_check.py` | `a6aa8e9ba503a78e1033c6253a06bc87be1ca932db2bb32765f74f85955bbecf` |
| `scripts/make_pack.py` | `7d810b2ba7525738966cfeec3229e30c1c681ca32a549d72dcfbe516e0112bfe` |
| `skills/vault-check-up/SKILL.md` | `3edbfd366336e1e5ad39c0bd67e5f15efddffeb7d0212932485513ea8b5beb4c` |
| `skills/prepare-pack/SKILL.md` | `d0fbf34a28e08ce1e54e8fe594e34234fd3e9d9d09bcc705c4e9af92dc08d9af` |

## 分发检查

功能测试、中文说明/错误/报告与实际ZIP提取复核在 TEST_REPORT.md 和 package-verification.json 中记录；打包前/后须核对本许可、修改声明和 provenance 哈希。用户手工测试仍为独立门槛。本轮只进行本地 Build，不推送、开交付PR、Hub提交或Release。

## 最终测试包逐项复核（2026-10-26）

市场包 `releases/agent-plugin/family-document-registry/1.0.0/family-document-registry-1.0.0.zip` SHA-256 `7434f44e68a3a42850c423019c7449f467c4d89d22896f2dea30087cc174dc56`；原生包 `test-packages/family-document-registry-1.0.0-workswarm.zip` SHA-256 `9316d2dd294f4ea488b65a7a466884d46c99f74dd198bfbc6d9ed29815bb3b37`。已提取两包并比较源/安装目录18文件摘要，完整MIT字节、THIRD_PARTY_NOTICES和实际移植核心来源/修改头均存在；provenance license_evidence与原始MIT哈希相同。包中不含账号、密钥、真实家庭数据、调试缓存或未授权上游素材。

中文交付名/说明/示例/指令/错误/help/生成清单与version1.0.0一致。源、两个提取目录及实际安装目录46项测试各自通过，含真实SDK16次调用；宿主导入及中文UI验证通过。手测目录未初始化；用户人工测试与原始截图尚待收集，不满足Phase3推送/交付PR门槛。宿主模型占位设置未修改，无paid model/API调用。
