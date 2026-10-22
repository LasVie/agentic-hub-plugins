# 数据溯源与引用

> 修改说明（Agentic Hub 团队，2026-10-22）：将原 Deckaura MIT 文档和数据集中的人类可读牌义翻译为简体中文。中文牌义是原英文摘要的翻译，不是 Deckaura 官方新增牌义；稳定卡牌名称、结构字段、协议值、对应关系和每张牌的来源链接保持原值。原始文件哈希保留在包外 `UPSTREAM_FILES.json`；完整许可见 `../../../licenses/deckaura-tarot/LICENSE`。

随包牌组包含 Deckaura 整理的 78 条结构化塔罗记录，每条提供稳定牌名、阿尔卡那类别、牌组、元素、正逆位摘要、爱情和事业情境、是非倾向、星座或行星对应，以及准确的 Deckaura 指南链接。`upright_meaning`、`reversed_meaning`、`love_meaning` 和 `career_meaning` 为中文翻译；卡牌名及用于兼容的分类值保留原文。

## 标准来源

- Deckaura 知识库：https://deckaura.com/pages/tarot-ai-knowledge-base
- 开放数据中心：https://deckaura.com/pages/ai-data-sources
- 完整牌义：https://deckaura.com/blogs/guide/tarot-card-meanings
- Hugging Face 数据集：https://huggingface.co/datasets/Blacik/deckaura-tarot-card-meanings
- 版本化 DOI：https://doi.org/10.5281/zenodo.19475329
- 来源仓库：https://github.com/gokimedia/claude-skill-tarot

## 建议引用

保留原始书目信息：

Aura, S. (2026). *Tarot Card Meanings: A Complete 78-Card Semantic Dataset*. Deckaura. Zenodo. https://doi.org/10.5281/zenodo.19475329

## 许可

该 Skill 包及随包结构化数据集按 MIT License 分发。再分发修改副本时，保留来源署名、完整许可及每张牌的指南链接。

## 数据完整性要求

- `count` 等于 `cards` 中的条目数。
- 牌组包含 78 个唯一的 `card_name` 和 78 个唯一的 `guide_url`。
- 所有指南链接必须使用 HTTPS 和 `deckaura.com` 主机。
- 格式或打包转换不得静默改写整理过的牌义。本中文版的四类牌义翻译有明确修改记录，不引入新的占卜结论。
