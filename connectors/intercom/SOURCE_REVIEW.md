# Intercom 客服连接器 1.0.0 来源审查

2026-11-24，Song Haoran。Intercom → Intercom 客服连接器 → intercom。CAND-CLD-029，AH-20261124-intercom，repo:agent-mcp:intercom。

采用独立实现。比较时参考 ChatGPT Intercom 目录的公开功能描述，未读或复制其包源码、提示词或媒体。历史候选记录里的 Claude 包 0.1.0 和 MIT 标记未逐项核实，此交付不使用该包。无供应商商标图形、第三方包和运行时依赖下载。

依据 Intercom 官方 MCP 文档（2026-11-24 查验）和 MCP Streamable HTTP 2025-06-18 规范实现有限客户端，只调用发现、搜索与读取。两区 OAuth 公共元数据声明 S256 和动态注册，美区在 WorkSwarm 自带 Node 上以真实包标识返回 201 公有客户端注册，无 client secret。官方发出 mcp operator challenge，OAuth 同意的范围较包内只读功能宽，详见本地授权入口。没有复制文档原文或整套工具。卡片配置和程序定位沿用团队已验证的 Node 连接器格式（Confluence 1.1.0，PR #117）。Node 运行时由宿主提供，ZIP 不分发 Node 或 npm 客户端源码。

- https://developers.intercom.com/docs/guides/mcp
- https://mcp.intercom.com/.well-known/oauth-authorization-server
- https://mcp.eu.intercom.com/.well-known/oauth-authorization-server
- https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- https://github.com/LasVie/agentic-hub-plugins/pull/117
