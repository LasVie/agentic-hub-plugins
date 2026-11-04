# 来源与适配审查

任务：`AH-20261102-change-verification`；候选：`CAND-DSH-145`；负责人：Wang Jie。

名称对应：TraceScope / `rebornace/dsh-tracescope#dsh-tracescope` → **变更影响与回归检查台** → `change-verification`。内部标识：`repo:agent-plugin:change-verification`，版本 1.0.0。

2026-11-02 已在共享表复核未认领、无同范围任务，并完成候选与任务的双向登记，才下载源码。功能比较包括 Git 分支全景、页面验收助手、开发与测试计划、流程执行台及项目资料导航。它们分别处理拓扑、页面断言、需求规划、通用阶段或资料检索，未覆盖本插件的 Git 对象差异、反向依赖候选和人工回归结果组合。

## 固定来源与许可

- 上游：https://github.com/rebornace/dsh-tracescope
- 固定提交：`b4f3c8e3be2b756ad9966463a65331e69fdee5f8`，声明版本 0.3.5。
- 仓库根 LICENSE 为完整 MIT，原权利人声明 `Copyright (c) 2026 rebornace`。
- 实际检索根及子目录 LICENSE/NOTICE、所选源码的版权和 SPDX 标记：仅根 MIT；所选算法没有单独许可或附加版权头，没有上游 NOTICE。
- 本次许可结论为所选代码可复用；采用 `ported`。完整 MIT 原文随内层包分发，保留原注释，不添加新的版权归属或整仓重许可声明。
- 仅选 `packages/core/src/deps.ts` 的纯内存索引、过滤和 BFS 段落，以及 `deps-refs.ts`、`heuristics.ts`、`skip-paths.ts`。将索引的文件系统、Git 读写、缓存入口移除，由适配层提供有界的提交对象快照。
- 开发期用上游 TypeScript 编译器生成 JS，运行包不分发编译器、Vitest、npm 依赖或 node_modules；转译后的运行算法仍适用上述 MIT。源 TS 与生成 JS 同包保留，构建脚本、固定来源及哈希在审计记录中核对。
- 没有使用图片、图标、字体、品牌标识、第三方新闻/业务数据。演示仓库与文案由适配任务生成，不声称真实项目测试通过。

## 适配范围与差异

保留多语言引用识别、反向依赖扩散与路径风险启发式，重新接入 WorkSwarm stdio MCP 和中文浏览器面板。只读取用户明确指定的本地 Git 仓库，不执行被分析项目代码。两个已有提交按端点比较，包含删除项，分别索引两个快照，以便保留旧依赖链。静态候选不是运行时覆盖证明。

不移植原版 DSH/Cordis 注入、远程克隆/拉取、`safe.directory=*`、仓库配置写入、工作树检出/重置、凭据、外部缺陷提交、设计平台或崩溃服务。用户测试状态由面板录入；模型工具不能自动将清单标记通过。报告和证据仅存插件自己的私有缓存，不写用户仓库。

原版所选算法的 11 项局部基线通过，实际编译器 TypeScript 5.9.3，原版局部测试 Vitest 3.2.7。上游 npm 开发锁文件哈希已记录，仅供构建审计，不打入运行载荷。三份完整算法 TS 保留原算法和注释，统一为 UTF-8/LF；deps 选取范围及变化如上。四份 JS 由同包 TS 转译，只有 Node 内置及本包导入，没有外部 npm 运行依赖。适配层没有带入上游下载、账户和配置自动写入逻辑。

## 最终归档核对

2026-11-02 实际生成标准包 `releases/agent-plugin/change-verification/1.0.0/change-verification-1.0.0.zip`，SHA-256：`e1ca8c8f2ef5e27f518f950fbf62b6da041bc32db118e3d9cde058d74a31faaa`。

从标准包提取相同内层，生成本地宿主测试包 `local-tests/change-verification/1.0.0/change-verification-1.0.0-workswarm.zip`，SHA-256：`4d760812e23fe870e32a8fba986df5eaf332fd3bdce579f69ebc3052712dd40d`。两种外层格式不同，不应互换哈希；25 个运行文件与源码及解压后的文件逐个一致。

完整上游 MIT 文件在解压包中存在，哈希 `da9c3ba5b56f1eddacc9eebe375b174b1cf03c0cd13ed303328e98954d480ea6`，与原文及 provenance 一致；许可、署名、修改摘要和八份 TS/JS 对应范围已核对。没有遗漏已复用代码所需的许可，没有媒体或外部 npm 运行包；没有 node_modules、测试、缓存或本地任务记录混入载荷。

解压包的 17 项运行测试与 39 项独立 MCP/浏览器检查均实际通过，包括中文默认界面、UTF-8、真实错误、状态/截图保存、跨进程读回和离线报告。用户已完成当前精确包的 WorkSwarm 简化流程，确认记录见 USER_TEST_CONFIRMATION.md，十一张原图及逐字节核对见 evidence.json；运行载荷及 ZIP 保持不变。本次进入 GitHub PR 交付，Project Lead 验收另行处理；不执行 Hub 操作或登记 Asset Ledger。
