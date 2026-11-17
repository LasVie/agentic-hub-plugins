# 第三方材料与许可

本插件是供本机使用的国际象棋分析工作台，不由 Stockfish、Chess.com 或 chess.js 项目背书。运行时不连接在线棋库、云分析或账户。

## Stockfish.js 19.0.1

- 来源：<https://github.com/nmrugg/stockfish.js/tree/0d5dd7944f88c817c07a26bc4fb1905d5f9c46d6>
- 发布：<https://github.com/nmrugg/stockfish.js/releases/tag/v19.0.1>
- 原发布标头：`Stockfish.js 19 (c) 2026, Chess.com, LLC`；Based on Stockfish，T. Romstad、M. Costalba、J. Kiiski、G. Linscott 及其他贡献者；完整名单见 `licenses/stockfish/AUTHORS`。
- 文件：`vendor/stockfish/stockfish-19-lite-single.js`、`stockfish-19-lite-single.wasm`；发布字节未修改。
- 引擎源文件声明 GNU GPL 第 3 版或更高版本。完整原许可：`licenses/stockfish/LICENSE`。
- 完整必要源码、构建脚本及精确小型网络：`corresponding-source/stockfish.js/`。构建/校验说明：`corresponding-source/重建说明.md`。同一 ZIP 直接提供源码，不需要另行申请。
- 非引擎脚本按原 README 的 MIT 声明；原 README、包信息和作者名单均保留。上游没有提供单独的非引擎 MIT 版权行；`NON_ENGINE_MIT.txt` 是明确标注的补充完整标准授权正文，不虚构缺失署名。
- 未分发上游未使用的整个 `examples/` 子树（包括旧 jQuery 和棋子图片），不属于引擎功能删改。保留的源文件及运行时文件均未改写、混淆或隐藏动态执行。

## Lite NNUE

- 文件：`corresponding-source/stockfish.js/src/nn-61e7af4bb97d.nnue`。
- 来源：<https://tests.stockfishchess.org/api/nn/nn-61e7af4bb97d.nnue>。
- 原发布标头署名：Nets by Chris Bao (sscg13)。
- SHA-256：`61e7af4bb97d51eeeb25d322916f86513b5cd3a827ce189c98c6e31946f99e5b`。
- Fishtest 官方网络下载/上传条款授予 CC0；锁定官方站点源码模板与完整 CC0 文本保留在 `licenses/nnue/`。策略模板提交：`f7af98f81f0c740a4de3d9a3721854709dcdc2bb`。

## chess.js 1.4.0

- 来源：<https://github.com/jhlywa/chess.js/tree/v1.4.0>。
- 原署名：Copyright (c) 2025, Jeff Hlywa (jhlywa@gmail.com)，All rights reserved。
- 文件：`vendor/chess/chess.js`，原样发布 ESM；对应源代码：`corresponding-source/chess.js/`。
- 许可：BSD-2-Clause，完整原文：`licenses/chess-js/LICENSE`。无运行时 npm 依赖；静态生成的 PGN 解析器已包含在发布模块中。

## Peggy 4.2.0：静态 PGN 解析器模板

- 锁定来源：<https://github.com/peggyjs/peggy/tree/6ce68af3334ba6c03fc729f1082ad0bbecf56569>，官方 `v4.2.0` 标签所指提交。
- 原署名：Copyright (c) 2010–2024 The Peggy AUTHORS。完整原始 MIT 授权和原作者名单分别见 `licenses/peggy/LICENSE`、`licenses/peggy/AUTHORS`。
- 实际范围：原样发布的 `vendor/chess/chess.js` 开头包含 Peggy 4.2.0 生成的静态解析器，其中包括 `SyntaxError`、错误格式化和位置跟踪等生成模板辅助代码。保留该文件原始生成标记，不把这些模板仅归为 chess.js 的 BSD-2-Clause 代码。
- 对应语法为 `corresponding-source/chess.js/src/pgn.peggy`；按照该目录原构建配置重建时生成 `src/pgn.js`。分发源码树不含预生成的 `src/pgn.js`，其静态输出已包含在运行模块中。
- Peggy 编译器本身不进入运行时，不在浏览器生成或动态执行解析器。此次仅补足模板来源的许可与署名，没有改动原发布解析器字节。

## incbin

- 来源：Stockfish.js 锁定树内的 `src/incbin/`，上游项目 <https://github.com/graphitemaster/incbin>。
- 原署名：Dale Weiler。Unlicense 原文：`licenses/incbin/LICENSE`。
- 所有源文件标头原样保留。

## Emscripten 6.0.9 与运行库

- 来源：<https://github.com/emscripten-core/emscripten/tree/6.0.9>，仅构建工具链的生成运行库出现在引擎中；不要求用户安装编译器。
- Emscripten 原署名：Copyright (c) 2010–2014 Emscripten authors，详见原 AUTHORS。本次选择其 MIT 授权；`licenses/emscripten/LICENSE` 仍保留上游完整 MIT/NCSA 双许可和 Node.js 来源授权。`AUTHORS` 原样随附。
- Node.js 来源部分：原署名 Copyright Joyent, Inc. and other Node contributors；完整 MIT 授权包含在上述 Emscripten 原许可中。Node.js 可执行程序不进入插件包。
- musl：MIT，Copyright © 2005–2020 Rich Felker, et al.；完整版权及相关第三方来源：`licenses/musl/LICENSE`。`MATH-NOTICES.txt` 保留该版本数学源文件原始声明，包括 Arm Limited 的 MIT 标头和 Sun Microsystems 的保留通知授权。
- libc++、libc++abi、compiler-rt：Apache-2.0 WITH LLVM-exception；原完整文本及历史许可分别在 `licenses/libcxx/`、`licenses/libcxxabi/`、`licenses/compiler-rt/`。未修改这些运行库源码。
- dlmalloc：Doug Lea 的公有领域/CC0 声明，原声明摘录和完整 CC0：`licenses/dlmalloc/`。

以上上游条款分别适用于其材料；本文件不重新许可整个团队仓库。工作台自主编写部分的权利归属与统一许可决定由项目负责人处理，不在本次审查中推定。
