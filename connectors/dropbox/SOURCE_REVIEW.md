# Dropbox 文件连接器 1.1.0 来源审查

2026-11-23，Song Haoran。CAND-CLD-001，AH-20261117-dropbox-connector，repo:agent-mcp:dropbox。Dropbox → Dropbox 文件连接器 → dropbox。仅改 Agentic Hub 包，目标原版 WorkSwarm 0.2.8。

复制与适配前审查：旧 Python 实现及历史测试属于本项目原有独立实现；保留到 history/1.0.3，八份历史 ZIP 字节不变。新 Node CLI 按公开 Dropbox Files API v2/OAuth 规范及用户需求实现，只用 Node 内置模块，无 npm 运行依赖、第三方 CLI 或 SDK。借鉴团队已验收的有限进程、本机引导和安装定位方案，不复制 Miro/Atlassian/Claude 插件代码、提示词或 OAuth SDK 适配。Candidate 的 Native Implementation Only 保持；不从上游目录的 Apache 声明推断完整复用许可。

官方 Dash MCP 面向 Dash 搜索与文档读取，DCR 客户端名单和其他客户端的应用授权另有要求，未证明等价替换原 Files API；本次保留文件名搜索、非递归目录列表、元数据和限长 UTF-8 下载。权限仅 account_info.read、files.metadata.read、files.content.read，不添加 Dash、写入、删除、共享、团队或 OpenID 权限。

已在团队原 openJiuwen 测试应用核对 http://localhost:53682/oauth/callback 已保存、Allow public clients 已开启、三项只读权限启用，其他写入/共享权限未启用。应用处于 Development / Only you；只能据此验证创建者账号，不能宣称任意 Hub 用户可连接此开发应用。连接页允许用户填写自己或团队维护的公开 App key，避免手工写文件；不要求客户端密钥，不把团队测试 App key 默认分发给所有用户。普通用户使用范围由其应用的 Dropbox 发布/用户限制决定。

原样保留官方 icon.png，SHA-256 77dc1afb3d82c5fcbde086580a7648e216cda8760629dad3f8079e62f25f24c8，原 DBX_Tab_128.png，来源为下列官方品牌材料。仅在安装的 WorkSwarm 卡片识别 Dropbox 服务，外层 Hub wrapper 不添加商标。保留独立品牌声明，不重许可为项目代码许可证，不表示 Dropbox 背书。

来源：
- https://docs.dropboxapi.com/dropbox-api/docs/oauth
- https://www.dropbox.com/developers/documentation/http/documentation
- https://help.dropbox.com/integrations/set-up-MCP-server
- https://docs.dropboxapi.com/dropbox-api/docs/developer-resources/branding-guide
- https://brand.dropbox.com/logo
- 原素材 https://www.dropbox.com/scl/fo/6qjduc7j5ujf09f75w1p7/AGATVvVEZHoOrsYEKaNctAI/Logos/Dropbox/Tab/DBX_Tab_128.png?rlkey=tkqw8jcoi7f24voc6577vakky&dl=0

最终包在原版 WorkSwarm 0.2.8 的 macOS 本地目录夹具中完成卡片安装/同范围授权、新聊天的目录/搜索/按 ID 元数据与完整文本读取。下载按真实无 .tag 的 FileMetadata 格式解析，保留修订/长度/内容哈希核验；17 项 Node 检查、官方 CLI 校验打包和两份最终 ZIP 验包通过。详见 TEST_REPORT.md。最终原生 SHA-256 d757e274494432b7c014a2ea24f3cb13d6739011d399433958ec02cf725a4bbe；Hub SHA-256 194a3cad40d4aadf9a5553b65f6074ae6e2748583a7091d8e31d8596c1a52c3e。Song Haoran 已确认最终包通过并批准五张原图公开提交 PR，当前 Submitting；不含自动合并或 Hub 发布。
