# Intercom 客服连接器 1.0.0 测试记录

2026-11-24 · AH-20261124-intercom · CAND-CLD-029 · macOS WorkSwarm 0.2.8 · 内置 Node 22.12.0。

- Node 测试 5 项通过。覆盖中文查询参数、读工具边界、SSE 回复 ID 核对、工具翻页、模拟欧区动态注册/PKCE/回调拒绝/令牌刷新和断开。模拟数据不能证明真实 Intercom 已连接。
- 使用官方 Agentic Hub CLI 0.0.1、源码 c8ee4ef44be0453470114aa5a19f4e1017462907，在干净 staging 执行 validate 和 pack。源码载荷、两份 ZIP 都通过动态 JavaScript preflight，扫描 3 个 JavaScript 文件，已知签名 0。两份 ZIP CRC 核验通过，7 份内层文件与源码 SHA-256 完全一致。
- 调用已安装 WorkSwarm 0.2.8 二进制中的 `jiuwenswarm.server.runtime.mcp.package_manifest.load_mcp_package` 读取解包目录，正确识别 Intercom 客服连接器 1.0.0。
- 真实 Intercom MCP 美区接口返回公有客户端注册 HTTP 201。最早试装包的浏览器地区表单被拒绝，在卡片点取消后回到「连接」，端口关闭。改为一次性地区链接后在新测试配置重装，真实 WorkSwarm 连接器卡片从本机 Hub 测试目录下载，两份 ZIP 与已安装的 7 份文件哈希相同。美区地区链接在内置浏览器打开真实 Intercom 同意页。
- 在美区 openJiuwen [DEV] 工作区测试。内置浏览器提交 Intercom 同意时，官方报告未收到会话 Cookie，未完成。取消后从同一卡片重新发起，用户在 Safari 完成授权，本机回跳，卡片显示「使用」。用已安装 CLI 在真实工作区通过 status，能搜索和读取实际会话及联系人，均返回官方链接。已读会话是开发工作区自动产生的事件，提供完整的事件字段，原记录没有正文。
- WorkSwarm 里的中文聊天已实际调用该安装包。搜索返回 1 条客服会话；用搜索结果 ID 读取事件详情及服务提供的原链接。联系人查询报告 4 条，首条 ID 与搜索结果及独立 CLI 读取一致，未在截图展示联系方式。独立再次读取核对 `company_updated` 和 `Body: [no body]`。这次验证的是有事件字段、无正文的开发工作区样本。
- 聊天起初遇到隔离模型登录过期、一次服务繁忙、一次宿主工作进程关闭。模型曾因 grep 将已核验文件的显示路径写成旧试装目录而停下；核对正式安装路径及 ZIP 内三个脚本的 SHA-256 后，通过新会话分步完成。模型初次汇总把 `[no body]` 当作正文，回读原字段后已纠正。
- 原始截图保存在 `test-evidence/20261124-stock-1.0.0/screenshots/`。含同意页、内置浏览器 Cookie 错误、卡片连接成功、中文搜索和独立回读五张。测试和证据等待 Song Haoran 确认。
- 当前还需实测正式 Hub、Windows/Linux、欧区真实工作区和远程浏览器回调。

Hub ZIP SHA-256：`d341ac06c87bf04ab45cad5e74c48bd27bdf9a24675a366cb0eb74447fa45c42`。
原生 ZIP SHA-256：`7b1885a1d61f0fecafea75717ab8cd90347cf35bf4947e0f2e0bc6e911d032b4`。
