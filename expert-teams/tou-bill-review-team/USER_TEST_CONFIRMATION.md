# 分时用电账单复核专家团 1.0.0 人工测试确认

- 任务 `AH-20261120-tou-bill-review-team`，负责人 Cai Zhenze，Candidate Not Applicable。
- 确认记录 `RPT-20261120-tou-bill-review-team-user-confirmation`。Cai Zhenze 在本次 Codex 会话明确确认本版人工测试完成且通过，授权仅通过 GitHub 交付。登记时间 `2026-11-20T16:07:57+08:00`（Asia/Singapore）。
- [原生测试 ZIP](test-packages/tou-bill-review-team-1.0.0-native.zip) SHA-256 `8281f525470dfa86164f444cead9f7320fdd5c779283f64b5791c0f3d142ec9e`。
- [规范包装 ZIP](release/1.0.0/tou-bill-review-team-1.0.0.zip) SHA-256 `f184969266e41f8f1110ab64f057c3c90c608a19d90102d6ce4e7a55ac87efc6`。

已安装的 16 个运行时文件与两包及源码逐文件一致。三位包内成员完成实际交接，独立复算先于候选。会话另委派交付核验员核对回执及生成中文档案。18:00 属非峰段，两段各 2 kWh。账单为 1.00 CNY，复算 0.80 CNY，差额 0.20 CNY。交付清单中的九个摘要匹配；重新运行已安装脚本得到了逐字节相同的十个档案文件（含清单）。

收到并核验了三张用户提交的原始 PNG。见 [截图索引](evidence/1.0.0/index.json)、[提交核验](tests/records/phase3-verification.json)。人工截图及保存的档案覆盖正常流程，缺读与候选错误的阻断证据见 [自动测试](TEST_REPORT.md)。人工会话使用已安装的包，未单独验证桌面文件选择器提交。暂无交付阻断项。
