# 多机器人路径规划复核专家团

版本 1.0.0；负责人 Cai Zhenze；任务 `AH-20261117-robot-route-review-team`；Candidate Not Applicable。

原生 AgentGroup：Leader、地图与规则核对员、同步路径规划员、独立路径复核员。2–4 个模拟机器人在有界离散网格中协同到达目标，禁止顶点冲突与反向换边；通过原始模型审查、实际规划和独立逐时刻回放交付中文离线动画、CSV、JSON、复核说明和输入摘要。Python 3.10+ 标准库；不依赖 ROS、GPU、外部服务或新增宿主代码。

原生源码在同名子目录。原生安装包见 `test-packages/`，规范包装包与完整摘要见 `release/1.0.0/`。安装和操作说明见 [MANUAL_TESTING.md](MANUAL_TESTING.md)，构建测试见 [TEST_REPORT.md](TEST_REPORT.md)，来源与许可见 [SOURCE_REVIEW.md](SOURCE_REVIEW.md)。

用户于 2026-11-19 确认 1.0.0 人工测试通过。见 [确认与证据](USER_TEST_CONFIRMATION.md)。
