# 来源与复用审查

首次审查日期：2026-11-13；当前补充审查：2026-11-16。任务：`AH-20261113-offline-chess-analysis-workbench`；候选：`CAND-EXT-015`；负责人：Cai Zhenze。

名称映射：Stockfish.js → 离线国际象棋分析工作台 → `offline-chess-analysis-workbench`。内部标识：`repo:agent-plugin:offline-chess-analysis-workbench`。

## 结论与边界

采用 `ported`：工作台包装、交互、状态和导出为本任务独立编写；计算引擎及规则库按明确的上游许可原样分发。仅使用已有原生插件 Tool/ToolCard 接口和插件自己的静态文件服务；不修改宿主、共享依赖或其他插件。原始署名不替换，不为整个仓库作新的统一许可决定。

## 实际复用材料

| 材料 | 锁定来源 | 实际覆盖与许可 |
| --- | --- | --- |
| Stockfish.js | `nmrugg/stockfish.js` 19.0.1；提交 `0d5dd7944f88c817c07a26bc4fb1905d5f9c46d6` | `vendor/stockfish/stockfish-19-lite-single.js` 与同名 `.wasm`，保留原始 GPLv3 标头；C++ 源文件明确 GPLv3 或更高版本，Stockfish developers 2004–2026；发布标头另署 Chess.com, LLC 2026 和 Stockfish 贡献者。完整 GNU 文本、AUTHORS、原 package.json 与 README 均随包。 |
| Stockfish 对应源代码 | 同一发布源码归档 | `corresponding-source/stockfish.js/` 保留源码、make/build 脚本、接口、测试、必要元数据及其原标头。不分发完全未使用的 `examples/` 子树和非构建必需的 Git/CI/格式化点文件；不是修改或隐藏动态执行点。其老 jQuery 含动态构造函数，且示例图片/字体不属于本工作台需要的材料。 |
| Lite NNUE | `nn-61e7af4bb97d.nnue`，Fishtest 官方精确下载 | 发布头署 Chris Bao (sscg13)。精确网络随对应源代码放入 `src/`。Fishtest 的网络下载页和上传条款明确 CC0；保留锁定模板、完整 CC0 文本、文件摘要。不假定其他网络同样被本次审查覆盖。 |
| chess.js | `jhlywa/chess.js` 1.4.0 | 原样 `vendor/chess/chess.js` ESM，静态包含生成的解析器；完整 BSD-2-Clause，Copyright (c) 2025 Jeff Hlywa；原源码、解析器语法及构建配置另随 `corresponding-source/chess.js/`。 |
| Peggy 生成解析器运行时 | `peggyjs/peggy` 4.2.0，提交 `6ce68af3334ba6c03fc729f1082ad0bbecf56569` | `vendor/chess/chess.js` 中的 SyntaxError、format、转义等生成辅助代码来自上游模板；保留完整 MIT 文本（Copyright (c) 2010-2024 The Peggy AUTHORS）及原始 AUTHORS。生成工具不作为运行时分发；不把所有生成输出一概视为工具许可覆盖。 |
| incbin | Stockfish 锁定源码中的 `src/incbin/` | Dale Weiler 的 Unlicense 原文与标头保留。 |
| Emscripten 运行时 | 6.0.9 | Emscripten 提供 MIT 或 NCSA；本次选择 MIT，同时保留上游完整双许可文件、AUTHORS 及其 Node.js 来源声明。不把这一许可视为 Stockfish 引擎的许可。 |
| C/C++ 编译运行库 | Emscripten 6.0.9 的 musl、libc++、libc++abi、compiler-rt、dlmalloc | musl 完整 COPYRIGHT 及数学源文件原始版权/授权头（包括 Arm、Sun）；libc++、libc++abi、compiler-rt 的完整 Apache-2.0 WITH LLVM-exception（含旧条款）；dlmalloc 的 Doug Lea 公有领域/CC0 原声明和完整 CC0。并非将这些库重许可为 GPL。 |

Stockfish README 对“non-engine code”明确声明 MIT，但锁定树不提供单独的 MIT 版权行/许可文件。因此保留原 README、package.json 作者元数据及 AUTHORS，并附有清楚标为补充的完整标准 MIT 授权正文；未虚构缺失的版权人或声称上游存在单独文件。GNU 引擎授权不由这一声明取代。

本工作台不复用第三方棋子图片、字体、书库、残局库、示例网页或在线服务。棋盘图形由本插件生成；系统字体不随包分发。运行时无需 npm、Node.js、Emscripten 或网络下载；这些仅用于本地开发验证/重建。

## 锁定字节

| 原文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| stockfish-19-lite-single.js | 28,230 | `ccb130d7ff29408531c47d859a49f91d59d4f482d05a53eb1a3231a4f624c91a` |
| stockfish-19-lite-single.wasm | 1,845,971 | `ee4f115bdb2d32cadf96cada104a05b5ec257d7ad6f57582190b49bc71f096de` |
| chess.js | 107,052 | `76c7c34f0e2e9ab076521a5d6fe786a9cce537bb1b6f29d32a9c9970b5b232d2` |
| nn-61e7af4bb97d.nnue | 1,166,381 | `61e7af4bb97d51eeeb25d322916f86513b5cd3a827ce189c98c6e31946f99e5b` |
| Stockfish 原始源码 tar.gz（仅留于审查暂存，不进入交付包） | 426,054 | `a18aa8a871f5265014b110b3e07804ff3637899d2e189be6ded2b99e2c17a10e` |
| chess.js 原始源码 tar.gz（仅留于审查暂存，不进入交付包） | 148,559 | `a927d148e7c877eaacb7752ab4ec1355780df2989b0f123532d274c30b84e9ce` |

