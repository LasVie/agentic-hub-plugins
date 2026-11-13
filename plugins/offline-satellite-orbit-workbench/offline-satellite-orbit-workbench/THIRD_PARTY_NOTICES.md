# 第三方来源与许可

本插件是独立集成的中文工作台，不是上游官方产品，也不表示上游或数据来源对本插件作出认可。插件自身的输入检查、有限时间窗分析、工作线程和界面代码不修改下列传播引擎模块。

## Satellite.js 7.2.0

- 来源：<https://github.com/shashwatak/satellite-js/tree/02cd3def8cd7a29ad2342c6382bea7d2098a893c>。
- 官方 npm 包：`satellite.js@7.2.0`；原始归档 SHA-256：`eebc66f7d16609a9cd67552facb67fa919cb471adbc6823001348195e912a6d2`。
- 原权利人声明：`Copyright (C) 2013 Shashwat Kandadai, UCSC Jack Baskin School of Engineering`。源码中其他作者和技术注释保持原样，包括 `io.js` 中 Hariharan Vitaladevuni 和 Theodore Kruczek 的作者注释。
- 许可：MIT。完整原文（保留原字节）位于 `licenses/satellite-js/LICENSE`；上游原始 Python 包信息位于 `licenses/satellite-js/ORIGINAL-PKG-INFO`。
- 覆盖文件：`web/vendor/satellite-js/` 中的 `io.js`、`propagation.js`、`transforms.js`、`constants.js`、`ext.js`，以及 `propagation/` 中的 `SatRec.js`、`check-for-decay.js`、`dpper.js`、`dscom.js`、`dsinit.js`、`dspace.js`、`gstime.js`、`initl.js`、`propagate.js`、`sgp4.js`、`sgp4init.js`。
- 修改：无。上述 16 个发布模块逐字节复制，合计 106,103 字节；完整路径和原始 SHA-256 见同目录 `UPSTREAM.json`。本插件直接使用本地相对模块路径；没有复制根导出文件、可选 WebAssembly、网络目录、其他上游测试集合或开发依赖。

## 继承的 SGP4 许可与出处

Satellite.js 的 README 说明其传播算法继承自 Brandon Rhodes 的 `python-sgp4` 和 Vallado 等人的原始 SGP4 实现。

- Brandon Rhodes：`Copyright © 2012–2016 Brandon Rhodes`，MIT 完整原文位于 `licenses/python-sgp4/LICENSE`。许可文件来源固定到提交 `9442470d5a286b4071ac105fbfe5173ef2b33ab7`，见 <https://github.com/brandon-rhodes/python-sgp4/blob/9442470d5a286b4071ac105fbfe5173ef2b33ab7/LICENSE>。
- Vallado, David A.; Crawford, Paul; Hujsak, Richard; Kelso, T. S. (2006). *Revisiting Spacetrack Report #3*. AIAA 2006-6753。来源：<https://celestrak.org/publications/AIAA/2006-6753/>。
- CelesTrak 的固定提交 `49df0479c950917c0a2c5ac31f2db6477bba57f6` 中的 `NOTICE` 明确说明，原始 C++ SGP4 实现保留其不限制用途的原始条款；其他 Python、MATLAB、C# 实现的 AGPL 条款不用于重新授权这里的原始 C++ 来源。完整声明位于 `licenses/celestrak-sgp4/NOTICE`。
- 为满足本仓库的许可材料文件名约定，`licenses/celestrak-sgp4/LICENSE` 逐字节保存同一份官方 `NOTICE` 的完整授权说明。上游并未把该份单独的 C++ 授权声明命名为 `LICENSE`；这里没有编造 MIT、AGPL 或其他新条款。本插件没有复制该仓库其他实现。

## 示例与边界

历史校验示例包含公开 TLE 的数值事实和本插件编写的中文名称；不是实时目录，也不代表该航天器当前仍在轨。测试目录中的位置、速度参考数字来自上述 AIAA 官方校验输出，仅用于数值回归。界面示意图不使用地图瓦片、第三方字体、图标或照片。几何过境区间不是实际可见性、真实轨道精度或航天操作安全的保证。
