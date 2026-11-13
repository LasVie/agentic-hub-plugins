# 第三方声明

## Adds Up

- 上游：https://github.com/Aphro4266/adds-up ，固定提交 `501af9e40e709780849cbedfd73af45d1eb7c6bd`（2026-10-24；上游 `plugin.json` 版本 0.2.0）。
- 版权声明：Copyright (c) 2026 Murat Matur。
- 许可：MIT。完整许可文本（含免责声明）随包提供：`licenses/adds-up/LICENSE`，与上游固定提交的 `LICENSE` 逐字节一致（SHA-256 `8e64120969b71eee850ba6cfccf0245dd0c72cb7c8118dc7665f38a37c00b501`，Git blob `9f1615b1aabc1df5a22b62aa0a1ddf8b86afa477`，LF 换行，1068 字节）。上游没有 NOTICE 文件。
- 实际复用范围：
  - `skills/check/scripts/adds_up.py`（Git blob `e4cf7d0f2351a7f49ce96dad0d487667b213e27c`，122101 字节）：移植为本包 `tools/adds_up.py` 的前半部分——数字解析、表格规则、正文规则、Office 与 PDF 提取、GRIM 的逻辑保持上游原样，按下面的修改摘要增加中文支持、中文输出和安全上限。上游文件没有单独的版权头；该文件头部的说明里写明了来源。
  - `skills/check/SKILL.md`（Git blob `021aabf7c1da37825260408d281132dca3498835`）：译为简体中文并改写为 `skills/document-number-check/SKILL.md`。
  - `skills/check/references/checks.md`（Git blob `0cd1c3bf0e19384706ddd48c7bc8e6fd4b9b5446`）：译为简体中文并增补中文材料常见的几项，成为 `skills/document-number-check/references/checks.md`。
  - `README.md`（Git blob `3594d96eec2e0fc54161bc776d49657a8b54a22f`）里的功能描述与示例思路被参考；本包 README 独立编写。
- 修改摘要：
  1. 增加中文支持：合计/总计/总额/共计/汇总/小计/平均/均值/其中等标签；“2026年3月5日”日期、“星期三/周三/礼拜三”星期、“共 14 周”之类的时长、全角百分号和括号、“N 人中有 n 人，占 p%”和“从 12% 升至 15%，增长 3%”的说法；“2025年”“1月”等年份、月份标签不当作数字；“总计划”不当作合计。英语、德语、土耳其语、法语、西班牙语的识别全部保留。
  2. 把全部输出（线索、说明、错误、报告标题、GRIM 结论）改为简体中文；位置标签（`P12`、`T3 R4 C2`、`Sheet!B7`）和线索类型名（如 `total-row`）保持上游写法。
  3. 增加安全上限：文件大小、压缩包条目数和解压后大小；拒绝含 DOCTYPE 或 ENTITY 声明的 XML。
  4. 去掉命令行入口（`argparse`、`main`），改成可直接调用的 `run_extract()`、`run_grim()`；增加两个原生工具类（`adds_up_extract`、`adds_up_grim`）、输入校验、并发保护、输出截断和错误处理。
  5. 技能说明由“在 Claude 里用 `python3 ${CLAUDE_SKILL_DIR}/scripts/adds_up.py` 运行脚本”改为调用两个原生工具；去掉德语、土耳其语报告用语对照表，报告固定用中文用语（错误、冲突、待确认）。
- 未复用：上游 `.claude-plugin/icon.png`、`.claude-plugin/plugin.json` 的清单、`PRIVACY.md`、`examples/` 示例文件和 `tests/` 测试代码。本包的 README 和测试为独立编写。
- 授权范围说明：MIT 许可覆盖上游的代码和文字；不授予上游图标、名称或商标的任何权利，也不表示上游作者认可本插件。

## 本插件独立编写的部分

- `tools/adds_up.py` 文件末尾的两个原生工具及其输入校验、并发保护、输出截断和错误处理。
- `skills/document-number-check/` 中为中文材料增补的内容，以及 README。
- 本插件不联网、不写任何文件、不保存任何内容，也不附带图片、字体、数据集或二进制文件。

## 效果声明

本插件只列出算术线索并帮助核对，不能替代审计、财务或法务复核，也不保证文档里没有别的错误。
