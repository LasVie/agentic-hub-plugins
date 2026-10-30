# Eigen 源码获取与许可

RDKit 官方构建日志确认使用 Debian bookworm 的 `libeigen3-dev 3.4.0-4`。其头文件含 Debian 补丁，因此这里同时提供原始源码、对应 Debian 补丁及源包描述文件，不仅提供上游链接。

- `sources/eigen3_3.4.0.orig.tar.bz2`：完整原始源码，保留全部文件与原始许可。
- `sources/eigen3_3.4.0-4.debian.tar.xz`：该版本 Debian 修改、补丁顺序与打包信息。
- `sources/eigen3_3.4.0-4.dsc`：版本、大小、校验和及签名原文；这里只核对 SHA-256，不宣称验证了 PGP 签名。

文件无需联网即可取得。安装了 Debian 源包工具的开发者可在独立目录运行 `dpkg-source -x eigen3_3.4.0-4.dsc` 重建对应源码树；本插件不会执行这些归档或安装任何工具。

Eigen 的 MPL-2.0 覆盖文件仍受 MPL-2.0 管理；对双许可文件选择 MPL-2.0，独立 BSD 文件保留 BSD 条款。完整源码归档中的测试、基准和其他未使用模块保持各自原始许可证，并不因同包分发而改为 MPL。我们没有修改这些归档或 Eigen 源文件。接收者的源码许可权利不受本插件说明限制。

原始下载地址： https://deb.debian.org/debian/pool/main/e/eigen3/ 。归档 SHA-256 见本包 `vendor/rdkit/UPSTREAM.json` 和项目 `provenance.json`。
