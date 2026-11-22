# Dropbox 文件连接器 1.1.0 测试记录

2026-11-23，Song Haoran，CAND-CLD-001，AH-20261117-dropbox-connector，repo:agent-mcp:dropbox。仅修改 Agentic Hub 包，未改 WorkSwarm 源码或 app bundle。Song Haoran 已明确确认最终包通过并批准五张原图公开提交 PR，当前 Submitting。交付范围限 GitHub PR，未发布 Hub。

## 最终包与环境

| 交付物 | SHA-256 |
| --- | --- |
| `test-packages/dropbox-1.1.0-native.zip` | `d757e274494432b7c014a2ea24f3cb13d6739011d399433958ec02cf725a4bbe` |
| `release/1.1.0/dropbox-1.1.0-agent-mcp.zip` | `194a3cad40d4aadf9a5553b65f6074ae6e2748583a7091d8e31d8596c1a52c3e` |

macOS、原版 WorkSwarm **0.2.8** 的内置后端/WebUI、独立数据目录与本地 Hub 目录夹具；宿主自带 Node 22.12.0，模型 gpt-6.1-sol。最终 Hub ZIP 从卡片重装，10 个安装文件与源文件、原生 ZIP 和 Hub ZIP 逐一相同。没有手工安装 CLI、Python/npm 依赖、导入 JSON 或粘贴令牌。公开 App key 在本机连接页填写并保存；不是无需 Dropbox 应用配置的共享生产服务。本地目录夹具不能称为正式 Hub 下载。

## 卡片授权

用户亲自允许原 openJiuwen 应用并完成回跳，回复来源为当前对话 `call_b91ffe430bad4da1bac74ef01fc04c3c`。业务解析修正后重新安装最终包，同一应用/权限范围的重新连接也已完成，官方页显示「Dropbox 授权完成」，WorkSwarm 显示「使用」，正常状态调用确认 connected=true。最终连接以实际页面/宿主结果为准，不把自动化 Allow 点击超时当作点击成功。

应用控制台只读核对了精确回调 `http://localhost:53682/oauth/callback`、Public clients 和三项 scopes：`account_info.read`、`files.metadata.read`、`files.content.read`。未更改应用设置，未增加 Dash、写入/删除/共享或团队范围。现有应用为 **Development / Only you**，仅创建者可用；最终包不默认捆绑团队 App key，其他用户须填写自己或团队已向其开放的公开 App key。未宣称该测试应用可供任意用户授权。

## 最终包真实聊天

从最终卡片「使用」进入新聊天并引用 dropbox 技能。以下四个操作均实际调用且成功，无 API 错误：

1. version、tools、status 验证 1.1.0、四项只读操作及正常连接。
2. `listFolder` 非递归列 `/open Jiu we` 一页；`searchFiles` 限定该目录和完整文件名 `WorkSwarm-Dropbox-QA-20261117.txt`。各返回一个普通文件，目录、名称和文件 ID 一致，has_more=false。
3. 按搜索返回的真实 ID `id:Y8OcbOCWzmAAAAAAAAAABg` 分别调用 `getMetadata`、`readText`。ID、修订 `0166070a4a280340000000348389531`、大小 **111 字节**及服务端内容哈希一致。full_read=true、truncated=false、dropbox_content_hash_verified=true。
4. 真实读取的正文及末尾换行完整保留：

```text
WorkSwarm Dropbox QA 2026-11-17
这是一条纯虚构的中文文本，用于验证 Dropbox 搜索和读取。
```

SHA-256：`56f42e73df70566fc1175b2a5996aceaa06af0e317a2325871a0de62ce6a4a3e`。Dropbox content_hash：`b7d673b3c92654d38a9b7cc07c23d8623c58a69f951cbc4acee287dd960058f6`。两者用途不同，未相互冒充。

