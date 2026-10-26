# 原生工具参数参考

固定端点：`https://mcp.percolateapp.com/mcp`；不接受用户提供的端点、凭据或任意远端工具名。
上游集成 1.0.0；2026-10-26 实际 MCP 1.0.2。工具卡中的 schema 是当前快照，调用前还校验远端实际 schema。

| 原生工具 | 必填字段 | 可选字段 |
| --- | --- | --- |
| `coffee_search_coffees` | 无 | query, category, roast_level, brew_method, price_min, price_max, limit |
| `coffee_get_coffee` | id_or_name | 无 |
| `coffee_find_similar` | coffee | limit |
| `coffee_get_recommendations` | preferences | budget, roast_level, brew_method, limit |
| `coffee_compare_coffees` | coffee_a, coffee_b | 无 |
| `coffee_trending_coffees` | 无 | limit |
| `coffee_dial_in_suggestion` | coffee | brew_method |
| `coffee_what_to_brew` | 无 | time_of_day, mood, brew_method |

- 所有参数直接位于对象顶层，不套 `arguments`。不允许额外字段。
- `limit` 为 1–10 整数；价格/预算为有限非负**美元数**；price_min 不得大于 price_max。
- query、id_or_name、brew_method、mood 最长 120 字符；coffee、coffee_a、coffee_b 最长 200 字符。
- preferences 为 1–20 个风味词，每项最长 60 字符。提供的文字参数/风味项不可仅为空白。
- 分类：espresso / single_origin / blend / decaf / dark。
- 烘焙度：light / medium-light / medium / medium-dark / dark。
- 时段：morning / afternoon / evening。品牌、ID 和这些协议枚举保持原文。

示例：

```json
{"category":"espresso","price_max":20,"limit":2}
```

```json
{"preferences":["chocolate","caramel"],"budget":20,"brew_method":"espresso","limit":2}
```

成功返回 `ok`、实际远端 `tool`、`source`、`server_version`、本次 `fetched_at_utc` 和原始 `data`。
原始空值、零、日期、配方来源、热度回退和 `attribution` 不被改写。助手按用户语言整理这些事实。

错误代码：`INVALID_ARGUMENTS`（本地拒绝）、`REMOTE_SCHEMA_CHANGED`、`TOOL_UNAVAILABLE`、
`SERVICE_ERROR`（保留实际错误 data）、`RATE_LIMITED`（保留可解析 Retry-After 秒数）、
`SERVICE_ACCESS_REQUIRED`、`TIMEOUT`、`CONNECTION_FAILED`。没有自动重试或备用查询。

源服务是公开目录；没有账户、API 密钥、购买、个人收藏或日志写入接口。
官方 [MCP 页面](https://www.percolateapp.com/mcp) 允许带 Percolate 署名引用数据；
这不是整个目录、产品图片或标志的再分发许可。不抓取全库，不将实时结果/图片打包。
遵守 [服务条款](https://www.percolateapp.com/terms) 和 [隐私政策](https://www.percolateapp.com/privacy)。
