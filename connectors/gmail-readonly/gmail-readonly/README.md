# Gmail 邮件连接器 1.7.0

使用 WorkSwarm 自带 Node，从连接器卡片配置自建 Google Desktop OAuth，在聊天中搜索、读取邮件和会话、创建及编辑草稿、发送和回复。保留历史内部名 gmail-readonly，不修改 WorkSwarm 源码。

## 安装和连接

1. 从 Hub 安装，点「连接」。需要 Node.js 22.12+ 和同一安装中的 npm；目标 WorkSwarm 0.2.8 自带该运行环境。首次自动下载固定 google-auth-library 11.3.4，需要访问 registry.npmjs.org；无需 Python、手工 CLI、gws 二进制或系统解压工具。
2. 自建 Google Cloud 项目启用 Gmail API，创建 **Desktop app** OAuth 客户端并下载 JSON；配置同意屏幕和可授权用户。Testing 项目的用户名单、刷新令牌期限、组织管理员规则和 Google 审核要求仍由 Google 管理，本包不代替发布或验证。
3. 卡片打开本机「连接 Gmail」页，选择自己的 Desktop OAuth JSON，点「保存并继续」，再点「前往 Google 授权」。JSON 仅在本机验证保存，无需终端导入。核对账号和 Gmail 读取、草稿/发送权限后亲自同意。只申请 `gmail.readonly`、`gmail.compose`，不追加邮箱/个人资料/OpenID/modify 权限。
4. 回到 WorkSwarm；连接状态通过真实 Gmail 账户资料接口确认。点「使用」，在聊天「上传 → 扩展 → 连接器」确认已勾选 Gmail，再使用 gmail-readonly 技能。若在已有会话启用后未找到技能，可从卡片「使用」进入新会话。没有卡片显示“已安装”就声称授权成功的替代路径。

授权入口最多等待30分钟，Desktop 回调只绑定运行机器 127.0.0.1。浏览器与宿主在不同机器时不能直接使用另一台机器的 localhost，本版不宣称服务器回调已通过。拒绝或失败后，如宿主仍显示等待，请点「取消连接」再试。

## 能力和边界

- 搜索邮件 ID、有界分页；读取邮件、会话及草稿正文和完整 To/Cc/Bcc，不下载附件。只读结果明确标注正文/会话截断；搜索排除垃圾邮件和回收站。
- 按用户明确要求创建普通草稿；编辑指定草稿的 To/主题/正文，核对最新内部消息 ID，保留未编辑头和附件字节。正文编辑同步纯文本/HTML部分，拒绝异常、签名或加密 MIME；草稿原始数据编辑上限4MiB。
- 发送新普通文本邮件、发送已核对的现有草稿、向唯一明确回复目标在原会话回复。每次写入先核对当前账号和全部 To/Cc/Bcc，以唯一 requestId 防止同一请求重复提交；未知结果不自动重试，须先独立回读。
- 不开放邮件删除、归档、标签/设置修改、附件传输、任意 API/URL。OAuth compose 权限宽于包内操作，并不代表本包开放其全部能力。

示例：「搜索标题为我指定主题的测试邮件，读邮件和会话」「在我指定草稿中修改正文，保留收件人和附件，回读确认」「确认只发给我的邮箱，没有抄送密送后发送，并在同一会话回复一次」。真实发信仍需用户明确指令。

## 存储、网络和已测状态

凭据、运行依赖和写入回执位于 WorkSwarm 数据目录 `connector-data/gmail-readonly/node-v1`；Unix目录700、文件600，不进入安装 ZIP。使用官方 Google 认证库处理 PKCE、令牌交换及刷新；业务是固定 Gmail REST 请求，无自动发送重试。需要访问 accounts.google.com、oauth2.googleapis.com、gmail.googleapis.com；Google账号权限、服务配额及费用由提供方管理。

断开只作废本包授权尝试并删除本机 Gmail 会话，不撤销 Google 中同一客户端或其他连接器的远端授权；可在 Google 账号安全页自行管理。Desktop配置、写入回执和下载的固定依赖保留，便于重新授权和核对未知结果。

此版采用用户自建 OAuth，历史团队 OAuth 服务版独立保留。本次目标为 macOS 原版 WorkSwarm 0.2.8；实际验收以外层同版本 TEST_REPORT.md 为准。平台命令声明不代表 Windows/Linux、自然过期、远程回调或正式 Hub 安装/人工审核已验证。
