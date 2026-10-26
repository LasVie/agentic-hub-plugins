# 来源、复用与范围审查

任务：AH-20261026-domain-renewal-research；候选：CAND-CLD-138；负责人：Nguyen Trung Dung。
名称映射：Cheapest Domains → **域名续费比价** → `domain-renewal-research`。
内部 ID：`repo:agent-plugin:domain-renewal-research`。

## 功能差异与入口复用

保持 **Partial Overlap - Extend Existing Capability**。现有 Cloudflare 开发运维助手
`62e9a479c4954481bb862b6d38d3a444`@1.0.0 和 Vercel 插件
`74bf008cf94a4082ac4eb4e15a7a2982`@1.0.0 继续负责域名账户、DNS 和部署。
本伴随插件补充公开跨注册商的续费优先比较、预算筛选、带日期的报价、估算和用户请求的名称研究；
不复制这些管理入口，不执行购买、注册、转移或续费。现有 Hub 包内部尚未逐项审查，不能声称完全不重叠。
2026-10-26 已复用前次结论并检查当前台账、任务和主分支，没有重新发明候选或资产 ID。

## 固定来源与逐路径许可

上游：https://github.com/igalil/cheapest-domains-integrations/tree/d81dd545228309d1e43f67832cf5da367883dfc9
固定提交：`d81dd545228309d1e43f67832cf5da367883dfc9`；集成版本 **0.11.0**。
2026-10-26 实际远端 API/MCP 是 **1.12.0**，协议 2025-11-25；这不是上游集成包的新版本。
完整根 MIT 原文、插件 README 的授权范围、Skill 和 API 参考均已读取。
MIT 原版权所有者是 **2026 Ilios Galil (PerfWebsite)**。

| 交付路径 | 使用的固定上游材料 | 许可与修改 |
| --- | --- | --- |
| skills/domain-research/SKILL.md | plugins/cheapest-domains/skills/domain-research/SKILL.md | MIT；中文翻译/改写，替换为 WorkSwarm 原生工具名；保留续费优先、来源日期、未知值、隐私和独立数据条款 |
| skills/domain-research/references/api.md | 同目录 references/api.md | MIT；中文协议说明和参数示例，区分 0.11.0 集成与当前服务，注明 get_price_history 为当前服务新增 |
| README.md | plugins/cheapest-domains/README.md | MIT；中文重写安装、范围、依赖和限制；保留真实来源及许可范围 |
| licenses/cheapest-domains/LICENSE | 根 LICENSE | 完整逐字节复制；核对 Git blob 791c5d5ab858d37c3bb8766c34c3077e67b3ff04 |
| tools/domain_tools.py 与 tools/tool_catalog.json | 公共 MCP 协议、公开参数接口与上述文档 | 新写宿主适配器及中文接口描述；不复制服务器实现；JSON 字段名/枚举保持协议兼容 |

## 分发条件与排除项

- `mode: ported`，所选集成文档范围的 `permission_status: verified`；MIT 全文和原版权随包保留。
- `THIRD_PARTY_NOTICES.md` 位于内层根目录，列出材料、版本和修改；没有发现上游 NOTICE，不杜撰。
- 不复制图标、商标素材、宣传图、Codex/Claude 专用安装钩子或市场目录。
- 上游托管服务/私有服务器源码不在 MIT 许可范围内，也未被复制；服务使用须遵守公开 terms/privacy 和请求限制。
- 不打包第三方注册商价格数据库、名称查询结果、Cloudflare Radar 数据、模型、凭据或第三方运行时。
- 可选 Radar 返回数据有独立 **CC BY-NC 4.0** 条款，保留署名、许可链接和数据日期；商业复用须另行获得许可。
- 原生适配依赖宿主现有 openJiuwen、MCP SDK 和 jsonschema；不分发这些依赖的副本。
- 中文名称与作者信息明确标记为社区适配，不暗示上游官方背书。

## 最终包复核

最终 1.0.0 已完成 8 文件源码/原生/外层逐字节核对、CRC、安全路径、UTF-8/LF 与许可哈希检查。
原生 SHA-256：`af6ef3967d0dcb88739abf6bf0df5e88e4eb39f98477b536386d0e93159b0d26`；外层：`532fefbc5aa7a94fa08ad76270ad9d491e8f4ffe7fac12713a3e4b1c6945a82c`。
实际结果见 TEST_REPORT.md / package-verification.json。2026-10-26 当前中文 1.0.0 用户确认及七张原始截图已收到，详见 USER_TEST_CONFIRMATION.md 与 evidence/1.0.0/evidence.json；Hub 提交与验收仍由项目负责人后续处理。

## 许可字节核对
完整原文 SHA-256：`177ce274838539489d3222b84b4759e4fdea7d5a5c13b357a1311b68c6f8c1c4`。Git blob 与固定来源逐字节一致；内层 UTF-8/LF，无 BOM。

固定上游完整 17 文件树已检查：根、插件、Skill 三份 LICENSE 均是同一 Git blob `791c5d5ab858d37c3bb8766c34c3077e67b3ff04`（1082 字节），均与包内完整原文相同。树中无 NOTICE；图标和 agents/openai.yaml 等未复制。
