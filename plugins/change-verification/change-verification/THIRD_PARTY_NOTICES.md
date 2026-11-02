# 第三方来源与许可

## TraceScope 0.3.5

- 原项目：https://github.com/rebornace/dsh-tracescope
- 固定提交：`b4f3c8e3be2b756ad9966463a65331e69fdee5f8`
- 原权利人声明：`Copyright (c) 2026 rebornace`
- 适用许可：MIT，完整原文见 `licenses/dsh-tracescope/LICENSE`，包括免责声明；上游没有独立 NOTICE。
- 范围：`packages/core/src/deps.ts` 的纯内存过滤、索引与反向依赖 BFS；`deps-refs.ts`、`heuristics.ts`、`skip-paths.ts`。对应包内 `vendor/*.ts` 与由这些文件转译的 `vendor/*.js`。
- 修改：deps 移除文件系统扫描、Git 读取、缓存及相关导入，仅保留纯内存逻辑；其余三份 TS 保留原算法与注释。使用 TypeScript 5.9.3 转译为无需编译器的 ES2022 JS。适配层重新提供有界 Git 对象读取、中文 MCP、人工结果面板、证据校验及导出；没有移植 DSH、网络服务、品牌资源或凭据。
- 开发工具 TypeScript/Vitest 及它们的依赖没有打入运行载荷；运行载荷的 JS 仅引用 Node 内置模块和上述本包模块，没有 npm 运行时依赖。

上述许可只覆盖相应上游材料；此记录不改变其版权归属，不声称原作者对本适配包背书，也不为整个仓库指定统一许可。
