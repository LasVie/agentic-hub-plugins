---
name: build-mcpb
description: 用户需要将 stdio MCP 服务打包为 MCPB，验证 manifest、运行时依赖或本地分发时使用。生成可运行的只读示例，保留依赖许可，并验证解包后的真实协议调用。
version: 1.0.4
---

# MCPB 配套开发

> 修改声明（2026-10-22）：基于 Anthropic mcp-server-dev 固定提交 d4226d062928f8d9505dbdeadd10217d23361052 的 build-mcpb/SKILL.md 改编。精简为经过实际验证的示例，纠正“必然自带运行时”的表述，不复制原本地文件访问示例。Apache-2.0 全文见 ../../licenses/claude-plugins-official/LICENSE。

> 中文补全声明（2026-10-22）：补充默认输出语言及生成项目说明、工具提示和错误信息的语言要求；保留协议、版本与许可原文。

默认使用简体中文输出打包说明、生成报告及可翻译的工具说明、帮助和错误提示；用户明确要求其他语言时按其要求执行。保留 manifest 键、slug、路径、命令、API、协议值和代码语法。依赖原始许可及第三方工具原生诊断保持原文；不要改写它们来掩盖失败。

本地服务通过 MCPB 分发；清单描述身份、入口和 command/args，宿主用 stdio 启动它。MCPB 包装本身不提供文件或网络沙箱。纯云 API 服务优先使用已有 MCP Builder 的远程方案。

在插件载荷根目录执行：

```bash
python3 scripts/devkit.py scaffold --kind mcpb --output /已有父目录/add-bundle --name add-bundle --author "实际作者"
cd /已有父目录/add-bundle
npm ci --ignore-scripts --omit=dev
node collect-licenses.mjs
npx --yes @anthropic-ai/mcpb@2.1.2 validate manifest.json
npx --yes @anthropic-ai/mcpb@2.1.2 pack . /已有父目录/add-bundle.mcpb
```

生成器要求 Python >=3.9。示例工程版本为 0.1.0，manifest_version 为 0.4，入口 server.mjs，启动参数引用 ${__dirname}，运行时要求 Node >=20。此示例不内嵌 Node；干净目标机器必须满足运行时要求。不要将“包已打出”描述为“无依赖可安装”。

保留 node_modules 中所有实际分发依赖及其原许可证。随示例生成的 THIRD_PARTY_NOTICES.md 说明模板来源；安装的 SDK 与传递依赖有各自许可。对最终 .mcpb 解包逐文件复核，排除密钥、开发缓存、测试文件和无关构建工具。没有选择新代码许可证时，不在 manifest 虚填 license。

执行真实 stdio 客户端测试：initialize、tools/list、tools/call（2+3=5），超界输入和未知工具产生错误后正常调用仍可成功。解包到另一目录，按清单 command/args 启动并重复；再在实际目标宿主安装、记录运行时和操作结果，提供真实截图。

后续业务扩展需要分别实现路径真实解析/包含检查（处理符号链接）、文件读量限制、数组 argv 执行、最小权限及敏感信息保护。注解只供宿主参考，不是权限边界。本示例无文件/网络访问。

MCPB 文件是用户生成的项目产物；本插件的 Agentic Hub 提交产物是 mcp-server-dev-1.0.4.zip，两者用途不同。插件不会自动签名、上传或发布。
