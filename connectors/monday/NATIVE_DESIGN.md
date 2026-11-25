# monday.com 连接器 1.1.0 设计

沿用任务 `AH-20261117-monday-connector`、候选 `CAND-CLD-086` 和现有卡片字段 `MONDAY_PERSONAL_TOKEN`。WorkSwarm 通过 stdio 启动随包定义的 Node MCP 进程。进程用固定 GraphQL 文档和独立变量请求 `https://api.monday.com/v2`，请求指定 `API-Version: 2026-10`。

提供四个工具。连接检查调用 `me`。列表调用 `boards.items_page` 和 `next_items_page`，验证返回条目的看板归属。读取调用 `items`，保留标题、看板和列文本。新建调用 `create_item`，输入仅含看板 ID 与标题，然后由读取工具独立回读。

每次工具调用限时，写入无自动重试。服务出错时显示简体中文，避免回显令牌或原始错误。保留旧版 ZIP 的原始字节用于之前的验收追踪。
