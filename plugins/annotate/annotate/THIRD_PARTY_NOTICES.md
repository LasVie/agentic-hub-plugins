# 第三方来源与许可说明

## Annotate 上游实现

- 来源：https://github.com/FinalAngel/claude-annotate
- 固定提交：d70e57a29ed480b05ff046296572fcc5b761f25e，版本 0.3.2。
- 原权利声明：Copyright (c) 2026 Angelo Dini.
- 许可：MIT。包含免责声明的完整原文保留在 `licenses/claude-annotate/LICENSE`，不改写法律文本。
- 复用材料：上游 `server/index.mjs`、`server/overlay.js` 以及派生的 `package.json`、`package-lock.json`，分别位于本包 `runtime/server/` 和 `runtime/`。
- 适配内容：WorkSwarm 清单和 Skill、标准 MCP 主动读取、内联截图、逐条结束状态、有界等待、运行缓存、启动与依赖准备、示例和测试文档。1.0.2 加入首次使用自动准备依赖、运行环境发现、并发锁和失败重试；1.0.3 将自有指令、工具说明、界面文案、反馈和诊断改为简体中文，协议名称、状态值与原许可不变。
- 复用 JavaScript 的原有文件头保持不变。固定提交的上游根目录没有 NOTICE。上游文档将 tomreinert/claude-annotate 列为灵感来源，本次适配未复制该另一仓库的文件。

## 运行依赖

`runtime/package-lock.json` 固定了依赖，包括 @modelcontextprotocol/sdk 1.32.0（MIT）和 playwright-core 1.63.0（Apache-2.0）。本 ZIP 不分发依赖实现或 node_modules。

首次使用时，启动器通过准备脚本执行锁定的 `npm ci`，保留下载包自带的许可证和声明，禁用依赖安装脚本。仅写入本地插件依赖及运行缓存，不安装全局包或修改 Conda。再次分发已安装依赖时须保留其原许可；传递依赖清单和许可证据另记于仓库来源审查。

Chrome、Python、Node.js 和 WorkSwarm 是外部运行前提，不包含在 ZIP 中。名称仅用于说明兼容性，不代表官方背书。未打包上游标志、媒体、字体或私有数据。

以上 MIT 归属适用于明确列出的上游材料，不自动扩展到仓库新增适配代码；新增代码的统一许可仍由项目负责人决定。
