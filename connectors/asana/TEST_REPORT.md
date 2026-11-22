# Asana 1.1.0 测试报告

本轮完成于 2026-11-23（Asia/Shanghai）；负责人 Song Haoran；原任务 AH-20261117-asana-connector；候选 CAND-CLD-323；内部 ID repo:agent-mcp:asana。中文名称 Asana 任务连接器。本轮补齐正确卡片安装、凭据输入和真实聊天验收，未修改 WorkSwarm 源码、连接器载荷或冻结 ZIP。旧报告及失败证据独立保留。

## 制品和环境

- 原生 ZIP：test-packages/asana-1.1.0-native.zip，12,584 字节，SHA-256 `4110e37f8a3ace88263ecffad7ad00d485e4ea5b7b57f58b62f9b4105b2a7d1d`。
- Hub ZIP：release/1.1.0/asana-1.1.0-agent-mcp.zip，7,072 字节，SHA-256 `57348470aea2ccc0ea85d733de007e059a636ad10c9f57d67f17fc6ae61d45e6`。
- 本机原版 WorkSwarm 0.2.8，随附 Node 22.12.0，macOS；原版前端、网关和 agent 使用全新隔离配置。
- 从市场卡片经本地目录测试夹具安装精确 Hub ZIP，5 个载荷文件逐字节等于原生 ZIP。没有手动放置载荷、注册自定义 MCP、安装 Python／pip／npm 包或读取／复制 PAT 文件。这不是正式 Hub 在线安装或人工审核通过。
- 用户在 Safari 官方 Asana 控制台自行接受 API 条款、生成 PAT，并在 WorkSwarm 原生凭据表单填写、保存、连接；令牌未发到聊天，未进入证据。
- 模型 gpt-6.1-sol。第一次聊天在调用 Asana 工具前因测试模型账号旧刷新状态失败，耗时 2.67 秒；只调整隔离环境对最近有效模型账号状态的引用，未读取或复制凭据内容，随后真实聊天成功。此错误不算 Asana 401。

## 旧 401 的结论边界

旧的成功 QA 运行与失败的默认实例自定义 MCP 注册不是同一个配置／凭据来源。1.0.0 和 1.1.0 的字段始终是 ASANA_PERSONAL_TOKEN。本轮正常安装包并由用户从卡片输入后，真实 asana_status 返回 connected=true，后续读写均成功。

已验证的解决路径是“完整原生包经市场安装器安装 → 卡片安全输入 PAT → 当前实例真实聊天”，没有复现旧 401。旧失败具体是哪项配置或凭据原因仍不能追溯定论，更不能声称用户旧 PAT 必然过期。没有为制造修复而改动业务代码。

本版 initialize／tools/list 只返回 MCP 元数据，不访问 Asana；卡片有四项工具不等于 PAT 验证成功。实际授权结论以 asana_status 和业务调用为准。来源及进一步分析见本轮 test-evidence/20261123-card-1.1.0/credential-flow-analysis.md。

## 中文聊天实际结果

四项范围不变：asana_status、asana_list_tasks、asana_read_task、asana_create_task。只支持指定项目列表、任务详情和新建有标题的任务，不支持更新／删除、负责人分配或任意接口。

| 步骤 | 实际结果 |
| --- | --- |
| 授权 | asana_status 返回 connected=true。 |
| 列表 | QA 项目 1220594404826613 返回原有 8 项任务，next_page=null，其中 3 项标题含 WorkSwarm。未臆造下一页。 |
| 读取 | 分别独立读取 3 条既有 WorkSwarm 测试任务，核对中文标题、notes 为空、completed=false、所属项目一致。 |
| 查重 | 再次完整查询原有 8 项并逐条比较完整唯一标题，未找到同名。 |
| 新建 | 只调用一次 asana_create_task，只传 container 和 title；新 ID 1220767735426842，标题“WorkSwarm Asana 卡片验收 WS-ASANA-110-20261123”。 |
| 回读 | 单独 asana_read_task，返回 ID、完整中文标题和项目一致。未更新或删除已有任务。 |

读取回合 54.41 秒（13 次宿主工具调用）；写入回合 28.78 秒（7 次宿主工具调用）。展开的真实 MCP 参数和输出已保存，不仅依赖模型总结。界面包装调用与底层 MCP 输出不重复计作两次服务写入。

测试任务：https://app.asana.com/1/1220595506484888/project/1220594404826613/task/1220767735426842 。

## 失败与生命周期

- 原有 4 项 Node 测试再次通过：未知操作／更新字段／路径注入拒绝；创建只含项目和标题；缺凭据不发请求及中文脱敏 401／403／429／503；写入异常不重试且要求先回读。403／429／503 是受控单元响应，不是真实故障。
- 对精确 ZIP 的 Node stdio 入口另做三项隔离探测，没有接触用户 PAT：缺令牌时中文提示填写；用明确虚构的无效令牌请求真实 users/me 得到授权失败；受控 DNS ENOTFOUND 得到中文网络失败。仅状态 GET，无业务写入。stdin 关闭后三项进程均正常退出。
- 无效令牌不代表用户 PAT 自然到期，DNS 注入不代表服务商宕机。真实 PAT 撤销／到期、真实 403／限流未测试。
- 业务后记录到 1 个正常连接中的 stdio Node 服务。原版 mcp.disconnect 返回 applied=true；mcp.show 为 disconnected、tools=[]；完整父子关系检查无残留 Node 子进程，卡片显示“连接”。这是受支持的 RPC 断开及界面核验，不是 GUI 卸载重装测试。
- 测试后的本地连接已断开。远端测试任务和用户创建的 PAT 未被撤销或删除。

## 格式、许可和证据

精确制品的官方 CLI 0.0.1 init／validate／pack、路径／CRC／大小／载荷等价、三处 JavaScript preflight 已在原打包记录通过。当前载荷及两份 ZIP 与原记录一致。早前真实冻结 0.2.8 loader 已接受同一原生 ZIP，本轮再完成实际市场安装和聊天调用。开发检查使用 Python 不构成用户端 Python 依赖。

独立编写 Asana REST/PAT MCP，没有复制第三方实现／提示／图标，无运行时 npm 依赖；官方文档仅为接口依据，见 SOURCE_REVIEW.md。未新建 OAuth 应用或扩大权限。

本轮原图、完整轨迹及 SHA-256 清单位于 test-evidence/20261123-card-1.1.0/。不收录生成后的令牌页面。模型失败图留在私有操作目录，正常连接器结论单独记录。旧报告快照为 history/1.1.0/TEST_REPORT-20261120.md。

## 待验证和交付状态

Windows／Linux、远程部署、真实多页列表、GUI 卸载重装、真实权限不足或自然到期，以及正式 Hub 在线安装／人工审核仍未验证。已测卡片安装、PAT 传递、中文读写和业务后断开路径无已知阻塞。

Song Haoran 随后在当前对话于 2026-11-23 明确确认：“确认 Asana 1.1.0 测试通过，附上实测截图提交 PR”。确认覆盖上述精确制品及当前实测结果；确认报告 RPT-20261122-asana-gui-auth-repair。交付只更新审查／测试记录与原图，载荷和两份 ZIP 均不重建。PR 地址和 CI 在真实创建后同步；GitHub 交付不等于 Hub 上架或项目负责人最终验收。
