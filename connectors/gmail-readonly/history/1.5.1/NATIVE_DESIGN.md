# Gmail 邮件连接器 1.7.0 设计

2026-11-23；Song Haoran；沿用 AH-20261111-gmail-connection、repo:agent-mcp:gmail-readonly。只修改连接器包，保留原 1.5.1、PR #93 和旧 ZIP。新版独立版本 1.7.0，不覆盖另存的团队 OAuth 1.6.x。

复用团队 Calendar 1.1.0 的 Node 安装定位、固定 npm 依赖、私有原子存储及 Desktop OAuth 本机配置页。只下载固定 google-auth-library 11.3.4；Google 官方库负责 S256 PKCE/state、授权和刷新。邮件业务独立使用 Node 内置 fetch，固定 Gmail REST 路径、无自动重试，不开放任意 URL、账号或 API。只请求 gmail.readonly、gmail.compose。干净环境没有预置 Gmail 会话或客户端；用户在卡片打开的本机页导入自己的 Desktop OAuth JSON。

保留搜索、邮件/会话/草稿读取、现有草稿编辑、发信、草稿发送、原会话回复；补充创建普通草稿供完整草稿流程使用，不扩大 Google 权限。只读有界分页、MIME/字符/响应限制及明确截断标志；不加载邮件内资源。草稿保留未编辑头和附件字节，签名/加密或异常 MIME 拒绝改写。修改正文时同步纯文本及 HTML 正文，附件不改；回复保留主题并使用有效 Message-ID、References、In-Reply-To 和 threadId。

写入须提供当前账号、明确核对的完整 To/Cc/Bcc、唯一 requestId；先读账户/目标，核对后执行一次。相同请求保存私有回执，未知结果禁止自动重试；正文和令牌不进公开错误。每次写入后需要独立业务回读。此次 QA 仅创建专用虚构测试草稿，所有实际收件人等于授权邮箱；不触碰其他草稿或收件人。

短时父/worker IPC 和有限等待；父进程退出、取消或超时停止 worker/网络/回调。logout 作废授权尝试并清本包本地令牌，不撤销其他连接器远端授权。宿主失败弹窗可能仍需手动取消；实际行为须实测。运行与业务成功、正式 Hub 安装及跨平台支持均待当前包测试，不能从声明推断。
