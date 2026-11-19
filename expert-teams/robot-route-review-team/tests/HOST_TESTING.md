# 本机宿主与脚本夹具

测试代码全部位于本团队内，不分发到原生包。测试运行目录 `.local/host-*` 为本团队独有状态；原始请求、事件、命令/响应与交付文件保留，不自动清理或重放已完成执行。

使用本机已有解释器：
`/Users/IDLE_And_R/Downloads/Huawei/jiuwenswarm/local-only/connector-import/venv/bin/python`。

按顺序运行 `tests/host_integration.py` 的 `prepare`、`start`、`check`、`plan`、`run`、`stop`。每个命令带 `--runtime` 指向新的本团队 `.local/host-名称`。`prepare` 还需 `--host` 指向既有 JiuwenSwarm checkout、`--python` 为其真实解释器；`check`/`run` 需 `--native` 精确原生 ZIP；`run` 的 `--record` 必须在本团队 `tests/records/`。`validate --payload` 用实际官方 creator 和 SDK 只读校验提取目录。`verify` 只回读保留执行，不重新发起聊天。

专用端口：HTTP6555，固定响应6556，Agent28555，WebSocket29555，Gateway30555；任何占用都拒绝启动。`start` 从既有构建提供前端，不编译/修改宿主。`stop` 逐个核对记录中的PID、命令与工作目录，仅停止本团队进程，不使用通用 kill/make stop。

`plan --scenario positive/collision/model-gap/search-limit`：分别用真实包脚本求解会车位、在专用合成候选副本注入中心格碰撞、在独立模型记录放入未解决问题、把高层限额降到1。正常/负例都通过实际宿主建队、私有/共享Skill、任务认领、命令调用、完成回执与最终交付；不更改包或其他会话。

两阶段复核：`verifier-model` 无上游依赖且只读原始案例；规划器等待该原始审查完成后运行；`verifier-review` 实际依赖原始审查与规划任务，读取两份真实文件。检查真实工具返回的上游交付、文件时间与摘要。固定模型只控制调用次序，不证明真实模型盲审、语义独立或优于单专家。所有结论保持人工测试未通过。

GUI 已观察到本机原生四成员详情、中文README与“上传文件创建”类别。实际文件上传与人工会话另行记录，不能由管理RPC导入或截图替代。离线HTML的file:浏览器访问被安全策略阻止；没有用别的浏览器/代理绕过。保留此局限供用户人工检查。
