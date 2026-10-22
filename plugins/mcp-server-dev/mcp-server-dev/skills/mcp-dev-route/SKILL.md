---
name: mcp-dev-route
description: 当用户开发 MCP 服务、选择远程 HTTP 或本地 stdio、添加 MCP App UI、打包 MCPB 时使用。先复用 MCP Builder 的通用服务开发能力，再选择配套专项技能与可执行示例。
version: 1.0.1
---

# MCP 开发路径规划

1. 从需求确认：是否访问本机文件/桌面、是否需要交互 UI、是否仅做原型。未明确的条件先询问，不能猜测认证或部署权限。
2. 在用户工作区保存 JSON，例如 `{"local_access":true,"interactive_ui":true,"prototype":false}`。三个键必须齐全且都是布尔值。
3. 定位本插件载荷根目录（包含 manifest.json），运行 `python3 scripts/devkit.py plan /绝对路径/spec.json`。该命令只输出规划。
4. 通用工具/资源/提示词、服务实现和远程认证使用已有 [MCP Builder](https://agentichub.openjiuwen.com/assets/4c94938898ed4d3580593e5535f2315b)。未安装时请用户取得该资产，或根据官方 SDK 完成相同工作；不要假称已调用或复制其源码。
5. UI 使用 [build-mcp-app](../build-mcp-app/SKILL.md)；本地分发使用 [build-mcpb](../build-mcpb/SKILL.md)；本地 UI 同时使用两项。纯云 API 默认规划远程 Streamable HTTP；原型默认 stdio。

本插件扩展现有 MCP Builder，不另外提供通用开发教程。生成的演示工程为 stdio：远程 HTTP 规划不表示自动生成、部署或验证了远程服务。插件自身不注册 MCP，也不调用云账户。

对每次交付分别记录：生成工程版本、SDK 版本、协议测试结果、宿主实测、最终提交状态。协议通过不能替代宿主 UI 实测；Hub“已提交待审核”和“已发布”分别记录。
