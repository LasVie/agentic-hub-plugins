# Confluence 连接器 1.1.0 来源审查

2026-11-23，Song Haoran。Confluence Cloud → Confluence 连接器 → confluence-cloud。原 Task AH-20261117-confluence-cloud-connector，Candidate Not Applicable，沿用 repo:agent-mcp:confluence-cloud。原任务尚在 Researching、无交付 PR；旧 1.0.x ZIP 和实测记录原样保留，历史 TWG CLI 1.4.4 的 AUTH_INVALID/401 不改写为新版本通过。

本次依用户明确要求复用团队 Jira 1.1.0（PR #116，提交 110d43ed51e3b424f5b6ebe5d987968a08244ab4）的有限 Node CLI、本机引导、父 IPC 断开退出、独立回调端口及 30 分钟有界授权流程。Confluence 工具范围和中文技能单独适配，不复制官方托管服务、上游技能或提示词。

标准客户端 mcp-remote 固定 0.16.6，源码提交 e4dc3713b0d6a727cbeb21f38324d20a6692dc5f，MIT 全文已审阅，Copyright (c) 2025 Cloudflare, Inc.。复用 Jira 已核验模块 dist/chunk-MKB2ICYW.js，SHA256 8e4e647f0b25dc52a28a6d1cbbb6727851ae0e5ae74a6f2ea23cb4acb7b47638；保留跳转适配原版权说明与完整许可证。客户端从 npm 固定版本下载，禁用安装脚本，模块哈希验证；不向 ZIP 分发 node_modules 或第三方二进制。该客户端不是 Atlassian 官方 CLI，远程服务是官方 MCP。

2026-11-23 核对官方 v2 文档和受保护资源元数据：Confluence 读/写/搜索 scopes 为 read:confluence:agent-interface、write:confluence:agent-interface、search:confluence:agent-interface，另带官方账号要求的 read:me/read:account/offline_access。仅申请这一集合，不复用 Jira 的令牌或权限。用户已亲自在独立 Confluence 同意页 Accept，原版 0.2.8 卡片显示「使用」；授权初稿的 10 个安装文件与其 ZIP 一致。

官方 v2 使用 getConfluenceContent、createConfluenceContent、searchConfluence，及空间元数据工具。授权后实际发现 7 个白名单工具的 schema：读取使用 content_id/detail=full/content_format=markdown；新建使用 parent.spaceId/parentContentId、contentType=page 和 body.format/value。已据此实现独立字段白名单及普通页/父页所属空间检查，源 CLI 已完成真实父页全文读取；不能沿用旧版字段。不开放 Jira、任意 execute/discover、评论、附件、已有页面更新/删除、分享或权限设置。OAuth 写 scope 比本包的新建范围更宽，不能把申请权限等同于工具暴露范围。

保留此前官方 Confluence PNG，未修改，SHA256 739da5cf8f9a986d3890577e600186ab617ba590d4993f2c02ede921c0e826cd；品牌来源与声明沿用旧审查。本次没有把公开商标材料自动重许可为 MIT，也不表示 Atlassian 背书。

来源：
- https://support.atlassian.com/atlassian-ai-gateway/docs/supported-tools/
- https://atlassian.github.io/atlassian-mcp-server/
- https://mcp.atlassian.com/.well-known/oauth-protected-resource/v2/mcp
- https://github.com/punkpeye/mcp-remote/tree/e4dc3713b0d6a727cbeb21f38324d20a6692dc5f
- https://github.com/LasVie/agentic-hub-plugins/pull/116
- https://atlassian.design/assets/a92416454bd0/logos/confluence_app.zip
- https://www.atlassian.com/legal/trademark

最终候选的真实卡片授权、中文聊天搜索/全文读取、新建普通子页 `1277953` 及独立全文回读已完成，实际工具与范围相符；拒绝授权、宿主断开/取消和进程清理已验证。最终两份 ZIP、源码和 10 个安装文件哈希一致；MIT 文本与图标 SHA256 已核对。旧 10 份 ZIP 全部保持原字节。详见 TEST_REPORT.md 与 tests/fixtures/workswarm-0.2.8-20261123.json。Song Haoran 已明确确认该精确版本通过并批准附五张原图提交 PR。许可/分发审查与材料门槛已完成；只提交本资产，未请求合并或 Hub 上架。
