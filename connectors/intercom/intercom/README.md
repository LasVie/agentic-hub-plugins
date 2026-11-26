# Intercom 客服连接器

在 WorkSwarm 连接 Intercom，搜索客服会话与联系人，读取指定记录，并取得服务提供的原链接。

1. 在 WorkSwarm 安装连接器并点击「连接」。
2. 在本机浏览器选工作区地区。地址是 `app.intercom.com` 时选美区，`app.eu.intercom.com` 时选欧区。
3. 在 Intercom 核对应用 **WorkSwarm Intercom Connector**、工作区、权限及 `http://127.0.0.1` 回调。Intercom 官方授权会申请会话及联系人等读取、添加内部备注、文章写入、查看 Fin 受众和使用 Fin Operator；本连接器只调用会话和联系人查询及读取。
4. 回到 WorkSwarm，启用该连接器后，在聊天里说「搜索含有某个标记的 Intercom 客服会话，读取指定会话并给出原链接」。

需要可以授权的 Intercom 工作区账号、到所选地区官方 Intercom MCP 的 HTTPS 网络和浏览器能访问本机回调。Node.js 22.12.0 或更新版本，无需另装包、OAuth JSON 或应用密钥。工作区、产品及账号权利由 Intercom 管理；开发工作区的功能和适用地区以官方说明为准。局限包括澳区、无法访问本机回调的远程部署和服务端权限限制。

卡片「取消连接」清除本机授权，可在 Intercom 管理远端授权。若在 Intercom 撤销后卡片仍显示「使用」，点「取消连接」再连。
