# 第三方组件说明

本包的 Calendar 白名单 CLI、状态/授权页面及中文技能由团队编写。Google、gws 名称仅用于说明集成来源，不表示官方背书或获得商标许可。

- **gws / @googleworkspace/cli 0.22.5**：https://github.com/googleworkspace/cli/tree/705fb0ecac6f4249679958f6325b809b63fdde17 ，源码标注 Copyright 2026 Google LLC，Apache-2.0。通过已审查的未修改 npm 安装器从固定 GitHub Release 获取原生程序。完整许可证 licenses/gws/LICENSE；根源码和已检查发行文件没有另附 NOTICE。未复制 Rust 源码、品牌素材或修改其发行文件。
- **google-auth-library 11.3.4**：https://github.com/googleapis/google-cloud-node/tree/main/core/packages/google-auth-library-nodejs ，实际使用 npm 11.3.4 完整性锁定发行版。OAuth2Client 标注 Copyright 2019 Google LLC，Apache-2.0。完整许可证 licenses/google-auth-library/LICENSE；未修改发行代码。
- 全部网络安装依赖的精确版本、npm 来源和完整性值在 skills/google-calendar-guide/scripts/package-lock.json 中。node_modules/原生程序不在此 ZIP 中；安装后保留各发行包附带的原始许可与标头。npm ci 禁用安装脚本，随后只显式执行已审查的 gws 固定安装器。

历史 1.0.0 Python 组件已从当前运行载荷移除；其历史包、许可证和源代码记录继续保留在仓库历史目录。
