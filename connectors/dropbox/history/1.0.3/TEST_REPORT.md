# Dropbox 文件连接器 1.0.2 测试报告

日期 2026-11-17。任务 `AH-20261117-dropbox-connector`。

Agentic Hub ZIP SHA-256 `5a4d1cbf8c83d6e8d0ab0fbd494c9f7ec6e39a60e4f9144c9d0aec1d84131e9f`。

官方 Agentic Hub CLI 验证和打包通过。原生和带外层元数据的 ZIP 的运行文件一致。
在 macOS Apple silicon 上，通过本机 Hub 兼容目录在原版 WorkSwarm 0.2.8 安装，通过运行文件哈希核对。

- 自建测试应用已启用 account_info.read、files.metadata.read 和 files.content.read。首轮实测中，开发者控制台没有保存该本机回调地址，Dropbox 拒绝了最初的回调请求。
- 1.0.2 通过备用流程在真实 Dropbox 页同意读取，由本机连接页提交一次性授权码，使用 PKCE 换取离线授权。WorkSwarm 0.2.8 返回已连接。
- 经用户批准，在测试目录 open Jiu we 用 Dropbox 网页上传一个独立的虚构 TXT。使用连接器实际列目录、按文件名搜索、读取元数据和原文。搜索文件 ID 与元数据一致，读取的 UTF-8 内容和上传源逐字一致。

首轮功能测试使用已安装包的命令入口。后续聊天实测见下节。

## WorkSwarm 0.2.8 聊天实测，2026-11-17

在隔离的 macOS 环境中使用原版 WorkSwarm、已连接的测试账号和实际配置的 gpt-6.1-sol。对照交付 ZIP 逐文件核对已安装载荷。在 WorkSwarm 对话中引用连接器技能，由模型通过 Bash 发起真实调用。

- 列出测试目录，以完整的唯一测试文件名搜索，按返回路径读取元数据和两行 UTF-8 正文。搜索与元数据文件 ID 一致，正文与测试源逐字匹配。搜索命令无目录过滤参数，实测通过精确文件名和结果路径限定测试文件。
- 原始 WorkSwarm 长图保存在本机验收目录，文件名 `04-dropbox-1.0.2.png`，SHA-256 `409822812a335248326e9828015343804f5af5b0607f8fb1c0d3d53ea16ccc9b`。
- 正式 Hub 安装、Linux 和 Windows 尚待实测。

## WorkSwarm 0.2.8 自动回跳实测，2026-11-17

- 在已用于测试的 Dropbox 开发应用 openJiuwen 登记 `http://localhost:53682/oauth/callback`，并在刷新控制台后确认该地址已保存。沿用原有只读授权范围。
- 在隔离 WorkSwarm 0.2.8 先断开该测试配置的连接，再从 Dropbox 1.0.2 卡片点击「连接」，打开默认的自动回跳入口。Dropbox 同意页返回本机 `/oauth/callback`，页面显示授权成功，WorkSwarm 卡片从「连接中」自动变为「使用」。流程全程没有输入一次性授权码。
- 从卡片返回聊天，引用 Dropbox 技能调用 `status`、`metadata` 和 `read`，确认连接状态并从真实 Dropbox 读取测试 TXT 的两行 UTF-8 原文。WorkSwarm 原始聊天长图保存在本机验收目录，文件名 `08-dropbox-1.0.2-auto-callback-readback.png`，SHA-256 `163f7e279952ff4bbb70284766392565f967b081ebea3f7757a3ce910cba69c8`。

## 1.0.3 官方图标版本，2026-11-17

原来的功能实测对应 1.0.2。本版增加官方 PNG、来源声明，并同步版本号。此次在 WorkSwarm 0.2.8 对实际交付包做安装和图标显示检查。

- 官方 Agentic Hub CLI 校验和打包通过。已检查外层、原生 ZIP 与源码中的图标和字节；运行命令差异仅为版本号。
- 在 macOS Apple silicon 的原版 WorkSwarm 0.2.8 隔离环境，通过本机 Hub 兼容目录安装交付 ZIP。安装文件全部匹配。连接器广场卡片成功解码包内 128 × 128 PNG，并以 48 px 宽度显示。
- 现有 1 项单元测试通过。本次范围为安装与图标显示，真实服务功能实测见上文的上一版本记录。
