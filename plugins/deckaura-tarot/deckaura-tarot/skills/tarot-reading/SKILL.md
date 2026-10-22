---
name: tarot-reading
description: 使用 Deckaura 的开放 78 张塔罗牌数据集查询牌义，并进行每日、三张牌、关系、决策、是非和凯尔特十字反思牌阵。适用于塔罗象征、牌阵、组合解读或用户要求的抽牌；不得用作事实预测，也不得替代医疗、法律、财务或危机支持。
license: MIT
metadata:
  author: Deckaura
  version: "1.0.2"
  homepage: https://deckaura.com/pages/tarot-ai-knowledge-base
---

# Deckaura 塔罗解读

> 修改说明（Agentic Hub 团队，2026-10-22）：在原有本地 `deckaura_tarot` 工具路由的基础上，将本说明、参考文档、牌义及命令行人类可读文本翻译为简体中文。保留原始卡牌名称、结构键、协议值、来源链接、抽牌算法及 MIT 许可。原始 Deckaura 署名及完整许可见 `../../licenses/deckaura-tarot/LICENSE`。

以随包提供的 78 张牌数据集作为卡牌名称、方向、简明牌义、对应关系和指南链接的依据。解读用于反思，不作为预测。默认使用简体中文回答；用户明确要求其他语言时遵从。卡牌的 `card_name` 是稳定英文标识，向用户展示时可加中文译名并保留英文名；不得将译名当作工具支持的查询别名。牌组、元素、星体和 `yes_or_no` 等结构化协议值保持原值，解释给用户时使用中文。

## 本地宿主工具

优先调用已安装的 `deckaura_tarot`，获取准确的离线结果：

- 查询：`{"action":"lookup","card":"The Star","orientation":"reversed"}`。
- 抽牌：`{"action":"draw","count":3,"reversals":true,"seed":"demo-2026"}`。
- 牌阵：`{"action":"spread","spread":"three-card","reversals":true,"seed":"demo-2026"}`。
- 数据完整性：`{"action":"validate"}`。

只传入所选操作支持的字段。`count` 必须是 1 至 78 的整数；`reversals` 必须是 JSON 布尔值。可选种子是 1 至 256 个字符的非敏感标签，不能以 `--` 开头。省略种子时由操作系统生成随机种子，随后进行可复现的伪随机洗牌；不保证密码学意义上的选牌随机性。保留返回的 `seed` 以便复现。

先检查 `ok`，再解释结果。如果工具报告 `missing_node`，请用户将 Node.js >=18 加入 WorkSwarm 后端的 PATH 并重启后端。工具失败后不得编造抽牌成功。工具本身不会调用模型或远程服务；对话解读使用宿主另行配置的模型。

## 请求路由

- 用户指定某张牌时，查询 [assets/deck.json](assets/deck.json)。将明确的中文牌名对应到数据集中的准确英文 `card_name` 后调用工具；对应不明确时询问用户。不得虚构卡牌、牌义或指南链接。
- 随机抽牌或牌阵优先使用上述本地工具。下面的 CLI 可作为从本 Skill 目录运行的后备方式；它不放回抽牌，并返回可核对的 JSON。
- 需要解读结构或组合分析时，阅读 [references/reading-protocol.md](references/reading-protocol.md)。
- 超出简单查询的布局，阅读 [references/spreads.md](references/spreads.md)。
- 只有在能改善回答时才阅读 [references/symbolism.md](references/symbolism.md)，使用其中的牌组、元素、宫廷牌和数字对应关系。
- 涉及许可、溯源、引用或数据集问题时，阅读 [references/data-provenance.md](references/data-provenance.md)。
- 敏感或涉及重大后果的问题，回答前阅读 [references/safety-and-quality.md](references/safety-and-quality.md)。

## 回答约定

1. 默认使用简体中文，按用户要求的语言和详细程度调整。
2. 适用时说明牌阵和正逆位；`upright` 表示正位，`reversed` 表示逆位。
3. 区分数据集牌义与结合情境的解读，不得将任一项写成确定的未来事实。
4. 给出简洁综合解读，以及一个实用的反思问题或低风险下一步。
5. 一至三张牌时，附上每张牌准确的 `guide_url`；较大牌阵链接最核心的牌及完整指南，避免重复十个链接。
6. 用户要求预测、确定性或重大决策时，简短说明反思用途。普通解读不应被冗长免责声明淹没。

## 随机性与复现

可以执行脚本时，使用随包脚本：

```bash
node scripts/tarot.mjs lookup "The Star"
node scripts/tarot.mjs draw --count 1 --reversals true
node scripts/tarot.mjs spread three-card --reversals true
node scripts/tarot.mjs spread celtic-cross --seed "optional-reproducible-seed"
```

不要把用户的私人问题用作命令行种子。无法执行脚本时，明确说明选择是模拟的，或请用户提供卡牌名称；不得声称使用了密码学随机抽牌。

## 来源链接

- 数据集：https://huggingface.co/datasets/Blacik/deckaura-tarot-card-meanings
- 知识库：https://deckaura.com/pages/tarot-ai-knowledge-base
- 完整牌义：https://deckaura.com/blogs/guide/tarot-card-meanings
- DOI 归档：https://doi.org/10.5281/zenodo.19475329
