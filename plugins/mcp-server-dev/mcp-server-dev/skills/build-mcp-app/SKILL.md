---
name: build-mcp-app
description: 为已有 MCP 服务添加交互式 UI，或生成一个可验证的 MCP App stdio 示例；涉及 ui:// 资源、MCP Apps SDK、文本回退时使用。远程服务及认证先使用 MCP Builder。
version: 1.0.1
---

# MCP App 配套开发

> 修改声明（2026-10-22）：基于 Anthropic mcp-server-dev 固定提交 d4226d062928f8d9505dbdeadd10217d23361052 的 build-mcp-app/SKILL.md 改编。替换宿主专属命令和未实现脚手架，改用随包可执行模板；上游 Apache-2.0 全文见 ../../licenses/claude-plugins-official/LICENSE。

MCP App 在 MCP 工具之外增加独立 UI 资源。工具返回文本/结构化数据，工具的 `_meta.ui.resourceUri` 指向单独注册的 `ui://` 资源；资源使用 `text/html;profile=mcp-app`。宿主不支持 UI 时，文本结果仍可使用。

先确认用户真的需要可视内容或选择操作。普通短表单可先检查宿主 elicitation 能力；不能假定所有客户端支持相同界面协议。

在插件载荷根目录执行：

```bash
python3 scripts/devkit.py scaffold --kind app --output /已有父目录/add-app --name add-app --author "实际作者"
cd /已有父目录/add-app
npm ci --ignore-scripts
npm run build
node server.mjs
```

要求 Python >=3.9（生成器）、Node >=20 和 npm。工程初始版本为 0.1.0；它与插件版本 1.0.1 不同。示例 add 工具只做有界数值加法，无文件、网络和账户访问。运行服务器会等待 MCP 客户端，不是交互命令行。

浏览器 SDK 在构建时打包进 HTML，保留内联许可注释，不依赖 CDN。渲染使用 textContent，不把工具结果作为 HTML 注入。资源路径相对 server.mjs 定位，因此可以从别的工作目录启动。不要将密钥放入资源或工具输出。

连接真实 MCP 客户端，依次验证 initialize、tools/list、tools/call（2+3=5）、resources/list、resources/read。检查资源 URI 和 MIME、非法输入错误以及 UI 不可用时的文本回退。仓库 tests/mcp_server_dev_smoke.mjs 提供可重复协议测试。

最后在实际 MCP Apps 宿主验证：结果显示为 5、明暗主题、错误回退，提供显示版本和关键操作的真实截图。协议测试不证明宿主 UI 兼容；Agentic Hub 是否支持展示此 UI 需实测。本示例没有远程 HTTP、OAuth 或生产业务后端；按 MCP Builder 扩展后另行测试。

本地 UI 若要进一步做 MCPB，请在完成构建后使用 build-mcpb 的打包和许可检查流程；本版本未自动生成两者合并的包，不宣称已测试此组合。
