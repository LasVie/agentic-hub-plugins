# 第三方来源与许可

本包为「立体网格布尔工坊」1.0.0（`solid-mesh-workbench`）。本项目仅提供独立的 WorkSwarm 原生插件、本地界面和受限计算接口，不代表下列上游项目，也未获得其商标或官方背书。

## 实际复制的运行文件

`vendor/manifold.js` 与 `vendor/manifold.wasm` 原样取自官方 npm `manifold-3d@3.5.4`，对应 [Manifold 源码提交 ce50d78021d64507f89e8c9fc2c2e51018117857](https://github.com/elalish/manifold/tree/ce50d78021d64507f89e8c9fc2c2e51018117857)。没有修改这两个文件，没有安装或复制完整 npm 依赖树、上游编辑器、示例素材、字体或图标。

Manifold 原始权利人声明为 The Manifold Authors；重要贡献者名单见 [AUTHORS](licenses/manifold/AUTHORS)。完整 Apache-2.0 文本见 [Manifold 许可证](licenses/manifold/LICENSE)。固定源码树和 npm 包均未发现上游 `NOTICE` 文件；此说明文件为本项目的来源清单，不冒充上游 NOTICE。

本项目独立编写网格解析、限制与拓扑检查、工程格式、工具、进程管理、中文界面和测试。上游编译产物保持不变；本项目未修改上游源文件。原生适配文件不据此被统一重新许可。

## 编译产物中的组件与保留声明

| 组件 | 固定来源及权利人 | 许可与包内证据 |
| --- | --- | --- |
| Manifold | 3.5.4；The Manifold Authors | [Apache-2.0](licenses/manifold/LICENSE)、[贡献者](licenses/manifold/AUTHORS) |
| Clipper2 | `46f639177fe418f9689e8ddb74f08a870c71f5b4`；Angus Johnson 2010–2025 | [Boost Software License 1.0](licenses/clipper2/LICENSE)、[原始文件头](licenses/clipper2/COPYRIGHT.txt) |
| DisjointSets | Manifold 固定源码中的 `src/disjoint_sets.h`；Wenzel Jakob 2015 | [完整 zlib 许可及上游修改说明](licenses/dset/LICENSE) |
| tbtSVD | Manifold 固定源码中的 `src/svd.h`；wi-re 2019、The Manifold Authors 2023 | [完整 MIT 许可及上游修改说明](licenses/tbtsvd/LICENSE) |
| Sun 数学函数 | Manifold 固定源码中的 `include/manifold/math.h`；Sun Microsystems 1993 | [原始宽松授权及保留声明](licenses/sun-math/LICENSE) |
| linalg | Manifold 固定源码中的 linalg 2.2 衍生代码；Sterling Orsten，贡献者 Stan Melax、Dimitri Diakopoulos | [原始声明](licenses/linalg/UPSTREAM_STATEMENT.txt)、[Unlicense 全文](licenses/linalg/LICENSE) |
| QuickHull | Manifold 固定源码中的衍生代码；Antti Kuukka | [原始公共领域声明与 Manifold 归属](licenses/quickhull/LICENSE) |
| PhysX 算法片段 | Manifold 固定源码中的 `src/tri_dist.h`；NVIDIA Corporation 2008–2025 | [BSD 3-Clause 全文](licenses/physx/LICENSE)、[来源与上游修改说明](licenses/physx/UPSTREAM_STATEMENT.txt) |
| Emscripten | 5.0.2，`dc80f645ee70178c11666de0c3860d9e064d50e4`；Emscripten authors | [完整双许可文本](licenses/emscripten/LICENSE)、[贡献者](licenses/emscripten/AUTHORS)；本包选择 MIT，原文保留其中 Node/Joyent 声明 |
| musl libc | Emscripten 5.0.2 随附版本；Rich Felker 等 | [完整 MIT 与来源说明](licenses/musl/LICENSE)、[逐文件原始数学/标准库声明](licenses/musl/THIRD_PARTY_COPYRIGHTS.txt) |
| LLVM libc++ / libc++abi / compiler-rt | Emscripten 5.0.2 随附版本；LLVM contributors | [libc++](licenses/llvm-libcxx/LICENSE)、[libc++abi](licenses/llvm-libcxxabi/LICENSE)、[compiler-rt](licenses/llvm-compiler-rt/LICENSE)；Apache-2.0 WITH LLVM-exception，保留完整历史许可与各目录 `CREDITS.TXT` |
| dlmalloc | Emscripten 5.0.2 的默认串行分配器；Doug Lea 2.8.6 | [上游公共领域声明](licenses/dlmalloc/UPSTREAM_STATEMENT.txt)、[所引用 CC0 1.0 全文](licenses/dlmalloc/LICENSE) |

此清单保守保留编译工具链可能嵌入的运行库声明，不宣称列出的每个源文件都在最终 WASM 内保留了机器代码。Manifold 发布流水线使用串行构建；本包没有加入 TBB、mimalloc、glTF/3MF 工具、sharp/libvips 或其他 npm 依赖。

上游原文许可证与版权声明保留英文。完整检索日期、固定来源、文件 SHA-256、具体许可选择、排除范围和验证结果记录在仓库的 `SOURCE_REVIEW.md` 与 `provenance.json`。
