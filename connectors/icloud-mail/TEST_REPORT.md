# iCloud 邮件连接器 1.0.0 测试记录

- 任务 `AH-20261124-icloud-mail`，成员 Song Haoran。执行日期 2026-11-24。
- 宿主为已安装的 macOS WorkSwarm 0.2.8，使用独立数据目录、进程端口、运行时套接字和本机连接器目录。本次未修改宿主源码。
- 运行时为这台 Mac 的 Python 3.9.6。使用标准库访问 Apple IMAP。

| 检查 | 结果 |
| --- | --- |
| Python 运行时 | `python3 -B -m unittest discover -s connectors/icloud-mail/tests -v` 共 17 项通过。包括子进程 MCP 握手、TLS 校验参数、IMAP 线协议、按主题／发件人查询、UTF-8、过期 UIDVALIDITY、附件排除、单邮件读取和安全中文错误。 |
| 独立 TLS IMAP 夹具 | 通过。锁定命令为只读 `EXAMINE`、`UID SEARCH` 和 `BODY.PEEK`，读回合成中文正文。 |
| Apple 网络 | 从测试 Mac 实际访问 `imap.mail.me.com:993`，证书校验通过，协商 TLS 1.2 并读取 IMAP4rev1 能力。该检查未登录账户。 |
| 平台包装 | 官方 Agentic Hub CLI 0.0.1（`c8ee4ef44be0453470114aa5a19f4e1017462907`）在干净暂存目录执行 `validate` 和 `pack` 通过。已对源负载和两个 ZIP 分别运行 `asset_release.py preflight`。 |
| WorkSwarm 卡片 | 从本机构建目录下载安装 1.0.0，出现「连接」及 App 专用密码、iCloud 邮箱地址两项。实装加载器认出 1.0.0，源负载、两个 ZIP 和已安装的五个文件字节一致。卡片保存后显示「使用」，连接详情列出三个工具。原始截图已保存。 |
| 真实账户认证 | 首次聊天调用 `icloud_mail_status` 时 Apple 拒绝登录，格式诊断发现邮箱栏使用了非 iCloud 域名的地址。用户在新的隔离 WorkSwarm 窗口用主 iCloud 邮件地址重新保存同一版本。真实工具调用返回 `connected: true`，Apple IMAP 以只读方式打开 `INBOX`。 |
| 中文聊天搜索和读取 | 经用户授权从 iCloud 网页版仅向同一邮箱发送一封测试邮件。网页收件箱出现唯一主题 `WorkSwarm iCloud QA 20261124`。中文聊天调用 `icloud_mail_search`，Apple 返回一个匹配。随后直接用该返回的 UID 和 UIDVALIDITY 调用 `icloud_mail_read`，正文为「蓝色笔记本，星期五核对。」，格式为 `plain_text`，`truncated` 为 `false`。原始聊天截图隐去工具明细，仅显示虚构主题与正文。 |

在 WorkSwarm 0.2.8，「使用」状态表示凭据已保存，账号认证以实际 IMAP 检查为准。Apple 自发自收的发件动作通过官方网页完成。连接器自身只做收件箱读操作，使用 `EXAMINE` 和 `BODY.PEEK`，实际邮件的已读状态没有单独在 Apple UI 核对。正式 Hub、Windows/Linux、远端宿主及 Apple 密码撤销恢复尚待验证。

2026-11-24 17:25（UTC+8），Song Haoran 在当前连接器会话回复「确认合入」，确认交付上述 1.0.0 实测包及原图。Hub 包 SHA-256 为 `cf9a15f7dc874dbbbe4b2840e694d881c240a3f618252971deea092dcfe24867`，本机包 SHA-256 为 `80bc03f57bdef3c35c0d000a95c672ec6c55a6c08a72f8da6b900693e73d9219`。追踪报告为 `RPT-20261124-icloud-mail-build`。
