# 第三方来源、版权与许可

本插件“离线分子结构工作台”使用 **RDKit.js 2026.9.1**（引擎版本 `2026.09.1`）进行本地分子结构计算。RDKit 上游固定提交为 `fece8caa860bdf6c9c82bdb9253f22a0cf87150c`，来自 `Release_2026_09_1`。本插件不是 RDKit 官方产品，也不代表任何下列权利人的背书。

`vendor/rdkit/RDKit_minimal.js` 与 `RDKit_minimal.wasm` 保持官方 npm 包的原始字节；我们没有修改上游程序、内嵌字体或源码归档。完整版本、下载地址与 SHA-256 见 `vendor/rdkit/UPSTREAM.json`。官方 npm 包没有附完整许可证，因此本包另行提供下列原文，不以一个 BSD 标签代替混合许可义务。

| 来源与版本 | 原始权利人或署名 | 覆盖范围及许可 | 本包原文位置 |
| --- | --- | --- | --- |
| [RDKit](https://github.com/rdkit/rdkit/tree/fece8caa860bdf6c9c82bdb9253f22a0cf87150c) | Rational Discovery LLC、Greg Landrum、Julie Penzotti、Novartis、Schrödinger、David Cosgrove、Gareth Jones/Glysade 及原文件列出的其他贡献者 | 化学引擎与包装层；BSD-3-Clause，保留各模块版权 | `licenses/rdkit/` |
| [Linchemin 固定提交 f44fda38](https://github.com/syngenta/linchemin/tree/f44fda38e856eaa876483c94284ee6788d2c27f4) | ©2022 Syngenta Group Co. Ltd. | RDKit 氧化数实现声明使用其代码；额外 MIT，不单独运行 Linchemin | `licenses/linchemin/` |
| [FreeType 2.13.3](https://github.com/freetype/freetype/tree/VER-2-13-3) | David Turner、Robert Wilhelm、Werner Lemberg、FreeType 团队及各文件贡献者 | 字体描绘引擎；选择 FTL，保留 BDF/PCF/哈希/Adobe 等独立声明 | `licenses/freetype/` |
| [InChI 1.07.3](https://github.com/IUPAC-InChI/InChI/releases/tag/v1.07.3) | ©2024 IUPAC and InChI Trust / InChI Project；Paul Bakker、Christophe Devine 等 | 二进制内化学标识组件；MIT。SHA-256 部分仅与 InChI 组合分发，不提供独立哈希工具 | `licenses/inchi/` |
| [CoordGen 3.0.2](https://github.com/schrodinger/coordgenlibs/tree/v3.0.2) | ©2017 Schrödinger, Inc. | 二维坐标生成；BSD-3-Clause | `licenses/coordgen/` |
| [Maeparser 1.3.3](https://github.com/schrodinger/maeparser/tree/v1.3.3) | ©2017 Schrödinger, LLC | CoordGen 构建依赖；MIT | `licenses/maeparser/` |
| [RingDecomposerLib 1.1.3_rdkit](https://github.com/rareylab/RingDecomposerLib/tree/v1.1.3_rdkit) | ©2016 University of Hamburg, ZBH；Niek Andresen、Florian Flachsenberg、Matthias Rarey | 环结构算法；BSD-3-Clause | `licenses/ringdecomposer/` |
| [Boost 1.87.0](https://github.com/boostorg/boost/tree/boost-1.87.0) | 各 Boost 文件原始作者 | C++ 模板与支持代码；BSL-1.0 | `licenses/boost/` |
| [zlib 1.3.2](https://github.com/madler/zlib/tree/v1.3.2) | ©1995–2026 Jean-loup Gailly and Mark Adler | 压缩支持；zlib 许可 | `licenses/zlib/` |
| [Eigen Debian 3.4.0-4](https://deb.debian.org/debian/pool/main/e/eigen3/) | Benoit Jacob、Gael Guennebaud 等原文件作者；Debian 补丁署名见原始归档 | 矩阵头文件；MPL-2.0 与独立 BSD 条款。双许可文件选择 MPL；完整原始源码保留其他文件各自许可 | `licenses/eigen/` |
| Telex Regular 1.100 | ©2011 The Telex Project Authors；保留字体名 Telex | WASM 内嵌字体；SIL OFL-1.1，字节与名称不变 | `licenses/telex/` |
| Roboto Regular 2.137（2017） | ©2011 Google Inc.；Christian Robertson | WASM 内嵌字体；Apache-2.0，保留原始署名与商标说明 | `licenses/roboto/` |
| GNU Bison 3.8.2 | Free Software Foundation, Inc. | 生成的 SMILES/SMARTS 解析器；GPL-3.0-or-later WITH Bison-exception-2.2。保留允许较大作品使用其他条款的例外 | `licenses/bison/` |
| Flex 2.6.4 | The Flex Project；The Regents of the University of California；Vern Paxson | 生成扫描器。原 COPYING 明确说明生成扫描器不受其版权约束；原文仍保留 | `licenses/flex/` |
| [Emscripten 6.0.11](https://github.com/emscripten-core/emscripten/tree/a0014542110d6078c3a1a7941fa1ddb3a2281f16) | Emscripten AUTHORS、Node 贡献者 | JavaScript/WASM 支持；Emscripten 自有代码选择 MIT，保留 Node 等独立声明 | `licenses/emscripten/` |
| Emscripten 随附 musl | Rich Felker 等；其他版权详见原文 | C 运行库；MIT 及原文件独立许可 | `licenses/musl/`、`licenses/emscripten/SOURCE_NOTICES.txt` |
| Emscripten 随附 LLVM compiler-rt、libc++、libc++abi、libunwind | LLVM Project 与原文件贡献者 | C++/编译器运行支持；Apache-2.0 WITH LLVM-exception 及保留的历史声明 | `licenses/llvm-compiler-rt/`、`licenses/llvm-libcxx/`、`licenses/llvm-libcxxabi/`、`licenses/llvm-libunwind/` |
| dlmalloc | Doug Lea | 内存分配支持；公共领域声明及 CC0-1.0 说明/后备条款 | `licenses/dlmalloc/`、`licenses/emscripten/SOURCE_NOTICES.txt` |

本软件部分基于 FreeType 团队的工作。

Portions of this software are copyright © 1996-2024 The FreeType Project (www.freetype.org). All rights reserved.

Eigen 的对应源码与 Debian 修改已经随包提供在 `licenses/eigen/sources/`，无需联网获取。如何还原源码以及许可权利说明见 `licenses/eigen/SOURCE_AVAILABILITY.md`。归档未修改；其中未参与本引擎构建的测试或其他模块仍保留各自许可证，不能将整个源归档误称为单一 MPL 许可。

`SOURCE_NOTICES.txt` 是从固定版本源码收集的原始版权/许可注释，含原路径，保守覆盖相应构建模块与运行库。它不表示每个函数都保留在优化后的二进制中。完整许可文本和免责声明保持原文；这些文件不对原作品重新许可。没有找到单独上游 NOTICE 的来源，不以本清单伪装成上游 NOTICE。

修改说明：我们新增 WorkSwarm 工具适配、输入与资源限制、简体中文交互、测试及打包材料；未修改上游 JS/WASM、内嵌字体或 Eigen 源码归档。官方 RDKit 构建自身对 InChI 的 Emscripten 条件和 RingDecomposer 的排序/头文件做兼容调整，记录见项目 `SOURCE_REVIEW.md` 与对应许可目录。没有复用上游图标、标志、截图或外部分子数据库。
