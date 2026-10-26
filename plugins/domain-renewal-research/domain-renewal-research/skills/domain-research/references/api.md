# 公开协议参考（中文适配）

改编自 Cheapest Domains 集成 0.11.0 的 MIT API 文档，固定提交 d81dd545228309d1e43f67832cf5da367883dfc9。
完整版权与许可见内层根目录 licenses/cheapest-domains/LICENSE；当前服务实测 1.12.0，与集成和本包版本分别记录。

本插件用原生 ToolCard 显示中文字段说明，参数**直接传入**。底层 MCP 为
`https://cheapest.domains/mcp`，Streamable HTTP，无认证。宿主负责正常模型访问。
它不购买、注册、转移或续费；远端用量、缓存和遥测写入使调用不是幂等操作。

| 原生工具 | 公开 REST GET 路径 | 主要字段 |
| --- | --- | --- |
| domain_search_prices | /prices | q, sort, maxRenewalCents, registrar/registrars, view, years, limit, offset |
| domain_get_tld_prices | /tlds/{tld} | tld 必填，其余报价筛选/分页 |
| domain_get_registrars | /registrars | 无参数 |
| domain_estimate_cost | /estimate | tld, registrar, years 必填 |
| domain_get_registrar_link | /registrar-link | tld, registrar, name 必填 |
| domain_get_naming_guidance | /naming-guide | 无参数 |
| domain_open_name_finder | /name-finder | 无参数，宿主内嵌 App 支持不保证 |
| domain_compare_domain_names | /name-comparison | domains 为逗号分隔的 1–10 个完整名称 |
| domain_check_availability | /availability | name, tld；可选 registrar, fresh |
| domain_check_availability_batch | /availability-batch | name, tlds；可选 cachedOnly |
| domain_get_domain_popularity | /popularity | name, tld；独立 CC BY-NC 4.0 数据条款 |
| domain_get_price_history | 当前服务声明的接口 | tld；可选 registrar, price, format，不猜 REST 路径 |

REST 基址为 `https://www.cheapest.domains/api/v1`，使用 www 主机保留 CORS 行为。
完整当前合同以 [OpenAPI](https://www.cheapest.domains/openapi.json) 和
[开发说明](https://www.cheapest.domains/developers.md) 为准。上表是兼容参考，不自动执行备用 HTTP 请求。

## 参数与单位

`maxRenewalCents` 为整数美元分，1500 表示 15 美元。`years` 为 1–10，`limit` 为 1–200，`offset` 为非负整数。
`sort=renewal|registration|total`；默认续费优先。`view=best|all`；搜索 `includeStale=true` 时须用 `view=all`。
`registrar` 与 `registrars` 互斥；`favorites` 至多两个逗号分隔注册商 ID，不保存偏好。
`orderBy`、`direction` 仅控制显示顺序；CSV/Markdown 仍分页，不能只看首屏就声称完整。

`name` 是 1–63 位 ASCII 单标签，不含点；`tld` 是一个后缀，不含点；不支持中文名称或多级后缀。
`domains` 为逗号分隔且不重复的 1–10 个完整名称；`tlds` 为逗号分隔的 1–20 个后缀。
MCP 布尔值用 JSON true/false；不要把字符串当布尔值。未知或重复字段应拒绝。

```json
{"q":".com,.org,.dev","sort":"renewal","maxRenewalCents":1500,"limit":3}
```

## 证据与价格解释

保留 offers、coverage、limits、pagination，以及 fetchedAt、stale、sourceUrl、pageUrl、registrarSearch。
价格仅比较覆盖的保存报价，不代表全市场；`coverage.partial=true` 时说明缺口和来源错误。
报价在成功更新前可能保留旧值；标注“已过期”而不是假装当前价格。
保留 originalCurrency、exchangeRate、税费、最低年限、公布正常价/涨价和溢价排除项。
`estimatedTotalCents=null` 不是零；新注册费用估算不是现有域名账单、转移报价或未来续费保证。
`comparison.omittedParameters` 记录网页不支持的参数；链接不保存名称检查结果。

Cloudflare 的 `sampled_standard` 是合成名称的标准报价，并要求其域名服务器；
GoDaddy 的 `sampled_api` 是 API 费率，网站/手动续费可能更贵。两者都不等于特定名称的精确溢价报价。

## 可注册性、配额与失败

名称检查将名称发送到服务和配置的检查提供方；构造搜索链接也会向本服务发送名称。
检查、价格样本和缓存共享门限。保留各提供方的 attempts、时间、独立 availability/premium 和部分错误。
`unknown`、`unsupported`、空价格、404 都不能改写为 taken。premium=null 是未确认；溢价不证明可注册。
可注册性证据通常五分钟失效；不能延长期限，也不保证名称被预留。

`cachedOnly=true` 批量路径只读已有证据；普通批量检查至多 20 个后缀，不对所有注册商扇出。
`fresh=true` 只用于用户明确要求的重新检查。保留 unconfirmedDomains 和已有有用事实。

匿名调用有共享限制。固定集成文档记录：名称/热度共享 10 次/分钟（突发 4）、300 次/UTC 日和
每对齐 32 天 3000 次；价格读取另有加权预算，完整目录请求较贵。
实际响应的 limits 和 retryAfterSeconds 优先于旧文档数字，不能将这些数值当作保证额度。
429 尊重等待时间；503 可能表示新鲜数据或准入不可用；不得自动轮询、绕过门限或恢复暂停提供方。
MCP 工具错误保留原始 error.code/message/retryAfterSeconds，外层提供中文提示。

## 可选 Radar 数据

仅用户请求 DNS 热度且用途符合条款时使用。保留 Cloudflare Radar 署名、source.licenseUrl、CC BY-NC 4.0 和 dataset 日期。
商业复用须另行许可。精确排名仅前 100，其余为分组/缺失；不是 SEO、搜索需求、流量保证或可注册性。

本包不保存项目背景、偏好或账户；只发送必要查询，服务访问日志可能记录 URL。
许可不包含私有托管服务器或第三方数据。参见服务 [条款](https://www.cheapest.domains/terms) 和 [隐私](https://www.cheapest.domains/privacy)。
