# Linear 1.2.1 测试报告

2026-11-22，Song Haoran；AH-20261117-linear-connector。仅改 Agentic Hub 包，不改 WorkSwarm 源码。当前为短时 Node CLI + 技能，调用 Linear 官方托管 MCP，使用 mcp-remote 0.16.6 的标准 OAuth 客户端。以下均针对精确 1.2.1 包；旧版本结果和制品独立保留。

## 精确制品与环境

- 原生 ZIP：`test-packages/linear-1.2.1-native.zip`，SHA-256 `44d4c15357d1bb28ecc08d6489dedbb9a51e30d43c8be35f3ee7eb14eb79140e`。
- Hub ZIP：`release/1.2.1/linear-1.2.1-agent-mcp.zip`，SHA-256 `1cf7401eeb36846d5a3d8a25eaf1c95b7c569f7b755f5e99b88b3c388f1e534f`。
- 实际运行本机 `/Applications/WorkSwarm.app` 的 0.2.8 后端、前端和所带 Node 22.12.0；隔离配置首次安装时 HOME、npm 缓存和本包授权均为空。模型使用已配置的 gpt-6.1-sol，既有模型账号通过引用使用，没有读取或复制令牌。
- 精确 Hub ZIP 经原版市场安装器和本地目录测试夹具安装，9 个安装文件与原生 ZIP 逐字节一致。没有手动安装 CLI 或导入 OAuth JSON。这不是正式 Hub 在线安装或人工审核通过。

## 安装与正常授权

- 9 项 Node 测试通过：成功后子进程退出／端口释放、超时后强制终止与端口复用、父进程终止后的子进程清理、错误脱敏与写入结果未确认提示、UTF-8 分片中文、固定运行时版本和模块校验、已有事项更新拦截、工具白名单、中文参数 schema。
- 官方打包 CLI 0.0.1 的 init／validate／pack、源码及两份 ZIP 的 JavaScript preflight、路径／CRC／解压比例／载荷等价检查通过。实际冻结的 0.2.8 解析器识别为 cli、cli-oauth、一项技能，无常驻 server_config。
- 卡片“连接”自动准备固定版本的标准客户端并打开正常 OAuth。官方页面显示 WorkSwarm Linear Connector、https://workswarm.app、Read / Write，回跳后卡片显示“使用”。未扩大原有读写 grant；包内操作限制不缩小服务授予的账号权限。
- 实际发现并限制为 8 项工具：list_comments、save_comment、get_issue、list_issues、save_issue、list_issue_statuses、list_teams、get_team。

## 中文聊天业务验收

在 OpenJiuwen 专用测试团队中，由 WorkSwarm 聊天实际读取当前技能，使用安装目录中的 Node CLI 执行，界面展开轨迹保留了真实 Bash Stdout，不仅依赖模型总结。

| 步骤 | 实际结果 |
| --- | --- |
| 团队、搜索与读取 | 核对团队 OpenJiuwen；搜索 WorkSwarm 得到既有 QA 工单 OPE-5／6／7，无下一页；读取 OPE-7 及已有中文评论标记 LINEAR-111-20261122。 |
| 新建前查重 | 按完整标题查询并逐条比较 7 个返回项，未找到同名；没有把服务的模糊查询当作严格匹配。 |
| 新建工单 | 仅创建一次 OPE-8，ID eb544132-0efb-43cd-9bc8-0ff839fbb59b；标题“WorkSwarm Linear CLI 1.2.1 回归验收 20261122”。 |
| 独立读取工单 | 单独 get_issue 回读，团队、标题及虚构测试描述一致。 |
| 添加评论 | 先查评论为空，再仅追加一次“短时 CLI 中文评论验收 LINEAR-121-20261122”；ID 16b798d3-5d83-4a88-a7d8-7a7ecfe75f98。 |
| 独立读取评论 | 单独 list_comments 返回这一条，ID 与正文一致，无下一页。 |
| 范围限制 | 直接对当前安装 CLI 传已有事项更新字段，调用前即被拒绝；没有更新已有工单、删除或读取认证文件。 |

读取回合 1m30s，写入回合 2m08s；进程检查覆盖本轮隔离实例所有父子关系，业务结束后没有其下残留 Node 进程。

## 失败、撤销与生命周期

