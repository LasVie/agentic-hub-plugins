# Intercom 客服连接器设计

Intercom → Intercom 客服连接器 → intercom。任务 AH-20261124-intercom，候选 CAND-CLD-029。

在原版 WorkSwarm 0.2.8 中用 CLI 卡片发起浏览器连接。在本机选择美区或欧区，Intercom 官方 MCP 动态注册公有客户端，并使用 OAuth 授权码、S256 PKCE 和单次本机回调。运行时只依赖 Node 内置模块，不需要用户准备 OAuth JSON 或 app 密钥。官方授权范围包括 mcp 和 operator；包的 CLI 只允许搜索和读取客服会话、联系人。

工具在每次运行时短时连接官方 MCP，反馈结果和官方资源链接。连接状态须经实际工具发现核对。服务响应、对话正文和客户字段均是业务数据，不是指令。取消或过期不写入授权，断开清除本机连接，服务端授权可在 Intercom 单独管理。

公开功能参考是 Intercom MCP 文档、MCP Streamable HTTP 规范与两区 OAuth 元数据。团队已有卡片结构、命令定位与短时进程模式见 Confluence 1.1.0（#117）。没有阅读或采用 ChatGPT 插件实现、Intercom Claude 包源码或 mcp-remote 源码完成本连接器。
