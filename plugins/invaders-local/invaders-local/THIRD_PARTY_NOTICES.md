# 第三方许可与修改记录

- 上游：Invaders 0.1.1，https://github.com/nison/claude-invaders
- 固定提交：`d332a1fc97e28e86042fc63d6802c5098733d746`
- 原始权利声明：Copyright (c) 2026 Nigel Hudson
- 许可：MIT，完整原文位于 `licenses/invaders/LICENSE`（包括免责声明）。原仓库没有独立 NOTICE 文件。
- 复用范围：`invaders/hooks/engine.ts` → `vendor/engine-source.ts` 及去除类型后的 `assets/engine.mjs`。保留原文件注释，增加适配声明；将可展示的英文标签改为中文或数值。`vendor/engine-source.ts` 随包提供，运行时不需要编译。
- 新增适配：浏览器画面和键盘控制、中文帮助、焦点暂停、严格本地存档校验，以及 Python 标准库导出工具。浏览器适配不使用上游浅层 `restore`/`isGame`。导出 HTML 也附带完整 MIT 原文。
- 未复用：Claude 专用 React/终端 UI、hooks、store、types API、图标、宣传 GIF/视频和测试框架。未捆绑第三方字体、图像、数据或 JavaScript 依赖。
- 原上游测试只用于理解期望行为；本项目用 Node 标准库与 Python 原生工具测试独立验证适配。上游 Claude 测试框架不随包分发或执行。

这些来源说明不表示原作者或任何平台背书，也不为本仓其他材料统一重新许可。
