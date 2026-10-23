# 第三方来源与修改说明

## Fisica（MIT）

- 原作者与版权声明：**Copyright (c) 2026 Carlotess**。
- 来源：<https://github.com/Carlotess/fisica>。
- 固定提交：`f53864e09df2a7d91f5c2a86ac60b4ac7e987bbf`；上游插件版本 `1.0.0`。
- 完整原始许可：[licenses/fisica/LICENSE](licenses/fisica/LICENSE)。本包保留原始版权、许可、条件与免责声明，不以团队署名替换它们。

| 上游文件 | 本包改编文件 | 修改说明 |
| --- | --- | --- |
| `README.md` | `README.md` | 依据实际适配功能重写中文安装、使用与限制说明。 |
| `skills/fisica/SKILL.md` | `skills/physics-review/SKILL.md` | 简体中文本地化、宿主工具调用、图示不确定性分支、两项独立检查、带编号的假设审校。 |
| `skills/fisica/references/errores-comunes.md` | `skills/physics-review/references/common-errors.md` | 简体中文本地化，并补充动量守恒、滚动摩擦功等结论的适用条件。 |
| `skills/fisica/scripts/ampliar.py` | `scripts/prepare_figure.py` | 保留裁剪、LANCZOS 放大及可选锐化/对比度思路；新增中文 JSON/命令行、输入尺寸限制、EXIF 方向校正、元数据移除和输出拒绝覆盖。 |

适配日期：2026-10-23。上游未包含适用的独立 NOTICE 文件。本包没有使用上游图标、外部教材图片或测试截图。上述改编不表示原作者为本次适配或任何解题结果背书。

## 外部运行依赖

图像工具通过 `requirements-local.txt` 声明 Pillow `12.2.0`。Pillow 和其二进制依赖不随本 ZIP 分发；应在本任务独立 Python 环境安装。Pillow 原有 MIT-CMU 及发行版包含的其他依赖许可继续适用，参见其完整发行许可：<https://github.com/python-pillow/Pillow/blob/12.2.0/LICENSE>。不使用第三方名称宣传本插件得到其认可。

WorkSwarm/openJiuwen 由宿主提供，也不随本 ZIP 分发。本地工具不需要网络服务、账号、模型权重或密钥；物理推导与读图仍取决于宿主模型和相应的图像查看能力。
