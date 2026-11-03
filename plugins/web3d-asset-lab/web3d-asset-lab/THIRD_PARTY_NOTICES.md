# 第三方来源与许可

本包保留以下实际运行组件的完整许可与版权声明。仅组合、打包和接入中文工作台；不暗示上游作者背书。

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
