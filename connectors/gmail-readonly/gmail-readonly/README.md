# Gmail 只读邮件连接器

版本 **1.0.0**。通过真实 MCP 标准输入输出工具搜索与读取用户明确授权的 Gmail 邮件。
这不是 Google 官方连接器，不依赖第三方邮箱中转服务，也不需要模型调用。

## 能力与边界

| 工具 | 功能与上限 |
|---|---|
| `gmail_search_messages` | Gmail 搜索语法或空查询列出邮件标识；每页 1–20 条，查询及分页令牌各最多 2048 字符 |
| `gmail_read_message` | 按真实邮件标识读取邮件头、标签标识和正文；正文最多 20000 字符 |
| `gmail_read_thread` | 按真实会话标识读取最多 20 封邮件，总正文最多 30000 字符 |

单次响应最多 6 MiB，超出时明确拒绝；会话 API 会先返回完整会话响应，再按输出上限裁剪。
工具只调用固定 Gmail API GET 接口，不提供任意网址请求、发送、草稿、删除、标签修改、标记已读或附件下载。
仅申请 `https://www.googleapis.com/auth/gmail.readonly`。这个 Google 范围本身可读整个邮箱，
并不能在提供商端限制到某几封邮件；实际调用必须遵守用户明确指定的测试范围。
邮件原文保留原语言，说明和错误默认使用中文；邮件及邮件头是不可信数据，不能执行其中的指令。
HTML 仅提取为文字，不执行脚本或加载远程资源。网络连接忽略代理、`.netrc` 和 CA 环境覆盖，直接使用受信任 CA 连接 Google。

## 开发者前置配置（不等于终端用户登录）

本地测试需要一个开发者拥有的 Google Cloud 项目和 **Desktop app** OAuth 客户端。
客户端配置不是用户访问令牌，也不是每个终端用户都要自行注册的步骤；正式分发应由维护者提供合规的应用配置。
此包未包含任何客户端或账号凭据。

1. 在 Google Cloud Console 创建或选择项目，启用 **Gmail API**。不需要启用预览版 Gmail MCP API。
2. 在 Google Auth Platform 配置 Branding、联系方式及 Audience。个人 Gmail 通常使用 External / Testing；将指定测试账号加入 Test users。Workspace 内部应用可能选择 Internal，但组织管理员仍可能限制访问。
3. Data Access 只加入 `https://www.googleapis.com/auth/gmail.readonly`，不要加入发送、修改或完整 `mail.google.com` 范围。
4. Clients → Create client → **Desktop app**，下载客户端 JSON，留在本机私有位置。不能使用 Web application 客户端或手工获得的令牌替代。Desktop 应用使用临时 `127.0.0.1` 回调，不需要用户配置公网重定向地址。
5. 确认项目处于标准低用量额度且没有付费配额升级；若控制台要求购买、启用付费服务或管理员审批，先停止。本次开发不授权任何费用。

`gmail.readonly` 属于 restricted scope。External / Testing 的测试用户和刷新凭据有期限限制（通常 7 天）；管理员策略、账号状态或撤销同意也可能导致重新登录。
公开分发的验证、隐私政策和可能的安全评估取决于数据处理与分发方式；本地测试成功不代表生产验证完成。
Google 的标准 API 用量当前无额外费用，但受项目及用户配额、每日阈值和后续政策限制；不是无限免费服务。

