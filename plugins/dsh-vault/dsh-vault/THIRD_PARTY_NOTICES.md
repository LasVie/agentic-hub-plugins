# 第三方来源与修改说明

上游：https://github.com/Ox0400/dsh-vault

固定提交：`deebe535663e17db5daf94683888e17928ec74e6`。完整 MIT 许可与原版权声明逐字保留在 `licenses/dsh-vault/LICENSE`。

复用路径：
- `vendor/crypto.ts`
- `vendor/totp.ts`
- `runtime/engine.mjs`

`vendor/` 保存实际复用 TypeScript 源码；生成的运行引擎通过 esbuild 0.25.12 编译。esbuild 仅用于开发，未随运行包分发。WorkSwarm 原生 Tool/Rail、文件锁与路径限制、中文说明及界面是本次适配新增工作。本说明不为整个仓库或新团队代码重新指定统一许可。

修改范围：替换 DeepSeek Harness 注册与专用界面；增加本地 Node stdin 桥、中文错误、输入限制、原子写入与会话隔离。
