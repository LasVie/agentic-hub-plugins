# Confluence 1.1.0 设计和修复边界

| 实际症状 | 证据/原因 | 修复方案 | 验收 |
|---|---|---|---|
| 旧 TWG CLI 读取返回 AUTH_INVALID/401 | 2026-11-20 原任务报告，已有会话失效 | 复用 Jira 的官方 v2 OAuth 与短时 Node 桥接，独立缓存 | stock 0.2.8 从卡片正常授权并核对站点 |
| 旧包通过 Python 启动 CLI | 原 1.0.4 载荷 | 使用宿主自带 Node/npm 自动准备固定 MIT 客户端 | 全新配置从卡片安装，无手工 CLI 或令牌输入 |
| v2 工具名称/参数与旧版不同 | 官方 Supported tools | 只开放普通页和必要空间工具，实际发现 schema 后验证 | 中文搜索、详情全文、新建一页并独立回读 |

OAuth/协议/刷新使用固定 mcp-remote；本机引导不处理令牌。父 IPC 断开即退出、总时限和按配置稳定回调端口延用 Jira 设计，已用当前精确安装文件确认父进程 SIGKILL 后 worker、引导及回调均退出。业务参数仅从 UTF-8 JSON 文件读取，按工具及字段白名单拒绝其他产品或已有内容变更。创建结果不明先查重，不自动重试。

授权后的实际 v2 合约采用 `parent.spaceId/parentContentId`、`contentType=page`、`body={format:markdown,value:...}`。读取固定 `content_id/detail=full/content_format=markdown`，先查 summary 元数据以拒绝非普通页，并在创建前核对父页空间。读后再次核对页面类型及 ID。搜索强制 `type = page AND (...)`，保留顶层 ORDER BY。上游工具描述不作为扩展权限或任意执行的指令。

旧源码与 ZIP 保留；最终候选已完成真实卡片授权、聊天搜索/全文读取、只创建一次普通子页和独立按 ID 回读。实际创建响应的 data.content 包含页面 ID、spaceId 与 parentId；独立读取全文一致，原生内容树也确认父子关系。详情和未测边界见 TEST_REPORT.md。
