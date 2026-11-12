# 来源与查重审查 — 流动效率与持续成本测算

Owner: Nguyen Trung Dung. Reviewed 2026-11-12, Asia/Singapore.
Task AH-20261112-agile-forge-praxis; Candidate CAND-CLD-161.
Mapping: Agile Forge Praxis -> 流动效率与持续成本测算 -> flow-cost-calculator; repo:agent-plugin:flow-cost-calculator.

## 任务与差异

- 关联历史/新增资产 ID：无。开工时（2026-11-12）按名称、描述、标签和范围检索 Asset Ledger（872 行）、Development Tasks（开工前 77 个任务行）和 Plugin Candidates（中英文关键词：流动效率、前置时间、触点时间、价值流、商业论证、回收期、投资回报、盈亏平衡、总拥有成本、运维成本等），没有流动效率或含运行成本的商业论证类资产，也没有同类开发任务或已认领候选。
- 最接近的已有资产及差异：
  - finance-ops（Skill）：用 QuickBooks 导出生成 CFO 简报（含 ROI），输入是会计账目导出，用途是财务简报，不是对一个拟议项目做含运行成本的商业论证，也不涉及流动效率。
  - 数据对账类 Skill（多表合并与对账、科研双源数据对账、月结差异核对等）：校对多份数据的一致性，不是项目或服务指标的测算。
  这些都不是“流动效率 + 含运行成本的商业论证”，因此不构成完整功能覆盖；本审查是按名称、描述和标签的比对，没有安装试用这些资产。
- 复用与独立实现结论：技能说明 ported（上游 MIT，已核实）；两个计算工具为 native（见 NATIVE_DESIGN.md）。上游没有任何可执行代码。

## 材料与授权证据

| 实际使用路径/材料 | 上游 URL 与固定提交/版本 | 适用许可与覆盖范围 | 许可文件及 SHA-256 | 复制/修改情况 |
| --- | --- | --- | --- | --- |
| `skills/flow-efficiency/SKILL.md`（Git blob d999680eaab5482a84fee89cc6a6dbed36d61d43）与 `skills/business-case-laufende-kosten/SKILL.md`（Git blob ae6a94ebefef48b697731e4e3ad53c434f53417d）的技能说明文字（德语） | https://github.com/agileforge01-arch/agile-forge-praxis-plugin @ db7c20facb516b7b7c0c2088882f52368c54468b（`plugin.json` 版本 0.1.0） | MIT，Copyright (c) 2026 Agile Forge (Philip Müller)；根目录 LICENSE 覆盖仓库全部文件，文件无单独版权头 | `licenses/agile-forge-praxis-plugin/LICENSE`，SHA-256 e48574787df82fe240185a85682b0020e066ca48d53810d4ae91d38df7e642be，与上游固定提交 LICENSE（Git blob e5513a6bc43501fd0768eba4f8725553860a8b19，LF 换行，1085 字节）逐字节一致，已用 `git cat-file blob` 取原始字节比对 | 译为简体中文并改写为两个 `SKILL.md`（见下） |
| 两个原生计算工具、有理数运算、输入校验、偏离情形参数、输出格式、README | 无上游 | 本团队原创；NATIVE_DESIGN.md | 不适用 | 无复制 |

代码、提示词、文档、图标、字体、数据、依赖分别核查：

- 代码：上游仓库只有 Markdown、JSON、一个 PNG 图标和许可文本，没有任何可执行代码；`tools/flow_cost.py` 为本团队独立编写。
- 提示词/文档：只改编上述两份技能说明，并参考上游 `README.md`（Git blob a0e651e287d9e016181351367ebda524d7b0f778）里的功能描述和示例问题的思路；本包 README 独立编写。
- 引用出处：上游流动效率技能引用了一项公开测量（Nick Brown，ASOS 技术博客，2023-07-27，63 个团队、十二个月，9% 到 68%、平均 35%）。本团队**没有核实**这一出处，本包把它改写为“上游说明称”，并要求教练在被问到时说明这是上游的说法、且只来自一家公司。
- 图标/图片/字体：上游 `.claude-plugin/icon.png`（133376 字节）未使用；LICENSE 写的是对“软件”的授权，图标这类品牌图形的授权范围不明确，所以不复用。本包没有图标、图片、字体或二进制文件。
- 数据：不随包分发任何数据；工具不联网、不读写文件、不保存任何内容。
- 依赖：只使用 Python 标准库和宿主 openjiuwen SDK，不打包依赖。

## 改动与上游的差异（修改摘要）

