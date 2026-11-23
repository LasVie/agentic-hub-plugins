# Gmail 只读邮件连接器 v1.0.0 — 本机测试交接

任务 AH-20261110-gmail-readonly；负责人 Cai Zhenze；候选编号不适用。
当前状态：本地包、导入、真实 MCP 注册、两个授权测试账号的浏览器登录与各自最新5封邮件读取已验证。
另已获准并读取第二个账号最新邮件所在的一个会话。2026-11-11 用户明确确认原生包与标准包装包 v1.0.0 人工测试通过，并提供6张原始截图。真实拒绝同意与 Google 端撤销检查仍未测试；用户明确允许记录这一限制后进行 GitHub 交付，不能把它们写成已通过。

## 当前包与网页

- 网页：http://127.0.0.1:6411/ → 扩展 → 连接器广场，搜索 Gmail。
- 卡片：Gmail 只读邮件连接器 / gmail-readonly / v1.0.0 / 本地测试 · 未发布；无 Hub ID。
- 当前保留第二个已授权测试账号的本机凭据与 MCP 连接；第一个账号的本地令牌已移除，Google 端同意未撤销。
  每次只使用一个账号。卡片连接状态本身仍不能替代真实邮件读取核验。
- 原生包：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/test-packages/gmail-readonly-1.0.0-native.zip`
  SHA-256：`b396d4adaedcfe48c7749570d777564482d50c9f23bfdc4d56b16b34a4051f52`
- 标准包装包：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/release/1.0.0/gmail-readonly-1.0.0-agent-mcp.zip`
  SHA-256：`9fb5f0ad60109cbd3d8cafd8087475147808be711a46c5d07efeb2766f26f9a4`
- 两包内15个运行文件逐字节一致；任选一个导入。已安装时重复导入应拒绝冲突，不要覆盖。

## 最小开发者设置

