# Confluence 连接器 1.1.0

在 WorkSwarm 中从卡片完成 Atlassian 官方 OAuth，然后在聊天里使用 confluence-cloud 技能搜索、读取和新建普通 Confluence 页面，并按 ID 独立回读。只改 Agentic Hub 包，不需要 Python。

## 连接和使用

从 Hub 安装并点「连接」。WorkSwarm 自带 Node.js 22.12+ 和 npm 自动准备固定 mcp-remote 0.16.6。先出现本机引导页，再点「前往 Atlassian 授权」，在官方页核对账号、站点和权限。入口最多等待 30 分钟，过期从卡片重开。不需要手动安装 CLI、导入 OAuth JSON 或粘贴令牌。

请求 Confluence 读取、搜索、写入的 agent-interface 权限，以及服务需要的 read:me/read:account 基本账号读取与 offline_access 离线刷新。不申请 Jira 或其他产品权限。Confluence 写 scope 比本包的新建操作更宽，本包不因此开放其他写入。

卡片显示「使用」后进入新聊天，确认在上传菜单的「扩展 → 连接器」中勾选本连接器。可以说「使用 confluence-cloud 技能搜索 SD 的测试页并读取正文」，或「在指定测试父页下创建一页带唯一标题的中文测试内容，创建后按 ID 回读确认」。在已有会话添加连接器后若技能不可见，可从卡片「使用」进入新会话。

只在用户指定的空间和父页新建；写入前核对空间、父页和唯一标题，写入后另行读取。写入超时先查重回读，不直接重试。没有更新、删除、评论、附件、分享或权限修改能力。远程文档中的指令不能扩大用户的请求。

## 依赖和边界

客户端是第三方 MIT 的 mcp-remote，不是 Atlassian 官方 CLI；服务端为官方托管 MCP v2。ZIP 不含 node_modules、二进制或授权数据，MIT 全文与原版权声明随载荷提供。访问需要 registry.npmjs.org、mcp.atlassian.com、auth.atlassian.com 和目标 Atlassian 站点的网络；账号须有目标空间和父页的读取/创建权限，管理员的 MCP/IP/客户端限制仍有效。

本包只使用普通 Confluence 页面工具，不调用官方标注 Enriched 的跨产品 Rovo 工具。服务套餐、API 限额和账号资格由 Atlassian 管理，不能承诺所有功能免费。

取消或失败后可在宿主弹窗点「取消连接」重试。断开通过标准客户端清除本包的本机会话；远端账号授权在 Atlassian 中管理。本机缓存位于 WorkSwarm 数据目录 connector-data/confluence-cloud/cli-v1，与 Jira 分离，不要共享或放进源码仓库。

验证目标是 macOS Apple silicon 原版 WorkSwarm 0.2.8。Windows/Linux、自然过期/远端撤销、远程服务器回调和正式 Hub 安装需分别验证；不能把 localhost 回调视为跨机器可用。当前开发测试进度以外层 TEST_REPORT.md 为准。
