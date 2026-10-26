# 咖啡选豆与冲煮

**1.0.0 · WorkSwarm 原生 Plugin · 默认简体中文 · 单智能体**

用 Percolate 的实际目录按风味、烘焙度、器具和预算选豆，比较两款咖啡，读取冲煮建议。
不连接个人收藏、冲煮日志或账户，不下单，也不安装或配置模型。
这是社区中文适配，不是 Percolate 官方发布；上游集成版本 1.0.0，实际服务版本另行返回。

## 安装

1. 在 WorkSwarm 插件管理中导入本次提供的 `coffee-brewing-research-1.0.0-native.zip`。
   原生 ZIP 根目录直接包含 `manifest.json`。仓库外层 ZIP 用于统一交付，不能混用导入方式。
2. 启用 **咖啡选豆与冲煮**，新建会话。
3. 必须在实际工具调用中看到 `coffee_` 工具，不能只根据助手自述判断加载成功。

需要兼容的 WorkSwarm/openJiuwen 原生工具宿主、Python 3.11+、宿主已有的 MCP SDK、httpx、jsonschema 和互联网。
没有 API 密钥或 Percolate 账户要求；插件不额外安装这些依赖。网络或服务限制会如实返回中文错误。

## 八个原生工具

| 工具 | 用途 |
| --- | --- |
| `coffee_search_coffees` | 按原名、分类、烘焙度、器具、美元价格检索 |
| `coffee_get_coffee` | 读取一个实际 ID 或原名的完整档案 |
| `coffee_find_similar` | 读取相似咖啡及匹配依据 |
| `coffee_get_recommendations` | 按风味、每袋预算和器具推荐 |
| `coffee_compare_coffees` | 对比两款实际咖啡 |
| `coffee_trending_coffees` | 热度列表，保留真实方法或目录回退说明 |
| `coffee_dial_in_suggestion` | 冲煮比例、水温和研磨建议，区分配方与起点 |
| `coffee_what_to_brew` | 按时段、简短场景和器具查询 |

参数直接传入，不套 `arguments`；价格单位是**美元，不是美元分**。首次查询建议 `limit=2` 或 `3`，最大 `10`。
`roast_level`、`category`、`time_of_day` 等枚举保留接口原文，中文解释见 [API 参考](skills/coffee-picks/references/api.md)。

## 示例

> 用中文找两款每袋不超过 20 美元、适合 espresso 的咖啡。调用 coffee_search_coffees，
> 直接使用 {"category":"espresso","price_max":20,"limit":2}。列出实际名字、ID、风味、价格和来源日期。

> 用刚才实际返回的咖啡 ID 调用 coffee_dial_in_suggestion，brew_method="V60"。
> 说明返回的是精选配方，还是按烘焙度给的一般起点；没有的参数不要编造。

## 如何理解结果

- 保留 Percolate 的 `attribution`、返回链接、`retrieved_at` 和每款咖啡的 `data_last_updated`。
  插件的 `fetched_at_utc` 只是本次获取时间，不能冒充目录更新日期。
- 价格是返回的目录参考，通常为每袋美元价；包装、规格或单位不明确时不做无依据的克价比较。
  空值、缺失和零按原始返回区分，不杜撰零售库存、当前批次或结账价格。
- 服务只列零售商和价格，不提供购买链接。不要生成猜测的购物 URL；保留实际返回的资料来源链接。
- 配方可能是精选记录，也可能是按烘焙度推导的起点。热度可能回退到目录人气；两者必须明确区分。
- 保留 `pods_only`、`formats` 和器具限制；espresso 分类也可能返回胶囊，不能把它当整豆或默认用于 V60。
- 部分目录 ID 已观察到无法用于比较，而实际返回的完整原名可用。错误会如实返回，插件不会自动替换参数重试。
- 默认中文回答；用户明确要求英语等其他输出语言时遵从。品牌、ID、接口字段和原始法律文本保持原文。

## 隐私、限制与许可

只将本次必要的名称、偏好、器具和预算发给固定官方端点 `https://mcp.percolateapp.com/mcp`。
不发送完整对话、用户身份或私密资料。服务会记录调用参数、客户端和结果数量；详见
[隐私政策](https://www.percolateapp.com/privacy) 与 [服务条款](https://www.percolateapp.com/terms)。
目录查询会更新远端日志/用量，因此不标记自动重放或并行安全；每次最多一次实际工具查询，总等待 60 秒，不自动重试。
不遍历或抓取全库，不绕过限流。429 时保留可解析的等待秒数；错误不会被解释为“没有咖啡”。

改编的 README/Skill 遵循 MIT，原版权 **Copyright (c) 2026 Timberline Ventures LLC**。
完整原文见 [LICENSE](licenses/timberline-percolate/LICENSE)，材料与修改说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
不分发上游标志、图片、目录数据库、实际查询结果或私有服务器；咖啡和烘焙商名称仅用于识别实际记录。
