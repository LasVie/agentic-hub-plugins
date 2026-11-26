# Jira Cloud 连接器 1.1.0 来源审查（2026-11-23）

Jira Cloud → Jira Cloud 连接器 → jira-cloud。原 Task AH-20261117-jira-cloud-connector，Song Haoran，Candidate Not Applicable。1.0.4 原包、PR #103、Completed/Accepted 和拒审证据保留；本次沿用原任务，不替换历史。

本次独立编写有限 Node CLI、中文技能及 Jira 工具白名单，连接 Atlassian 官方托管 MCP v2。只参考其公开接口和工具说明，不复制服务端实现、上游提示词或技能。官方示例清单不等于 WorkSwarm 0.2.8 已实测成功；工具和 OAuth 可随服务端改变。

标准客户端 mcp-remote 固定 npm 0.16.6，对应 punkpeye/mcp-remote 提交 e4dc3713b0d6a727cbeb21f38324d20a6692dc5f，原作者版权 Copyright (c) 2025 Cloudflare, Inc.，MIT 全文及免责声明已审阅。沿用本团队 Linear 1.2.1 已验证的固定导出模块 dist/chunk-MKB2ICYW.js，SHA256 8e4e647f0b25dc52a28a6d1cbbb6727851ae0e5ae74a6f2ea23cb4acb7b47638；安装脚本禁用，运行时从 npm 下载，不在 ZIP 中分发客户端源码/二进制。复用团队有限子进程、客户端定位和 OAuth/MCP 协调方式，只改 Jira 业务约束；没有修改 mcp-remote 发行文件。完整 MIT 随载荷附 licenses/mcp-remote/LICENSE，说明见 THIRD_PARTY_NOTICES.md。该客户端不是 Atlassian 官方产品；服务端才是官方托管 MCP。

官方 2026-11-23 文档推荐 https://mcp.atlassian.com/v2/mcp，tools=all 参数可分页列出完整工具，不需向模型开放任意 execute/discover。已读接口公开的受保护资源元数据，默认有多个产品、管理和删除 scopes。因此显式固定 read:jira:agent-interface、search:jira:agent-interface、write:jira:agent-interface 、read:me、read:account 和 offline_access，授权跳转若扩大到此集合以外则拒绝继续。此次保留搜索/读取/创建工单及创建必需的项目类型元数据，不开放 Confluence、跨产品 Rovo 搜索、删除、编辑、评论或管理工具。

保留 1.0.4 已审查、未修改的 Jira PNG 标识（SHA256 1db5048d57adcd0bfd50c6dd2a7f62e51e9689630c2dfb5f5af438c79c97df73），沿用官方品牌来源、商标说明和使用边界，不表示 Atlassian 背书。

来源：
- https://atlassian.github.io/atlassian-mcp-server/
- https://support.atlassian.com/atlassian-ai-gateway/docs/supported-tools/
- https://support.atlassian.com/atlassian-ai-gateway/docs/configure-oauth-2-1/
- https://mcp.atlassian.com/.well-known/oauth-protected-resource/v2/mcp
- https://github.com/punkpeye/mcp-remote/tree/e4dc3713b0d6a727cbeb21f38324d20a6692dc5f
- 原团队 Linear 实现：本仓库 PR #113 的 1.2.1 代码和来源审查。

最终精确包已在 stock WorkSwarm 0.2.8 完成卡片 OAuth、中文搜索/读取、新建 KAN-6 及独立回读；11 项回归、真实拒绝及卡片取消清理已验证。测试边界、原图及当前 ZIP 哈希见 TEST_REPORT.md 和 release/1.1.0/artifact.json。以下首轮记录保留实际排查过程，不能替代最终结果。

## 首轮真实 OAuth 及官方兼容要求

第一轮精确包已通过 stock 0.2.8 卡片安装，9 个文件一致，用户在真实同意页选择测试站点并 Accept；服务在回调前返回 invalid_request / Incorrect request parameters，未取得会话、没有执行业务写入。首次四权限候选已归入本地操作记录，不交付。

2026-11-23 在官方缺陷 https://jira.atlassian.com/browse/ID-9242 核实同样表现及服务要求：产品权限之外还须 read:me、read:account、offline_access。按该建议增加两个基本账号读取权限，不增加其他产品、删除或管理权限；更新精确包后会让用户核对新的授权请求。该结论来自官方记录，实际修复效果仍须下一次正常授权验证，不能把首轮失败记为成功。

第二轮补充基本账号权限后，宿主未取得可显示的授权链接、只提示 CLI 已开浏览器。本包据此增加先就绪的本机 URL 引导页，标准 OAuth 回调仍由固定客户端负责；尚未完成本轮授权，待重建及真实验证。

进一步只读核查发现首轮测试登录 worker（PID 4143，PPID 1，命令精确指向本次隔离 Jira 包）在宿主取消后仍占用默认回调端口。已仅清理此已核实孤立进程。后续授权等待不能仅归因于网络或宿主抓取时机；标准客户端还会跟随同端点既有回调监听。因此新增 worker 的父 IPC 断开即退出、独立总超时，并为每个宿主数据目录选择稳定的独立回调端口；实际固定客户端回归已通过：首个输出为本机引导 URL，5.59 秒后取得精确六项权限的官方授权 URL；对测试 CLI 父进程执行 SIGKILL 后，真实 OAuth 回调监听已关闭。该探测未进行用户同意或业务调用；真实卡片和聊天仍待验证。

第二轮六项权限已不再返回 invalid_request，浏览器在用户同意后尝试回本机；此时五分钟等待已超时，端口关闭并报 ERR_CONNECTION_REFUSED。此为实际失败结果，不等于已经得到可用会话。下一候选将固定客户端、协调器和包内总登录时限一起延至 30 分钟，界面明示；权限不变，等待真实验证。

## 实际 v2 返回适配

已使用现有官方会话完成只读工具发现：服务确实提供白名单内七项工具。getAccessibleAtlassianResources 返回 data.resources，其站点键是 cloudId；原解析只适配发现 REST 的 id，导致登录后误判没有站点。已兼容实际封装及 Jira 产品过滤。createJiraIssue 实际必填参数为 issueType，已据真实 schema 修正，继续禁止 assignee、额外字段等；未知的范围外必填字段现在直接阻止使用，不再静默删除。新增两项真实格式回归，合计 11 项通过。

修正源码的真实 status 已返回 connected=true，站点为 openjiuwenofficial.atlassian.net；实际读取 KAN 类型清单得到 Task（10003）等四个类型。尚未写工单，也未完成聊天测试。这是组件只读验证，不能替代最终精确包的卡片安装和聊天验收。

最终精确制品的 OAuth 和业务通过，不等于已通过 Hub 人工审核。SDK 负责令牌刷新，但未实际等待自然过期或撤销远端授权，不能声称这两项已实测成功。

2026-11-23，Song Haoran 明确确认本版实测通过、接受已列明边界，并批准五张原图随 PR 公开。该确认对应 artifact.json 的当前精确包，未改变运行载荷或 ZIP。
