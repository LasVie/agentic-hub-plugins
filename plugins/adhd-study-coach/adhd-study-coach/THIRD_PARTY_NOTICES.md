# 第三方声明

## ADHD Study Coach

- 上游：https://github.com/itsAalaa7/adhd-study-coach ，固定提交 `eec04896c443b76d34546698905ec0911fa3f17f`（`plugin.json` 版本 0.2.0）。
- 版权声明：Copyright (c) 2026 Aalaa Fahiem。
- 许可：MIT。完整许可文本（含免责声明）随包提供：`licenses/adhd-study-coach/LICENSE`，与上游固定提交的 `LICENSE` 逐字节一致（SHA-256 `d9487d7e75e16293408fe8556dc940f400c0d6e7fbeed42a7d149a5be43fd748`，Git blob `b0ed61b8356ec0529ba1ca429dc38074ca34e688`）。
- 实际复用范围：上游的两份教练说明文字——`agents/adhd-study-coach.md`（Git blob `a2287fe5ccce6891e575dbd98df2519090f8fdac`）和 `claude-ai-skill/adhd-study-coach/SKILL.md`（Git blob `5670b9b1dc456ce55d28e4f5d6a88289c50ff947`）。它们被翻译成简体中文并改写为 `skills/adhd-study-coach/SKILL.md`：保留环节 0–4 的结构、评分与改期规则、各条教学规则、反思问题、闪卡格式和对“是否科学”的回答，以及其中引用的研究出处名称。
- 修改摘要：全文译为简体中文；进度卡由英文改为中文固定格式，并改由 `adhd_card_` 原生工具读写和计算日期（上游由模型自己写卡和算日期）；去掉上游依赖本地文件、Claude Code 工具（Read/Write/Bash/PowerShell）和 `${CLAUDE_PLUGIN_DATA}` 的部分；增加“不是临床工具、不诊断”的边界说明；改动的具体规则和理由见 `SOURCE_REVIEW.md` 所在的仓库记录。
- 未复用：上游的 `README.md`、`RESEARCH.md`（仅在说明里以链接指向，没有随包分发）、`SECURITY.md`、`CHANGELOG.md`、`.claude-plugin/` 下的清单和图标、`docs/` 网站、`universal/` 与 `integrations/` 下的其他平台提示词，以及 `claude-ai-skill` 压缩包。本插件的 README 与原生工具代码为独立编写。
- 授权范围说明：MIT 许可覆盖上游的文字和代码；不授予上游图标、网站或其引用的第三方论文内容的权利。上游文字里列出的研究（例如 Roediger & Karpicke 2006、Dunlosky et al. 2013）只以作者和年份引用，作者结论属于各论文的作者，本插件没有复制论文正文。

## 本插件独立编写的部分

- `tools/study_card.py`：三个原生计算工具（读取进度卡、复习改期、记录学习），为本团队独立编写，不含上游代码。间隔序列 1→3→7→16→35→90 天以及“扎实 / 不稳 / 空白”的改期规则来自上游的说明文字；“不稳”按“间隔不变、明天再复习”的具体实现是本团队的解读。
- 本插件不联网、不读写任何文件、不保存任何内容，也不附带图片、字体或数据集。

## 医疗与效果声明

本插件是学习辅助，不是临床工具，不提供诊断或治疗，不能替代专业医疗，也不承诺提高成绩。
