# Google 日历连接器 1.1.0 实测记录

2026-11-23，Task **AH-20261116-google-calendar**，Song Haoran。原 1.0.0 的 PR #98、测试确认、Completed/Accepted 和 Hub 拒审记录均保留；本次候选仍在本地 Build，尚未取得 1.1.0 用户完成确认，也未提交 Calendar 新 PR。

## 结果

本机正式安装的 WorkSwarm **0.2.8**（Info.plist 实查）、Apple silicon macOS、随应用 Node **22.12.0**。独立配置 `/private/tmp/workswarm-calendar-1.1.0-20261123`，未修改 WorkSwarm 源码或应用包。使用本地 Hub 兼容目录让原生广场下载安装精确的包装 ZIP，**不是正式 Hub 安装/审核证明**。安装的 12 个文件与本次原生 ZIP 和包装 ZIP 完全一致。

- 最终源代码在另一全新目录、系统 PATH 下成功自动下载锁定 npm 依赖及 gws 原生发行版；无需系统 Python。官方 Agentic Hub CLI 0.0.1 validate/pack 通过；载荷及两种精确 ZIP 都扫描 3 个 JS 文件，动态执行签名为 0。7 项 Node 参数、范围、OAuth 选项及超时/错误脱敏测试通过。
- 从卡片安装/连接，复用已有自建 Desktop OAuth 客户端配置，不复用任何旧连接器令牌。Google 页面显示 WorkSwarm Google Demo 与团队测试账号已有同一项「自有日历中的日程」权限。最终候选重新完成正常浏览器回跳；请求只含 `calendar.events.owned`、PKCE S256、随机 state 和 `include_granted_scopes=false`。未增加身份或其他 Google 服务权限。
- 卡片显示「使用」。独立 status 真实查询主日历成功，stock mcp.show 返回 connected / cli。工具清单为空是此 CLI + 技能形态的正常结果，不是声称挂载了远端 MCP 工具。
- 使用实际配置的 **gpt-6.1-sol / OpenAIAccount** 进行中文聊天，不使用确定性测试模型。最终轮耗时界面显示 **1m22s**，11 个宿主工具事件。模型成功通过 skill_tool 读取 `google-calendar`；最初猜错脚本目录发生一次 MODULE_NOT_FOUND，随后 glob 定位宿主管理的技能副本并恢复。成功的业务调用为 status、list、create、read 各一次；不能将恢复前的失败隐藏为全程无错误。
- 主日历按完整标题及北京时间 2026-11-24 00:00—11-25 00:00 查重，返回 0 条且无 nextPageToken。只创建一条 **WorkSwarm 日历卡片验收 WS-CALENDAR-110-20261123**，开始 2026-11-24 20:00、结束 20:15，UTC+08:00，描述为虚构测试说明。
- 创建返回 ID **552d2f6e1483d78ad5fa9964cdf10f08** 后，聊天另写读取参数文件并独立执行 read。ID、完整标题、描述、起止时间和 confirmed 均一致；private、transparent、useDefault=false、无参会者，无通知。Google 返回时区名称 Asia/Singapore，偏移 +08:00 与本次北京时间要求相同。未更新或删除已有日程；该测试日程保留以供核对。

## 失败与生命周期

- 缺少凭据：中文提示从卡片连接；故意虚构的 refresh token 对真实 Google token 端点失败后返回 AUTH_REQUIRED。这不是自然过期测试。受控不可用 HTTPS 代理返回 SERVICE_FAILED，这不是 Google 服务真实故障。
- 受控本机回调测试验证错误 state 被拒且流程继续，匹配 state 的 access_denied 正确退出，SIGTERM 取消与拒绝后回调端口均关闭。此受控测试不冒充 Google 真正的拒绝页。
- 最终精确包另从真实 Google 权限页点击 **Cancel**。本机页显示「Google 授权未完成，请返回 WorkSwarm 重新连接」，未写新会话，回调端口关闭。**WorkSwarm 0.2.8 的授权弹窗仍显示等待，需要点「取消连接」才恢复卡片「连接」；本包不宣称宿主会自动关闭失败弹窗。**这是已验证的宿主交互限制，不修改宿主源码。
- stock mcp.disconnect 返回 applied=true；mcp.show 为 disconnected，账号凭据文件不存在，宿主技能副本撤下，卡片可重新连接。只读检查本测试进程树，最终无 Node/gws 子进程存活；没有残留回调监听。断开只清本地会话，未撤销同一 Google 客户端上其他连接器的远端授权。

## 修正记录及限制

首轮 gws authorized_user 文件取得令牌失败（401 / Failed to get token），同一会话经官方 Node 库刷新及 gws 直接短期 token 查询都成功。因此最终版由 Google 官方 Node 库管理授权/刷新，仅通过子进程环境变量把短期 token 交给 gws，不写命令参数或日志。gws 内部失败的更深层原因未被错误信息证明，不认定为用户令牌过期。第一、二轮候选仅保存在本地操作记录，未交付；最终包以后面的哈希为准。

Windows、Linux、组织管理员策略、真正多页数据、自然过期、浏览器与服务器不同机、正式 Hub 上架及人工审核仍未验证。gws 为 googleworkspace 仓库维护的 CLI，项目明确它不是 Google 正式支持的产品。初次下载仍受 npm/GitHub 网络及系统解压工具影响；原生安装器 fetch 不自动读取 HTTP_PROXY。

## 精确包与证据

- 原生 ZIP `test-packages/google-calendar-1.1.0-native.zip`：`1951aa274ddc89da2eab20b62d9d3c7c39060c75d55cb13598a7fe2414fb93ba`。
- Hub ZIP `release/1.1.0/google-calendar-1.1.0-agent-mcp.zip`：`53ba2d3dc8cda301213c7d699a9ebe04e6ad1a536d6bde04febb18cb2d7f445a`。
- 原图与真实调用记录：`test-evidence/20261123-card-1.1.0/`。截图未经裁剪或重新压缩；原生长图导出未产生可取得的下载，交付证据使用实际界面原图，不伪造导出文件。没有 Asana 令牌页、OAuth code/token/secret 或真实业务内容进入证据。
- 用户 1.1.0 测试完成确认待收集。当前确认仅覆盖 Asana 1.1.0，不移用历史 Calendar 1.0.0 的确认。
