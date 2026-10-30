# 第三方许可与改动说明

本插件「离线光学实验室」包含 **Ray Optics Simulation v5.4.0** 的选定几何与光线算法移植。上游项目：<https://github.com/ricktu288/ray-optics>；固定提交：`811f508d2b070898c241a568b0c167dcb8645251`。作者与贡献者的原始版权声明和完整 Apache License 2.0 原文位于 `licenses/ray-optics/LICENSE` 及 `licenses/ray-optics/upstream/` 中对应源码。未发现该提交含独立 NOTICE 文件。本文件是本插件补充说明，不替代原始许可。

> Copyright 2024 The Ray Optics Simulation authors and contributors

`engine/geometry.mjs` 与上游 `src/core/geometry.js` 内容相同，仅扩展名改为 `.mjs`。`engine/core.mjs` 是 **2026-10-30 修改的移植文件**，保留 Apache-2.0 声明；下表列明使用范围。保留的完整原始文件用于来源和许可核对，不由运行时导入。

| 原始文件（相对上游根目录） | 本插件使用和修改 |
| --- | --- |
| `src/core/geometry.js` | 原文保留几何运算；运行时调用点、线、距离、交点、向量等函数 |
| `src/core/sceneObjs/LineObjMixin.js` | 移植正向光线与有限线段相交判断，增加平行、退化与距离边界检查 |
| `src/core/sceneObjs/lightSource/SingleRay.js` | 单光线起点/方向和等量 s/p 初始分量 |
| `src/core/sceneObjs/lightSource/Beam.js` | 均匀中点采样和法向发射；改为明确 rayCount、固定总相对功率，去除视口密度与随机角度 |
| `src/core/sceneObjs/mirror/Mirror.js` | 移植 `onRayIncident` 的平面反射公式 |
| `src/core/sceneObjs/glass/IdealLens.js` | 移植 `onRayIncident` 的二倍焦距几何构造，支持正负焦距和旋转 |
| `src/core/sceneObjs/glass/PlaneGlass.js` | 移植入射侧判断与法向构造；仅均匀折射率 |
| `src/core/sceneObjs/glass/Glass.js` | 参考直边多边形的交点与入射侧处理；本版用有向边与绕序确定出入，拒绝顶点/重叠歧义，不含弧线和随机探测 |
| `src/core/sceneObjs/BaseGlass.js` | 移植向量 Snell/Fresnel 方程、全内反射和 s/p 能量分裂；移除表面/体积合并、GRIN 和低功率显示抽样放大 |
| `src/core/sceneObjs/other/Detector.js` | 移植有向功率、法/切分量与分箱累计；增加端点分箱保护 |
| `src/core/Simulator.js` | 参考逐光线寻找最近交点的组合追踪顺序；另写有界队列、分段输出与明确截断报告，未捆绑完整 Simulator 类 |

本插件不是上游完整浏览器应用，不保证接受其 JSON 格式。未复制上游图库、图像、字体、界面翻译、网站、主题、模块库或示例场景。本插件示例由维护者独立构造，中文界面和 Python 服务为本插件文件。

上游完整应用声明的 i18next、seedrandom、mathjs、bezier-js、canvas2svg、Vue、Bootstrap 等包 **未安装、未打包、未在运行时导入**。保留的原始证据源码中存在相应 `import` 语句，不代表交付这些包。执行入口仅加载 `engine/cli.mjs` → `engine/core.mjs` → `engine/geometry.mjs`；所选执行路径没有外部 npm 依赖、联网或模型服务。

## 再现与核对

无需生成压缩 bundle 或重新下载依赖；发布的是可读 ES 模块。安装现有 Node.js 18+ 后运行 `node engine/cli.mjs`，输入格式见 `engine/README.md`。维护仓库中的 `SOURCE_REVIEW.md` 和 `provenance.json` 记录固定来源、逐文件 SHA-256 与测试。任何修改仍须保留本通知、原始许可和适用的版权声明。
