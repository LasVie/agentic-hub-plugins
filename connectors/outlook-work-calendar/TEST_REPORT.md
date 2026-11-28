# Outlook 工作日历连接器 1.0.0 测试记录

2026-11-24，macOS，原版 WorkSwarm 0.2.8 和自带 Node.js 22.12.0。使用干净的本机数据目录和 Hub 测试目录。改动仅在 Agentic Hub 包。

- 官方 Hub CLI 0.0.1（`c8ee4ef44be0453470114aa5a19f4e1017462907`）在干净 staging 通过 `validate` 和 `pack`。源码、Hub ZIP 和原生 ZIP 通过仓库预检。原版 WorkSwarm 加载器通过。实际安装的 7 个文件与源码和两份 ZIP 的有效载荷逐一匹配。
- Node.js 8 项自动化测试通过，覆盖最小委派权限、PKCE、回调 state、Graph 日期与事件路径、中文标题筛选、分页、权限及服务错误、令牌续期。本机 HTTP 回跳使用实际回环服务，Microsoft 登录和 Graph 响应使用测试数据模拟。
- 通过 WorkSwarm 卡片安装最终 ZIP，自动开出工作日历本机配置表单。表单要求目录（租户）ID 和应用程序（客户端）ID。取消后卡片恢复为「连接」。已保存 2 张本机原图。
- 当前没有可用的企业 Exchange Online 邮箱。Microsoft 组织账号授权、真实日程查询和独立回读、聊天验收，以及正式 Hub、Windows/Linux、远程宿主均待验证。
