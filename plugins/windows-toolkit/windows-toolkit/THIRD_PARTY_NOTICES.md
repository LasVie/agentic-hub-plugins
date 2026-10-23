# 第三方材料与许可声明

本插件包含的上游材料及其许可如下。

## dsh-win-toolkit 0.1.3

- 上游：https://github.com/Edge-Echo/dsh-win-toolkit
- 固定版本：npm `dsh-win-toolkit@0.1.3`（gitHead `665bc6947c52e5f66e73233eff4950d11525430c`）
- 许可：MIT
- 版权：Copyright (c) 2026 dsh-mcp-bridge contributors
- 许可全文：`licenses/dsh-win-toolkit/LICENSE`

### 实际复用与修改情况

| 本插件路径 | 来源 | 情况 |
| --- | --- | --- |
| `tools/windows_toolkit.py` | 上游 `lib/index.js` | 改写：把 DSH/Cordis `defineTool` 注册替换为 WorkSwarm/OpenJiuwen `Tool`/`ToolCard` 类；保留每条工具的 PowerShell 脚本语义、Base64 传参方式与返回字段；新增结构化中文错误返回、输入校验与 UTF-8 输出前置设置 |
| `skills/windows-toolkit/SKILL.md` | 上游 `README.md` / `README.zh.md` | 新写：面向 WorkSwarm 的中文使用说明与调用纪律，内容依据上游工具语义 |
| `README.md` | 上游 `README.md` | 新写：中文安装与使用说明 |
| `licenses/dsh-win-toolkit/LICENSE` | 上游 `LICENSE` | 逐字节保留 |

未复用上游的 `cordis.patch.yml`、`lib/cli.js`、`lib/env.js`、`lib/index.d.ts` 等 DSH 宿主专用文件；它们不属于 WorkSwarm 运行时。

上游 README 中的截图与 banner 素材未纳入本交付包。
