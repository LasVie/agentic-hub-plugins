# Google 日历连接器

查询 Google 主日历，创建单次个人日程，再回读确认。查看时可按时间段和关键词筛选。

1. 在 WorkSwarm 安装连接器。运行设备需要 Python 3.11 或 3.12，并能访问 PyPI、Google OAuth 和 Google Calendar API。
2. 使用已配置的 Google Workspace Desktop OAuth 客户端，或在自己的 Google Cloud 项目启用 Google Calendar API，创建 Desktop app OAuth 客户端后导入 JSON。已配置 Drive、Docs、Sheets 或 Slides 的设备可以复用同一份客户端配置。
3. 点击连接器卡片的「连接」，在 Google 核对并同意自有日历的日程权限。授权在运行 WorkSwarm 的本机浏览器回跳。
4. 点击「使用」，在聊天中选用 Google 日历技能。可以说「查明天 09:00 到 18:00 的日程」或「明天 20:00 创建一条 15 分钟的测试日程，设为私密、空闲、无提醒，再回读确认」。提供使用的时区。

如需导入 Desktop OAuth JSON，macOS 或 Linux 可以在安装后运行：

```bash
python3 -B "${JIUWENSWARM_DATA_DIR:-$HOME/.jiuwenswarm}/agent/workspace/mcp/mcp_hub/google-calendar/launcher.py" configure --client-file "/本机路径/client_secret.json"
```

Windows 使用 `py -3.12` 与对应的本地启动器路径。首次启用需要授权此卡片的 `calendar.events.owned`。CLI 使用 `primary` 主日历，支持查询、读取和创建带时间的单次日程。创建时没有参会人。选择测试模式可创建私密、空闲、无提醒的条目。

凭据与现有 Google Workspace 连接器使用同一受限目录。Calendar 单独保管会话。点「断开」会清除这张卡片的本地授权。

[Calendar API 权限](https://developers.google.com/workspace/calendar/api/auth) · [Google Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)
