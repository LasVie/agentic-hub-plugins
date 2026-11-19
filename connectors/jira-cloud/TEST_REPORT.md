# Jira Cloud 连接器 1.0.3 测试报告

日期 2026-11-17。任务 `AH-20261117-jira-cloud-connector`。

Agentic Hub ZIP SHA-256 `71091f0d1902791a1a7c582904ebbdba679b9db824b6a1c5ad0108f8efff34e7`。

- 官方 Agentic Hub CLI 验证和打包通过。原生 ZIP 与带外层元数据的 ZIP 的运行文件一致。
- 在本机 macOS Apple silicon 上，使用 WorkSwarm 0.2.8 隔离配置，通过宿主安装接口从本机 Hub 兼容目录下载并安装 1.0.3，核对了安装后的文件和包中哈希。宿主的连接接口返回浏览器授权入口。
- 隔离运行环境使用官方 Atlassian CLI `1.3.40-stable`。此前在干净目录验证了自动下载、发行校验值、版本查询和未授权状态。用实际 CLI 帮助核对了 JQL 搜索、按工单键读取及创建参数。单元测试覆盖工单键、写入参数和单站点／多站点选择解析。
- 用户在早期版本同意了 Atlassian 权限，浏览器报告授权成功。官方 CLI 随后还要求选择 Jira 站点，即使只列出一个站点也需要选择。1.0.3 在连接页承接此步骤。模拟 CLI 测试使用实际安装的 1.0.3，验证了多站点显示、非法请求拒绝、传入正确选项以及页面反馈连接成功。
- 真实授权使用 `openjiuwenofficial.atlassian.net`。首次 1.0.3 授权会话超时。新会话完成 Atlassian 浏览器同意，包的本地连接页展示该站点，提交站点选择后，WorkSwarm 0.2.8 的 `mcp.wait_auth` 返回 `connected`。官方 ACLI `jira auth status` 也报告同一个站点。
- 对安装后的 1.0.3 命令执行 JQL `project = KAN ORDER BY created DESC` 搜到 3 条记录，按键读取 `KAN-1` 成功。通过同一个包在 `KAN` 创建了一条测试工单 [KAN-4](https://openjiuwenofficial.atlassian.net/browse/KAN-4)，随后按键回读，工单键、中文标题和描述均与写入一致。Jira 工单页面也显示相同内容。
- 首轮测试覆盖 WorkSwarm 宿主安装、连接接口和已安装的连接器命令。正式 Agentic Hub 目录安装、Linux 和 Windows 运行仍待实测。

## WorkSwarm 0.2.8 聊天实测，2026-11-17

- 从已安装的 1.0.3 包引用 Jira Cloud 技能。实际配置的 `gpt-6.1-sol` 通过 Bash 调用连接器 CLI。在隔离的 macOS 环境中，校验了安装载荷与交付 ZIP 中的 7 个文件一致。
- 在团队测试项目 `KAN` 用 JQL 搜索到 `KAN-4` 并按键读取。查重后创建一条中文测试任务 [KAN-5](https://openjiuwenofficial.atlassian.net/browse/KAN-5)，按工单键单独回读，项目、标题和描述一致，未分配人员。
- WorkSwarm 原始聊天长图保存在本机验收目录，文件名 `07-jira-cloud-1.0.3.png`，SHA-256 `bfce77ee47fca3a8eebff633202d99ad36ea4dd2aee4b7ddf2f7aa825f0a53a8`。

## 1.0.4 官方图标版本，2026-11-17

原来的功能实测对应 1.0.3。本版增加官方 PNG、来源声明，并同步版本号。此次在 WorkSwarm 0.2.8 对实际交付包做安装和图标显示检查。

- 官方 Agentic Hub CLI 校验和打包通过。已检查外层、原生 ZIP 与源码中的图标和字节；运行命令差异仅为版本号。
- 在 macOS Apple silicon 的原版 WorkSwarm 0.2.8 隔离环境，通过本机 Hub 兼容目录安装交付 ZIP。安装文件全部匹配。连接器广场卡片成功解码包内 96 × 96 PNG，并以 48 px 宽度显示。
- 现有 2 项单元测试通过。本次范围为安装与图标显示，真实服务功能实测见上文的上一版本记录。
