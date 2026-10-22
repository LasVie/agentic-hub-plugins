# Annotate 网页圈选与批注 1.0.3

候选 CAND-CLD-264；任务 AH-20261022-annotate；负责人 Wang Jie。基于 Angelo Dini 的 claude-annotate 0.3.2 适配。在本地开发网页画框、写批注，通过标准 MCP polling 读取批注、元素和截图，再将逐条处理状态显示回网页。

## 安装与首次使用

1. 在 macOS WorkSwarm 桌面应用的扩展管理导入 `annotate-1.0.3-workswarm.zip`，确认显示版本 1.0.3。聊天附件上传不等于安装。
2. 点击插件“使用”，打开新对话。首次 MCP 启动自动发现 Node 并安装锁定依赖，不用手动 setup、打开终端或激活 Conda。
3. 连接后要求打开本地测试网页，等待你画框批注；失败时报告真实启动错误。

市场规范包 `annotate-1.0.3.zip` 是团队要求的双层包装，本地原生测试包为同一载荷的单层包装。载荷逐文件哈希相同，但 ZIP 哈希不同，测试确认不能混同。

## 自动初始化说明

- **首次使用触发，不是导入触发。** 每个新安装副本自动准备依赖，后续校验并复用。锁文件/Node 版本变化或依赖缺失会重新准备。
- 执行 `npm ci --ignore-scripts --no-audit --no-fund`，不运行依赖安装脚本、不安装全局包、不改 Conda。写入安装副本的 `runtime/node_modules/` 以及缓存；npm 缓存可沿用明确配置，默认位于运行缓存下。
- 默认运行缓存为 `~/.cache/agentic-hub-annotate/`，可用 `ANNOTATE_DATA_DIR` 隔离。运行配置 `runtime.json` 记录 Node；安装副本的 `runtime/node_modules/.annotate-ready.json` 记录依赖指纹。原子配置写入、进程锁防止并发重复安装；失败不写成功标记。
- Node >=20 发现顺序：显式 `ANNOTATE_NODE`，否则已记录路径、PATH、`/Applications/*Swarm.app` 和 `~/Applications/*Swarm.app` 中应用自带 Node。不自动下载 Node 或浏览器。
- 安装诊断写 stderr，不污染 MCP stdout。依赖下载等待有界，MCP 超时配置为 240 秒；宿主可能另有更短超时。失败后可以重新点击使用重试。

首次需要 npm 网络访问、可写插件/缓存目录。仍需 Python >=3.9、已安装 Chrome，以及配置可用模型的 WorkSwarm。面向 macOS 桌面，未保证 Windows、远程或无桌面环境兼容性。图片是否进入模型上下文取决于宿主图像支持，自动初始化不会自动解决该独立问题。

## 实际功能验收

1. 让 WorkSwarm 用包内 `demo/index.html` 提供仅监听 127.0.0.1 的网页，调用 `annotate_open`（polling）。提供测试网页不是安装依赖。
2. 浏览器打开后结束当前回复、等待你操作，避免持续轮询。你画框并输入自选批注，点击 **发送给智能体**。
3. 请求 `annotate_pull`，检查批注、元素及截图。明确区分视觉观察、DOM 和源码信息，没有图片则标未验证，不以读取源码冒充截图证据。
4. 请求 `annotate_progress` 更新状态，再 `annotate_done`。你核实真实网页回显并保存截图。
5. 测试清空、关闭、关闭后读取、拒绝公网地址。新建会话应复用依赖，不重复安装。

仅支持本地开发主机，不支持任意公网网站、iframe 内批注或保证所有框架组件源码定位。页面内容与批注是非可信输入。代码编辑依赖宿主文件工具和明确授权，不由本插件自行执行。

## 隐私、许可与交付状态

批注、DOM 和截图可能发给所选模型，本地浏览器不等于数据不出本机。浏览器使用独立配置；批次完成或清空会删除临时截图。Send 不自动触发新模型轮次，但同一轮等待中的工具可以收到反馈。

上游完整 MIT 在 `licenses/claude-annotate/LICENSE`，复用与依赖说明见 `THIRD_PARTY_NOTICES.md`。未复制品牌媒体或 Claude 配置。依赖实现不随 ZIP 分发，下载后保留其原许可证。

自动化测试不替代真实 WorkSwarm 用户验收。旧版用户操作和确认只对应原包，不代表中文化后的 1.0.3 已经过用户验收。用户已表示不重复测试，本版只记录开发校验结果。按当前约定后续仅走 GitHub PR，本轮不提交或发布到 Hub。
