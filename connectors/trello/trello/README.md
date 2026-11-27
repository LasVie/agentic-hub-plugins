# Trello 看板连接器

在 WorkSwarm 聊天中查询 Trello 看板、列表和卡片，在指定列表新建一张卡片，并按卡片 ID 回读确认。

1. 登录 [Trello 应用管理](https://trello.com/apps/admin)。使用有管理权限的工作区创建或选中 Power-Up。在 **API Key** 设置页生成或查看应用 Key。
2. 按 [Trello 官方授权说明](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/) 生成同一 API Key 对应的用户令牌。查询需要 `read`，创建卡片还需要 `write`。Trello 的用户令牌权限覆盖此账号可访问的资源，以服务端授权为准。
3. 安装连接器，点击卡片的「连接」，把 Key 和用户令牌填入各自字段并保存。请勿把凭据发到聊天。
4. 可在聊天中说「查找季度复盘看板，列出待办列表中的风险排查卡片」，或者「在季度复盘看板的待办列表创建一张标题为风险复盘的卡片，创建后读回」。

需要 Trello 账号、有权限的工作区、WorkSwarm 的 Node.js 22 和到 `api.trello.com` 的 HTTPS 网络。令牌过期或撤销时重新生成并在卡片中保存。创建请求结果不明时，先查目标列表中相同标题，核对后再决定是否重试。
