# Gmail 邮件连接器

标识 `gmail-readonly`，版本 **1.5.1**。用你自己的 Google Cloud 项目授权后，可以在 WorkSwarm 聊天中搜索和读取邮件与会话、编辑草稿、发送和回复。

## 在 Google Cloud 创建自己的 OAuth 客户端

1. 在 [Google Cloud Console](https://console.cloud.google.com/) 新建或选择自己管理的项目，启用 [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)。在 Google Auth Platform 配置应用信息、用户类型和数据访问权限。
2. 个人 Gmail 用户可以选择 External / Testing，并把要连接的 Gmail 地址加到 Test users。Google 会显示测试应用提示，Gmail 授权通常在 7 天后过期，届时从 WorkSwarm 重新连接。Google Workspace 账号还受组织管理员的应用访问策略限制。[Google 项目与测试用户说明](https://support.google.com/cloud/answer/15549945)
3. 在 Clients 中创建 **Desktop app** 类型的 OAuth 客户端，下载 JSON。保存在本机，导入时只使用文件路径。 [Google Desktop OAuth 配置指南](https://developers.google.com/workspace/gmail/api/quickstart/python)

| Google 权限 | 用途 |
| --- | --- |
| `https://www.googleapis.com/auth/gmail.readonly` | 搜索和读取邮件、会话及草稿 |
| `https://www.googleapis.com/auth/gmail.compose` | 编辑草稿、发送新邮件或草稿、在原会话回复 |

## 在 macOS WorkSwarm 0.2.8 安装和连接

1. 确认电脑已安装 Python 3.11 或 3.12，能够访问 Google、PyPI 和 Agentic Hub。在「扩展 → 连接器广场」安装 Gmail。安装过程中会准备独立运行环境。首次弹出缺少 Desktop OAuth 配置的提示后，先关闭提示。
2. 打开 Mac 的终端，运行以下命令，把 JSON 路径改成你下载的文件路径。使用自定义 WorkSwarm 数据目录时，把下方默认路径中的 `~/.jiuwenswarm` 换成实际数据目录。

   ```bash
   python3 -B "$HOME/.jiuwenswarm/agent/workspace/mcp/mcp_hub/gmail-readonly/launcher.py" configure --client-file "/本机路径/credentials.json"
   ```

3. 回到 Gmail 卡片点「连接」，选择已添加的 Gmail 账号，核对权限后同意。浏览器需能访问同一台电脑上的 `127.0.0.1` 本机回调。看到卡片变成「使用」后，即可在聊天里操作 Gmail。账号到期或需要更换配置时，先在卡片断开连接。连接器将凭据保存在本机 `~/.local/share/agentic-hub/gmail-readonly/`，也可在 Google 账号设置中撤销授权。

### 独立 CLI

若需要直接在终端使用 CLI，可将原生 ZIP 解压到固定目录并运行 `python3 "/实际解压目录/launcher.py" prepare --bin-dir "$HOME/.local/bin"`，再用 `gmail-readonly configure --client-file "/本机路径/credentials.json"` 导入配置。Windows 使用 `py -3.12` 和已在 PATH 上的目录，入口为 `gmail-readonly.cmd`。共享服务器、远程浏览器或多用户环境须另行验证回调与凭据隔离。

## 用法

| 命令 | 用途 |
| --- | --- |
| `gmail-readonly search --query 'subject:测试邮件' --max-results 5` | 搜索并返回邮件与会话标识 |
| `gmail-readonly read-message --message-id '实际邮件标识'` | 读取一封邮件 |
| `gmail-readonly read-thread --thread-id '实际会话标识'` | 读取一个会话 |
| `gmail-readonly list-drafts --max-results 5` | 获取草稿标识 |
| `gmail-readonly read-draft --draft-id '实际草稿标识'` | 查看草稿正文和收件人 |
| `gmail-readonly edit-draft --draft-id '实际草稿标识' --subject '新主题' --body '新正文'` | 更新现有草稿。可用一个或多个 `--to` 替换收件人 |
| `gmail-readonly send --to '收件人邮箱' --subject '主题' --body '正文'` | 发送新邮件 |
| `gmail-readonly send-draft --draft-id '实际草稿标识'` | 按草稿已有收件人发送 |
| `gmail-readonly reply --message-id '实际邮件标识' --body '回复正文'` | 在原会话中回复该邮件 |

编辑草稿仅修改传入的字段，保留其他邮件头和附件。更改主题后，由 Gmail 判断草稿所属会话。编辑正文使用纯文本，原有 HTML 正文会按新文本重新生成，复杂草稿的原有版式可能变化。发送和回复使用纯文本。回复使用原邮件的 Reply-To 或发件人，沿用原主题。若操作结果无法确认，先在 Gmail 检查草稿箱或已发送邮件，再决定是否重试。

实际验证范围见测试报告。共享服务器部署需要独立的回调和凭据隔离。
