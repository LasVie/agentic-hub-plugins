# Asana 凭据路径复核

原任务 AH-20261117-asana-connector；候选 CAND-CLD-323；负责人 Song Haoran。2026-11-22 开始，进入 2026-11-23 时仍按同一任务继续。只改 Hub 包，不改 WorkSwarm。

## 已核实

- 1.0.0 和精确 1.1.0 包的宿主字段均为 ASANA_PERSONAL_TOKEN；1.1.0 mcp.json 的环境占位符与 token-schema.json 一致。没有字段更名证据。
- 旧业务成功运行在专用 QA profile；旧失败来自默认桌面实例的自定义 MCP 注册入口。配置及认证来源并不相同，不能用一个实例的成功证明另一个实例的凭据相同。
- WorkSwarm v0.2.8（公共源码 068f148b59e140a179e31c9fe58eed8ea1700c1e）按连接器名称查询 CredentialStore；build_mcp_credential_resolver 在该实例没有存储凭据时会保留占位符。自定义 MCP 不等同于安装包含 manifest 和凭据 schema 的原生包。
- 该版 Asana 的 initialize 和 tools/list 只返回协议／工具元数据，没有向 Asana 发请求。卡片发现四项工具不等于真实 PAT 验证成功。perform 中的 users/me 才能验证真实服务授权。
- 旧 401 只说明那次 Asana 请求没有被接受，不能判定 PAT 已过期。Asana 官方文档也要求把令牌视为不透明字符串，不能从固定格式推断有效性。
- 精确 1.1.0 Hub 包已经从原版 0.2.8 卡片经本地目录夹具安装到新的隔离环境，5 个安装文件与原生 ZIP 一致。初始没有该连接器凭据；正常显示“个人访问令牌”及“保存并连接”。没有手动读取或复制凭据文件。

## 待确认

旧失败的直接原因仍可能包括旧自定义配置未完整安装、默认实例没有对应令牌、不同启动环境导致凭据不可解密或 PAT 本身不可用；现有证据不足以在这些原因间定论。不复制旧凭据或改变宿主加密机制来验证。

本轮优先使用正常卡片表单由用户重新输入有效 PAT，再用同一实例、同一包内工具完成中文 status／列表／读取／新建一次 QA 任务／独立回读。写入仅限原专用测试项目 1220594404826613，不修改或删除已有任务。失败即停，不切换接口掩盖结果。

授权前记录：Safari 已按官方入口 https://app.asana.com/0/my-apps 打开 Create new token 表单，用途 WorkSwarm QA 20261123。Asana API 条款接受、创建凭据及复制交由用户亲自完成；不读取、截图或记录生成后的令牌。

## 2026-11-23 后续实测

用户明确回复已创建并保存连接，卡片显示“使用”。首次聊天在 Asana 工具执行前因测试模型账号旧刷新状态失败；仅调整隔离环境的模型账号文件引用，不读取／复制凭据内容，重试后工具执行成功。真实 asana_status 为 connected=true；列表返回原有 8 项且无下一页；独立读取 3 条既有 QA 任务。之后按唯一完整标题查重，仅创建一次 1220767735426842，再独立回读核对 ID、中文标题和项目。使用的是原生 MCP 工具，没有 Python／shell 业务替代路径。

本轮确认原生安装和正常安全表单可正确传递 PAT，旧 401 未再现；旧失败的确切原因仍无逐次运行证据，不反推旧 PAT 失效。连接器运行时代码和两份 ZIP 均未修改。已通过原版 mcp.disconnect 核验断开，tools=[]，完整进程树无残留 Node 服务；本地测试连接保持断开，远端任务及 PAT 未撤销。

## 来源

- https://developers.asana.com/docs/personal-access-token
- https://developers.asana.com/reference/gettasksforproject
- https://developers.asana.com/reference/createtask
- https://github.com/openJiuwen-ai/jiuwenswarm/blob/068f148b59e140a179e31c9fe58eed8ea1700c1e/jiuwenswarm/common/mcp_config.py
- https://github.com/openJiuwen-ai/jiuwenswarm/blob/068f148b59e140a179e31c9fe58eed8ea1700c1e/jiuwenswarm/server/runtime/mcp/credential.py
