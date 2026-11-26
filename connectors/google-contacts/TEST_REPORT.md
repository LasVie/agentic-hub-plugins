# Google 联系人连接器 1.0.0 测试记录

2026-11-24 · AH-20261124-google-contacts · macOS WorkSwarm 0.2.8 · 宿主 Node 22.12.0。

- Node 6 项测试通过，覆盖合法与越界参数、唯一只读范围、S256 PKCE、空查询预热、实际资源名和联系人来源核对、本机文件导入及错状态回调、People API 未启用与临时故障。模拟响应只验证本包行为。
- 官方 Agentic Hub CLI 0.0.1（c8ee4ef44be0453470114aa5a19f4e1017462907）在独立目录 validate 和 pack 通过。原生与 Hub ZIP CRC 检查通过，动态 JavaScript preflight 均扫描 2 份文件，已知签名 0。两份 ZIP 内的 6 个载荷文件与源码及 WorkSwarm 已安装文件逐一核对。
- 在已安装 WorkSwarm 0.2.8 的二进制里执行实际 load_mcp_package，识别为 Google 联系人连接器 1.0.0。在隔离配置下，从 WorkSwarm 卡片下载本地 Hub 测试目录的精确包，打开本机授权页，通过文件选择器导入已有 Desktop OAuth 配置。未授权状态返回 AUTH_REQUIRED。
- 已在团队测试账号的 Google Contacts 页面创建虚构测试联系人「WorkSwarm联系人验收」，邮箱 workswarm-contacts-qa@example.com。该写入用于准备测试数据，连接器只读。
- Google 官方授权页面已实开。首次团队用户访问 My First Project（forward-aura-261913）返回 403 access_denied，说明该项目还没给此账号测试权限。团队当前 Console 账号无权管理该项目。People API 启用页面实际显示另一项目。补加测试用户后 Google 同意页成功回跳，但实际请求返回 SERVICE_DISABLED。使用 Safari 的项目管理员会话核对 My First Project 页面仍显示 Enable。用户亲自在该项目启用，确认 Manage 后重新从卡片连接，Google 回跳显示「Google 联系人授权已完成」，实际 People API 校验与卡片「使用」均通过。

- 已安装 CLI 实际 status 返回授权有效，按完整中文姓名和虚构邮箱检索各命中 1 条，两次搜索的资源 ID 相同。随后使用同一资源 ID 独立读取详情，核对姓名、虚构邮箱和空电话号码。WorkSwarm 中文聊天实际执行 search 和 read 两个命令且成功，使用预先准备的搜索参数文件和卡片安装路径，回读结果与 Google 联系人页面一致。
- WorkSwarm 的「重试」曾打开已关闭的旧授权端口，先「取消连接」再点卡片「连接」可生成新入口。本轮验证的是 macOS 本机回调与本地 Hub 测试目录。正式 Hub 下载、Windows/Linux、远程回调、自然过期和远端撤销恢复仍待实测。
- 四张原始截图保存在 `test-evidence/20261124-stock-1.0.0/screenshots/`，等待 Song Haoran 确认本版本测试结果。

Hub ZIP SHA-256 `ecf6ee6e497e7ad584597116dac4e677ace46a18fbe7ead6189c4845a3b72abc`。
原生 ZIP SHA-256 `a3937f7f99d49002e0d93ab1807fee05b777116ec97166479a806100841ff731`。
