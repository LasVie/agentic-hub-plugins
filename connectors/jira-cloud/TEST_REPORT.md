# Jira Cloud 连接器 1.1.0 测试记录

2026-11-23，Song Haoran；原 Task `AH-20261117-jira-cloud-connector`，Candidate Not Applicable。**原版 WorkSwarm 0.2.8 的卡片安装、正常 OAuth、中文搜索/读取、新建一条工单及创建后独立回读已实测通过。只修改 Agentic Hub 包。** Song Haoran 已明确回复「确认通过并提交 PR」，确认本版测试结果、接受列明的未测边界，并批准公开五张原图；现进入 Submit。未声称 Hub 已审核或上架。

历史 1.0.4 的 Completed/Accepted、PR #103、旧 ZIP、来源与拒审证据保留；旧 Python 源码逐字保存在 `history/1.0.4/native-source/`，没有重写历史测试结论。

## 环境与精确制品

- macOS Apple silicon；本机 stock WorkSwarm 0.2.8，使用其自带 Node.js 22.12.0。未修改应用源码或安装包。
- 全新隔离 WorkSwarm 配置使用本机 Hub 目录夹具下载精确 Hub ZIP，实际卡片执行安装及连接；无需手动安装 CLI、Python 或粘贴令牌。**本机夹具不是正式 Hub 安装、公开目录或人工审核证据。**
- 官方 Agentic Hub CLI 0.0.1 对干净 staging 执行 validate、pack；原生 ZIP、Hub ZIP、审查源码及最终安装的 10 个文件逐项 SHA256 相同。
- 原生包：`test-packages/jira-cloud-1.1.0-native.zip`，SHA256 `d6c5a3bfa636f2d943dd12b8b17404a3687157d5eb8ef89bb55ae6d3297cf1fd`。
- Hub 包：`release/1.1.0/jira-cloud-1.1.0-agent-mcp.zip`，SHA256 `fa99ccbddaaf41077c1fac3455b5726b19e3dcd8d3eaa6dc28ec4f108d1fad9f`。
- 两个精确 ZIP 的动态 JavaScript 预检均为 3 个文件、0 个已知签名。详细映射及审查文件哈希见 `release/1.1.0/artifact.json`。

## 实际功能与失败验证

