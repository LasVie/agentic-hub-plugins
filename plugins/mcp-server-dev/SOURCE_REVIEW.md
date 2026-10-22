# 来源审查：mcp-server-dev 1.0.0

审查日期：2026-10-22（Asia/Singapore）。
候选：CAND-ANT-011；任务：AH-20261022-mcp-server-dev；负责人：Vannes Wijaya（用户明确指派 Vannes）。
交付类型：Plugin / agent-plugin；内部稳定 ID：repo:agent-plugin:mcp-server-dev。
来源模式：ported；不是独立原生实现。未为本仓自有代码选择统一许可证。

## 查重和范围

实时读取在线“插件候选”“资产总账”“开发任务”“进展汇报”、成员与可用下拉。
资产总账 A1:N593 包含 592 条历史记录，当时未有新增资产或同名 mcp-server-dev。
任务表 A6:B1000 当时为空，没有可复用的实际任务 ID；新 ID 唯一。
候选 CAND-ANT-011 原负责人待分配、未关联任务；按用户指派同步为 Vannes Wijaya。
研究快照（Skill 初判、热度、原许可声明）保持原值，实际交付选 Plugin，以承载三项 Skill 和脚本。

| 关联资产 ID | 功能对照 | 处理 |
| --- | --- | --- |
| 4c94938898ed4d3580593e5535f2315b / MCP Builder | 输入 MCP 服务需求，输出 Python/TS 服务、工具、资源、提示词及评估设计；依赖 SDK | 明确有重叠。扩展其工作流：路由回该资产处理通用实现/认证，只新增 UI、MCPB 配套能力与可执行示例；不搬运/重发通用教程，不复制其 Hub 源码。以不同 Plugin 包提供配套入口，不变更历史资产 ID/版本/发布者。 |
| 4862208069dc4ed9b1838f6ddfabbcc4 / MCP 编排管理器 | 输入已有服务器，输出启停、健康和权限编排 | 本次生成开发工程和本地示例包；不管理外部 MCP 服务。 |
| 921c641aa26e42eaacf2b9bee14a8eba / HTTP 接口探测助手 | 输入本机 HTTP 地址，输出探测结果 | 本次验证 MCP stdio 协议/UI 资源及 MCPB；不提供 HTTP 探测。 |
| c05b57f698fc47038bfdbff3824a65eb / 项目初始化向导 | 输入已有仓库，输出技术栈体检/推荐 | 本次显式生成 MCP App/MCPB 工程，不扫描或自动配置工作区能力。 |

## 固定来源与许可覆盖

上游：https://github.com/anthropics/claude-plugins-official/tree/d4226d062928f8d9505dbdeadd10217d23361052/plugins/mcp-server-dev
完整提交：d4226d062928f8d9505dbdeadd10217d23361052，无插件 manifest 版本声明。
根 README 指明各插件以各自 LICENSE 为准；已分别核对根 LICENSE 和插件 LICENSE，均为完整 Apache-2.0，同一字节哈希。
检查了该插件完整文件清单、插件级 LICENSE、manifest 作者信息、选定 Skill 文件头、示例代码和引用；选定路径没有子目录许可证或附加权利限制。
插件作者 metadata 为 Anthropic / support@anthropic.com；未另见具体版权年份声明。LICENSE 附录中的 [yyyy] / [name of copyright owner] 是上游原有占位文字，原样保留，不将其编造成新版权声明。
固定提交的仓库根、插件根及所选子目录没有适用 NOTICE，记录“无”；未伪造 NOTICE。

下载了根许可证及插件的 22 个文件，只作为审查输入，逐文件 Git blob SHA-1 与官方固定提交清单核对。
审查上下文接触过这些获 Apache-2.0 许可的实现，采用 ported，不声称 clean-room。
`audit-upstream` 原始检测为 unknown，仅为辅助证据；下列人工范围审查及实际随包复核才支持 permission_status=verified。

