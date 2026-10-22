# 第三方来源与修改说明

上游：https://github.com/Laplace-bit/dsh-pianist

固定提交：`6ab631567700efa80a954f33eb5534b265d91ddd`。完整 MIT 许可与原版权声明逐字保留在 `licenses/dsh-pianist/LICENSE`。

复用路径：
- `vendor/audio/generated-piano.ts`
- `vendor/core/errors.ts`
- `vendor/core/normalizer.ts`
- `vendor/core/performance-payload.ts`
- `vendor/core/performance-state.ts`
- `vendor/core/tempo-map.ts`
- `vendor/core/timeline-index.ts`
- `vendor/core/timeline.ts`
- `vendor/core/transpose.ts`
- `vendor/core/types.ts`
- `vendor/core/validator.ts`
- `runtime/engine.mjs`
- `runtime/player.js`

`vendor/` 保存实际复用 TypeScript 源码；生成的运行引擎通过 esbuild 0.25.12 编译。esbuild 仅用于开发，未随运行包分发。WorkSwarm 原生 Tool/Rail、文件锁与路径限制、中文说明及界面是本次适配新增工作。本说明不为整个仓库或新团队代码重新指定统一许可。

修改范围：替换 DeepSeek Harness 注册与专用界面；增加本地 Node stdin 桥、中文错误、输入限制、原子写入与会话隔离。

仅使用 MIT 的 `src/audio/generated-piano.ts` 合成备用音色；未复制或下载 Salamander Grand Piano CC BY 3.0 录音、MP3 包、sample manifest 或其他媒体资源。播放器是本次中文适配界面。
