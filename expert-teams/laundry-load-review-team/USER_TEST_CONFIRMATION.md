# 日常洗衣分批复核专家团 1.0.0 人工测试确认

- 任务 `AH-20261120-laundry-load-review-team`，负责人 Cai Zhenze，Candidate Not Applicable。
- 确认记录 `RPT-20261120-laundry-load-review-team-user-confirmation`。Cai Zhenze 在本次 Codex 会话明确确认 v1.0.0 人工测试完成且通过，授权仅通过 GitHub 交付。登记时间 `2026-11-20T17:48:55+08:00`（Asia/Singapore）。
- [原生测试 ZIP](test-packages/laundry-load-review-team-1.0.0-native.zip) SHA-256 `5a5ee96e6a2705d73a09ed7d6358acbd5a77b8209662bd5f5384145c119560bb`。
- [规范包装 ZIP](release/1.0.0/laundry-load-review-team-1.0.0.zip) SHA-256 `487147dce54755e37fef5a9f4fec37a350042a0814642aafa5b1718a97b5ce7d`。

实际安装的 14 个运行时文件与源码及两包逐文件一致。核验三份真实任务回执和输出摘要，顺序为复核员独立初核、规划员生成候选、同一复核员核对候选。11 件均有交代，9 件分入 3 批机洗，围巾仅手洗和未确认标签的新衣共 2 件待处理。档案状态 `reviewed_with_holds`，复运行得到与人工档案逐字节相同的 7 个文件（含清单）。

[三张用户原图与摘要](evidence/1.0.0/index.json)展示版本、真实成员与任务交接、最终中文版清单。[验收前核验记录](tests/records/phase3-verification.json)保存摘要。人工证据覆盖安装后正常流程；冲突、错误输入与缺失可用程序由[自动测试](TEST_REPORT.md)覆盖。桌面文件选择器提交没有独立证据。暂无交付阻断项。
