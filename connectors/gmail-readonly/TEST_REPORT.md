# Gmail 邮件连接器 1.7.0 测试记录

2026-11-23；Song Haoran；AH-20261111-gmail-connection；repo:agent-mcp:gmail-readonly。只修改 Agentic Hub 包，复用 Calendar Node CLI＋技能方案；WorkSwarm 源码、应用安装目录均未修改。本轮开发和测试完成；2026-11-23用户明确确认1.7.0测试通过并批准9张实测原图公开附在PR中，现按授权提交PR，不执行合并或Hub上架。

## 精确交付物

- Hub ZIP：release/1.7.0/gmail-readonly-1.7.0-agent-mcp.zip；SHA-256 `1264e564ef1f60ff4e7ca597693949bd5e778248dd8ccf1d27c7e42debcfebcb`。
- Native ZIP：test-packages/gmail-readonly-1.7.0-native.zip；SHA-256 `38e5378f1bbf70cbd452acd0e22c0a90d2df41c79e667d3814b56899ab954be2`。
- 源码、Native、Hub及最终实际安装的12个载荷文件摘要完全一致；官方 Agentic Hub CLI 0.0.1 在干净 staging validate/pack；三份 JS preflight 均4文件、零已知特征。不能用通用仓库 CI 代替本连接器检查。
- 原1.5.1、PR #93与旧用户验收仍属历史；34份历史文件和4份旧ZIP逐字节保留，不把历史验收移用到1.7.0。

## 环境与安装授权

原版 `/Applications/WorkSwarm.app` 0.2.8，macOS、宿主 Node 22.12.0/npm。独立 HOME/data/工作区/会话；首次无 Gmail CLI、Node依赖、客户端配置或授权会话。使用本地 Hub 目录夹具调用原版卡片安装器，不是正式 Hub 下载安装证明。模型通过原宿主已有账户配置正常连接，不复制或打印凭据值。

冷安装自动下载锁定的 google-auth-library 11.3.4及23个npm包；不需要 Python、手动pip或额外CLI二进制。通过卡片本机页面的系统文件选择器导入已授权使用的自建 Desktop OAuth JSON，再由用户亲自在 Google 页面核对并同意 gmail.readonly、gmail.compose。实际 getProfile 确认账号 openjiuwen.official@gmail.com，未增加身份或modify权限。自建测试项目仍会有未验证提示，本包不绕过Google审核。

发现问题后用标准界面卸载、重装最终精确包：旧会话与技能清除，固定依赖和客户端配置按设计保留；用户重新授权，12文件匹配后新建最终聊天 `web_1a2066f754e_23ab7f0da338`。因此最终一轮是同一隔离 profile 的正常重装，未冒称第三次完整冷依赖安装；依赖准备代码与已冷装代码相同。

## 实际聊天业务

全部通过实际 WorkSwarm 聊天和安装技能，非外部 API 调用冒充聊天。先核对实际账号和 WORKSWARM_GMAIL_SELF_ONLY=1。所有真实写入的唯一To均为当前账号，Cc/Bcc空；只访问专用虚构测试主题。

| 操作 | 实际结果 |
| --- | --- |
| 空草稿列表与空邮件搜索 | 精确D1主题均成功返回零条、无更多页 |
| 创建及独立读取草稿 | draft `r-845649259567416069`，message `1a2067101db19802`；完整中文正文一致 |
| 编辑及独立读取草稿 | 同一draft，内部message变为 `1a20672204913530`；完整正文变更、收件人保持 |
| 发送草稿一次 | message `1a20673315216dc4`，thread `1a2067101db19802`；发送前重新读最新版本；发送后独立列表确认草稿消失 |
| 搜索、读邮件、读会话 | 搜索命中实际发送ID；正文与编辑结果完全一致、未截断；读到真实From/To |
| 原会话回复一次及独立回读 | reply `1a2067502e342a25`，thread不变；真实In-Reply-To/References与原邮件实际Message-ID一致；会话两封正文完整 |
| 普通send一次及独立回读 | message `1a2067829c8f6ad5`；精确D2查重后发送，主题/中文正文/From/To一致且未截断 |

最终包独立聊天涵盖10项业务操作，每种写操作各一次，所有业务命令成功。完整真实调用结果、参数及顺序见 `test-evidence/20261123-stock-1.7.0/chat-business-proof.json`，不依赖聊天总结文字判断成功。参数从专用测试文件采集；这些文件不是历史快照，写入参数使用不同文件保留未改。发送前原草稿原文与写入回执明确空Cc/Bcc；发送后的Gmail回读未出现cc/bcc头，不把头缺失单独当作服务端空数组证据。

