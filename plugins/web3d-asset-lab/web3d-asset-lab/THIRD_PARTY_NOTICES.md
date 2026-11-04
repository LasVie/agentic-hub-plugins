# 第三方来源与许可

本包保留以下运行组件以及历史依赖的完整许可与版权声明。仅组合、打包和接入中文工作台；不暗示上游作者背书。

构建输入与锁定版本见外层build-evidence；完整许可保存在本包licenses/。

- @gltf-transform/core@4.5.1 — MIT；licenses/gltf-transform--core--4.5.1/LICENSE
- @gltf-transform/extensions@4.5.1 — MIT；licenses/gltf-transform--extensions--4.5.1/LICENSE
- @gltf-transform/functions@4.5.1 — MIT；licenses/gltf-transform--functions--4.5.1/LICENSE
- iota-array@1.0.0 — MIT；licenses/iota-array--1.0.0/LICENSE
- is-buffer@1.1.6 — MIT；licenses/is-buffer--1.1.6/LICENSE
- ktx-parse@1.1.0 — MIT；licenses/ktx-parse--1.1.0/LICENSE
- ndarray@1.1.1 — MIT；licenses/ndarray--1.1.1/LICENSE
- ndarray-lanczos@0.3.0 — MIT；licenses/ndarray-lanczos--0.3.0/LICENSE
- property-graph@4.1.0 — MIT；licenses/property-graph--4.1.0/LICENSE
- three@0.187.0 — MIT；licenses/three--0.187.0/LICENSE

仅采用glTF Transform的有界模型操作；原生Sharp/libvips及其LGPL二进制不打包。未提供的原生图像I/O入口替换为显式报错模块。彩色贴图缩放由独立浏览器Canvas与SDK实现，属于用户主动选择的有损分辨率调整。演示模型由本插件自行构造，不搬运第三方模型。

## 1.0.5 修改记录（2026-11-04）

固定 glTF Transform 4.5.1，提交 `41156dfa2324ac6c44ddf0a40ec0da194c4731d6`。本项目从官方 ESM 源输入构建只导出 `dedup`、`weld`、`prune` 的模型处理子集，实际移除未使用的 `ndarray`、`ndarray-lanczos` 导入和相关代码生成模块；不对动态执行字符串改名、编码或隐藏。原算法、原生图像 I/O 的显式不支持边界，以及独立 Canvas 贴图缩放保留。修改构建脚本、原始/派生输入哈希和实际依赖图记录在外层 `build/` 与 `build-evidence/`。

`ndarray`、`ndarray-lanczos`、`iota-array`、`is-buffer` 的代码已不在当前运行包；其完整 MIT 许可作为历史来源声明保留，不表示仍提供这些功能。Three.js 和浏览器贴图处理文件保持原字节。此构建是本项目派生子集，不声称为上游官方安全构建或已获 Hub 审批。