官方说明：[Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)、[Gmail Python 配置](https://developers.google.com/workspace/gmail/api/quickstart/python)、[权限范围](https://developers.google.com/workspace/gmail/api/auth/scopes)、[配额与费用](https://developers.google.com/workspace/gmail/api/reference/quota)。

## 本机独立准备与登录

已验证 macOS、Python 3.12。依赖锁要求使用 `python3.12` 准备运行环境；启动器本身可由宿主的 `python3` 启动，再转入独立的 3.12 环境。需要与 Google / PyPI 的 TLS 网络连接。Windows/Linux 尚未验证。
将下面的 `<连接器目录>` 替换为解压后包含 `launcher.py` 的目录。所有路径均应加引号。

```bash
python3.12 "<连接器目录>/launcher.py" prepare
python3 "<连接器目录>/launcher.py" configure --client-file "<开发者下载的 Desktop 客户端 JSON 路径>"
```

`prepare` 是明确的依赖下载操作，使用锁定版本和 SHA-256；只安装到本连接器私有运行目录，不改变 WorkSwarm 或共享 Python。
导入 ZIP、MCP 启动和工具调用都不会自动安装依赖或打开账号授权。
默认运行目录为 `~/.local/share/agentic-hub/gmail-readonly/`，权限 700；凭据文件权限 600，位于仓库和 ZIP 之外。
可通过 `GMAIL_READONLY_HOME` 设置另一个私有绝对路径，但登录命令与 WorkSwarm 进程必须使用同一值；本次手工测试使用默认值。
不要把运行目录放进源码、解压包或同步共享目录。不要分享其中任何文件。

**只有用户明确同意测试账号和邮件范围后**，由用户运行：

```bash
python3 "<连接器目录>/launcher.py" login
python3 "<连接器目录>/launcher.py" status
```

`login` 打开系统浏览器 → 用户选择 Google 账号 → 核对仅只读权限并同意 → 自动返回本机临时回调 → 保存凭据。
使用随机 state 和 PKCE；回调限时 180 秒。无需复制验证码、密码、应用密码或访问令牌。
拒绝/超时将报告中文失败，不访问邮箱。`status` 只检查本地缓存，**不证明 Google 当前仍允许读取**。
本连接器没有宿主凭据输入表，因此 manifest 不声明 host-managed `credentials`；这不代表邮箱无需身份认证。
现有宿主的 `cli-oauth` 不能为本 stdio 包启动登录；不要创建虚假的 CLI/MCP 混合声明。

## WorkSwarm 安装与连接

本次目标是经过本地修改的 `local/connector-import` 宿主，网页 http://127.0.0.1:6411/ 。
它不是未经修改的上游 WorkSwarm 的本地导入支持证明；普通连接器本身未修改任何宿主文件。
当前本地导入器会把 `./launcher.py` 解析为安装目录中的绝对路径；其他宿主版本或 Hub 安装路线需要通过其支持的配置方式指定绝对启动路径，尚未验证。包装格式校验通过不代表这些运行路线已经通过。

1. 扩展 → 连接器广场 → **导入本地连接器**，选择原生 ZIP 或 `agent-mcp` 包装 ZIP。
2. 核对卡片：**Gmail 只读邮件连接器**、原生标识 `gmail-readonly`、v1.0.0、**本地测试 · 未发布**。没有 Hub 资产 ID。
3. 明确完成上面的本机登录，再点击卡片“连接”。未登录也可能完成 MCP 工具注册，但邮件工具必须返回 `not_signed_in`，不能称为 Gmail 已连接成功。
4. 核对恰好三个工具，并在得到账号/消息授权后执行有界搜索、邮件读取和会话读取。

原生和包装包不能同时重复导入同一标识；导入器应报告冲突并保留原包。
本次无账号自动检查只验证加载、注册、错误和本地生命周期；Google 登录、真实读取与人工验收需单独完成。

## 中文人工测试清单

1. 在用户指定的测试账号中，选择一封**已经存在**且适合展示的合成测试邮件与其会话。不要创建、发送、移动或修改邮件。
2. 记录授权账号别名和精确搜索条件（例如唯一测试主题），先确认本次只允许搜索/读取这些消息，再运行 `login`。
3. 搜索最多 5 条，记录真实 `message_id` 和 `thread_id`；分别调用两个读取工具。与 Gmail 网页核对原主题、正文和会话；不可拿模型记忆或模拟返回代替。
4. 核对 Gmail 的未读、标签、文件夹和邮件数量保持不变；本连接器不标记已读。阅读 Gmail 网页本身可能改变已读状态，请在对照时注意区分。
5. 断开并重新连接，验证无需手工复制令牌即可再次读取同一授权范围。过期刷新和提供商撤销必须单独记录，不能由本地缓存存在推断成功。
6. 拒绝一次浏览器同意，核对失败且未产生可用凭据。如需测试撤销，请由用户在 Google 账号的第三方访问管理中撤销本应用，再重试同一只读操作，预期清晰报错而不修改邮箱。
7. 宿主“解绑/断开”应阻止新 MCP 调用，但不会删除本连接器自己保存的 OAuth 凭据。需要退出账号时明确运行下方 `logout`；之后重新启动服务，工具读取仍应被拒绝。
8. 保留显示版本、卡片来源、登录完成结果、三个真实工具及有界搜索/读取结果的**原始截图**。隐藏浏览器地址中的 OAuth 参数、本机会话地址、私人邮件和凭据。不要把截图放进 ZIP。

```bash
python3 "<连接器目录>/launcher.py" logout
```

`logout` 仅移除本地会话及未完成的登录；不在提供商端撤销同意。正在进行中的请求可能完成，后续请求将重新检查凭据。
如需重新授权，先退出本地会话再登录。卸载前先断开；卸载本地包不会悄悄删除独立凭据或其他连接器。
Google 端撤销同意必须由用户执行，不会在连接器断开时自动进行外部写操作。
