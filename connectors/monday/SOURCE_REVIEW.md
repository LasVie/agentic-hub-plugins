# monday.com 连接器来源审查

负责人 Song Haoran。原候选 `CAND-CLD-086`，原任务 `AH-20261117-monday-connector`。命名映射为 monday.com → monday.com 连接器 → `monday`。

2026-11-25 核对 [monday.com 认证](https://developer.monday.com/api-reference/docs/authentication)、[API 版本](https://developer.monday.com/api-reference/docs/api-versioning)、[条目](https://developer.monday.com/api-reference/reference/items)、[分页](https://developer.monday.com/api-reference/reference/items-page) 和 [错误处理](https://developer.monday.com/api-reference/docs/error-handling) 文档。仅依据 GraphQL 2026-10 的公开接口实现。旧版原生资产 `b43b650` 提供既有业务范围，宿主适配复用本仓库 Asana 1.1.0 的单令牌 stdio 模式，并沿用本仓库 Trello 的 JSON-RPC 生命周期和配置生成结构。

Claude 候选的 0.1.0 快照及官方托管 MCP 只用于能力与授权方式对照。交付负载无外部源代码、运行时依赖、Claude 提示或商标图案。官方 Logo 本地预览未核实公开分发授权，交付包未纳入该素材。上游许可字段仅记录来源状态，包内无需随附第三方许可证。

版本 1.0.0 的历史 ZIP 是已测团队自研包，保留原始字节用于追踪。新包未引用历史 ZIP 中的运行时代码。