完整实际复用路径、对应源代码和许可文件摘要由 `source-audit.json` 与 `provenance.json` 记录。禁止把含未用示例的原始归档作为不透明源代码包塞入交付物。

## 分发与重建

依据 GNU GPLv3 第 6(d) 节，在与对象代码同一 ZIP 中直接提供机器可读对应源代码、精确 NNUE 和构建说明，接收者不需另行申请。保留所有适用许可和署名；引擎未作源代码或发布字节修改。SDK、编译器等通用构建工具不作为运行时分发；确切版本与获取方法见 `corresponding-source/重建说明.md`。不以原始二进制 SHA-256 相同代替功能验证，也不把功能等价误称为逐字节可复现。

## 验证状态

原始来源、完整授权条件及原标头已在执行引擎前审查。精选后的 Stockfish 110 个文件（含精确 NNUE）和 chess.js 59 个文件逐一与锁定上游来源比较，字节全部一致。省略的 12 个非构建点文件完整清单见 `source-audit.json`；原始源码归档及被省略文件仍保留在本任务审查暂存。构建不读取这些 Git、CI、格式化或发布忽略清单。

官方 Emscripten 6.0.9 在任务专用隔离目录安装并成功重建。首次原样命令因 macOS 目标自动探测带入原生编译标志失败；使用原 Makefile 支持的 `MAKEFLAGS=TARGET_KERNEL=Emscripten` 后，未修改源文件即成功。重建的 JS 和 WASM 均与发布字节完全相同，SHA-256 如上。原发布与重建引擎分别通过同一组九项规则、UCI、将死、三主变化、取消和故障恢复测试；紧凑证据与具体边界见 `tests/records/source-rebuild.json`。包装层 Worker 故障注入不伪称真实浏览器故障。

初步 63 个 JS/TS 文件额外检查无动态字符串执行签名；随后主代理的锁定官方内容检查器扫描当前脚本也无命中。这不是 Agentic Hub 接受保证。最终 ZIP 的格式、安全与解包检查由打包报告记录。该段为 2026-11-13 的 1.0.0 工程验证历史；后续状态见下文。

## 2026-11-16：用户确认与分发材料修正

Cai Zhenze 已在当前会话明确确认 1.0.0 人工测试完成并通过，提交七张原始全分辨率截图；完整确认与逐图摘要见 `USER_TEST_CONFIRMATION.md` 和 `evidence/user-testing-1.0.0/index.json`。原始 1.0.0 ZIP 保持不变。

交付前独立复核发现先前漏记 Peggy 4.2.0 的生成解析器运行时许可：虽然无需在运行时安装 Peggy，chess.js 发布文件包含上游 `lib/compiler/passes/generate-js.js` 约 857–1019 行模板中的实质辅助代码。锁定 README、许可与官方文档未发现对这些模板的单独输出豁免。依据仓库 MIT 分发规则，在载荷新增 `licenses/peggy/LICENSE`、`AUTHORS`，并补充 `THIRD_PARTY_NOTICES.md`、provenance 与源码审计。原始许可 SHA-256 为 `32c43eac6ae56c751cf85a9181a0753145cb9ae993943ae80699ba64e75843b0`；AUTHORS 为 `df057b32b11800151822dba548c9d9df5d968cb5bf5fb006aa8494faf2b331cc`。

修正版为 1.0.1。没有修改任何 Stockfish JS/WASM、chess.js、NNUE 或对应源代码；其原始摘要和已完成重建证据仍适用。改动仅为许可/署名、插件版本声明和相应文档。1.0.0 的用户通过记录不应用于新 ZIP；在 1.0.1 明确完成确认前留在 Build，不推送、创建交付 PR、合并或操作 Hub。

## 2026-11-17：当前包确认

Cai Zhenze 在当前会话明确确认修正后的 1.0.1 人工测试完成并通过，另供六张当前版本原始截图。原生 ZIP SHA-256 `e8baa13cb6eaead5702f122bb861dd5280b10dc1137150e52af759bf0ffc79f7`；规范 ZIP SHA-256 `581bf7dccb464218a48a6a5d3ebfcd7c3386ef3685aa7a03a65b8e580daea513`。源码、两个ZIP和209份载荷摘要仍一致；22份许可证据原文与记录摘要一致。先前 Peggy 署名漏项已在准确被测包中解决，无未完成的分发条件。原有源码/重建/功能证据继续适用，未以文档更新改写包装或运行时。

准确的用户确认及原图索引见 `USER_TEST_CONFIRMATION.md` 和 `evidence/user-testing-1.0.1/index.json`；此前「待确认」为历史阶段状态，当前转入 GitHub 交付。有限搜索、完整 WorkSwarm 0.2.8 和 Linux 未验证、Windows 生命周期不支持等边界仍如实保留，不以本次确认扩大兼容性结论。Project Lead acceptance 与 Hub 操作仍归 Song Haoran。

首次 GitHub 交付仅包含当前完整许可的1.0.1包及其当前证据；旧1.0.0包、原图、审查和自测报告在本任务本地保护保存，文中的旧历史路径不表示旧包也被提交。精确旧摘要及修正历史保留在当前确认记录。