原生 Dropbox 预览独立显示相同两行文本。按该可见文本重建的本地 UTF-8 对照夹具（含末尾换行）为 111 字节，并与服务端 content_hash 和聊天实际字节哈希吻合。浏览器下载事件等待超时，未获得可核验的下载文件；**不声称浏览器下载成功或找到了最初上传源**。本轮未进行任何 Dropbox 文件写入。结构化证据见 `tests/fixtures/dropbox-stock-acceptance-20261123.json`。

## 发现并修正的问题

- 初稿本机表单使用 no-referrer，浏览器表单 POST 的 Origin 为 null，严格校验拒绝了它。改用 same-origin，保留精确 Origin 检查，表单导航只允许本机和固定 Dropbox 官方域名；实际浏览器跳转已成功。[说明](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referrer-Policy)
- 早期聊天用 offset=1 回读单行 JSON 后停下；技能已明确默认偏移/offset=0，最终新聊天没有此问题。
- 初稿把 get_metadata 的 union 标签要求用于 Download FileMetadata，错误拒绝无 .tag 的真实下载头。按[官方下载格式](https://docs.dropboxapi.com/dropbox-api/api-reference/user-endpoints/files/download)修正并加入真实响应形态回归检查；ID/修订/长度/内容哈希核验均保留。

两份失败候选 ZIP 和安装记录已本地归档，不能用它们的哈希宣称最终包通过。旧 1.0.2 功能/1.0.3 图标证据在 history/1.0.3 保留，历史八份 ZIP 字节不变。

## 异常、取消及断开

| 检查 | 实际结果 |
| --- | --- |
| 无凭据的最终安装 CLI | AUTH_REQUIRED、connected=false，不自行授权 |
| upload 等未开放操作 | SCOPE_REJECTED，未调用业务写接口 |
| 官方同意页 Cancel | AUTH_DENIED，回调端口关闭 |
| 授权等待中父进程 SIGKILL | worker 自行退出，回调端口关闭 |
| 宿主标准断开 | applied=true，随后 CLI 为 AUTH_REQUIRED，挂载技能移除 |
| 卡片连接后取消 | 先确认 53682 已监听，再点「取消连接」；卡片恢复「连接」，端口关闭 |

测试环境最终保持断开；不把本地退出称为撤销 Dropbox 服务端授权。

## 包装与检查

17 项 Node 检查全部通过，覆盖只读边界、分页、完整 UTF-8/哈希和版本核验、无 .tag 的真实下载头、非文本/超限拒绝、精确 scopes/PKCE、保存前账号验证、代际取消、私有存储、参数错误、固定端点及 CSRF/state/进程清理。

官方 Agentic Hub CLI（openjiuwen-agentichub 0.0.1）干净 staging validate/pack 通过。原生和 Hub 最终 ZIP 精确验包均为 4 个 JS 文件、0 个已知签名；全部载荷/许可证声明/路径和历史文件逐一检查。普通 check-repo/CI 不验证 agent-mcp，不能代替这些实际功能检查。

已保存最终回跳、连接卡片、聊天文件核对、全文和原生文件预览五张原图，未经修改；Song Haoran 已批准公开，原图与确认记录在 `test-evidence/20261123-stock-1.1.0/`，清单为 `tests/fixtures/dropbox-screenshot-manifest-20261123.json`。另保存早期问题、初次同意页、拒绝和卡片取消图，不将初稿图冒充最终新聊天。

Windows/Linux、正式 Hub 安装、自然过期/远端撤销后的恢复、实际刷新、远程回调、备用授权码、新账号/其他应用和套餐限额耗尽均未实测。搜索依赖服务端索引，不能当作完整遍历；本包只读 UTF-8 文本，不是任意文件解析器。

## 用户确认

2026-11-23，Song Haoran 在当前对话回复 `call_e23e01e72044465998f4ba3794e07fd0`：「确认通过并附五张原图提交 PR」。确认覆盖上列最终原生/Hub ZIP、已列明账号配置约束与未测边界；允许包推送、五张原图公开与创建 PR，不含自动合并或 Hub 发布。追踪报告 RPT-20261123-dropbox-runtime-repair。
