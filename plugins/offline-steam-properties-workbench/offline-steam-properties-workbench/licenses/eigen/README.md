# Eigen 对应源代码

本插件包含 CoolProp 8.0.0 的原始二进制 wheel。它使用的 Eigen 5.0.1 是头文件库，主要遵循 MPL-2.0，另有原文件注明的 BSD、Apache 和 MINPACK 条款。

同目录的 `eigen-5.0.1-corresponding-headers.tar.gz` 提供这些部分的可修改源代码：全部 `Eigen/` 头文件、CoolProp 实际引用的 `unsupported/Eigen/Polynomials` 模块、原始 README 以及完整原始许可文件。源文件保持原样；归档仅省略不参与这部分使用的测试、基准、文档媒体和其他 unsupported 模块。归档内 `SOURCE_MANIFEST.json` 记录每个原始文件的 SHA-256。

原始官方归档：
https://gitlab.com/libeigen/eigen/-/archive/5.0.1/eigen-5.0.1.tar.gz

原始归档 SHA-256：`e9c326dc8c05cd1e044c71f30f1b2e34a6161a3b6ecf445d56b53ff1669e3dec`。

随包对应头文件归档 SHA-256：`0a44ffcab8abdb2515f3b418d298da9a78ed7c309bdbfce3ed54e756d47dfca0`。

您可直接解压随包源代码，无需付费或联网。MPL-2.0 赋予的查看、修改和分发相关源代码的权利继续适用；分发修改时请保留相应声明并遵守原许可。`LICENSE` / `COPYING.MPL2` 和其他 `COPYING.*` 保留完整原文。本说明不改变其他上游组件或插件集成代码的许可，也不把整个插件重新授予 MPL 许可。

该归档用于源代码可获取性；运行插件不需要编译器。官方 CoolProp wheel 未作修改。需要重建数值引擎时，应从所记录的 CoolProp 提交和其依赖配置开始；本项目未承诺字节一致的重建结果。