| 场景 | 结果及证据范围 |
| --- | --- |
| 尚未授权 | status 返回 connected=false / AUTH_REQUIRED，不主动打开浏览器。 |
| 真实拒绝授权 | 在 Linear 点 Cancel，返回 access_denied；在 WorkSwarm 点“取消连接”，卡片恢复“连接”，无残留 Node 进程。 |
| 未完成授权超时 | 精确安装 CLI 的真实 OAuth 等待 165.04 秒后 TIMEOUT、退出码 1；回调 22227 可重新绑定。未把它表述为卡片自动关闭已验证。 |
| 已连接但尚未聊天就断开 | 原版 mcp.disconnect 返回 applied=true，mcp.show 已断开且 tools=[]；本地授权清除，完整父子进程检查为零。绕开旧常驻 MCP 的宿主 probe 缓存。 |
| 受控网络故障 | 只对 mcp.linear.app 注入测试 DNS ENOTFOUND；tools 约 0.2 秒返回中文 CLIENT_FAILED，恢复正常网络后 status 成功。没有写入；不是服务商真实宕机。 |
| 真实远端撤销 | 经 Song Haoran 许可，在原测试账号撤销 MCP（Read, Write）。不手改本地缓存，status 和 get_issue 分别在 5.35／6.92 秒返回 AUTH_REQUIRED，无业务结果。 |
| 撤销后的中文聊天 | 实际聊天仅执行读取 OPE-8，收到 AUTH_REQUIRED 后停止，没有自动登录或写入；完整工具轨迹与原图已保存。 |
| 恢复授权 | 用原版 mcp.disconnect 清除本地连接状态，再从广场卡片“连接”完成相同工作区、相同范围的正常授权。卡片恢复“使用”；CLI status 为 true，get_issue 读到 OPE-8 原标题。未新增写入；恢复后没有残留 Node 进程。 |

## 卡片卸载重装恢复授权（后续补测）

前轮的恢复使用了断开 RPC，不能证明普通用户 GUI 恢复。Song Haoran 随后明确批准卸载重装这个隔离测试连接器。本轮再次从同一测试账号撤销 MCP Read/Write，保持本地缓存不手改；status 在 5.16 秒返回 AUTH_REQUIRED。随后全部恢复动作均在原版 0.2.8 界面进行：

1. “我的扩展 → 连接器 → Linear 连接器 → 卸载”，核对删除本地配置／凭证／技能的提示后确认。列表变为“暂无我的连接器”，实际安装目录消失，无残留 Node 子进程。
2. 回“连接器广场”，同一资产显示“安装”；点击后从本地目录夹具重新下载精确 1.2.1 ZIP，9 个载荷文件与冻结原生包一致。
3. 安装器自动准备客户端并打开正常 Linear OAuth，应用身份和 Read/Write 范围不变。选择同一测试工作区后正常回跳，卡片恢复“使用”。
4. 独立 status 为 connected=true；从恢复后的卡片点“使用”进入中文聊天，按技能发现工具，get_issue 读到 OPE-8 原标题、团队和描述。随后独立 list_comments 返回原来唯一一条评论，ID 16b798d3-5d83-4a88-a7d8-7a7ecfe75f98、中文正文和 LINEAR-121-20261122 标记一致，无下一页。聊天回合 1m04s，7 次宿主工具调用的展开轨迹含真实 Bash Stdout。

本轮未手动调用断开或认证重置 RPC，没有手动安装 CLI、导入 OAuth 配置、编辑认证缓存或修改 WorkSwarm 源码。外部 status 和安装文件校验只用于只读断言，不负责恢复。没有新增／更新／删除远端数据；卸载后及恢复聊天结束后，完整父子关系检查均无本测试实例的残留 Node 子进程。当前连接保持可用。

仍需区分：授权失效后卡片不会即时刷新；此版验证的是用户主动“卸载 → 安装 → 授权”的恢复路径，不是卡片自动察觉失效或原地重连。前轮自动审批拒绝卸载的记录保留；本轮在用户明确批准后通过界面执行，不是绕过该拒绝。

## 证据与交付状态

当前证据位于 `test-evidence/20261122-cli-1.2.1/`，清单与 SHA-256 见 evidence-index.json。聊天展开轨迹中的 Bash 输出、原图、安装等价、超时、撤销、恢复及完整进程检查分开保存。只收录核对过的测试截图原图；带无关用户标签页的 Safari 图与账号安全页留在工作区私有证据中，不进入交付目录。

Windows、Linux、远程服务器 OAuth、自然到期的刷新令牌、正式 Hub 在线安装和人工审核尚未验证。远端撤销覆盖的是失效分支，不等于自然到期实测。Song Haoran 随后在当前对话明确确认：“确认 Linear 1.2.1 测试通过，附上实测截图提交 PR”。确认涵盖上述精确 ZIP 与纯卡片恢复补测；本次交付不重建载荷或 ZIP。确认记录：RPT-20261122-linear-first-auth-repair，当前对话，2026-11-22（Asia/Shanghai）。本报告的交付记录变更不改变已测包。尚未创建 PR 时不填虚构链接，GitHub 交付和项目负责人最终验收分别同步。
