# Outlook 工作日历连接器

从卡片授权 Microsoft 365 工作或学校账号，在聊天里查询和读取 Outlook 主日历的日程基本信息。首版使用 Microsoft Graph 全球服务。

1. 用组织账号登录 [Microsoft Entra 管理中心](https://entra.microsoft.com/)，在该租户创建「仅此组织目录中的账号」应用。给应用添加「移动和桌面应用程序」平台并注册回调 `http://localhost`。
2. 在 Microsoft Graph API 权限中配置「委派权限」`Calendars.ReadBasic`。如果租户要求管理员同意，请让管理员在本组织核准此授权。记录「目录（租户）ID」和「应用程序（客户端）ID」。桌面公共客户端使用 PKCE，无需客户端密钥。
3. 在 WorkSwarm 安装并点击「连接」，填入两个 ID 后点「前往 Microsoft 授权」，在 Microsoft 页面用拥有 Exchange Online 邮箱的工作账号授权。完成回跳后返回 WorkSwarm。
4. 在聊天中说「查询本周的 Outlook 日程，读取标题含项目例会的那一条」。

使用授权账号主日历。返回标题、开始和结束时间、地点、全天状态及 Outlook 原链接。时间范围需要明确时区，Graph 以 UTC 返回时间。支持按服务游标继续查询，同一时间段中的重复会议实例由 Graph 返回。内容范围是仅凭 `Calendars.ReadBasic` 可读取的基本日程信息。

运行依赖 WorkSwarm 自带 Node.js 22.12.0，要求本地浏览器能访问回环地址，并能访问 `login.microsoftonline.com` 和 `graph.microsoft.com`。测试账号需有有效的 Exchange Online 邮箱和应用授权。连接器无需另购 API，组织现有 Microsoft 365 许可和租户策略仍适用。取消连接会清除本机授权记录。
