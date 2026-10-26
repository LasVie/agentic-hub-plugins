# 第三方来源与修改说明

上游：vibe-any/dsh-plugin-save-token；DSH2.4.1，独立适配器1.0.0。
固定提交：e241dbc23288d7d1b6865cf726c8e777c4ce7e08。
来源：https://github.com/vibe-any/dsh-plugin-save-token/tree/e241dbc23288d7d1b6865cf726c8e777c4ce7e08

Original rightsholder statement: Copyright (c) 2026 PlayWithAI.
License: MIT. Full original license: licenses/save-token/LICENSE.
Original src/compress.js and standalone tools.js/store.js file headers: licenses/save-token/UPSTREAM_HEADER.txt.

runtime/recovery.py 将 src/compress.js 的首尾/错误上下文/采样预览思路，以及独立适配器 tools/store 的先存后预览与回取流程移植到 Python。README 改编流程说明。新增持久原文字节快照、SHA-256、真实源行坐标、带类型的 JSON 预览、路径校验、排他导出与中文输出；移除宿主钩子、Shell、内存限定引用、自动去重/清理与计费估算。历史原始文件头中的产品主张不作为本插件承诺。

未打包上游基准数据、第三方测试素材、媒体、构建产物、开发依赖或研究报告；没有适用的上游 NOTICE。此说明不替换完整 MIT 文本，也不为本仓原创部分另行指定统一许可证。
