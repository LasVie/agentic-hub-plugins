# 第三方来源与修改记录

## anidoodle

- 上游：https://github.com/alexgreensh/anidoodle
- 固定提交：`f746cbd8a7032463bd0bc88ee8ff852599193b8c`；上游插件和引擎均为 0.9.6。
- 原作者声明：Copyright 2026 Alex Greenshpun。
- 许可：Apache-2.0；完整原文及 NOTICE 位于 `licenses/anidoodle/`。
- 复用范围：`engine/src/canvas-core/` 的 core、bake、input、storybook、bitRig、mascotHero、formMascot、scrollHero；`engine/src/hosts/interactive.ts`；这些文件编译生成 `engine/art.js`。
- 修改：中文交互标签及无障碍说明；input.ts 删除首版未使用的 Film 适配函数及其类型导入。修改文件均含显著声明。新增中文入口、页面模板、Python/宿主工具与构建脚本由 Gan Mingrui 维护。
- 未包含：上游音色包、图片参考、宣传素材、字体、视频/音频管线、Remotion 及其他画风。原 NOTICE 完整保留不表示这些可选材料已装入本包。
- 生成 HTML 内保留完整上游许可和 NOTICE；继续传播作品或源码时不得删除适用声明。

## 构建与测试依赖

esbuild 0.25.12 用于本地源码编译，MIT，Copyright (c) 2020 Evan Wallace，许可附于 `licenses/esbuild/LICENSE`。编译器及 node_modules 不分发。Playwright 仅用于开发测试，不进入插件或作品。普通创建流程不需要 npm，也不调用外部服务。
