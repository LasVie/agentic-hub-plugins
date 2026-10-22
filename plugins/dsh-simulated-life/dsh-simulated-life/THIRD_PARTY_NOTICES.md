# 第三方来源与修改说明

上游：https://github.com/john-walks-slow/dsh-simulated-life

固定提交：`93cbc648fa4efb6da11513aff9eaf7888db94105`。完整 MIT 许可与原版权声明逐字保留在 `licenses/dsh-simulated-life/LICENSE`。

复用路径：
- `vendor/deduplication.ts`
- `vendor/formatter.ts`
- `vendor/loader.ts`
- `vendor/types.ts`
- `runtime/engine.mjs`

`vendor/` 保存实际复用 TypeScript 源码；生成的运行引擎通过 esbuild 0.25.12 编译。esbuild 仅用于开发，未随运行包分发。WorkSwarm 原生 Tool/Rail、文件锁与路径限制、中文说明及界面是本次适配新增工作。本说明不为整个仓库或新团队代码重新指定统一许可。

修改范围：替换 DeepSeek Harness 注册与专用界面；增加本地 Node stdin 桥、中文错误、输入限制、原子写入与会话隔离。

`vendor/formatter.ts` 的两处标题已改为中文，其余上游算法保留；宿主调用前增加文件与路径预检，反应写回和状态持久化由原生适配层实现。

额外修正：loader 限制日期目录名并跳过无效事件；deduplication 在窗口完全为空时也清理过期指纹。
