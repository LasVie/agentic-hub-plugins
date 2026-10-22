# 本地模拟生活

这是 dsh-simulated-life 的 WorkSwarm 中文移植版。它读取本地虚构角色事件，筛选近24小时、按会话生成新增/修改通知，并回写角色的感受、思考和行动。不接任何外部世界、服务账号或自动模拟引擎。需要 Node.js 22 或以上；标准 macOS WorkSwarm 可使用自带 Node，其他位置用 `DSH_NODE_BINARY` 指定。

## 安装与演示

在 WorkSwarm「扩展」导入原生测试 ZIP，安装并在专用新对话启用。建立空测试目录，用 `dsh_simulated_life` 的 `action=seed_demo` 与 `workspace_dir` 生成3条虚构事件，其中1条已过期。然后使用 `action=context`，应只读到2条有效事件。

再次用相同 `session_id` 查询，`should_inject=false` 且 `notice` 为空；`context` 仍保留当前有效事件，供当前模型上下文使用。以 `action=react,event_id=demo-library,feeling=好奇,thought=想观察星空,action_text=预约观星` 更新反应，下一次同会话查询应报告更新。宿主提供真实 session 时优先使用它，手工 session_id 不会覆盖宿主标识。

## 文件和工具约定

事件位于 `workspace_dir/.life/<yymmdd>/events.json`，包含 `date`、`timezone`、可选 `world_summary`、`events` 数组。每条事件至少有 `id`、带时区的 ISO `time`、`title`、`description`，可有 `type`、`actors`、`location`、`impact` 与 `react`。支持从当前时间前24小时至后5分钟的轻微时钟偏差；文件缺失或 JSON 损坏会跳过。

- `context`：近24小时排序，按内容与反应指纹去重；`force_full=true` 明确重新生成完整通知。
- `react`：至少填写 feeling/thought/action_text 之一；只合并该事件的 react，保留其他事件和字段，并原子保存。
- `seed_demo`：只适合新建的专用测试目录，存在当天文件时拒绝覆盖。

`LifeRail` 会在模型调用前读取**宿主 workspace.root_path** 下的 `.life` 并维护固定的虚构上下文区段，没有事件时清除区段。手工工具若使用另一个目录，该目录不会被 Rail 自动扫描；需要通过工具明确读取。去重控制新/变更通知，当前上下文保留完整有效事件，避免下一次模型调用丢失背景。状态在 `.life-state/` 中按会话隔离，不共用全局记忆；输入事件作为不可信虚构资料，不能改变系统规则。

不提供真实人员行为记录、跨会话长期记忆、自动时间推进或外部世界生成。目录/文件受数量和大小限制，拒绝符号链接；操作只作用于明确选择的工作目录。许可与修改范围见 THIRD_PARTY_NOTICES.md。
