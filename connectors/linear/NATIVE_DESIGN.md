# Linear 1.2.1 独立设计

用户 Song Haoran 于 2026-11-22 明确选择继续只改 Agentic Hub 包，评估短时 Node CLI + 技能绕开宿主缓存。沿用原任务 AH-20261117-linear-connector、slug linear 与原读写范围。

## 已知问题与设计依据

1.1.1 已证明原版 WorkSwarm 0.2.8 中的正常首授和中文读写，但「连接探测成功、尚未聊天即断开」会保留宿主探测进程。源码机制与现场证据详见test-evidence/20261122-cli-1.2.1/host-lifecycle-analysis.md。不修改 WorkSwarm，不给正常会话增加会破坏使用的空闲杀进程定时器。

本版只声明 integration.type=cli，不含 mcp.json。宿主只管理安装、CLI 授权和技能。查询、状态、写入在独立 Node 操作进程中连接托管 MCP，完成或超时就退出；成功输出必须晚于子进程退出。宿主没有本包的常驻 MCP 连接可缓存。

## 运行与授权

prepare 通过 Node 随附 npm 下载固定 MIT 客户端；只保存非秘密的安装路径，校验版本及客户端模块哈希。使用固定版本导出的 Client、NodeOAuthClientProvider、OAuth 发现与连接函数；不复制或重写 OAuth 交换、PKCE、令牌解析或刷新实现。

login 使用正常浏览器 OAuth。status 和 call 禁止交互式授权跳转；可以使用标准客户端的正常刷新，失效则返回中文 AUTH_REQUIRED。logout 调用标准客户端的本地凭据失效 API。此包专用缓存与其他连接器隔离。

父进程监督单个操作进程，定时结束、信号转发及强制退出覆盖取消和卡死。返回业务 JSON 之前等待操作进程结束，避免把短时连接交给宿主资源缓存。业务失败／超时后若已经发起写入，返回结果未知并要求先回读。

## 操作边界

复用独立编写的固定白名单和参数校验；未知工具默认拒绝，Issue 和评论只允许创建。参数通过 UTF-8 JSON 文件传入，不将远程文本拼进 shell 或 JavaScript。服务元数据只用于核对当前白名单工具，不开放资源、采样、任意 URL 或本地文件读取能力。

## 已见资料与复用

已阅读 Linear 公开 MCP 文档、mcp-remote 0.16.6 MIT 源码／导出接口，以及 WorkSwarm 0.2.8 公共源码。未复制宿主实现。品牌原图和完整许可证沿用已核查材料。外部客户端实现由 npm 正常下载，不打入 ZIP；内部导出接口随版本可能变化，固定版本和哈希是本包的实际运行要求。
