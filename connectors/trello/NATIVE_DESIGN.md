# Trello 看板连接器设计

在 WorkSwarm 卡片填写 Trello 应用 API Key 和授权用户的令牌。Node stdio MCP 使用 Trello 文档规定的 OAuth 凭据请求头访问固定的 `https://api.trello.com/1/`，由技能引导查询开放看板、列表和指定列表中的卡片。

创建操作仅使用卡片的标题、描述和目标列表。连接器先确认目标列表开放并属于明确指定的看板，再发起一次创建。用返回的卡片 ID 独立读取详情。写入结果不明时先查同名卡片。