- 全文由德语译为简体中文，默认用简体中文回答（用户明确要求其他语言时按用户的要求）；上游是“用用户的语言回答”。
- 上游让模型自己心算；本包改为两个原生工具用精确有理数运算，输出带代入数字的公式，并严格校验输入。上游的拒绝规则（缺失、非数字、≤0、处理工时超出容量、天数 > 5000、每年事项数范围、成本全为 0、收益为 0、金额超过 10 亿）改由工具强制执行。
- 货币：上游用欧元；本包金额不限货币，默认显示“元”，可用 `currency` 参数改标签。校验用例的数字不变。
- 新增参数：杠杆 A 的倍数 `speedup_factor`（上游示例 2）、杠杆 B 的比例 `wait_reduction_ratio`（示例 0.5）、用量偏离 `usage_ratio`（上游 70%）和成本超支 `running_cost_overrun_ratio`（上游写“高出 u”，没有给默认值，本包默认 0.5）。这些是本团队为把上游的示例做成可调参数而做的解读。
- “旋钮拧到底”的比较沿用上游的公式（用量降到 40% 的损失 vs 运行成本再多 100% 的损失）。
- 去掉上游对 Agile Forge 网站工具和课程的指引，以及“与这些工具同一公式”的说法。

## 服务条款与独立限制

- 无外部服务、无账号、无网络访问。
- 商标/署名：本包不是上游作者发布或认可的版本——README 明确写明，THIRD_PARTY_NOTICES.md 写明不授予上游品牌、网站、课程的权利、也不表示上游作者认可本插件；保留 Agile Forge (Philip Müller) 的版权与 MIT 全文。不使用 Agile Forge 的品牌、网站、课程或图标。
- 效果：本包只做算术，不判断好坏，不给正常值或经验法则，不保证任何商业结果；技能说明要求不要编造没有返回的数据。
- 专利、商标和服务条款：独立实现不构成对这些权利的自动豁免；本审查没有对它们作出结论。

## 最终 ZIP 许可复核

复核对象：`releases/agent-plugin/flow-cost-calculator/1.0.0/flow-cost-calculator-1.0.0.zip`（SHA-256 a75d6c68f867bb0f8c06c10a76bb542dc6838ce230f98e00508aa107ab1bebb8，50606 字节）及其内层载荷；原生测试包 `test-packages/flow-cost-calculator-1.0.0-native.zip`（SHA-256 fd00eb2942c388963f6e633e4ca9fca5acf1bcce9e99ae7de89d4b6d937fa802）。复核日期 2026-11-12，已解压后逐项检查：

- `provenance.json` 的 `license_evidence` 指向的 `licenses/agile-forge-praxis-plugin/LICENSE` 存在于 ZIP 内，SHA-256 与记录一致（e48574787df82fe240185a85682b0020e066ca48d53810d4ae91d38df7e642be，1085 字节，LF，无 CR）；其内容与上游固定提交的 LICENSE 原始 Git blob（e5513a6bc43501fd0768eba4f8725553860a8b19）逐字节一致；含完整的授权声明和免责声明。
- 两个复用路径 `skills/flow-efficiency/SKILL.md` 和 `skills/business-case-running-costs/SKILL.md` 都在 ZIP 内，且被 `THIRD_PARTY_NOTICES.md` 逐条列出（上游路径、Git blob、复用方式、修改摘要）。
- `THIRD_PARTY_NOTICES.md` 含上游 URL、固定提交、版权声明 “Copyright (c) 2026 Agile Forge (Philip Müller)”、许可文件路径与哈希、复制范围、修改摘要、未复用清单和授权范围说明。上游没有 NOTICE 文件，所以没有需要保留的 NOTICE（MIT 本身不要求）。
- MIT 不要求在文件里写修改通知；本仓库约定的修改摘要放在 `THIRD_PARTY_NOTICES.md`；两个 `SKILL.md` 的文件头没有上游版权头可保留（上游文件没有）。
- ZIP 内没有图标、图片、字体、压缩包或可执行文件；上游图标未使用。
- 本次未发现未满足的许可条件。尚未解决的事项（不构成许可障碍）：ASOS 引用出处未核实（已改为“上游说明称”）；上游品牌与商标未获授权，也未使用。

`audit-upstream`、`check`、`check-repo`、CI 和 Hub 接受上传都不能代替上述内容复核；本复核是人工逐项核对。`check-repo` 的结果见 TEST_REPORT.md：在本机（`core.autocrlf=true`）工作区直接运行 `check-repo` 会报告“license evidence hash mismatch: LICENSE”，原因是该设置把仓库里部分既有资产的 LICENSE 检出成了 CRLF（本包的 LICENSE 已用 `-text` 规则保护，并已确认与上游 Git blob 逐字节一致）；所以改在保留 LF 的独立克隆里运行 `check-repo`，结果为通过。
