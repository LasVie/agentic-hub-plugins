# Notion 工作区连接器

按标题搜索 Notion 页面，读取 Markdown 正文，并在你指定的页面末尾追加一个文本段落。

1. 在 WorkSwarm 的连接器广场安装。运行端需要 Python 3.9 或更新版本，并能访问 npm 和 Notion。连接器会自动下载并校验固定版本的 Notion CLI。
2. 点「连接」，在打开的本机页面记下验证码，再点「前往 Notion 授权」。登录 Notion，选择测试或工作空间，核对验证码后确认。需要该工作区的正式成员资格。
3. 返回 WorkSwarm，在聊天中选中连接器。可说「按标题搜索项目周报并读取正文」或「在这个 Notion 页面末尾追加这条纪要，再回读确认」。
4. 点「断开」可清除本连接器的本地会话。如需撤销服务端访问，可在 Notion 检查已连接的应用。

授权页在 WorkSwarm 的运行设备上打开。本机 Mac 是本轮测试环境。Linux、Windows 和远程运行场景需要分别验证。连接器使用专用本地目录保管 CLI 授权，不要求用户粘贴令牌。Notion 的页面权限和 API 请求限制仍适用。

[Notion CLI 认证说明](https://developers.notion.com/cli/get-started/authentication) · [Notion API 配额](https://developers.notion.com/reference/request-limits)
