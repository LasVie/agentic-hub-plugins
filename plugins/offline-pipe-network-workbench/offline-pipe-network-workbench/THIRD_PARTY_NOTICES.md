# 第三方组件与复用说明

本插件使用以下未修改的开源计算组件。此清单不替代原始许可全文；完整许可、作者名单与组件声明均随包附带。新编写的模型适配器、界面和测试不冒充上游作品，也不表示上游背书。

| 组件 | 固定来源与版本 | 实际范围与许可 |
| --- | --- | --- |
| epanet-js | epanet-js/epanet-js-toolkit，0.9.0，84fcb48880a640119ad968161d08a97815931584 | 仅 `web/vendor/epanet/` 三个原始文件；Luke Butler，2019；MIT 全文见 licenses/epanet-js |
| OWA-EPANET | OpenWaterAnalytics/EPANET，2.3.5，444725fbf16ab28b0470ef0ed281dc4849d49583 | 非 MSX 水力引擎；MIT，原始 AUTHORS 与许可全文见 licenses/owa-epanet |
| Emscripten | emscripten-core/emscripten，4.0.6 | 生成的浏览器运行时代码，选择 MIT 许可，完整双许可文本与原始 AUTHORS 保留 |
| musl | Emscripten 4.0.6 sysroot | C 运行时与数学库，完整 COPYRIGHT 及组件版权/许可头见 licenses/musl；包含 Rich Felker、Sun Microsystems、Arm 和其他贡献者声明 |
| compiler-rt | Emscripten 4.0.6 sysroot | 链接的底层编译器运行时；Apache-2.0 WITH LLVM-exception，完整原始许可见 licenses/compiler-rt |
| dlmalloc | Doug Lea，2.8.6 | 内存分配器；原始公共领域/CC0 声明及 CC0 全文见 licenses/dlmalloc |
| Graphics Gems | Steve Hill，Graphics Gems III；原始存储库许可文本快照 SHA-256 7205a055fc9b7e2d3345724e9e0b181212c7730e2f6356ce3a0a1dbfe9045294 | OWA mempool 原始致谢与原始宽松使用授权均保留 |
| GENMMD | Joseph W. H. Liu，York University | OWA 分发的稀疏重排代码；保留其原始作者声明及 OWA MIT 条款 |

原始文件未经修改，逐文件摘要见 web/vendor/epanet/UPSTREAM.json。模型适配器通过公开 C API 调用显式版本引擎，未使用或修补高层默认 MSX 包，也不包含单独 FSL 许可的 EPANET-JS 网站应用。无图片、字体、在线底图、真实水务数据或远程服务素材。

插件自身的 POSIX 服务生命周期源于本仓 offline-score-workbench 1.0.0 的维护机制，已按本插件身份和用途调整。没有修改宿主、SDK、共享依赖或其他插件。
