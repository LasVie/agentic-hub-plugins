# Miro 白板连接器 1.1.0 测试记录

2026-11-23，Song Haoran，CAND-CLD-003，AH-20261117-miro-connector，repo:agent-mcp:miro。Song Haoran 已明确确认本版测试通过并批准五张原图公开提交 PR，当前 Submitting。仅修改 Agentic Hub 包，未修改 WorkSwarm 源码或 app bundle；提交范围限 GitHub PR，未发布 Hub。

## 最终交付物与环境

| 文件 | SHA-256 |
| --- | --- |
| `test-packages/miro-1.1.0-native.zip` | `ac5cdae05a24b024ede223feb1907075f89f2c71e129add9a9445acd8064d80b` |
| `release/1.1.0/miro-1.1.0-agent-mcp.zip` | `fedd4957b91f38040de50775dd5641b682b448ecc00f887ad3a64a8cd5dc420e` |

原版 WorkSwarm 0.2.8 内置后端/WebUI、macOS、本地隔离数据目录和本地 Hub 目录夹具；模型 gpt-6.1-sol，聊天启用 miro 技能。最终 ZIP 从卡片重装，11 个安装文件逐一与源文件、原生 ZIP、Hub ZIP 一致。宿主 Node 22.12.0/npm 自动准备固定 mcp-remote 0.16.6，无手动 CLI 安装、JSON 导入或令牌粘贴。本地目录夹具不等于正式 Hub 下载实测。

## 授权与聊天

授权初稿由用户亲自在 openJiuwen 组织/团队官方同意页 Add again、完成回跳。依据真实 schema 完成适配后，最终包重装，在同团队、同范围下重新授权成功，卡片显示「使用」，技能挂载成功。未借用旧版缓存。客户端只请求 `boards:read boards:write`，未申请公开支持的 openid/email；官方同意页仍列出当前用户资料读取，用户已核对同意。47 个服务端工具中，本包仅使用 4 个内部接口，开放 3 个受限本地操作。安装卡片原图证明包已出现在广场，不能仅凭该图证明「使用」按钮；连接状态另有实际界面观察和宿主结果核对。

唯一目标为已有测试白板 [My First Board](https://miro.com/app/board/uXjVENX_jBk=/)。真实聊天完成：

1. 按名称搜索返回 1 项，`has_more=false`。读取明确矩形 `0,0,3840,2160` 返回 2 条旧便签、`skipped_count=0`；另按旧 ID `3458764690692182654` 独立回读中文全文。矩形读取不等于全板遍历。
2. 目标区域为空后，仅调用 `createStickyNote` 一次，在 `x=1200,y=100` 新建 350×228 黄色便签。上游 `created_count=1`，新 ID `3458764691249643739`。
3. 首次回读前，模型给本地 JSON 追加了多余字符，并读取单行文件时误用偏移，按指令停止；该次没有发出新控件的读取调用。后续仅修正另一个本地 JSON 文件、禁止再创建，按新 ID 独立调用读取成功。没有包修改或重复创建。
4. 独立回读 `item_count=1`、`skipped_count=0`；白板、ID、位置和全文完全一致：`WorkSwarm 中文便签验收 WSQA-MIRO-20261123-NODE-C1`。标记出现一次，原生 Miro 界面的中文显示也已核对并截图。

本轮累计创建 **1 条**，未更新/删除旧内容。保留[测试便签](https://miro.com/app/board/uXjVENX_jBk=/?moveToWidget=3458764691249643739)供复核。安全精简证据见 `tests/fixtures/miro-stock-acceptance-20261123.json`，未打包远端技能/风格提示词或凭据。

## 异常与生命周期

| 检查 | 实际结果 |
| --- | --- |
| 无凭据 status | AUTH_REQUIRED、connected=false，不自动授权 |
| 非开放操作 | SCOPE_REJECTED，不执行远端工具 |
| 已授权白板不存在的控件 ID 1 | READ_UNVERIFIED；不等于无权白板实测 |
| 官方页 Deny | AUTH_DENIED，回调和本机引导端口关闭 |
| 授权等待时强制结束父进程 | worker 退出，回调和引导关闭 |
| 宿主标准断开 | mcp.disconnect 返回 applied=true，CLI 再检查 AUTH_REQUIRED，挂载技能移除 |
| 卡片连接后取消 | 回调 43433 已监听后点「取消连接」，卡片恢复「连接」，回调关闭 |

测试环境最终保持断开。本地退出不声称撤销 Miro 服务端授权。

## 检查、原图与边界

14 项 Node 检查通过：精确授权范围/地址、受限操作与参数、读取边界、未知必填 schema 拒绝、中文/XML/富文本转义、读取缺失、非空区域阻止写入、单次创建及同标记只读重试、未知写入禁止重试、有界子进程和引导关闭。

官方 CLI 干净 staging validate/pack 成功；两份最终 ZIP 精确验包均为 4 个 JS 文件、0 个已知签名。11 个载荷文件一致，最大压缩比 1.0/13.7428，历史 10 份 ZIP 字节不变。MIT 全文、改编注释、第三方声明及原样图标已检查。普通仓库 CI 不替代功能验证。

五张拟公开原图为最终团队同意页、最终安装卡片、聊天读取、独立回读、原生便签，未经修改，摘要见 `tests/fixtures/miro-screenshot-manifest-20261123.json`；Song Haoran 已批准公开，原图与确认记录位于 `test-evidence/20261123-stock-1.1.0/`。另保存官方拒绝和卡片取消原图。

Windows/Linux、自然过期/远端撤销后的恢复、远程回调、正式 Hub 安装、无权白板、其他控件类型及套餐限额耗尽未实测。SDK 刷新能力不等于自然过期实测通过。仅开放搜索白板、范围读取、新建一条文本便签；不提供已有内容编辑/删除、任意 SVG、评论或权限管理。后续新客户端授权可能替代同账号旧 MCP 连接。历史 1.0.x 源码/ZIP 保留，不将旧版结果当作本版通过。

## 用户确认

2026-11-23，Song Haoran 在当前对话回复 `call_e556f38ae531484f9f1924853eb22707`：「确认通过并附五张原图提交 PR」。该确认覆盖上列原生/Hub ZIP 与已列明未测边界；允许推送、公开五张原图和创建 PR，不包含自动合并或 Hub 发布。追踪报告 RPT-20261123-miro-runtime-repair。
