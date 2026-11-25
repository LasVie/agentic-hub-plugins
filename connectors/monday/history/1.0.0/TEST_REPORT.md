# monday.com 连接器 1.0.0 测试报告

日期 2026-11-17。任务 `AH-20261117-monday-connector`。

Agentic Hub ZIP SHA-256 `7052835c40a52125b90a8ab2df2983d2e062045fe76c07181538a8662b7d0c8c`。

官方 Agentic Hub CLI 验证和打包通过。原生和带外层元数据的 ZIP 的运行文件一致。
在 macOS Apple silicon 上，通过本机 Hub 兼容目录在原版 WorkSwarm 0.2.8 安装，通过运行文件哈希核对。

- 在隔离 WorkSwarm 0.2.8 的 monday.com 卡片保存真实个人 API 令牌，卡片变为可使用。本机测试进程仅在内存按宿主已保存的凭据调用安装后的包。
- 真实 monday.com GraphQL 接口返回账号有效。在测试看板 openJiuwen 列出已有条目并读取一条，创建一条中文测试条目。按返回 ID 回读，标题及所属看板一致。 [monday.com 测试条目](https://openjiuwenofficials-team.monday.com/boards/5032516681/pulses/2910224522)

首轮功能测试使用已安装包的命令入口。后续聊天实测见下节。

## WorkSwarm 0.2.8 聊天实测，2026-11-17

在隔离的 macOS 环境中使用原版 WorkSwarm、已连接的测试账号和实际配置的 gpt-6.1-sol。对照交付 ZIP 逐文件核对已安装载荷。在 WorkSwarm 对话中引用连接器技能，由模型通过 Bash 发起真实调用。

- 通过卡片已保存的凭据列出 openJiuwen 测试看板，读取已有测试条目，查重后仅创建一个新条目 `2910613877`，再按新 ID 单独回读，核对中文标题和所属看板。
- 原始 WorkSwarm 长图保存在本机验收目录，文件名 `06-monday-1.0.0.png`，SHA-256 `f62d948d1d05e5fdd6efd3010d8ade258375fff0b123161646e0c1816047f919`。
- 正式 Hub 安装、Linux 和 Windows 尚待实测。
