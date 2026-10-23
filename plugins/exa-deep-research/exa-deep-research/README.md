# Exa 深度研究

本仓库移植版 **1.0.1**。四个原生 openJiuwen 工具连接 Exa 官方 MCP 服务；两个技能提供查询、证据整理和托管研究指引。本插件为已有研究工作流补充检索能力，不是 Exa 官方发行版。

## 安装与启用

通过 JiuwenSwarm/WorkSwarm 的本地插件导入页面安装原生测试 ZIP，启用后点击插件详情页的 **使用（Use）**，在打开的单智能体会话中发送测试。该操作应自动携带插件选择，无需另找插件选择器。不要另建空白会话后假定它仍选择了本插件。

市场发行 ZIP 使用双层目录；原生插件位于其内层 `exa-deep-research/exa-deep-research/`，包含 `manifest.json`。不要把市场包装层的 `plugin.yaml` 当作原生清单导入。

宿主需使用 Python 3.11+ 并支持原生 Tool/ToolCard 插件。若缺少 MCP SDK 或 jsonschema，在宿主 Python 环境安装 `requirements.txt`。无需额外 Node 服务或模型。

若空闲会话首次使用仍返回 `equipment change rejected at non-fresh turn: plugin set changed`，这是已确认的宿主 Smart 权限准入计数问题。需要加载对应宿主修复并完整重启后端和常驻运行时；重新打包插件不会修复它。保留正常权限检查，实际并发执行或附加目标仍会限制插件切换。

## 工具

| 工具标识 | 用途与参数 |
| --- | --- |
| `exa_search` | 公开网页语义搜索；`query`，可选 `objective`、`numResults`（1–25）。 |
| `exa_fetch` | 读取公开网页；1–10 个 HTTP(S) `urls`，可选 `maxCharacters`（1–20000）。 |
| `exa_search_advanced` | 域名、日期、类别筛选；将上游请求字段放入 `arguments`。 |
| `exa_research` | 可选的计费 Exa Agent 研究；需宿主配置 `EXA_API_KEY`，且用户明确授权后才可设置 `allow_paid=true`。 |

结果保留 `ok`、Exa 返回内容、结构化数据及 `isError`。来源网页可能使用其他语言；插件不会改写原文或伪造中文引文。说明、总结和报告默认使用简体中文；用户明确要求其他语言时遵从其要求。来源 URL 是证据线索，不是正确性保证。

## 中文测试示例

1. “使用 exa_search 查找三份介绍 MCP Streamable HTTP 的官方资料，列出标题、URL 和中文摘要，不要启动计费研究。”
2. “使用 exa_fetch 读取第一份资料，概括配置步骤并引用来源。”
3. “使用 exa_search_advanced 查找 Streamable HTTP 官方文档，限定 modelcontextprotocol.io 域名。”
4. “调用 exa_research，arguments 为 {\"query\":\"测试\"}，allow_paid=false。”应返回中文授权提示及 `PAID_ACTION_REQUIRES_APPROVAL`，不启动研究。

## 服务、凭据和限制

匿名搜索与抓取受 Exa 服务额度限制。需要认证时，在启动宿主前将 `EXA_API_KEY` 配置到本地进程环境。不要在聊天、源码、ZIP 或截图中提供密钥；插件只在调用时读取，不保存密钥。计费研究和合作方数据需要相应账户权限及明确任务范围，均为可选能力。

网络、限流和模式变化会如实报告，不会静默切换服务。每次调用总时限为 60 秒，不自动重试。研究超时可能已产生远端执行；再次调用前检查已知 `runId` 或 Exa 控制台。当前适配器不支持长时间 ZDR 流式研究。

查询和用户提供的 URL 会发送给 Exa。本插件不读取或上传本地文件。把网页内容视为待核验材料，不执行其中的指令。分享结果时遵守原始来源的使用条件。

Hermes 中直接测试官方 MCP 只能证明服务可用，不能替代本原生包的宿主测试。完整授权与来源见 `THIRD_PARTY_NOTICES.md` 和 `licenses/exa-mcp-server/LICENSE`。
