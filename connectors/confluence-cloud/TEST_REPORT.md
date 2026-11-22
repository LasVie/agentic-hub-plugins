# Confluence 连接器 1.1.0 测试记录

2026-11-23，Song Haoran，原 Task AH-20261117-confluence-cloud-connector。本版已完成测试并获 Song Haoran 明确确认，正在准备交付 PR。旧测试与 1.0.x ZIP 原样保留。

## 环境与制品

macOS Apple silicon，原版 WorkSwarm 0.2.8 应用内置后端和 WebUI，通过浏览器操作，自带 Node 22.12.0/npm；独立临时宿主配置及仅含当前资产的本地目录测试夹具。没有修改 WorkSwarm 源码或 app bundle，也没有手动安装 CLI、导入 OAuth JSON 或粘贴访问令牌。此流程是本地目录/卡片安装，不是正式 Hub 线上安装结果。

最终候选版本 1.1.0：

- 原生 ZIP：`test-packages/confluence-cloud-1.1.0-native.zip`，SHA256 `d1a538d4bc6dbeba23a695f35a9bb50c3d2ab0891330b3cc6909c54940812e7e`。
- Hub ZIP：`release/1.1.0/confluence-cloud-1.1.0-agent-mcp.zip`，SHA256 `3ee1f9bdc59c7d6721574a4b5b4a1fad8dcf04f22e8bb8468580e73ce6c7e35e`。
- 官方 agentichub validate/pack 成功。两份精确 ZIP 均执行 preflight：各扫描 3 个 JavaScript 文件，已知动态执行签名为 0；这不代替业务验证。
- 两份 ZIP 的 10 个载荷文件、当前源码及最终候选的实际安装文件逐个 SHA256 一致。图标未改，许可证全文保留。

## 已完成

1. 授权初稿从 WorkSwarm 卡片自动准备固定 mcp-remote 0.16.6；用户在官方同意页亲自接受 Confluence 读取、写入、搜索以及必要基本账号/离线刷新范围，卡片显示「使用」。无 Jira 权限。初稿的两份 ZIP 与最终候选不同，不用其授权结果冒充最终包业务通过。
2. 用该真实会话发现 7 个白名单工具的实际 schema；getConfluenceSpace 核对 SD 空间 ID `229380`，searchConfluence 找到原测试父页 `589826`。修正最终源代码后，用源 CLI 经 summary 类型/空间检查及 full Markdown 读取，拿到父页完整 `body.value`。未修改或创建远端页面。
3. 12 项 Node 检查通过：精确 OAuth 范围、禁止跨产品/任意执行/已有内容修改、嵌套新建字段、全文读取、页面类型/父空间核对、CQL 排序与引号、中文 JSON 文件输入、工具 schema 变化、超时、回调隔离、本机引导及关闭。
4. 最终候选从卡片卸载初稿后重新安装，全部 10 文件与最终 ZIP 匹配；用户再次亲自接受同范围的官方同意页，最终候选卡片显示「使用」。从卡片进入全新会话，模型 gpt-6.1-sol，连接器选择开关已开启，聊天实际读取 confluence-cloud 技能并执行包内 CLI。
5. 精确已安装 CLI 在独立未授权配置下自动 prepare 成功；status 返回 `AUTH_REQUIRED` 且 connected=false，不打开登录；executeWrite 返回 `SCOPE_REJECTED`。用测试启动器仅观察该 CLI 创建的 worker PID，在授权入口就绪后 SIGKILL 父进程，worker 已退出，本机引导及 OAuth 回调端口均关闭。未借用正常授权会话，也没有业务写入。
6. 中文聊天只读验收通过：status 确认连接、tools 只显示 7 个白名单工具；读取 SD 元数据，按完整标题搜索父页，独立按 ID `589826` 读取 full/markdown 正文。工具真实结果和最终中文回答一致。
7. 中文聊天写入验收通过：核对 SD `229380` 和普通父页 `589826` 后，唯一标题查重返回 0；只执行一次 createConfluenceContent，新建普通子页 `1277953`，标题为「WorkSwarm Confluence 中文验收 20261123-Node-C1」。创建响应核对 spaceId=229380/parentId=589826；随后用不同工具调用按 ID 独立 full/markdown 回读，全文与要求一致（仅末尾换行符规范化），首尾标记均存在。未修改旧页或操作评论、附件、分享、权限。
8. Confluence 原生页面核对成功，左侧内容树显示该子页位于既有测试父页下，中文标题及正文完整。页面保留作验收证据：<https://openjiuwenofficial.atlassian.net/wiki/spaces/SD/pages/1277953/WorkSwarm+Confluence+20261123-Node-C1>。
9. 在独立未授权配置的官方同意页点击 Cancel 实测，返回 `AUTH_DENIED` 中文提示、退出码 1；引导与回调端口关闭。标准宿主 mcp.disconnect 实际 applied=true，status 随后 AUTH_REQUIRED，挂载技能删除；刷新宿主状态后卡片恢复「连接」。再从卡片发起连接，确认 OAuth 回调已监听后点「取消连接」，卡片恢复「连接」，回调端口关闭。测试结束保留安装，已断开专用 QA 本地会话；没有撤销用户远端 Atlassian 账号授权。

## 可复核证据

脱敏业务结果、创建次数、独立回读核对、安装文件 SHA256、精确 ZIP 审计和生命周期结果记录在 `tests/fixtures/workswarm-0.2.8-20261123.json`。不含 OAuth 凭据或远端作者 accountId。12 项检查使用宿主 Node 22.12.0 执行。官方 CLI 实际发行包为 openjiuwen-agentichub 0.0.1；该 CLI 不支持 --version，版本从安装分发元数据核实。

已保存五张未经编辑或重新压缩的原始截图：最终候选同意页、连接卡片、聊天搜索/全文读取、聊天新建/独立回读、Confluence 原生子页。文件名、字节数和 SHA256 见上述证据 JSON。Song Haoran 已在当前对话回复「确认通过并附原图提交 PR」，授权将五张原图公开附到交付 PR；图片不会放入运行载荷。

测试宿主的 web 入口在深层 `/chat/...` 路径直接刷新时曾空白；从原根入口重开恢复。业务验收此前已完整结束，该现象没有通过修改宿主源码处理。标准 RPC 断开后原前端状态也须刷新才反映，不能把 RPC 返回当成界面即时更新。

## 尚待完成与边界

上述当前版本实测已完成，Song Haoran 已明确确认 1.1.0 通过并批准附五张原图提交 PR。确认仅覆盖上述精确 ZIP；不改变尚未实测的边界。

Windows/Linux、自然过期、远端撤销、远程服务器回调、管理员限制、正式 Hub 线上安装没有实测。写 scope 宽于本包实际工具范围；本包只提供普通页面搜索/读取/新建，不开放更新、删除、评论、附件或权限修改。

确认记录时间：2026-11-23T02:56:51+08:00。原话、当前对话来源、精确哈希及图片授权记录于 tests/fixtures/workswarm-0.2.8-20261123.json。未请求合并或 Hub 上架。

五张公开授权原图按原字节保存在 `test-evidence/20261123-stock-1.1.0/screenshots/`，SHA256 与 `evidence.json` 对应，并嵌入 [PR #117 正文证据](https://github.com/LasVie/agentic-hub-plugins/pull/117#issue-6546381329)。原图和证据目录不在运行载荷或 ZIP 内。