| 上游文件 | SHA-256 |
| --- | --- |
| LICENSE（根和插件一致） | cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30 |
| skills/build-mcp-app/SKILL.md | d2fd94f0096506469ec855c581e48293d35480e58e6405b2bfcdba0486a0c218 |
| skills/build-mcpb/SKILL.md | 6bb90afd0415754e13f353ee5982d13857c14826edbcbdf5f1481fa5563cd56b |

## 实际复用、修改和排除

下列路径相对发布载荷 `mcp-server-dev/mcp-server-dev/`。实际分发改编内容全部列入 provenance.reused_paths，并在对应文件作显著修改声明。

| 载荷路径 | 上游输入 | 具体修改 |
| --- | --- | --- |
| skills/build-mcp-app/SKILL.md | 同名 Skill | 中文步骤、已有 MCP Builder 路由、实际测试模板和宿主待验证边界；删除未完整实现的业务/宿主特定示例与失效引用。 |
| skills/build-mcpb/SKILL.md | 同名 Skill | 用实际加法示例替换本地文件访问示例；明确 Node 先决条件、官方 CLI 固定版本、解包再测。 |
| templates/app/server.mjs | build-mcp-app/SKILL.md 工具和资源注册示例 | 改成 stdio、有界加法、绝对 HTML 路径、结构化结果和文本回退。 |
| templates/app/widget.mjs | build-mcp-app/SKILL.md App 生命周期示例 | 单一结果组件、textContent、解析失败回退、宿主主题变量。 |
| templates/app/build.mjs | build-mcp-app/SKILL.md 本地 SDK 内联模式 | 改用 esbuild 编译，不依赖修改压缩 SDK 尾部 exports；保留合法注释，转义 script 终止序列。 |
| templates/mcpb/server.mjs | build-mcpb/SKILL.md SDK stdio 注册示例 | 不分发原文件访问工具；用有界加法演示协议、注解和输入错误。 |

manifest、规划/生成脚本、元数据、锁文件、中文使用文档及测试为本仓新增的集成工作；整个混合载荷按 ported 记录。
没有复制上游通用 build-mcp-server Skill、其参考资料、Claude marketplace manifest、图标、字体、数据或品牌素材；不声称官方背书。
既有 MCP Builder 仅按公开资产功能说明和链接集成，没有取得或复制其实现。

## 依赖与素材逐项复核

- 运行插件生成器：Python >=3.9 标准库，无第三方 Python 运行依赖。
- 生成工程：Node >=20；@modelcontextprotocol/sdk 1.32.1、@modelcontextprotocol/ext-apps 1.7.5、zod 4.6.7；构建工具 esbuild 0.28.1。直接版本固定，传递依赖以随模板 package-lock.json 的 registry URL 和 integrity 锁定。
- 已读取以上四项实际安装包的完整许可原文及原版权声明；SDK、zod、esbuild 为 MIT，ext-apps 实际 LICENSE 是许可迁移文本：新贡献 Apache-2.0、未获重授权同意的旧贡献仍为 MIT、文档（不含规格）CC-BY-4.0；npm 的 MIT 字段不代表全文件统一许可。未从该 SDK 复制文档或实现进入 Plugin ZIP。生成的 App 构建时收集完整实际 LICENSE/NOTICE，保留 Apache 和 MIT 文本；不能仅保留 metadata 或压缩注释；安装文件许可证 SHA-256 分别为 SDK 5e13dbbc1d120fc2a03cecde7c91424ae2d7de11b63d58ded2f4431e261ee50d、ext-apps 0382b0057770ca05e9c350a50aa3b1c1fea84da0bc81d723bf00b9aa841be58a、zod 3f1189b28e3866e0d979968d466b78f813f76827cfdca1fbb124cc0a5c8841f8、esbuild b40ec5baec7bb34fa5b1c09521fa3cd52d5fad7adafed74932a2010d3612a681。
- 自动 collect-licenses.mjs 为两个生成工程逐包收集实际许可全文/NOTICE 到 licenses/npm 并写清单；该动作仅收集证据，不自动许可放行。它们的实现未放进 Plugin ZIP，只在测试或用户生成工程中另行安装；不把外部安装路径冒充随包许可证据。生成的 MCPB 保留真实 node_modules 及依赖许可证，解包实测 SDK/LICENSE 与 zod/LICENSE 存在；生成项目未来分发仍需逐依赖复核。
- 官方 MCPB CLI 2.1.2（MIT）仅在测试工具目录安装，不放进插件 ZIP 或生成的演示 MCPB；CI/包装器的 PyYAML 6.0.3 为已有仓库开发依赖，不是插件运行依赖。
- 无外部 API Key、云账户、字体、图标、数据、外部服务调用或新增付费服务；云端部署、OAuth 和其他权利/服务条款不在本地测试覆盖中。
- 新代码许可证尚待总控决定，不填虚构 SPDX、不声称上游许可自动覆盖原创工作。这不改变已有仓库政策。

