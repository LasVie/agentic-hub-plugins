#!/bin/bash
# 改编自 Anthropic math-olympiad（claude-plugins-official@d4226d062928f8d9505dbdeadd10217d23361052，
# plugins/math-olympiad/skills/math-olympiad/scripts/compile_pdf.sh），Apache-2.0，见插件根目录 LICENSE。
# 修改说明（2026-10-27，Vannes Wijaya）：文档类改为 ctexart 以支持中文，仅使用 xelatex 编译；
# 定理环境名称改为中文；去掉重复的 enumitem 加载；注释与报错信息译为中文。
#
# 将 LaTeX 证明正文编译为独立 PDF。
# 用法：compile_pdf.sh <正文.tex> <输出目录>
# 正文文件只包含 \begin{document}...\end{document} 之间的内容（定理、证明、引理），本脚本补上导言区。

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "用法：compile_pdf.sh <正文.tex> <输出目录>" >&2
    exit 2
fi

BODY="$1"
OUTDIR="${2:-.}"
mkdir -p "$OUTDIR"
BASENAME=$(basename "$BODY" .tex)
FULL="$OUTDIR/${BASENAME}_full.tex"

cat > "$FULL" <<'PREAMBLE'
\documentclass[11pt]{ctexart}
\usepackage[margin=1.25in]{geometry}
\usepackage{amsmath, amssymb, amsthm, mathtools}
\usepackage[shortlabels]{enumitem}
\usepackage[colorlinks=true, linkcolor=blue, citecolor=blue]{hyperref}

\theoremstyle{plain}
\newtheorem{theorem}{定理}
\newtheorem{lemma}[theorem]{引理}
\newtheorem{claim}[theorem]{断言}
\newtheorem{proposition}[theorem]{命题}
\newtheorem{corollary}[theorem]{推论}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{定义}
\newtheorem{remark}[theorem]{注}

\renewcommand{\proofname}{证明}

\begin{document}
PREAMBLE

cat "$BODY" >> "$FULL"

cat >> "$FULL" <<'CLOSE'
\end{document}
CLOSE

if ! command -v xelatex >/dev/null 2>&1; then
    echo "未找到 xelatex，无法编译中文 PDF" >&2
    exit 1
fi

cd "$OUTDIR"
xelatex -interaction=nonstopmode -halt-on-error "${BASENAME}_full.tex" >/dev/null
xelatex -interaction=nonstopmode -halt-on-error "${BASENAME}_full.tex" >/dev/null
echo "$OUTDIR/${BASENAME}_full.pdf"
