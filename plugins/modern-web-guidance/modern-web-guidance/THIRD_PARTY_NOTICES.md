# 第三方来源和修改说明

本插件为中文精选适配版，不代表 Google 或上游维护者背书，不使用其标志、图标或字体。

## 指南与技能

- 来源：https://www.npmjs.com/package/modern-web-guidance/v/0.0.196
- 分发仓库：https://github.com/GoogleChrome/modern-web-guidance/tree/4f2b13e25c5815b3f080ca0d983e828d96561a0f
- `package.json` 发布者原文为 `GoogleChrome`。所选指南及 SKILL.md 无单独著作权行，不据此编造作者或年份。
- Apache License, Version 2.0 完整原文：`licenses/modern-web-guidance/LICENSE`。
- 范围：同名 SKILL.md、guides.json 的 12 个索引条目，以及 `data/guides/` 每篇对应的同名指南，逐篇附固定来源。
- 2026-10-27 修改：中文翻译与节选、减少示例、补充边界及检查项；修正 IME 处理顺序、无动画隐藏状态、表格语义和选择器降级注意事项。中文适配由 Gan Mingrui 维护。
- 未发现单独 `NOTICE`。npm 原包的 `THIRD_PARTY_NOTICES` 原样保存在 `licenses/modern-web-guidance/THIRD_PARTY_NOTICES`。其中列出的 TensorFlow、tokenizer、long、seedrandom 等依赖没有进入本版；保留文本用于保存原始归属证据，不表示本版使用它们。

## BM25

- 来源：https://github.com/GoogleChrome/modern-web-guidance-src/blob/8a0a736723558e9ae484e4b6bbf3cc6a8d6ba4ad/src/rag/bm25.ts
- 上游组织 `GoogleChrome`，该文件无单独著作权行。
- Apache License, Version 2.0 完整原文：`licenses/modern-web-guidance-src/LICENSE`。固定源码树未发现单独 NOTICE 或子目录许可证。
- `runtime/bm25.mjs` 于 2026-10-27 去除类型、翻译注释和错误、添加中文双字分词；BM25/RRF 计算保留。

## 排除内容

未打包品牌媒体、语义模型、向量数据、TensorFlow/分词依赖、Chrome 扩展技能、在线安装更新或遥测。原生 Python 工具桥接及 JSON 入口为本次新增，不宣称对整个团队仓库重新许可。指南外链仅用于注明来源，查询时不会访问。
