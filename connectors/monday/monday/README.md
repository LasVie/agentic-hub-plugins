# monday.com 连接器

在 WorkSwarm 聊天里列出指定看板的条目、按 ID 读取条目，或在用户确认的看板新建一条标题并回读。

## 安装与连接

1. 安装连接器，打开 monday.com 卡片并点「连接」。
2. 在 monday.com 的头像菜单打开 Developers，进入 API token 页，复制个人 API 令牌。只把令牌填进 WorkSwarm 卡片的「个人访问令牌」输入框，再点「保存并连接」。令牌沿用该用户在 monday.com 的账号权限。
3. 点击卡片「使用」，在聊天里说「列出 monday.com 看板 123456 的条目」或「读取看板 123456 上条目 654321 的标题和列文本」。新建时给出目标看板 ID 和标题，要求随后用返回的 ID 回读。

宿主需要可启动 Node.js 22.12 或以上版本，并能通过 HTTPS 访问 `api.monday.com`。连接器使用 Node 标准功能，运行时无需安装 npm 依赖。API 调用计入 monday.com 账户额度。看板地址中 `/boards/` 后的数字是看板 ID。

工具支持分页列出、读取和新建标题。新建结果不确定时，先在原看板搜索同名条目并核对。预期的列表和读取权限由当前账号决定，新建还需要目标看板的编辑权限。

[monday.com 令牌指南](https://developer.monday.com/api-reference/docs/authentication) · [条目 API](https://developer.monday.com/api-reference/reference/items)
