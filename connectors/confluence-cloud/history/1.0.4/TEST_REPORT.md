# Confluence 连接器 1.0.3 测试报告

日期 2026-11-17。任务 `AH-20261117-confluence-cloud-connector`。

Agentic Hub ZIP SHA-256 `8bbcf50db875209d79815f72d85073e753c8fa4b64f063c35d0d0b765e10d7e1`。

官方 Agentic Hub CLI 验证和打包通过。原生和带外层元数据的 ZIP 的运行文件一致。
在 macOS Apple silicon 上，通过本机 Hub 兼容目录在原版 WorkSwarm 0.2.8 安装，通过运行文件哈希核对。

- 1.0.3 在本机浏览器提交了 Atlassian 站点，官方 TWG CLI 1.4.4 进入设备授权等待，团队测试账号同意后，原版 WorkSwarm 0.2.8 返回已连接。
- 1.0.1 通过官方 CLI 终端补齐站点授权后，在示例空间 SD 搜索并读取原页面，创建了唯一一页中文测试文档。1.0.3 完成完整卡片授权后按同一页面 ID 回读，空间、标题及正文匹配。 [Confluence 测试页](https://openjiuwenofficial.atlassian.net/wiki/spaces/SD/pages/557057)
- 早期页面虽显示同意，CLI 还停在是否打开浏览器的终端提示。1.0.3 按提示实际出现的顺序操作，并等待 CLI 开始轮询后才显示设备授权入口。

首轮功能测试使用已安装包的命令入口。后续聊天实测见下节。

## WorkSwarm 0.2.8 聊天实测，2026-11-17

在隔离的 macOS 环境中使用原版 WorkSwarm、已连接的测试账号和实际配置的 gpt-6.1-sol。对照交付 ZIP 逐文件核对已安装载荷。在 WorkSwarm 对话中引用连接器技能，由模型通过 Bash 发起真实调用。

- 在 SD 空间按标题搜到并读取测试页 `557057`，查重后创建 `589826`，再按新 ID 单独回读，核对空间、标题及返回摘要中的完整测试句。首次自然指令只触发工具搜索，明确按所引用技能调用 CLI 后成功。当前读命令返回页面摘要。
- 原始 WorkSwarm 长图保存在本机验收目录，文件名 `01-confluence-1.0.3.png`，SHA-256 `1129014eb4c94dc3fd9e87880c9c36f4fb3ec2c74d34daba1ad71e34ad7fe65f`。
- 正式 Hub 安装、Linux 和 Windows 尚待实测。

## 1.0.4 官方图标版本，2026-11-17

原来的功能实测对应 1.0.3。本版增加官方 PNG、来源声明，并同步版本号。此次在 WorkSwarm 0.2.8 对实际交付包做安装和图标显示检查。

- 官方 Agentic Hub CLI 校验和打包通过。已检查外层、原生 ZIP 与源码中的图标和字节；运行命令差异仅为版本号。
- 在 macOS Apple silicon 的原版 WorkSwarm 0.2.8 隔离环境，通过本机 Hub 兼容目录安装交付 ZIP。安装文件全部匹配。连接器广场卡片成功解码包内 96 × 96 PNG，并以 48 px 宽度显示。
- 现有 1 项单元测试通过。本次范围为安装与图标显示，真实服务功能实测见上文的上一版本记录。
