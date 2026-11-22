# Linear 1.2.1 来源与复用审查

负责人 Song Haoran；原任务 AH-20261117-linear-connector。中文名称 Linear 连接器，slug linear。1.2.1 已经 Song Haoran 在当前对话确认测试通过，准备交付 PR。历史制品与试验资料在原维护工作区保持不变，本次只交付当前版本。

## 新增价值与范围

保留 Linear 工作区内的团队／Issue 查询、Issue 新建和 Issue 评论追加及回读。公开目录 864 项（连接器 54 项）的相关 Todoist、TAPD、GitHub、Sentry 使用不同服务账号和对象，未发现完整 Linear 替代；不将相似任务管理功能直接认作同一连接能力。比对摘要见 test-evidence/20261122-cli-1.2.1/catalog-overlap.json。

## 来源和许可证

- Linear 官方托管 MCP：https://linear.app/docs/mcp ，端点 https://mcp.linear.app/mcp 。只使用公开服务和 OAuth 发现能力，不复制服务端实现。账号权限与服务条款仍适用。
- mcp-remote 0.16.6：https://github.com/punkpeye/mcp-remote ，来源 commit e4dc3713b0d6a727cbeb21f38324d20a6692dc5f，MIT。完整原许可证已随包放在 licenses/mcp-remote/LICENSE。实现由 npm 固定版本下载，未随包复制。
- 本版调用固定模块 dist/chunk-MKB2ICYW.js 的导出接口；SHA-256 为 8e4e647f0b25dc52a28a6d1cbbb6727851ae0e5ae74a6f2ea23cb4acb7b47638。采用 Client、NodeOAuthClientProvider、发现、连接和协调接口，不自行读取令牌／客户端／PKCE 文件。内部接口不构成上游稳定兼容承诺，升级须复核。
- 官方 Linear 标志来源 https://static.linear.app/design-assets/Linear-Brand-Assets.zip?v=3 ，原图 logo-dark.png SHA-256 1fb31df139bb786a3c5662bc53b3f82bd6804629fd7ea6002ec603bb6eafb113。沿用已核查 https://linear.app/brand 的紧凑服务标识使用范围，原图未修改，不表示合作或背书。
- WorkSwarm v0.2.8 公共源码 commit 068f148b59e140a179e31c9fe58eed8ea1700c1e 只用于核对安装、CLI 命令和宿主生命周期。未复制宿主源码、修改本机应用或修改宿主安全规则。

## 独立编写内容

Node CLI 的固定版本准备、短时操作监督、工具白名单、参数文件读取、中文技能、说明和测试由本项目编写。OAuth 与 MCP 客户端由第三方 MIT 库承担；相关原许可证和版权文字保持原样。授权仍申请 Linear 原有 read/write，操作白名单不改变账号 grant。

本机状态检查、授权、聊天写入和断开结果以同版本 TEST_REPORT.md 为准；许可核查与打包不能证明业务接入成功或平台人工审核通过。
