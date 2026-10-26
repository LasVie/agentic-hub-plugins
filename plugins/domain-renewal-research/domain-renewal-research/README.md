# 域名续费比价

**版本 1.0.0 · WorkSwarm 原生 Plugin · 默认使用简体中文**

本社区适配基于 Cheapest Domains 的 MIT 集成说明，为现有域名管理流程补充公开报价研究。
优先比较**年度续费**，把首年注册价格分开列出，并保留来源日期、覆盖不足和未知结果。
它不是注册商，不执行购买、注册、转移、续费、DNS 修改、部署或账户操作。
这些管理工作继续使用已配置的 Cloudflare、Vercel 或注册商入口。

## 安装与要求

1. 在 WorkSwarm 的扩展管理中导入 **domain-renewal-research-1.0.0-native.zip**。
   此文件的 manifest.json 位于 ZIP 根目录，供本机导入器使用。
2. 启用 **域名续费比价**，在启用后新建会话，再进行工具测试。
3. 默认用中文提问。工具名以 `domain_` 开头；本插件不配置模型或子智能体。

需要互联网、支持原生 Tool/ToolCard 的宿主及其现有 `openjiuwen`、`mcp`、`jsonschema` 依赖。
不需要 Cheapest Domains 账户、API 密钥、本地 Node 服务或单独模型账户。
宿主自己的模型访问仍由用户现有配置提供。本包不修改宿主或安装额外依赖。

仓库交付包 `domain-renewal-research-1.0.0.zip` 含 marketplace 外层；本机扩展导入应选择上述 native ZIP。
精确路径、SHA-256、安装验证环境和实际测试结果见包外 MANUAL_TESTING.md / TEST_REPORT.md。

## 可用工具

| 工具 | 用途 |
| --- | --- |
| `domain_search_prices` | 后缀、注册商、续费预算筛选及分页 |
| `domain_get_tld_prices` | 一个后缀的注册商报价 |
| `domain_get_registrars` | 覆盖来源、注册商 ID 和健康状态 |
| `domain_estimate_cost` | 新注册多年费用估算 |
| `domain_get_registrar_link` | 名称对应的注册商搜索链接，不打开网页 |
| `domain_get_naming_guidance` | 命名研究指导 |
| `domain_check_availability` | 单名称可注册性证据 |
| `domain_check_availability_batch` | 同一名称的 1–20 个后缀，支持只读缓存 |
| `domain_compare_domain_names` | 至多 10 个已检查名称的缓存证据与续费排名 |
| `domain_open_name_finder` | 命名表单说明；未实现内嵌 MCP App 时使用网页链接 |
| `domain_get_price_history` | 当前服务新增的后缀价格历史 |
| `domain_get_domain_popularity` | 可选 DNS 热度；保留独立数据许可，不是 SEO 指标 |

直接把参数作为 JSON 对象传给工具，**不要再包一层 arguments**。金额参数是整数美元分。

```json
{"q":".com,.org,.dev","sort":"renewal","maxRenewalCents":1500,"limit":3}
```

可以问：

> 用 domain_search_prices 比较 .com、.org、.dev 每年续费不超过 15 美元的三条报价。
> 用中文列出注册商、首年注册费、年度续费、来源时间和比较链接；说明覆盖是否完整，不检查具体名称。

## 结果与隐私

查询发送到 `https://cheapest.domains/mcp`。项目背景留在会话中，只传需要的后缀、筛选条件和名称。
价格比较不等于可注册性检查。名称查询会把该名称传给服务；可注册性会进一步发送给检查提供方。
即使只是构造注册商搜索链接，输入的名称也会到达该服务。查询 URL 可能进入访问日志。

保留 `fetchedAt`、`stale`、`coverage.partial`、来源链接、样本价、税费、汇率和最低年限。
空报价、未知结果、404 和可点击的搜索链接都不能证明名称被注册或可注册。
可注册性有时效，不预留名称；溢价与可注册性是两个独立事实。
多年估算用于新注册，不是现有域名账单、转移报价或未来续费保证。

Cloudflare `sampled_standard` 是标准名称样本报价，并要求使用其域名服务器；
GoDaddy `sampled_api` 是 API 价格，网站结账可能更贵。未知金额不能按零处理。

命名表单只准备请求，不在服务器调用模型。WorkSwarm 未必能渲染内嵌 MCP App；
工具会提供公开网页入口，不声称已经显示原生表单或打开浏览器。

## 限制与故障

服务只覆盖选定注册商，名称为 ASCII 单标签和单级后缀，不支持中文域名或 `co.uk`。
有匿名配额；服务可能返回 429、503、部分结果或旧报价。
保留 `error.retryAfterSeconds`，本适配器不自动重试、刷新或遍历整个目录。
超时、断网或远端模式变化会返回中文错误；不得将故障解释为价格为零或名称已被注册。

可选 Cloudflare Radar 结果有独立 **CC BY-NC 4.0** 条款；仅在用户请求且用途符合该条款时使用，
保留原始署名、许可链接和数据日期。商业复用须另行获得许可。基础比价不调用该工具。

## 来源与许可

集成说明固定为 [0.11.0 / d81dd545](https://github.com/igalil/cheapest-domains-integrations/tree/d81dd545228309d1e43f67832cf5da367883dfc9)。
2026-10-26 实际公开服务为 1.12.0，共 12 个工具；服务版本与本包版本分别记录。
上游集成文档的完整 MIT 原文和版权位于 `licenses/cheapest-domains/LICENSE`，修改与范围见
`THIRD_PARTY_NOTICES.md`。托管服务器源码、品牌和第三方数据不在该 MIT 授权范围内。
使用服务须遵守其 [条款](https://www.cheapest.domains/terms) 与 [隐私政策](https://www.cheapest.domains/privacy)。
