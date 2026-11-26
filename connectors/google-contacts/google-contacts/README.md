# Google 联系人连接器

在 WorkSwarm 查找 Google 账号中已保存的联系人，读取指定联系人的姓名、昵称、邮箱、电话和单位。搜索使用 People API 的前缀匹配。

1. 在 Google Cloud 项目启用 People API，创建 `Desktop app` 类型的 OAuth 客户端。如果项目处于 Testing，将使用的账号加入测试名单。
2. 在 WorkSwarm 安装并点击「连接」。在本机授权入口选择 Desktop OAuth JSON，点击「保存并继续」，再前往 Google 授权。
3. 核对所选账号和联系人的只读权限。授权后返回 WorkSwarm，卡片显示「使用」。
4. 在聊天中启用该连接器，例如「搜索名为 WorkSwarm联系人验收 的 Google 联系人，再读取匹配结果」。

连接器仅申请 `https://www.googleapis.com/auth/contacts.readonly`，业务数据来自已保存联系人。修改联系人、企业目录及「其他联系人」不在支持范围内。需 Node.js 22 或更新版本、能访问 Google API 和 OAuth 的网络，以及浏览器能到达运行 WorkSwarm 的机器的本机回调。账号类型、管理员策略、测试有效期及 API 配额由 Google Cloud 项目决定。连接器本身没有独立付费服务或外置 OAuth 服务。

卡片「取消连接」移除本机授权会话。其他 Google 连接器各用独立会话。远端授权由 Google 账号管理页管理。
