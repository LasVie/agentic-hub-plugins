# HiGHS 对应源码与重新链接说明

本包的求解程序取自 HiGHS 1.16.0 官方发布，源提交为 `f3f113d230429a8c0014b12ab0dd1a3847e58c55`。二进制未作修改；不能把它或其全部组成部分统称为 MIT 软件。

`HiGHS-1.16.0-corresponding-source.tar.gz` 随包提供整个组合 CLI 所需的机器可读源码：HiGHS 核心、命令行入口、IPX、BasicLU、cuPDLP CPU、外部头文件、CMake 配置和版本输入。只省略未参与本构建的测试数据、示例程序、文档图片、Python 包装器及 Git 数据库；由于上游 CMake 无条件读取 `examples/CMakeLists.txt`，保留该文件。原始源文件哈希及五个仅添加许可注释的文件见 `SOURCE_MANIFEST.json`。数值实现未改动。

CSparse 派生代码分别位于 `highs/pdlp/cupdlp/cupdlp_cs.c/.h`、`highs/ipm/ipx/sparse_utils.cc/.h`、`highs/ipm/basiclu/lu_dfs.c`。原始代码已由上游做过前缀、接口和数据结构适配；本包于 2026-11-12 仅为这五个源码文件添加来源、LGPL 与修改日期注释，保留其余原文。它们的 CSparse 派生部分按 LGPL-2.1-or-later 提供。完整 LGPL 2.1 及 CSparse 原始声明均随包附带。

本包按 LGPL 2.1 第 6(a) 节提供源码。允许用户为自身使用修改组合程序、修改这些库并重新链接，也允许为调试这些修改而逆向工程。此许可说明不会将仓库或独立编写的插件包装代码整体重新许可。无需付费、联系开发者或依赖书面源码要约即可取得本包附带的对应源码。

## 独立构建

这些命令只在用户选择的新目录构建，不会安装或改写 WorkSwarm、SDK、其他插件或系统库。需要预先具备 CMake 3.15 或更新版本、Apple Clang 的 C++11 工具链、make 和 macOS SDK（官方二进制使用 SDK 26.5，最低 macOS 26.0；建议使用匹配的当前 SDK/Apple Clang 17 或更新版本）。CMake 不属于插件运行依赖，也未随插件分发。构建使用系统 zlib/libc++/libSystem；这些系统库不在本包中。

```sh
mkdir highs-local-rebuild
cd highs-local-rebuild
tar -xzf /绝对路径/HiGHS-1.16.0-corresponding-source.tar.gz
cmake -S HiGHS-1.16.0 -B build \
  -DCMAKE_BUILD_TYPE=Release -DFAST_BUILD=ON \
  -DBUILD_STATIC_EXE=ON -DBUILD_SHARED_LIBS=OFF \
  -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF \
  -DFORTRAN=OFF -DCSHARP=OFF \
  -DHIPO=OFF -DHIPO_PYTHON=OFF -DBUILD_SHARED_EXTRAS_LIB=OFF \
  -DCUPDLP_GPU=OFF -DHIPDLP_GPU=OFF -DHIGHS_VCPKG=OFF \
  -DZLIB=ON '-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64' \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=26.0
cmake --build build --target highs-bin --parallel 2
```

产物为 `build/bin/highs`。可先修改源码中的库实现，再重新执行构建命令以得到重新链接的 CLI。构建不启用 HiPO、AMD/METIS/BLAS 提供者、CUDA、ROCm、Python 或网络下载。所带 `extern/` 仅保留本构建使用的实现与必要接口头文件。即使 HiPO 关闭，核心仍包含 AMD、RCM、BLAS 接口头文件；因此保留其版权与完整 AMD BSD 三条款及 RCM MIT 许可。METIS/AMD/RCM 提供者实现、Catch 测试框架及其他未选构建数据均已省略。

若本机旧 Command Line Tools 找不到 `<utility>` 等 C++ 标准头文件，可在上述配置命令中显式加入本次构建的 SDK 头文件目录；无需修改系统设置：

```sh
'-DCMAKE_CXX_FLAGS=-isystem /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/c++/v1'
```

本包的源码移除了 Git 数据库，所以重新构建的版本横幅可能显示 `git hash: n/a`。编译器和 SDK 不同也会改变二进制字节；不承诺重建产物与官方二进制逐字节相同。

## 使用自行重新链接的程序

先备份你自己的插件目录，仅在该插件自己的 `vendor/highs/bin/highs` 替换程序。随后用自行计算的 SHA-256 更新同目录上级 `vendor/highs/binary.json` 的 `sha256`；该完整性校验不是对用户修改、重新链接或调试的禁止。保留适用许可证及修改说明，按修改后的真实最低系统要求与架构更新元数据并自行重新测试。不要修改宿主或其他插件。下游分发修改版本时仍需履行相应许可义务。

原始版权与完整许可文本见 `licenses/highs/`：HiGHS、CLI11、pdqsort、zstr、IPX、BasicLU、cuPDLP 与 CSparse。IPX 和 BasicLU 各自选择 MIT 选项；其中 CSparse 派生部分的 LGPL 条件另行保留，不能由该 MIT 选择替换。
