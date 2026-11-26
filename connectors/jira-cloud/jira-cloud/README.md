# Jira Cloud 连接器 1.1.0

在 WorkSwarm 中连接 Atlassian 官方托管 MCP，查询 Jira 工单、按键读取、创建一条个人测试工单并独立回读。只改连接器包，不需要 Python；保留现有 Jira 图标。

## 安装、授权与使用

从 Hub 安装后点「连接」。卡片使用 WorkSwarm 的 Node.js 22.12+ 与 npm 自动准备固定版本 mcp-remote 0.16.6，需要访问 registry.npmjs.org、mcp.atlassian.com、auth.atlassian.com 和目标 Jira 站点。标准客户端处理 OAuth、回调、凭据保存和刷新，连接器不要求手动导入 OAuth JSON 或粘贴令牌。

卡片会先打开本机引导页；入口准备好后点「前往 Atlassian 授权」。入口最多等待 30 分钟，超时后从卡片重开。这只转交标准客户端的官方链接，不接收令牌或 OAuth 回调。

在 Atlassian 浏览器页面检查测试账号、站点及权限并同意。请求 Jira 读取/搜索/写入的三个 agent-interface 权限，以及服务要求的 read:me、read:account 基本账号读取和 offline_access 离线刷新权限；不申请 Confluence、删除或管理权限。基本账号信息用于识别当前用户和发现授权站点；这是独立于 Jira 数据的账号读取授权，连接时请一并核对。如果站点管理员限制第三方 MCP 客户端、域名、IP 或账号访问，需要按站点规则处理，不能由连接器绕过。包不自建 Atlassian OAuth 应用或运行托管 OAuth 服务。

授权后卡片的状态通过真实 MCP 连接、工具清单和授权站点读取确认。聊天可说「查询 KAN 项目最近的测试工单」「读取 KAN-1」「创建一条指定标题和描述的测试 Task 并按键回读」。写入先检查项目/类型及重复标题，只在用户指定项目操作，不修改已有记录或分配人员。必填自定义字段暂不支持。

授权取消/失败时保持未连接；如果宿主弹窗仍显示等待，可点「取消连接」后重新从卡片尝试，不要在聊天或终端反复启动登录。断开清除本包的本机会话，远端应用授权可在 Atlassian 账号中单独管理。

## 实际范围与依赖

本包只开放 Jira 查询、读取、创建及创建所需的项目/类型元数据；不开放任意 execute/discover、Confluence、跨产品 Rovo 搜索、评论、编辑、删除或管理工具。即使远端服务增加工具，本包也按明确白名单过滤。OAuth 的 Jira 写权限比本包的新建操作更广；本包不会因此开放所有写操作。

使用官方 MCP v2 的 tools=all 工具目录，实际工具定义与后台可随服务方变化。使用的 mcp-remote 是第三方 MIT 标准客户端，**不是 Atlassian 官方 CLI**；其版本/模块完整性固定，完整许可证和来源说明随包附上。依赖在本机安装，ZIP 不包含二进制、node_modules 或用户授权数据。

账号、项目权限、API 限额与服务套餐由 Atlassian 管理。当前仅选择普通 Jira 工具，不调用官方标为 Enriched 的 Rovo 工具；不能由此承诺所有 Atlassian 功能免费。授权缓存位于 WorkSwarm 数据目录 connector-data/jira-cloud/cli-v1，和其他连接器隔离；不要共享该目录或放进源码仓库。

本次验证目标为 macOS Apple silicon 的原版 WorkSwarm 0.2.8；Windows/Linux、不同浏览器与服务器的远程回调，以及正式 Hub 安装和人工审核需另行验证。桌面 OAuth 回调绑定运行机器的本机端口；远程服务端不能直接假定能使用另一台电脑的 localhost。
