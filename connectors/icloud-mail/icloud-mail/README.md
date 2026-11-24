# iCloud 邮件连接器

在 WorkSwarm 聊天里按主题或发件人搜索 iCloud 收件箱，并读取选中邮件的正文。

## 连接

1. 确认 Apple 账户已启用 iCloud 邮件及双重认证。打开 [Apple 账户](https://account.apple.com/)，进入「登录与安全」中的「App 专用密码」，为 WorkSwarm 生成一个专用密码。
2. 在 WorkSwarm 的 iCloud 邮件连接器卡片点「连接」。填 iCloud 邮箱地址和刚生成的专用密码，保存。邮箱地址填实际的 iCloud 邮件地址，Apple 账户的登录地址可能属于其他邮件服务。
3. 在聊天里说「用 iCloud 邮件搜索主题含 WorkSwarm 验收的邮件，读取这封邮件的正文」。至少提供主题或发件人之一，搜索在收件箱最近 100 封内匹配。建议提供完整或唯一主题。含中文等非 ASCII 字符的搜索会在本机比较最近邮件的邮件头。

宿主需要能启动 Python 3.9 或以上版本的 `python3`，并通过 TLS 访问 Apple 的 `imap.mail.me.com:993`。连接过程使用 Apple 的 iCloud 邮件服务和用户自有账户。连接器依赖 Python 标准库，无额外 Python 包或连接器订阅。

第一版支持 iCloud 收件箱的只读操作。Apple 授予的是 App 专用密码，收件箱和只读范围由连接器的代码限制。发件、草稿、附件下载、其他文件夹和修改已读状态不在工具范围内。若 Apple 撤销了专用密码，先在卡片取消连接，再生成新密码并重新连接。

[Apple 邮件服务器设置](https://support.apple.com/en-ie/102525) · [Apple App 专用密码](https://support.apple.com/en-us/102654)
