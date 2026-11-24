# Fathom 会议连接器独立设计

以 Fathom 公开 REST API 文档为依据，使用个人 API Key 读取该账号可访问的录制会议。沿用仓库 Asana 连接器已在 WorkSwarm 0.2.8 验证的 token 卡片与 Node stdio MCP 配置。Node 内置模块运行连接器，API Key 由卡片经环境变量提供，HTTP 请求固定到 Fathom 官方 HTTPS REST 端点。

- 查询按会议创建时间过滤，对当前服务页的标题进行不区分大小写的匹配，返回录制 ID 及服务游标。
- 摘要按录制 ID 获取，保留 Fathom 生成的 Markdown 内容并省略其中的录制分享链接。
- 逐字稿按录制 ID 获取，保留说话者、原文和时间戳，在本地按条分页。
- 保留必要的录制数据，不请求回调、不输出 API Key、会议邀请链接、参会者邮箱或原始错误响应。
