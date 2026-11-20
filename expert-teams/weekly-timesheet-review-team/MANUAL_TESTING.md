# v1.0.0 人工测试

任务 `AH-20261120-weekly-timesheet-review-team`，开发负责人 Cai Zhenze。请用合成案例，不需要真实员工或客户资料。

1. 在带已授权模型的 WorkSwarm 打开「我的专家 → 专家团 → 创建 → 上传文件创建」。选 `test-packages/weekly-timesheet-review-team-1.0.0-native.zip`。检查名称、版本和主理人、分析员、独立复核员三个角色。
2. 打开专家团会话，把下列测试提示中的绝对路径换成你实际要授权的路径。确认结果目录尚不存在。主理人应先收取初核回执，再派发分析，最后请同一复核员完成复核与交付。
3. 打开交付目录内的 `checklist.html`。期望合计 **260 分钟**，11 月 16 日 **105 分钟**，11 月 17 日 **155 分钟**。第 2、3 行重叠 **30 分钟**，第 4、5 行重复，第 8 行缺结束时间，这五行全部暂缓。第 9 行属于周外，11 月 18 日需确认有无记录。摘要清单涵盖七份文件，交付状态为 `reviewed_with_holds`。
4. 若结果符合预期，请明确确认通过，并保留团队任务及结果页的原始截图。若发现问题，请提供对应失败步骤。

## 可粘贴的测试提示

```text
请使用已安装的「每周工时记录复核专家团」v1.0.0，对单人合成工时进行真实团队测试。先核对安装版本。

授权只读以下两个文件：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/weekly-timesheet-review-team/tests/fixtures/mixed-week.json
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/weekly-timesheet-review-team/tests/fixtures/mixed-week.csv

仅在下列全新目录保存报告和交付文件。若目录已存在，请停下：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/weekly-timesheet-review-team/.local/manual-test-v100-1/

使用宿主真实任务和已安装的 timesheet-review 脚本。先让 reviewer 只依据原始文件保存独立初核和任务回执，再让 analyst 根据相同原始文件分析。随后由原 reviewer 使用初核与分析执行正式复核。主理人核实三份真实任务回执及文件摘要后交付。请给出两个有工时的日期、计入总分钟、暂缓行及原因、需核实的预计日期、成员回执路径和 checklist.html 的绝对位置。原始文件只读。本轮不提交工时或发布。完成后由我确认人工测试结果。
```
