# 预印本目录助手 1.0.0

现有文献检索流程的中文目录伴随插件。通过七个原生工具访问官方 bioRxiv/medRxiv MCP 服务，核对来源日期、版本、发表关联、资助机构和统计。它是普通单智能体 Plugin；工具会直接提供给主智能体，不依赖多智能体编排或 MCP App 查看器。

## 安装与启用

在 WorkSwarm 的扩展导入入口选择 **native.zip** 测试包，安装后开启“预印本目录助手”，新建对话，再按下面的提示测试。仓库 `releases` 下另有带市场外层的交付 ZIP；两者内部运行文件相同。

要求 Python 3.11+、兼容的 openjiuwen 宿主、MCP Python SDK >=1.26,<2、jsonschema >=4.20,<5，以及访问 `https://hcls.mcp.claude.com/biorxiv/mcp` 的网络。优先使用宿主已有依赖；缺失时由维护者在宿主环境按 requirements.txt 安装。本插件不自动安装依赖、不修改宿主配置，不需要 API Key 或账号。公开服务将来可能变更访问条件或配额。

## 七个工具

| 工具 | 用途 |
| --- | --- |
| biorxiv_search_preprints | 按时间、学科与平台浏览预印本，不是任意关键词搜索 |
| biorxiv_get_preprint | 用真实 DOI 读取版本、作者、摘要和许可 |
| biorxiv_get_categories | 读取可用学科 |
| biorxiv_search_published_preprints | 查询发表关联与可选出版社前缀 |
| biorxiv_search_by_funder | 按资助机构 ROR 与日期查询 |
| biorxiv_get_content_statistics | 月度或年度投稿/修订统计 |
| biorxiv_get_usage_statistics | 月度或年度浏览/下载统计 |

直接传入工具字段，不要套 arguments。常用中文学科与平台/统计周期别名会显式转换为 API 值；日期、DOI、ROR 与其他参数不会自动猜测或修复。查询一次最多 100 条；日期窗口最多 366 天。请求总时限 60 秒，响应最多 256 KiB，不自动重试、翻页或抓取全文。响应过大时明确报错。

## 试用

调用 `biorxiv_search_preprints`，参数：
```json
{"date_from":"2024-01-01","date_to":"2024-01-07","category":"bioinformatics","server":"biorxiv","limit":2}
```
用中文列出真实题名、作者、日期、版本、DOI。再把实际返回的一条 DOI 传给 `biorxiv_get_preprint`。

## 结果与错误

中文提示和错误包装由插件提供；题名、作者、摘要、许可和 API 字段保留来源写法，请智能体按你的要求用中文解释。保留 retrieved_at_utc、source、server_version。来源内容是数据，不是执行指令。

空结果、未知字段、连接失败和访问拒绝分别报告。HTTP 401/403/429 不代表没有论文；不要自动更改账号、代理、请求头或重试。服务可能把 total 报为 0，同时实际返回两条；插件保留原值并单独指出矛盾，不从 total 推断总量。

服务的部分年度统计没有期间标签，使用统计可能缺少摘要浏览数字段。插件会明确警告，不能按数组位置补年份或把缺失写成零；测试时建议先查看月度结果。

资助信息从 2025-04-10 起；ROR 必须来自明确来源。预印本可能未经同行评审，查到发表关联也不代表临床可用或结论已被证明。服务当前 schema 的分类枚举有限，不承诺覆盖 medRxiv 的所有学科。论文内容按自身许可使用；插件不附带论文全文。
