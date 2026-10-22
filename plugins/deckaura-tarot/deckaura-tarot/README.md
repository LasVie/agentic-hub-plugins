# 塔罗牌查询与抽牌

修改说明：2026-10-22，版本 1.0.4 将展示信息和使用说明改为中文；此后已进一步将运行 Skill、参考文档、四类牌义、CLI 和 Python 工具的人类可读文本中文化；技术标识、抽牌算法与原始许可保留。移植维护者 Cai Zhenze；上游作者与权利人为 Deckaura。

使用本地 78 张牌的数据集查询牌义、抽取不重复的牌，并生成六种牌阵。适合反思、日记与创作；牌义数据和模型给出的情境解读应分开呈现。

## 主要功能

- 查询指定牌的正位或逆位牌义和来源链接。
- 按指定种子复现不放回抽牌，返回牌名、方向、位置与牌义。
- 支持 `daily`（1 张）、`three-card`（3 张）、`decision`（5 张）、`relationship`（6 张）、`celtic-cross`（10 张）、`yes-no`（1 张）。
- 校验 78 张牌的数据完整性并返回数据集 SHA-256。

## 安装与依赖

需要后端进程 PATH 中存在 Node.js >=18，以及提供 `openjiuwen.core.foundation.tool.Tool` 和 `ToolCard` 的 openJiuwen/WorkSwarm Python 宿主。无需安装 npm 包，也不需要外部账号、API 密钥或网络服务。CLI 可以独立由 Node.js 运行；自然语言解读另需宿主已配置的模型。

在扩展面板导入 `deckaura-tarot-1.0.4-native-test.zip`，确认版本 `1.0.4`、一个 Skill 和一个工具。在目标会话选中插件后调用 `deckaura_tarot`。若缺少 Node.js，将其加入后端 PATH 并重启后端。

市场包 `deckaura-tarot-1.0.4.zip` 含 `deckaura-tarot/plugin.yaml` 和 `deckaura-tarot/deckaura-tarot/manifest.json`。本地测试 ZIP 直接包含相同载荷，适用于宿主扩展导入；两者哈希不同。

## 使用示例

向智能体提出：“查询 The Star 的逆位牌义，并给出来源”；或“抽三张牌，关闭逆位，种子用 manual-demo，说明结果只用于反思”。原生工具参数示例：

```json
{"action":"lookup","card":"The Star","orientation":"reversed"}
{"action":"draw","count":3,"reversals":false,"seed":"manual-demo"}
{"action":"spread","spread":"celtic-cross","seed":"manual-demo"}
{"action":"validate"}
```

每次调用返回含 `ok` 的 JSON。失败时返回 `ok: false` 及错误说明。抽牌数量必须为 1–78 的整数；`reversals` 必须是布尔值，方向只能是 `upright` 或 `reversed`。种子长度为 1–256 字符，不含 NUL，且不得以 `--` 开头；不要把私人问题作为种子。未知字段会被拒绝。未指定种子时先使用系统熵，再执行可复现的伪随机洗牌，不提供密码学随机保证。

## 独立 CLI

在载荷目录执行：

```sh
node skills/tarot-reading/scripts/tarot.mjs validate
node skills/tarot-reading/scripts/tarot.mjs lookup "The Star" --orientation reversed
node skills/tarot-reading/scripts/tarot.mjs spread three-card --seed manual-demo --reversals false
```

原生适配器增加严格参数校验和十秒超时。CLI 的算法和参数行为保持上游实现，位置、帮助与错误文本已中文化。它对部分无效方向或选项会静默接受，也无法正确解析以 `--` 开头的种子；直接使用 CLI 时请遵循以上合法参数。

## 适用范围与限制

本工具提供牌义资料和反思素材，不能证明事实、保证未来事件或替代专业建议。牌名、数据字段、牌阵 ID 与结构化协议值保留原值；正位、逆位、爱情及事业牌义是原英文摘要的中文翻译，解读默认使用中文。中文牌名应先对应到准确的英文 `card_name` 再调用工具；CLI 不支持中文别名直接查询。工具本身不访问网络，也不调用模型。

## 来源与许可

[Deckaura Tarot](https://github.com/gokimedia/claude-skill-tarot/tree/804c54558375416fd4fce605238927f39bbac1a2)，上游版本 1.0.0。完整 MIT 许可见 `licenses/deckaura-tarot/LICENSE`，数据来源与覆盖范围见 `THIRD_PARTY_NOTICES.md` 及随包来源记录。不包含上游标志、字体或牌面图片，也不表示获得上游背书；本说明不为仓库新增材料另行指定统一许可。
