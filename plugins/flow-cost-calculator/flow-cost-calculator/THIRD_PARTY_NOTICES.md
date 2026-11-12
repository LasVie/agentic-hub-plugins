# 第三方声明

## Agile Forge Praxis

- 上游：https://github.com/agileforge01-arch/agile-forge-praxis-plugin ，固定提交 `db7c20facb516b7b7c0c2088882f52368c54468b`（`plugin.json` 版本 0.1.0）。
- 版权声明：Copyright (c) 2026 Agile Forge (Philip Müller)。
- 许可：MIT。完整许可文本（含免责声明）随包提供：`licenses/agile-forge-praxis-plugin/LICENSE`，与上游固定提交的 `LICENSE` 逐字节一致（SHA-256 `e48574787df82fe240185a85682b0020e066ca48d53810d4ae91d38df7e642be`，Git blob `e5513a6bc43501fd0768eba4f8725553860a8b19`，LF 换行，1085 字节）。
- 实际复用范围：上游的两份技能说明——`skills/flow-efficiency/SKILL.md`（Git blob `d999680eaab5482a84fee89cc6a6dbed36d61d43`，德语）和 `skills/business-case-laufende-kosten/SKILL.md`（Git blob `ae6a94ebefef48b697731e4e3ad53c434f53417d`，德语）。它们被译成简体中文并改写为 `skills/flow-efficiency/SKILL.md` 和 `skills/business-case-running-costs/SKILL.md`：保留输入问询、公式、拒绝输入的规则、解读话术、局限说明和校验用例；`README.md`（Git blob `a0e651e287d9e016181351367ebda524d7b0f778`）里的功能描述与使用示例也被参考。
- 修改摘要：全文译为简体中文并默认用简体中文回答；上游让模型自己心算，本包改为由 `flow_cost_flow_efficiency` 和 `flow_cost_business_case` 两个原生工具用精确有理数运算并返回带代入数字的公式；欧元改为不限货币的数字（默认显示“元”）；增加偏离情形的可调参数（用量比例、成本超支比例）和货币标签；上游引用的 ASOS 测量数字改写为“上游说明称”，本包没有核实；上游“金额超过 10 亿欧元多半是输入错误”的提示改为不限货币的 10 亿上限；去掉对 Agile Forge 网站工具的指引。
- 未复用：上游 `.claude-plugin/icon.png`、`.claude-plugin/plugin.json` 的清单、Agile Forge 的商标与网站（agile-forge.com、praxis.agile-forge.com）、其收费课程与工具。本插件的 README 与工具代码为独立编写。
- 授权范围说明：MIT 许可覆盖上游的文字；不授予上游图标、品牌、网站或课程的权利，也不表示上游作者认可本插件。

## 本插件独立编写的部分

- `tools/flow_cost.py`：两个原生计算工具，为本团队独立编写，不含上游代码。公式取自上游说明文字里写出的算法；有理数运算、输入校验、错误处理、偏离情形参数和输出格式是本团队的实现。
- 本插件不联网、不读写任何文件、不保存任何内容，也不附带图片、字体、数据集或二进制文件。

## 效果声明

本插件只做算术，不判断好坏，不能替代财务、控制或流程分析，也不保证任何商业结果。
