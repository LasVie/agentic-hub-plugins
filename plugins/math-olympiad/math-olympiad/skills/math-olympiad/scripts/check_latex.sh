#!/bin/bash
# 改编自 Anthropic math-olympiad（claude-plugins-official@d4226d062928f8d9505dbdeadd10217d23361052，
# plugins/math-olympiad/skills/math-olympiad/scripts/check_latex.sh），Apache-2.0，见插件根目录 LICENSE。
# 修改说明（2026-10-27，Vannes Wijaya）：中文排版需要 xelatex 与 ctex 宏包，改为检测二者；注释译为中文。
# 若可编译中文 LaTeX 则退出码为 0，否则为 1。SKILL.md 据此决定是否提供 PDF 编译。
command -v xelatex >/dev/null 2>&1 || exit 1
command -v kpsewhich >/dev/null 2>&1 || exit 1
kpsewhich ctexart.cls >/dev/null 2>&1