本轮最终包发出3封自收邮件（草稿发出、回复、普通send）。此前候选另发出2封自收邮件，共5封，均只给团队邮箱自己，没有重新发送同一请求。没有删除测试邮件。Google可改写Date和RFC Message-ID；回执的rfc822_message_id是提交时头，真正回复关联由独立读取的服务端实际头验证。没有声称提交头一定原样保留。

## 自动与生命周期验证

23项Node回归通过、0失败：scope/OAuth参数、路由白名单、注入/Unicode/MIME/截断、HTML不加载与附件保留、异常/签名/加密MIME拒绝、账号/收件人/草稿版本守卫、重复请求一次提交与未知结果不重试、会话引用、私有存储及空草稿投影回归。

独立负向 profile：缺会话返回AUTH_REQUIRED；未开放路由SCOPE_REJECTED；合成无效客户端/刷新令牌对真实Google token endpoint返回AUTH_REQUIRED；受控fetch失败返回脱敏SERVICE_FAILED、受控204空响应返回INVALID_RESPONSE（二者未访问Gmail）。错误state拒绝且不结束正常入口，匹配state的合成access_denied回调退出AUTH_DENIED并关闭端口；实际强杀该脚本创建的父进程后worker退出、回调关闭、无授权保存。这些是受控回调，未声称在真实Google页面点拒绝。

最终标准mcp.disconnect返回成功，CLI随后AUTH_REQUIRED/connected=false，本包凭据及安装技能消失。再次从卡片点连接，回调确实监听；点击“取消连接”后端口关闭、没有新凭据，隔离宿主下无Gmail CLI/worker残留。详见 `test-evidence/20261123-stock-1.7.0/final-card-lifecycle.json`；不撤销Google账号远端授权，不影响其他连接器。本轮临时页面已关闭；在逐个核对命令、工作目录和独立进程组后，4个隔离QA后台服务均通过SIGTERM退出，详见owned-host-teardown.json。

## 修复中发现并处理的问题

第一候选真实卡片授权成功，但刷新后聊天未启用连接器；正常界面启用后模型猜错技能路径。更新技能为卡片同一套ID/版本校验的定位命令，再从全新profile重测。第二候选通过主要业务后，空草稿列表只选列表/页字段，实际传输诊断收到HTTP204；CLI误报SERVICE_FAILED。保留官方resultSizeEstimate字段后相同精确查询返回HTTP200/零草稿，增加空body显式错误与回归后重装最终包，最终聊天的发送前/后空列表均通过。不推断所有Google环境都恒定返回204。

第二候选一次模型请求在本地写参数后长时间无响应；最终候选普通send明确成功后，模型又在下一次API调用前停滞。两次均正常停止并另发按真实ID只读回读的短提示恢复，没有重复写入。模型偶发把非JSON字符附在参数文件末尾，已在CLI调用前自行修正。最终业务所有CLI命令成功，但长轮次模型停滞仍是实际体验限制，不能把这份验收描述为全程无人干预的一条长任务。

## 证据、许可与边界

9张最终包原始JPEG已保存于 `test-evidence/20261123-stock-1.7.0/screenshots/`，未裁剪/重压缩；index记录版本/哈希/尺寸，部分原图含团队邮箱、真实测试ID和正文。2026-11-23用户已明确批准这9张原图公开用于本次PR，具体原话与精确哈希见USER_TEST_CONFIRMATION.md和证据目录的user-test-confirmation.json。最终原图可复核授权、卡片、空查询、编辑、发信/会话、回复、普通send及断开/取消。

Google认证库未修改；完整Apache LICENSE与安装原件摘要匹配，包不含node_modules。团队自写Gmail REST/MIME与CLI框架的具体复用范围见SOURCE_REVIEW.md。Google许可/品牌/审核和账号政策另行适用。

未测：Windows/Linux、远程服务器回调、正式Hub下载安装与平台审核、自然令牌到期/真实远端撤销恢复、真实Google点拒绝、复杂附件/签名/加密邮件的在线编辑（仅单元验证相关分支）。草稿版本检查是读后检查，服务端没有原子compare-and-swap；多端并发修改仍需用户协调。保留自建Desktop JSON准备与本机导入要求，不声称本版是共享生产OAuth或免JSON服务版。
