# mcp-server-dev 1.0.0

负责人：Vannes Wijaya。候选 CAND-ANT-011；任务 AH-20261022-mcp-server-dev。

这是历史 [MCP Builder](https://agentichub.openjiuwen.com/assets/4c94938898ed4d3580593e5535f2315b) 的配套扩展：路径规划、MCP App UI 示例和 MCPB 打包。三个 Skill 由 Hub Plugin manifest 注册。插件本身不注册 MCP；用户主动运行脚本时才创建工程。

- 从 skills/mcp-dev-route/SKILL.md 进入；先说明本地访问、UI 和原型需求。
- Python >=3.9 可执行 scripts/devkit.py；生成 App/MCPB 示例要求 Node >=20、npm 和网络安装依赖。
- 生成器拒绝已有目标目录。示例版本 0.1.0，与插件版本 1.0.0 分别记录。
- 原型工具仅做有界加法。App 构建后注册 UI 资源并保留文本回退；MCPB 包声明外部 Node 运行时。
- 通用 MCP 实现、远程 HTTP 和认证复用已有 MCP Builder；本插件未测试远程部署或真实宿主 UI。
- 参考各 Skill 中完整步骤；测试驱动与记录在仓库资产父目录，不进入发布 ZIP。

THIRD_PARTY_NOTICES.md 和 licenses/claude-plugins-official/LICENSE 保留移植来源与 Apache-2.0；不宣称 Anthropic 官方背书，不替仓库原创部分选定许可证。发布者字段记录本次负责人显示姓名，不推测其 Hub 登录名；最终上传账号及平台身份以实际登录结果为准。