| 项目 | 实际结果及证据边界 |
|---|---|
| 卡片授权 | 卡片打开本机引导页，再进入官方 Atlassian 同意页。实际会话可用，卡片显示「使用」，工具及站点读取成功。 |
| 权限和工具 | 精确请求 Jira 读/搜/写、read:me、read:account、offline_access；请求与令牌 scope 均检查范围。实际发现七项白名单工具，不开放 Confluence、任意 execute/discover、现有工单修改/删除/评论/分配。OAuth 写 scope 本身比本包新建操作更宽。 |
| 中文搜索和详情 | 在已选中 Jira 的新聊天中，由模型读取 jira-cloud 技能并调用已安装 CLI；查询 KAN 最近五条工单，独立读取 KAN-5 的中文标题、描述和状态。 |
| 新建前检查 | 实际读取 KAN 类型及必填字段元数据；Task 为 10003；完整唯一标题查重为 0 条且无后续页。 |
| 唯一写入 | 聊天实际只调用一次 createJiraIssue，新建 **KAN-6 / ID 10047**。标题 `WorkSwarm Jira 中文验收 20261123-Node-QA-0210`；正文 `这是一条由 WorkSwarm 聊天创建的中文连接器测试工单，仅用于验证新建与独立回读，不包含真实业务数据。` 未指定负责人，未评论、修改或删除已有事项。 |
| 创建后独立回读 | 另行 getJiraIssue 核对同一编号、标题及正文；该响应省略项目/类型。再按 key = KAN-6 查询核对同一 ID、项目 KAN、类型 Task 及标题；该响应省略正文。**两次读取共同覆盖验收字段，不能称为同一个响应的原子快照。** Jira 真实页面也显示同一测试工单、正文及未分配状态。 |
| 缺少授权 | 对独立无令牌配置和实际断开后的本机配置执行精确安装 CLI status，均返回 AUTH_REQUIRED、connected=false，不自动开启浏览器。 |
| 不允许的工具 | 对精确安装 CLI 请求 editJiraIssue，实际退出 1、SCOPE_REJECTED，在业务调用前拒绝。 |
| 真实拒绝授权 | 用精确安装 CLI 的独立无授权配置进入官方同意页，实际点 Cancel；回调显示 User did not authorize the request，CLI 退出 1、CLIENT_FAILED，没有误报成功。该项是安装包 CLI 测试，**不是 stock 卡片拒绝测试**。本机引导及回调端口均关闭。 |
| 标准断开 | 通过 stock 宿主 mcp.disconnect RPC 返回 applied=true；本地会话失效、state 记录和技能目录清除。通过 RPC 从外部断开后，已打开详情视图曾保留缓存，刷新后显示「尚未连接」；未宣称 UI 自动刷新。 |
| 卡片取消 | 在真实卡片点击连接，再点弹窗「取消连接」。界面恢复「尚未连接」、使用禁用、可重新连接；引导端口 57256 和回调端口 45483 均关闭，未发现该测试包残留 worker，随后 status 为 AUTH_REQUIRED。 |
| 父进程异常结束 | 用精确安装 CLI 及固定客户端实测：3.66 秒取得六项 scope 的官方 URL，主动 SIGKILL 本次探测父进程后回调端口关闭。该探测未替用户同意或调用业务。 |
| 范围和进程回归 | 11 项 Node 检查通过，覆盖权限 URL、字段/工具限制、中文文件参数、未知写入结果提示、有限子进程超时、引导页、按配置稳定回调端口、实际 v2 站点封装及创建参数。 |

## 排查所得与剩余边界

首次四项 scope 候选在 Atlassian 同意后返回 invalid_request。官方 ID-9242 要求额外 read:me/read:account，补齐后真实授权成功。第二轮曾超过五分钟才回跳，端口已关闭；当前包明确等待 30 分钟。另发现旧候选在宿主取消后遗留登录 worker，已仅清理核实的测试进程；本版增加父 IPC 断开退出及独立总超时，并实际回归通过。

实际 v2 工具返回 data.resources/cloudId，创建类型参数为 issueType，本版已按真实响应适配；未知的范围外必填字段将阻止使用。服务端元数据和接口仍可能变化，包不能保证未来版本永久兼容。

首轮聊天因测试时刷新模型页面丢失连接器选择，没有业务执行；随后旧聊天还保留错误的技能基线。重新从卡片「使用」进入已选中 Jira 的新会话后，正常读取技能并完成全部业务步骤。没有给模型手工注入脚本绝对路径来冒充正常技能加载。旧失败记录没有改成成功。

未实际等待自然令牌过期，也未撤销远端账号授权；其后的自动刷新与恢复仍需另测，缺少本地会话测试不能替代它们。Windows、Linux、服务器远程回调、正式 Hub 安装及审核未验证。测试结束保留 KAN-6 为验收证据，隔离 WorkSwarm 中连接已断开。

## 原始证据

`test-evidence/20261123-stock-1.1.0/evidence-index.json` 列出精确包和原图 SHA256。该目录保存最终安装逐文件比对、实际业务响应（创建计数 1）、真实工具 schema、失败/生命周期结果、历史文件完整性和规则复核。五张 PNG/JPEG 原图未裁剪、涂改或重新压缩：连接状态、聊天最终记录、Jira KAN-6、官方拒绝授权及卡片取消后状态。

用户确认和五张原图公开授权已记录于 user-test-confirmation.json；确认对应上述两种精确 ZIP，运行载荷与 ZIP 字节未变化。仅授权提交 PR，未授权合入。
