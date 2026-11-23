# Linear 宿主探测生命周期核查

2026-11-22，Song Haoran，原任务 AH-20261117-linear-connector。

## 已观察事实

1. 原版 macOS WorkSwarm 安装包 package.json 为 0.2.8，内置 Node.js 22.12.0。
2. 1.1.1 在空配置中正常安装、授权并进行中文读写；随后重连而不聊天，再断开，mcp.disconnect 返回 applied=true，但三条已核对工作目录的 npm／适配器／mcp-remote 进程仍存在，mcp.show 为 disconnected 却仍列出 8 个工具。现场记录为 v111-disconnect-residue.json。
3. 第一次按命令字符串包含测试根目录的检查漏掉了不带根路径的父进程；已改为完整父子链核查并保留纠正。手工只结束已核对的试验适配器后，它正常结束其子进程；此手工清理不计入正常断开通过。
4. 1.2.1 CLI 版本安装和授权后尚未聊天即断开，mcp.show 为 disconnected、无工具；完整隔离实例父子链中无 Node 子进程。状态命令返回 AUTH_REQUIRED，证明该包本地授权已清除。

## 公开源码机制与推断

对照官方 v0.2.8 标签 commit 068f148b59e140a179e31c9fe58eed8ea1700c1e：

- [mcp_config.py](https://github.com/openJiuwen-ai/jiuwenswarm/blob/068f148b59e140a179e31c9fe58eed8ea1700c1e/jiuwenswarm/common/mcp_config.py) 的 probe_mcp_live_connection 将连接放入全局 Runner.resource_mgr，标记 mcp.probe，独立于聊天适配器。
- [agent_manager.py](https://github.com/openJiuwen-ai/jiuwenswarm/blob/068f148b59e140a179e31c9fe58eed8ea1700c1e/jiuwenswarm/server/runtime/agent_manager.py) 的 apply_mcp_change 主要对已存在的 agent 逐个移除；配置项不存在时还可作为无服务器的 no-op 返回成功。
- [interface_deep.py](https://github.com/openJiuwen-ai/jiuwenswarm/blob/068f148b59e140a179e31c9fe58eed8ea1700c1e/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py) 的 unregister_mcp_by_name 枚举适配器已登记服务器；未登记到聊天适配器的探测实例存在清理遗漏的可能。

这些源码机制与实测一致，支持宿主探测缓存生命周期问题的判断。应用没有提供 gitHead，未将公开标签代码与本机二进制宣称为逐字节相同，也未修改或重新打包 WorkSwarm。

## 已授权的后续方案

用户在本会话明确选择继续只改 Hub 包，评估短时运行的 Node CLI + 技能绕开宿主缓存。1.2.x 仅声明 CLI 与技能，OAuth／MCP 由固定 MIT 客户端处理，每次操作完成前等待其独立进程退出。当前现场验收以同版本 TEST_REPORT.md 为准；不把旧版结果或人工清理冒充新版本通过。
