# 木料定尺下料复核专家团 1.0.0 人工测试确认

- 任务 `AH-20261119-timber-cut-list-review-team`，负责人 Cai Zhenze，Candidate Not Applicable。
- 确认记录 `RPT-20261120-timber-cut-list-review-team-user-confirmation`。用户在本次 Codex 会话明确确认 v1.0.0 人工测试完成并通过，授权进入 GitHub 交付。2026-11-20（Asia/Singapore），登记时间 `2026-11-20T11:51:05+08:00`。
- [原生测试 ZIP](test-packages/timber-cut-list-review-team-1.0.0-native.zip) SHA-256 `917a0db257030bdbea9c82e9debce9994fcefc6ff71625115df3dbc035f9c01e`。
- [规范包装 ZIP](release/1.0.0/timber-cut-list-review-team-1.0.0.zip) SHA-256 `1f32a70c78847bf6be87641b270148bae1cc29ae4317791bc3145d2fe0335387`。

人工会话使用已安装的原生团队，全部 18 个运行文件与两份 ZIP 及源码一致。实际任务回执显示库存员完成前置核验与库存报告，规划员完成候选，独立复核员从原案验算，规划员随后执行交付。正例为 `verified`，每块用 2,391 mm，余 9 mm，CSV 共四件。四份原始快照和清单的八项 SHA-256 一致。重新生成含清单的九个档案文件，逐字节相同。

三张用户提供的原始 PNG 展示中文排样、实际成员和任务交接。见 [截图索引](evidence/1.0.0/index.json) 与 [提交前核验](tests/records/phase3-verification.json)。截图和保存的工作目录覆盖正例。负例及错误候选拒绝的单独证据来自 [自动测试](TEST_REPORT.md)。用户随后在本会话给出的人工通过结论保存在本记录。现场测量和切削安全由用户另行核对。暂无交付阻断项。
