# Google 日历连接器 1.1.0 来源审查（2026-11-23）

原 Task AH-20261116-google-calendar，负责人 Song Haoran，slug/google-calendar 与中文名不变；1.0.0、PR #98、验收和拒审证据保留。历史审查在 history/1.0.0。

## 本次方案与许可

自行编写短时 Node CLI、主日历参数白名单及中文技能。gws 0.22.5 源码固定在 googleworkspace/cli 705fb0ecac6f4249679958f6325b809b63fdde17；根 LICENSE 是完整 Apache-2.0，源码标注 Copyright 2026 Google LLC。源码/发行包没有另附 NOTICE。只调用未修改的固定发行版，不拷贝其 Rust 实现或品牌图片。README 明确它并非 Google 正式支持的产品，不将其描述为 Google 产品保证。

google-auth-library 11.3.4 来自 Google 官方 googleapis/google-cloud-node 的 core/packages/google-auth-library-nodejs；npm 发行版 OAuth2Client 文件保留 Copyright 2019 Google LLC 和 Apache-2.0 标头，完整 LICENSE 已核对。使用公开 API generateAuthUrl/generateCodeVerifierAsync/getToken，传入唯一原权限 calendar.events.owned，PKCE S256 与随机 state。库不会自行追加身份权限。

完整上游许可证随包放在 licenses/{gws,google-auth-library}/LICENSE；网络安装的原始发行文件不修改。24 个精确版本依赖由 package-lock 锁定 tarball、integrity 和许可证；不把 node_modules 或原生二进制放进 Hub 包。npm ci 禁用全部安装脚本，再单独运行已审查的固定 gws install.js；其固定 GitHub release 下载及 SHA-256 校验、系统解压步骤已读。下载仍需要 npm/GitHub 网络；安装器原生 fetch 不自动使用 HTTP_PROXY，代理环境需实测，不能宣称全平台可用。

## 选择范围

官方 Calendar MCP 仍为 Developer Preview，需预览资格、单独 MCP API 和 AI-agent OAuth 客户端，文档事件写入权限 calendar.events 超出原范围。gws 自带 auth login 即使 --scopes 也追加 openid、userinfo.email/profile，故本包不调用它；由官方 Node 认证库获取原范围的 authorized_user 会话，并由该库负责刷新；只将短期 access token 通过 gws 已支持的 GOOGLE_WORKSPACE_CLI_TOKEN 环境变量传给有限子进程（不写 argv/stdout）。业务仅固定 primary 的 events list/get/insert，不开放任意 gws/API 命令。

## 已查看与实际复用

已读原团队 Python Calendar/Docs 授权代码、团队 Linear 1.2.1 的 Node 启动约定；复用团队启动定位方式，独立实现 Calendar 包，未把 Python 放进新运行载荷。历史依赖许可证在历史源码目录保存。无第三方图标、用户数据、OAuth 凭据进入包。品牌与服务权限不由 Apache-2.0 授予。

## 来源

- https://github.com/googleworkspace/cli/tree/705fb0ecac6f4249679958f6325b809b63fdde17
- https://registry.npmjs.org/@googleworkspace/cli/0.22.5
- https://registry.npmjs.org/google-auth-library/11.3.4
- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/workspace/calendar/api/guides/configure-mcp-server
- https://developers.google.com/workspace/calendar/api/v3/reference/events

以上为构建前评估；本次最终实物、真实测试及宿主限制以文末和 TEST_REPORT.md 为准。

## 首轮真实授权定位

首轮浏览器已回跳，但 gws 的 authorized_user 凭据文件路径在实际环境取得令牌失败（401 / Failed to get token）；官方 Node 库用同一会话刷新成功，gws 直接短期 token 的实际主日历查询成功。因此保留官方 Node 库管理授权及刷新，gws 只执行业务。gws 内部失败的更深层原因未被现有错误信息证明，不能归为令牌过期。该修正已在最终候选中重新构建并实测，结果见文末与 TEST_REPORT.md。

## 最终实物审查

最终原生 ZIP SHA256 1951aa274ddc89da2eab20b62d9d3c7c39060c75d55cb13598a7fe2414fb93ba；Hub ZIP SHA256 53ba2d3dc8cda301213c7d699a9ebe04e6ad1a536d6bde04febb18cb2d7f445a。12 个载荷文件与源码/安装目录逐项相同，许可证路径及哈希见 provenance.json 与 artifact.json。无 Python、依赖源码/二进制、图标、凭据或测试资料进入最终载荷。实际卡片授权、中文查询/创建/独立回读已跑通；拒绝授权的宿主弹窗需手动取消，详见 TEST_REPORT.md。当前无新权限扩张、源许可阻塞，正式 Hub 审核仍独立待验；待用户确认当前候选后才提交 PR。
