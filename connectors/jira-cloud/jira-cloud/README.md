# Jira Cloud 连接器

在授权的 Jira Cloud 项目中查询、读取和创建工单。

安装包后在 WorkSwarm 打开连接器卡片。macOS 和 Linux 首次连接时会下载并校验 acli 1.3.40-stable。Windows 请按官方文档安装 acli。在 WorkSwarm 点连接，再点「前往 Atlassian 授权」。macOS 和 Linux 会在当前浏览器的新标签页继续授权。Windows 会打开默认浏览器。在 Atlassian 页面核对目标站点和权限。授权后回到原来的连接页，选择 Jira 站点并确认。官方 CLI 的 OAuth 同意页同时列出 Jira 和 Confluence 权限。执行者的本机回调端口 53197 须可用。命令使用 Jira Cloud 项目键和工单键。若组织限制应用授权，请联系站点管理员。

需要 Python 3.9 或以上，Windows 卡片命令使用 Python Launcher 选择 Python 3.12。需要访问 Jira Cloud。服务免费额度、组织授权策略和可用操作由提供商及账号决定。

聊天中选择该连接器及其技能，明确给出目标 ID、操作和目标内容。按目标对象的 ID 回读写入结果。

[提供商文档](https://github.com/atlassian/homebrew-acli/blob/4e8f74c483ab002f2a6b0f17f9babbd62a9ffa95/Formula/acli.rb)
