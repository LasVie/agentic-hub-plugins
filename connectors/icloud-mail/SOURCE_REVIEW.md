# iCloud 邮件连接器来源审查

任务 `AH-20261124-icloud-mail`，成员 Song Haoran。名称映射为 iCloud Mail → iCloud 邮件连接器 → `icloud-mail`。独立开发，无对应候选项。

2026-11-24 核对了 Apple 关于 IMAP 主机、端口、用户名称和 App 专用密码的公开设置说明。只参考可互操作的接口事实。使用已安装 Python 的 `imaplib`、`ssl`、`email` 等标准库，没有复制、分发 Python 字节码、源代码或第三方依赖。参考 [Apple 的邮件服务器设置](https://support.apple.com/en-ie/102525)、[App 专用密码说明](https://support.apple.com/en-us/102654)、[IMAP4rev1](https://www.rfc-editor.org/rfc/rfc3501) 和 [Python IMAP 客户端](https://docs.python.org/3.9/library/imaplib.html)。

调研时检查了已上架的网易邮箱 1.0.0（`e9f8dee41809496eb64bca3052551e93`）的卡片字段和 IMAP 服务器选择。它提供通用的 `IMAP_HOST` 环境变量，但卡片没有该字段，也没有 iCloud 主机预设。仅比较接入范围。广域候选 `CAND-DSH-257` 仅用已有的候选记录比较，未复用其代码。本连接器运行时由未接触这些第三方实现的新开发上下文依据公开协议独立实现。包装结构沿用本仓库连接器契约。

交付包无需附第三方软件许可证。使用 iCloud 名称说明目标服务，未分发 Apple 图标、字体或站点素材。
