# Google 日历连接器 1.1.0

从 WorkSwarm 卡片连接 Google，查询主日历、创建一条单次个人日程并独立回读。新版本改为短时 Node CLI + 技能，不需要 Python；WorkSwarm 源码无需修改。

## 安装和连接

1. 从 Agentic Hub 安装，首次连接会准备固定版本的 gws 0.22.5 与 Google Node 认证库 11.3.4。需要 Node.js 22+ 与 npm；目标 WorkSwarm 0.2.8 提供其 Node 运行环境。首次联网下载需要能访问 registry.npmjs.org 和 GitHub Releases，macOS/Linux 解压需要 tar、Windows 使用 PowerShell。原生安装器 fetch 不自动使用 HTTP_PROXY，受限代理网络可能下载失败。
2. 自建 Google Cloud 项目启用 Calendar API，创建 **Desktop app** OAuth 客户端，配置同意屏幕及测试用户。Testing 项目可能要求加入名单并定期重新授权；组织管理员也可能限制访问。连接器不会代替 Google 的发布和验证要求。
3. 点卡片「连接」。本地页面需要时可选择自己的 Desktop OAuth JSON 并保存；已有团队 Workspace 本机客户端配置可复用，但不复用其他连接器令牌。点「前往 Google 授权」，核对并亲自同意。只请求 `https://www.googleapis.com/auth/calendar.events.owned`，不追加 OpenID、邮箱或个人资料权限。
4. 回到 WorkSwarm。连接状态经过真实主日历查询确认。聊天里可以说「查询明天的测试日程」「创建一条指定标题、起止时间的个人测试日程，并回读确认」。

## 范围和存储

固定主日历 primary，支持按时间及关键词列表、按 ID 读取，以及创建单次个人日程。新建固定为私密、空闲、无提醒、不发送通知；无参会者、重复、更新或删除能力。OAuth 自有日历权限覆盖范围比包内命令更广，包内仅开放上述操作。

授权及运行缓存保存在 WorkSwarm 数据目录的 connector-data/google-calendar/node-v1；Unix 凭据目录 700、文件 600。断开只清除本连接器本地会话，不撤销同一个 Google 客户端上其他连接器的授权；可到 Google 账号安全页面管理远端授权。授权入口绑定当前运行机器的 127.0.0.1；远程服务器若浏览器不在同一台机器，不能直接用此桌面回调，当前版本不宣称支持这种环境。

本包不打包用户 JSON、令牌、node_modules 或 gws 二进制。gws 由 googleworkspace 仓库维护，README 明确并非 Google 正式支持的产品；固定依赖和许可见 THIRD_PARTY_NOTICES.md。Google API 配额、账号和网络约束由服务方管理；连接器不提供付费服务承诺。macOS Apple silicon 为本次验证目标；其他系统须另行实测，不能从命令映射推断已兼容。
