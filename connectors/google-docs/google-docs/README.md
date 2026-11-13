# Google 文档连接器

读取指定标签页、新建文档、追加或替换指定标签页的正文。

## 配置并连接

1. 在自己的 Google Cloud 项目启用 `docs.googleapis.com`，在 Google Auth Platform 的 Data Access 登记 `https://www.googleapis.com/auth/documents`。同一项目可启用多项 Workspace API。个人账号可选 External / Testing 并把自己加到 Test users。该模式的授权 7 天后需要重连。组织账号还受管理员访问策略限制。
2. 创建 Desktop app 客户端，下载 JSON 到本机。若创建界面提供「Use this client for an AI-powered agent」，为本连接器创建专用客户端时可以勾选。
3. 在 macOS WorkSwarm 0.2.8 的「扩展 → 连接器广场」安装。需要本机 Python 3.11 或 3.12，并能访问 Google 和 PyPI。安装时会准备 CLI 依赖。打开终端导入一次配置，替换文件路径。

   ```bash
   python3 -B "${JIUWENSWARM_DATA_DIR:-$HOME/.jiuwenswarm}/agent/workspace/mcp/mcp_hub/google-docs/launcher.py" configure --client-file "/实际路径/credentials.json"
   ```

4. 回到卡片点「连接」，用浏览器选择账号并同意。浏览器需要与 WorkSwarm 运行在同一台设备，能访问 `127.0.0.1`。四张 Workspace 卡片共用本机配置，各自保存授权。更换 Google 项目之前须先断开已连接的 Workspace 卡片。单卡断开会删除本地会话，Google 账号设置可撤销整个项目的授权。

独立使用时可解压并运行 `python3 -B launcher.py prepare`，随后使用同一个启动器执行 `configure`、`login` 和业务命令。Linux、Windows 和远程服务器需要单独验证。

## 示例参数

以下各行追加在启动器命令后。传入实际文件链接或标识。

- `read --file '实际文档链接'`
- `read --file '实际文档标识' --tab '实际标签页标识'`
- `create --title '项目纪要'`
- `append --file '实际文档标识' --tab '实际标签页标识' --revision '刚读取的版本' --text '补充本周结果'`
- `replace --file '实际文档标识' --tab '实际标签页标识' --revision '刚读取的版本' --old '旧日期' --new '新日期'`

读取会列出所有标签页，默认读取第一个标签页。修改前核对标签页和版本。替换只处理指定标签页正文中唯一匹配的一处文字，支持中文及表情。替换后的样式由 Google Docs 决定。

Google API 标准用量无需额外付费，项目仍受 Google 的配额和计费规则约束。
[桌面授权说明](https://developers.google.com/identity/protocols/oauth2/native-app) · [测试模式规则](https://support.google.com/cloud/answer/15549945) · [API 配额](https://developers.google.com/workspace/tools-safety)
