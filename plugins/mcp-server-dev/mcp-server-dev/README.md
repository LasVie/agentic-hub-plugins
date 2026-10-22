# MCP 应用与打包开发助手

修改说明：2026-10-22，版本 1.0.4 补全展示信息、使用说明、三个 Skill 的默认中文指令、生成器帮助与可读错误，以及示例模板中的工具说明、校验提示、界面和构建消息。保留工程生成接口、MCP 协议标识、有界加法和打包处理算法、依赖锁文件、示例工程版本 0.1.0，以及完整原始许可和署名。负责人 Vannes Wijaya；候选 `CAND-ANT-011`，任务 `AH-20261022-mcp-server-dev`。

作为历史 [MCP Builder](https://agentichub.openjiuwen.com/assets/4c94938898ed4d3580593e5535f2315b) 的配套扩展，提供接入路径规划、MCP App 界面示例和 MCPB 本地打包流程。三个 Skill 通过原生 Plugin manifest 注册；用户主动运行脚本时才创建工程。

## 主要功能

- `mcp-dev-route`：根据本地访问、交互界面和原型需求选择开发路径。
- `build-mcp-app`：生成带界面资源与文本回退的 Node.js 示例。
- `build-mcpb`：生成本地打包示例，指导验证、打包、解包和迁移运行。
- 示例工具只执行有界数值加法，便于验证 MCP 协议与错误处理。

## 安装与使用

在兼容宿主的扩展面板导入 `mcp-server-dev-1.0.4-native-test.zip`，确认版本 `1.0.4` 与三个 Skill，然后在目标编程会话选中插件。

从 `skills/mcp-dev-route/SKILL.md` 开始。示例：“我要开发一个带简单交互界面的本地 MCP 原型。请先规划路径，在新目录生成 App 示例，再按 Skill 中的步骤构建与验证。”

也可在载荷目录直接运行生成器：

```sh
python scripts/devkit.py --version
python scripts/devkit.py scaffold --kind app --output /absolute/path/new-app --name demo-app --author "Your Name"
python scripts/devkit.py scaffold --kind mcpb --output /absolute/path/new-mcpb --name demo-mcpb --author "Your Name"
```

将路径和作者替换为实际值；生成器拒绝已有目标目录。完整安装、构建与验证步骤见对应 Skill。MCP 服务器会等待客户端连接，不是交互式命令行程序。

市场包 `mcp-server-dev-1.0.4.zip` 采用 `mcp-server-dev/plugin.yaml` 外层和 `mcp-server-dev/mcp-server-dev/` 内层；本地测试 ZIP 直接包含相同载荷。生成的 `.mcpb` 属于用户工程产物，与本插件市场 ZIP 用途不同。

## 必要依赖

- 生成器要求 Python >=3.9。
- 生成和运行 App/MCPB 示例要求 Node.js >=20、npm；首次安装锁定依赖需要网络。
- 插件不附带 Node.js 或依赖安装目录。MCPB 示例声明外部 Node 运行时。
- 在会话中使用 Skill 需要宿主已配置的模型与相应文件、命令权限。

## 适用范围与限制

通用 MCP 服务实现、远程 HTTP 和认证需求优先复用既有 MCP Builder。插件本身不注册外部 MCP，不自动部署、签名、上传或发布。协议和本地打包验证不等于目标宿主已经支持 App UI；真实宿主界面渲染、远程 OAuth 和云端部署尚未由本轮测试确认。

示例首次安装的依赖各自有许可条件。构建流程会收集实际安装依赖的完整 LICENSE/NOTICE；重新分发生成项目时需保留这些文件。`@modelcontextprotocol/ext-apps` 的实际 LICENSE 包含许可过渡说明，不能只按包元数据概括。

## 来源与许可

上游为 Anthropic 的 `mcp-server-dev`，固定提交 `d4226d062928f8d9505dbdeadd10217d23361052`。完整 Apache-2.0 许可见 `licenses/claude-plugins-official/LICENSE`，复用范围和逐文件修改声明见 `THIRD_PARTY_NOTICES.md`。保留原始许可和署名，不表示获得 Anthropic 官方背书，也不为仓库原创部分另行指定统一许可证。