1. 打开 [Google Cloud Console](https://console.cloud.google.com/)，选择自己控制的项目，启用 **Gmail API**。
2. Google Auth Platform → Branding：填写应用名称、支持邮箱、开发者联系方式。
3. Audience：个人 Gmail 使用 **External / Testing**，将准备测试的账号加入 **Test users**；组织账号可能另需管理员允许。
4. Data Access：仅加入 `https://www.googleapis.com/auth/gmail.readonly`。这是 restricted scope，但不包含发信/改信权限。
5. Clients → Create client → **Desktop app** → 下载 JSON。不要选择 Web application；不需要公网 redirect URL，也不需要手工复制访问令牌。
6. 确认使用标准低用量额度、无付费升级；若控制台要求购买/付费或审批，停止并反馈。测试应用和刷新令牌通常7天到期；生产验证、可能的安全评估与正式分发是后续独立事项。

这是开发者应用配置，不是每个终端用户的普通登录步骤。此包没有预置公共 OAuth 应用。
官方流程：[Gmail Python 设置](https://developers.google.com/workspace/gmail/api/quickstart/python)、[Desktop OAuth/PKCE](https://developers.google.com/identity/protocols/oauth2/native-app)。

## 本机配置与用户登录

本次独立 Python3.12 依赖及用户提供的 Desktop 客户端均已配置，无需重新配置或安装。
以下配置命令供以后全新安装使用；将最后的示例路径换成实际 JSON 路径：

```bash
python3 "/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/gmail-readonly/launcher.py" configure --client-file "/实际路径/Desktop客户端.json"
```

JSON 会复制到权限700的 `~/.local/share/agentic-hub/gmail-readonly/`，凭据文件权限600。
不要把客户端 JSON、令牌或目录内容发进聊天、源码、日志或截图。如需代理/非标准 CA，本版直接连接策略不适用，应先反馈，不要自行降低 TLS 校验。

本轮已经获得两个指定账号各最新5封邮件，以及第二个账号最新邮件所在一个会话的明确授权。
请把后续测试限制在这一范围；若以后换账号或扩大范围，应先明确授权，再由用户运行登录：

```bash
python3 "/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/gmail-readonly/launcher.py" login
python3 "/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/gmail-readonly/launcher.py" status
```

系统浏览器 Google 登录/只读同意 → 自动回调本机。拒绝、超时或管理员阻止时如实反馈。
`status` 只检查本地缓存，未验证提供商当前授权。

## 不调用模型的真实后端测试

网页中的模型配置保持 disabled-local-test；不要发送聊天或改模型设置。
以下命令连接正在运行的实际 WorkSwarm AgentServer，**不是独立 SDK 模拟服务**。
真实 search/read 命令只能在用户已经授权账号和该范围后执行。

```bash
gmail_test_python="/Users/IDLE_And_R/Downloads/Huawei/jiuwenswarm/local-only/connector-import/venv/bin/python"
gmail_test_probe="/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/tests/live_backend.py"
"$gmail_test_python" -B "$gmail_test_probe" tools
"$gmail_test_python" -B "$gmail_test_probe" search --authorized --newest-five
"$gmail_test_python" -B "$gmail_test_probe" read-message --authorized --id "替换为真实返回的message_id"
"$gmail_test_python" -B "$gmail_test_probe" read-thread --authorized --id "仅替换为已获额外授权的第二个账号最新邮件的thread_id"
```

预期恰好三个工具、版本1.0.0，真实结果与授权测试消息一致；空结果、截断和失败均应如实记录。
工具不会标记已读；Gmail 网页打开邮件本身可能标记已读，核对时应区分。
不要把真实邮箱结果重定向到仓库文件；只在本机查看经过授权的合成测试邮件。

1. 保留明确授权的账号别名和消息范围，独立核对有界搜索/读取结果；会话读取仅限已额外批准的第二个账号最新邮件所在的一个会话，不扩展到其他邮件或会话。
2. 网页断开后，用 `invalid-input` 探针确认 MCP_NOT_FOUND，再明确连接，验证同一范围读取。
3. 由用户操作拒绝一次同意/撤销 Google 端同意，再验证明确失败；刷新过期及重新授权结果分别记录，不能用模拟测试代替。
4. 退出本地账号后再次尝试读取，应拒绝；需再次登录时由用户操作。

```bash
python3 "/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/connectors/gmail-readonly/gmail-readonly/launcher.py" logout
```

宿主断开只终止 MCP 并禁用连接；不删除独立 OAuth 凭据。logout 删除本地会话，不在 Google 端撤销授权。
卸载前先断开；本次无须删除包或重启整个宿主。当前进程/配置恢复只做连接器级测试，避免干扰其他工作。

## 宿主基线、启停与证据

仅验证既有本地修改版：`jiuwenswarm` 分支 `local/connector-import`，HEAD
`fa91394e42a7af731424222db82b02351e694de9` 加既有未提交导入功能；本连接器未修改宿主。
相对启动参数由这一路本地导入解析。标准 Hub 安装与未经修改宿主的运行路线未验证，不能由包装校验推断通过。

本实例已运行，正常测试不需启停。仅在必要且不会干扰其他测试时，使用原有实例管理器：

```bash
cd "/Users/IDLE_And_R/Downloads/Huawei/jiuwenswarm"
local-only/connector-import/venv/bin/python -B local-only/connector-import/manage.py status
local-only/connector-import/venv/bin/python -B local-only/connector-import/manage.py stop
local-only/connector-import/venv/bin/python -B local-only/connector-import/manage.py start
```

请保留版本/来源卡片、浏览器授权完成、有界真实搜索/读取及失败恢复的原始截图，遮住账号私密内容和 OAuth/本机会话地址。
显式确认这两个确切 ZIP 的人工测试完成之前，不提交 GitHub、不创建 PR、Release 或执行 Hub 操作。

## 已完成与待人工核对

- 已完成：90项离线/协议回归；官方 CLI 包装校验；真实本地卡片及3个 MCP 工具；两个账号的 Google 浏览器登录和各5封邮件读取；获准的1个会话读取；两个账号的显式令牌刷新、实际后端断开/重连；第一个账号本地退出后拒绝读取。
- 同一邮件在刷新/重连前后的**有界正文和标签**相同，不代表对整个邮箱做了完整状态审计。
- 人工验收与6张原始截图已收到；两个确切包哈希保持不变。仍未验证真实拒绝同意、Google 端撤销、自然过期和整机服务重启。用户明确接受前两项未测试并授权 GitHub 交付；不得据此宣称这些检查通过。
