# 第三方品牌标志

`icon.png` 源自 [Atlassian 官方品牌素材](https://atlassian.design/foundations/logos)，原文件为 `jira/PNG/Jira_icon.png`。商标归 Atlassian 所有。该图标用于在 WorkSwarm 中识别所连接的 Jira 服务。连接器由 openJiuwen 团队提供。

[适用品牌使用条款](https://www.atlassian.com/legal/trademark)

## 标准 MCP 客户端与适配

运行时使用 mcp-remote 0.16.6（https://github.com/punkpeye/mcp-remote/tree/e4dc3713b0d6a727cbeb21f38324d20a6692dc5f）。MIT，Copyright (c) 2025 Cloudflare, Inc.，完整文本见 licenses/mcp-remote/LICENSE。客户端从固定 npm 发行版下载、不修改、不打进 ZIP；它不是 Atlassian 官方产品。有限 Node CLI 基于本团队 Linear 1.2.1 的连接方式；OAuth 跳转适配保留 MIT 客户端的待处理流程、注册预检及重试保护检查，改为把 URL 交给 WorkSwarm 卡片。更改日期 2026-11-23；来源及复用范围见仓库 SOURCE_REVIEW.md。

Atlassian 官方托管服务 https://mcp.atlassian.com/v2/mcp?tools=all 由服务方运行，本包不复制其服务端代码或技能。商标及服务权限独立于开源客户端许可。
