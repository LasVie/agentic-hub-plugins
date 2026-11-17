# 第三方组件与源代码说明

本包为 **离线水与蒸汽物性工作台 1.0.0**，上游数值引擎为 **CoolProp 8.0.0**，内部标识为 `offline-steam-properties-workbench`。它通过本插件调用本机数值引擎；不修改 WorkSwarm、SDK 或其他插件。没有复制上游品牌图标、字体、截图或论文内容，也不表示上游作者认可本插件。

## 数值引擎

来源：https://github.com/CoolProp/CoolProp

固定提交：`ae81610e7d23efc57f9d051c8e70a4d66e87537f`。

原始发布：https://pypi.org/project/CoolProp/8.0.0/ 。

原版权声明为 `Copyright (c) 2012-2018 Ian H. Bell and other CoolProp developers`。完整 MIT 文本保存在 `licenses/coolprop/LICENSE`，原始 wheel 内的声明和文件头保持不变。

`vendor/coolprop/` 保存四个完整、未修改的官方 macOS wheel：CPython 3.11 的 ARM64 / x86_64 版本，以及供兼容 CPython 3.12 及以后解释器使用的 `cp312-abi3` ARM64 / x86_64 版本。`binaries.json` 记录原始文件名、来源、版本、架构、ABI 与 SHA-256。插件仅把匹配的文件解压到自己的临时工作目录，不把它安装到宿主或共享 Python 环境。

实际运行还要求本机已有兼容的 Python 和 NumPy >=1.20。本包不附带、不安装 NumPy。macOS 的 C++ 与系统动态库也不随包分发。其他操作系统不属于这些 wheel 的适用范围。

## 已保留的混合许可

| 组件、固定版本或提交 | 原作者或声明 | 随包证据与适用说明 |
| --- | --- | --- |
| CoolProp 内 Devin Lane 三次样条代码 | Devin Lane；原始 Beer-Ware 通知与上游修改说明 | `licenses/coolprop/BEER-WARE.txt`。保留该完整通知；其中可选的啤酒回赠句不构成购买要求。 |
| CoolProp superancillary | NIST；后续修改 Ian Bell | `licenses/coolprop/NIST.txt`。保留包含美国及境外使用、修改、分发许可和免责声明的完整通知。 |
| CoolProp 三次状态方程实现 | I. Bell、A. Jäger；原文件明确声明 public domain | `licenses/coolprop/PUBLIC-DOMAIN-CUBIC.txt`。保留原始声明和论文引用。 |
| Eigen 5.0.1 | 各头文件的原始作者 | `licenses/eigen/` 包含完整 MPL-2.0、BSD、Apache、MINPACK 许可，以及原样对应头文件源代码。主要许可为 MPL-2.0，不能笼统称为 MIT。 |
| fmt 12.0.0 | Victor Zverovich 与贡献者 | `licenses/fmt/LICENSE`；完整 MIT 及原始可选目标代码例外。wheel 内 fmt 头文件的原始声明保留。 |
| msgpack-c `919908742b4fdbc575e77fe1a8657e70c9573c44` | FURUHASHI Sadayuki 等 MessagePack 作者 | `licenses/msgpack/`；Boost Software License 1.0 与原始入口头文件版权。 |
| nlohmann/json 3.12.0 | Niels Lohmann；Evan Nemerson、The Abseil Authors、Björn Hoehrmann、Florian Loitsch 等原头文件作者 | `licenses/nlohmann-json/`；MIT、嵌入 Abseil 片段的 Apache-2.0，以及包含完整原始归属的头文件。上游根目录无单独 NOTICE，本包不虚构它。 |
| Valijson 1.0.6 | Tristan Penman、Akamai Technologies, Inc. | `licenses/valijson/LICENSE`；BSD 二条款。 |
| IF97 `7aaced024a702f0985474bf293cdaae9c8d06521` | Ian H. Bell | `licenses/if97/LICENSE`；完整 MIT。虽然界面固定为 HEOS Water，仍保留已编译后端的声明。 |
| REFPROP-headers `b4faab1b73911c32c4b69c526c7e92f74edb67de` | 原接口头文件版权声明 | `licenses/refprop-headers/LICENSE`；MIT 仅覆盖这些接口头文件。本包不提供或调用专有 REFPROP 库、流体文件或服务。 |
| Boost headers `c68104660ca4bd80d0d5cb34c4eba0cf5bab3f73` | 包括 John Maddock、Matt Borland 的 TOMS748 实现 | `licenses/boost/`；Boost Software License 1.0 与原始版权文本。 |
| miniz 3.1.1 | RAD Game Tools、Valve Software、Rich Geldreich、Tenacious Software LLC | `licenses/miniz/`；完整 MIT 与代码内原始 Unlicense 通知。 |
| incbin | 原始 public-domain / Unlicense 声明 | `licenses/incbin/LICENSE`；完整 Unlicense。 |
| nanobind 2.12.0 | Wenzel Jakob 与原文件注明的其他贡献者 | `licenses/nanobind/`；BSD 三条款及原始代码文件版权清单。 |
| robin-map `4ec1bf19c6a96125ea22062f38c2cf5b958e448e` | Thibaut Goetghebuer-Planchon | `licenses/robin-map/LICENSE`；完整 MIT。 |
| Cython 3.2.6 生成的辅助模块 | Cython / Pyrex 原始许可声明 | `licenses/cython/COPYING.txt` 明确说明编译输出中嵌入的代码片段不会为输出附加许可限制。Cython 编译工具不随包分发。 |

这些许可分别适用，不把整个仓库或插件集成代码统一重新授予某个上游许可。完整原文优先于本中文说明；原作者、版权和免责声明未以本项目的新归属替换。

## 对应源代码与修改范围

`licenses/eigen/eigen-5.0.1-corresponding-headers.tar.gz` 随包提供 MPL 覆盖部分的可修改源代码，包含 420 个来自官方归档、保持原样的文件。其内部清单给出逐文件哈希；同目录中文说明列出原始来源和验证方法。获取这份随包源代码不需要付费或联网。

原始 CoolProp wheel、数值实现和模型数据未修改。新增工作为本插件的中文界面、固定 HEOS Water 输入验证、隔离工作进程与结果呈现；生命周期、回环服务和打包机制复用并适配 Cai Zhenze 的维护中仓库实现。该内部复用不宣称整个包装层均为独立重写，也不改变其他插件或其环境。

本版本不向使用者开放任意流体定义、REFPROP 后端或引擎配置加载。内置物性数据库随官方 MIT 包提供，原始模型文献引用留在引擎及其 BibTeX 数据中；没有附带论文全文或下载外部图片。测试专用 multicomplex 实现未包含在这些 Python 运行构建中，也未复制到本包。