## 最终 ZIP 随包复核

唯一外壳 `mcp-server-dev/plugin.yaml`；唯一载荷 `mcp-server-dev/mcp-server-dev/`。
必须含 `THIRD_PARTY_NOTICES.md` 和 `licenses/claude-plugins-official/LICENSE`（完整 Apache-2.0、原字节哈希 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30）。
六个改编路径均携带 2026-10-22 修改声明；不存在适用上游 NOTICE，故无需虚造。
provenance.json 的 license_evidence 路径与哈希须与解包文件一致；artifact.json 列出最终载荷每文件哈希。测试记录、上游研究缓存、node_modules、实际测试 MCPB 不进入发布 ZIP。
最终检查使用实际 ZIP 解包、文件集合/哈希比较并运行解包载荷的工程生成和协议测试，实际结果：17 个载荷文件逐项一致，完整许可哈希及六处修改声明全部通过，解包载荷的完整功能复测通过；见 TEST_REPORT.md / RELEASE_TEST.log。

## 当前交付边界

真实协议测试与包装合格支持提交本次开发 PR；不证明 Agentic Hub 已提交、审核通过、已发布或已获总控验收。
实际 MCP Apps 宿主渲染、目标桌面安装、两类真实截图、Hub 最终提交状态和 Song Haoran 明确验收仍按追踪表记录，不由 AI 自动补齐。


## 1.0.1 local test patch (2026-10-22)

Reuses task AH-20261022-mcp-server-dev and its existing source/license review. Adds original integration metadata display_name/display_description and updates version declarations to fix the blank native plugin card reported by the user. No new third-party code, icon, font, documentation or dependency is distributed. Existing full Apache license bytes and six change notices remain present. Native host functions and frontend localization are inspected/executed in memory from the user's local checkout solely for compatibility verification; no host source enters the runtime payload. Both final ZIPs contain 17 byte-identical payload files; audit records and hashes are in the workspace outputs/mcp-server-dev/1.0.1 directory. This package is not yet merged or submitted; it remains in Build pending current-package user test completion. Historical 1.0.0 evidence above is retained.

## 1.0.1 submission review (2026-10-22)

The user has now explicitly completed testing and authorized submission/merge of the marketplace package; USER_TEST_CONFIRMATION.md preserves that statement and the original screenshot hash. Marketplace SHA-256 acd7f7b1c2fecb6ac1887e80cce5f86e0a7502fd60c6dc546f77ef909249701f is unchanged. The complete bundled license hash, six modification notices and all 17 runtime files were rechecked against both packages. Only external test/confirmation documentation and release-record hashes change in this step; no third-party reuse scope or runtime bytes change. The PR is a GitHub delivery of the market-wrapper ZIP. Per current AGENTS.md, Song Haoran owns later Agentic Hub operations; no Hub status or final acceptance is inferred from this submission.
