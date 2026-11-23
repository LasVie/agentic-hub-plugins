# Dropbox 文件连接器

搜索 Dropbox 文件名，列出文件夹，读取元数据和 UTF-8 文本。

安装包后在 WorkSwarm 打开连接器卡片。在 Dropbox 开发者控制台创建 Scoped access 应用，启用 account_info.read、files.metadata.read 和 files.content.read。要读取已有文件需选择 Full Dropbox。把非机密的 App key 写到当前 WorkSwarm 数据目录下的 connector-data/dropbox/app-key.txt，再点连接。有已登记的回调 http://localhost:53682/oauth/callback 时可直接回跳。若应用未登记回调，可在连接页选一次性授权码，将 Dropbox 页面显示的码填回本机连接页。连接页及直接回跳共用本机端口 53682。只读取 1 MiB 内的 UTF-8 文本。

需要 Python 3.9 或以上，Windows 卡片命令使用 Python Launcher 选择 Python 3.12。需要访问 Dropbox。服务免费额度、组织授权策略和可用操作由提供商及账号决定。

聊天中选择该连接器及其技能，明确给出目标 ID、操作和目标内容。按目标对象的 ID 回读写入结果。

[提供商文档](https://docs.dropboxapi.com/dropbox-api/docs/oauth)
