# 第三方组件与许可说明

本插件「离线资源配置优化台」由 Cai Zhenze 负责。上游名称为 HiGHS，内部标识为 `offline-allocation-workbench`。插件包装、有限 JSON 模型、工作台及验证逻辑独立编写；此说明不为仓库其余代码指定统一许可证，也不表示获得上游商标或官方背书。

## HiGHS 1.16.0 与组合求解程序

官方源提交：`f3f113d230429a8c0014b12ab0dd1a3847e58c55`。来源：https://github.com/ERGO-Code/HiGHS/releases/tag/v1.16.0 。保留的实际二进制为官方 macOS 通用包中的 `bin/highs`，仅重新放置于本插件自己的 `vendor/highs/bin/highs`，字节未修改。macOS 26.0 或更新版本；含 x86_64、arm64 两种架构。动态依赖系统已有的 zlib、libc++ 与 libSystem；不分发这些系统库，不安装 Python/NumPy 或共享依赖。

HiGHS 主体：Copyright (c) 2026 HiGHS，MIT；作者名单原文见 `licenses/highs/AUTHORS`，完整许可见 `licenses/highs/LICENSE`。所带 IPX、BasicLU、cuPDLP 和外部部件分别保留其原始声明。原始上游第三方说明见 `licenses/highs/UPSTREAM_THIRD_PARTY_NOTICES.md`；下面补充其中未列出的 CSparse 派生代码许可，不能把整个组合程序只标作 MIT。

| 部件 | 来源、版本与原始权利人 | 本包覆盖内容 | 许可和修改 |
| --- | --- | --- | --- |
| CLI11 | https://github.com/CLIUtils/CLI11 ，2.5.0；Copyright (c) 2017-2025 University of Cincinnati，Henry Schreiner，NSF AWARD 1414736 | 官方 CLI 的参数解析器 | 原始 BSD 三条款式全文及版权在 `licenses/highs/cli11/LICENSE`；二进制未改 |
| pdqsort | https://github.com/orlp/pdqsort ，上游 HiGHS 标识 `git:b1ef26a`；Copyright (c) 2021 Orson Peters | HiGHS 内排序实现 | Zlib；完整原文在 `licenses/highs/pdqsort/LICENSE`；未自行修改 |
| zstr | https://github.com/mateidavid/zstr ，1.0.6；Copyright (c) 2015 Matei David, Ontario Institute for Cancer Research | 压缩模型流支持 | MIT；`licenses/highs/zstr/LICENSE`；未自行修改 |
| IPX | https://github.com/ERGO-Code/ipx ，HiGHS 固定源快照；Copyright (c) 2018-2020 ERGO-Code | 官方二进制中的 IPX 与 HiGHS 适配代码 | 明确选择 MIT 选项，完整双许可原文在 `licenses/highs/ipx/LICENSE`；CSparse 派生部分另适用下述 LGPL 条件 |
| BasicLU | https://github.com/ERGO-Code/basiclu ，HiGHS 固定源快照；Copyright (c) 2016-2020 ERGO-Code | 官方二进制中的稀疏 LU 实现 | 明确选择 MIT 选项，完整双许可原文在 `licenses/highs/basiclu/LICENSE`；CSparse 派生部分另适用下述 LGPL 条件 |
| cuPDLP-C | https://github.com/COPT-Public/cuPDLP-C ，`7b94c41efca42fa176a129a935b59718e1455fad`，HiGHS 自述的 CPU 集成版本；Copyright (c) 2023 COPT-Public | 官方二进制中的 CPU PDLP 与适配代码 | 项目自有部分 MIT，见 `licenses/highs/cupdlp/LICENSE`；原始作者与集成说明一并保留；CSparse 派生部分另适用下述 LGPL 条件 |
| 必要接口头文件 | HiGHS 固定快照内 AMD、RCM、BLAS 接口；保留 Timothy A. Davis 等原始版权 | 关闭 HiPO 时核心仍需包含的接口声明 | AMD BSD-3-Clause、RCM MIT 及上游原始声明，见 `licenses/highs/amd/LICENSE`、`licenses/highs/rcm/LICENSE`；不编入其提供者实现 |
| CSparse 派生部分 | https://github.com/DrTimothyAldenDavis/SuiteSparse ，CSparse；Copyright (c) 2006 Timothy A. Davis | cuPDLP `cupdlp_cs.c/.h`、IPX `sparse_utils.cc/.h`、BasicLU `lu_dfs.c` 中的派生程序 | LGPL-2.1-or-later，采用 LGPL 2.1 条件；全文及来源在 `licenses/highs/csparse/LICENSE` 和 `NOTICE`；完整组合程序对应源码、许可注释及重新链接方法随包提供 |

IPX, Copyright (c) 2018-2020 ERGO-Code. Used in 离线资源配置优化台 under the MIT license.

BASICLU Copyright (c) 2016-2020 ERGO-Code. Used in 离线资源配置优化台 under the MIT license.

CSparse: Copyright (c) 2006 Timothy A. Davis. LGPL-2.1-or-later; see `licenses/highs/csparse/LICENSE`.

## CSparse 源码、修改、调试与重新链接

本包显著声明组合求解程序使用 CSparse 派生部分，其库及使用按 LGPL 条件分发。按照 LGPL 2.1 第 6(a) 节，同一个插件包内直接提供整个组合 CLI 的对应机器可读源代码 `vendor/highs/source/HiGHS-1.16.0-corresponding-source.tar.gz`，不依赖外部下载或书面索取。库源码、CLI/HiGHS 其余源码、接口、构建配置、所需版本文件与适用许可均在其中。构建所需的系统编译器/SDK/标准库由本机提供，不随插件分发。

允许接收者为自己使用修改该组合程序和库、重新链接产生修改版本，以及为调试这些修改而进行逆向工程。插件的文件完整性检查不改变该权利：用户可在自己的插件副本中替换重建程序，并更新自己的 `vendor/highs/binary.json` 哈希。完整步骤见 `licenses/highs/REBUILD.zh-CN.md`。不要求修改宿主、SDK、系统文件或其他插件。

上游对 CSparse 的改动包括名称前缀、稀疏结构与接口适配；HiGHS 已带有来源注释。我们未改动官方二进制。仅在所附对应源码的上述五个文件前添加标明 2026-11-12 的许可/来源说明，数值代码保持原样。其余原始源文件与原始文件头逐字节保留；每个原始与分发文件的哈希见源码中的 `SOURCE_MANIFEST.json`。原始文件头摘录另保存在 `licenses/highs/original-headers/`。

## 未启用、未分发的运行组件

本包不分发官方发行包中的头文件安装树、静态库、`highs_extras`、Python wheel、NumPy、CMake、CUDA/ROCm/BLAS 驱动或额外数据与商标图片。HIPO、GPU 选项关闭；METIS、AMD、RCM、BLAS 提供者未编入选定程序。对应源码仅保留本构建使用的实现和必要接口头文件；包含仍需的 AMD、RCM、BLAS 接口声明及其原始版权/许可，省略 METIS、AMD、RCM 等提供者实现和 Catch 测试框架。接口声明的存在不等于启用提供者功能。

原始许可、免责声明、作者与版权文本保留英文原文；本文件中文解释不取代它们。最终 ZIP 的逐文件一致性检查由本任务打包阶段记录。
