# Third-party notices

## Deckaura Tarot

- Source: https://github.com/gokimedia/claude-skill-tarot
- Fixed commit: `804c54558375416fd4fce605238927f39bbac1a2`; upstream version 1.0.0.
- Original notice: **Copyright (c) 2026 Deckaura**.
- License: MIT; full text including disclaimer is bundled at `licenses/deckaura-tarot/LICENSE`.
- Covered files: `skills/tarot-reading/SKILL.md`, `skills/tarot-reading/scripts/tarot.mjs`, `skills/tarot-reading/assets/deck.json`, and all five Markdown files under `skills/tarot-reading/references/`.
- Upstream `references/data-provenance.md` explicitly licenses the package and bundled structured dataset under MIT and asks to preserve source attribution/per-card guide URLs. These are retained. Suggested citation: Aura, S. (2026), *Tarot Card Meanings: A Complete 78-Card Semantic Dataset*, Deckaura, https://doi.org/10.5281/zenodo.19475329.
- Modifications: Skill instructions add native host-tool routing and describe its input/error contract; the original script, curated dataset and reference files are unchanged. The manifest, Python adapter and adaptation README are new repository work.
- No upstream NOTICE exists in the pinned recursive tree. No upstream icon/logo SVG, external fonts, card images, external model service or npm dependency is included.

This adaptation preserves upstream rights and attribution; it does not assert trademark permission or official endorsement and does not assign a unified license to repository-owned additions.


## 中文版本修改说明（2026-10-22）

版本 `1.0.3` 将展示信息与使用说明中文化；保留技术标识、原始许可和署名。 本说明不替代或改变上方原始许可条款。


## 运行内容完整中文化（2026-10-22）

上方英文修改摘要记录此前版本；本次进一步修改的范围如下，原始版权、许可与来源署名均保留：

- `skills/tarot-reading/SKILL.md`：中文使用指令、默认中文解读、中文牌名到准确英文标识的路由说明。
- `skills/tarot-reading/references/` 下全部五份文档：中文流程、牌阵、象征、安全边界与溯源说明。
- `skills/tarot-reading/assets/deck.json`：仅将 78 张牌的 `upright_meaning`、`reversed_meaning`、`love_meaning`、`career_meaning` 共 312 项摘要译为中文；没有增加或删除结构字段，原始牌名、分类协议值、对应关系及每张牌的指南链接保持不变。中文内容为翻译，并非 Deckaura 官方新牌义。中文数据文件 SHA-256：`43ba47133d04091e31fb220aec7bcd858cf87a0f86a9496a104b5fc20ab95840`。
- `skills/tarot-reading/scripts/tarot.mjs`：中文位置、帮助与错误文本；抽牌、种子、洗牌、正逆位和参数逻辑不变。
- `tools/tarot_tool.py`：中文工具说明、参数帮助及错误；输入限制、十秒超时和本地执行边界不变。

MIT 原文完整保留于 `licenses/deckaura-tarot/LICENSE`，SHA-256：`2a870b98a936750e931a5833bc362778ae474aa3042532609a97cbe1b09cb654`。没有添加第三方材料，也没有引入网络服务、模型或 npm 依赖。原始文件哈希与译后文件哈希分别留存在仓库 `UPSTREAM_FILES.json`；本说明不改变任何许可条款或负责人。


## 中文运行版本 1.0.4（2026-10-22）

按最新中文交付要求翻译实际 Skill、工具说明、帮助及可读提示；模板与资料按实际复用范围记录。技术标识和原始法律声明保持原值。最终包及宿主验证范围见资产测试记录。
