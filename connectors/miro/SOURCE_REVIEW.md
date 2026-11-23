# Miro 白板连接器 1.1.0 来源审查

2026-11-23，Song Haoran。沿用 CAND-CLD-003、AH-20261117-miro-connector、repo:agent-mcp:miro。命名 Miro → Miro 白板连接器 → miro。此次仅改 Agentic Hub 包，目标原版 WorkSwarm 0.2.8。原 1.0.3 业务实测、1.0.4 图标测试及后续两次 MCP 超时均保留原结论，不能当作本版通过。

复制/适配前审查：复用团队 Confluence 1.1.0 PR #117 的短时 Node 传输与授权框架（3ff569b0e523469fef701da43627773bd615edb8），不复用 Atlassian 的业务参数或权限。保留父 IPC 断开退出、独立回调端口、30 分钟有界授权、本机引导及标准 SDK 的缓存/刷新。Miro 业务边界独立开发，仅读取用户指定白板和新建一条便签后回读，不开放已有内容更新/删除、评论或权限管理。

标准客户端 mcp-remote 固定 0.16.6，源码 e4dc3713b0d6a727cbeb21f38324d20a6692dc5f，MIT 全文已重新审阅，Copyright (c) 2025 Cloudflare, Inc.。保留复用的 OAuth 跳转适配原版权注释、完整 MIT 文本及包内第三方声明。运行模块 dist/chunk-MKB2ICYW.js 的 SHA256 为 8e4e647f0b25dc52a28a6d1cbbb6727851ae0e5ae74a6f2ea23cb4acb7b47638。只从 npm 固定版本解析并校验，禁用安装脚本，不向 ZIP 分发 node_modules 或第三方二进制。此客户端不是 Miro 官方 CLI；服务端是 Miro 官方托管 MCP。

未复制 Miro/Claude 插件代码、技能或提示词，原 Candidate 的 Native Implementation Only 审查继续保留。官方文档和授权后的工具 schema、格式说明只作为公开接口/功能规范核对，远端文字不能扩大工具或用户授权。当前许可模式标为 ported，只表示标准 MIT 客户端适配的实际复用，不表示已获得 Miro/Claude 插件全部内容的重用许可。

已验证公开元数据：官方根地址 https://mcp.miro.com/ 返回 401 及 protected-resource 元数据位置；授权服务器公开 DCR、S256 PKCE、授权码及刷新。实际仅请求 boards:read / boards:write，openid/email 虽公开支持但未申请；服务同意页仍列出当前用户基本资料读取，用户已亲自核对并 Add again/回跳。卡片显示「使用」，实际 SDK 授权/工具发现成功。

授权后核对当前 4 个接口 schema、My First Board、既有测试便签与指定区域。格式说明仅作协议资料，独立实现一张 rect/data-type=sticky 的文本便签，不把远端风格/技能提示词打包或交给模型执行。结构化参数、非空区域/不完整读取拒绝、原子防重和未知写入不重试均已实现；14 项 Node 检查通过。最终包已在原版 WorkSwarm 0.2.8 本地目录夹具中重装并重新授权，真实聊天完成搜索、读取、新建一条中文便签与独立全文回读，详见 TEST_REPORT.md。

沿用官方未修改 PNG，SHA256 8d165ee50fdb031b656084b248333b56c82f292fc3ef7c63291218fdec2cdbdb。原来源 https://files.readme.io/17d4a23-miro-logo-color-square.png，由官方图标文档发布；开发者条款 2.3 允许用标志识别兼容关系。图标保留 Miro 权利及品牌声明，不将商标重许可为 MIT，不表示 Miro 背书。

来源：
- https://developers.miro.com/docs/miro-mcp-server-frequently-asked-questions
- https://developers.miro.com/docs/miro-mcp-server-faq-and-troubleshooting
- https://developers.miro.com/changelog/canvas-tools-replace-layout-tools
- https://developers.miro.com/docs/mcp-usage-and-daily-limits
- https://mcp.miro.com/.well-known/oauth-authorization-server
- https://mcp.miro.com/.well-known/oauth-protected-resource
- https://github.com/LasVie/agentic-hub-plugins/pull/117
- https://github.com/punkpeye/mcp-remote/tree/e4dc3713b0d6a727cbeb21f38324d20a6692dc5f
- https://developers.miro.com/docs/add-a-logo-to-your-app
- https://miro.com/legal/developer-terms-of-use/

最终原生/Hub ZIP 分别为 ac5cdae05a24b024ede223feb1907075f89f2c71e129add9a9445acd8064d80b / fedd4957b91f38040de50775dd5641b682b448ecc00f887ad3a64a8cd5dc420e，已提取核对 11 个载荷文件及许可证。Song Haoran 已确认本版通过并批准五张原图公开提交 PR，当前 Submitting；不包含自动合并或 Hub 发布。
