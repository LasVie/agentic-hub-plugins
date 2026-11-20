# v1.0.0 人工测试

任务 `AH-20261119-timber-cut-list-review-team` · Cai Zhenze

- [隔离 WorkSwarm](http://127.0.0.1:6585/) 已预装 1.0.0。专家管理 → 我的专家 → 专家团，核对名称与四名成员。若在另一已授权实例测试，使用创建 → 上传文件创建，类别保持「专家团」，选择 [原生 ZIP](test-packages/timber-cut-list-review-team-1.0.0-native.zip)。
- 原生 SHA-256 `917a0db257030bdbea9c82e9debce9994fcefc6ff71625115df3dbc035f9c01e`。规范包装 [ZIP](release/1.0.0/timber-cut-list-review-team-1.0.0.zip) SHA-256 `1f32a70c78847bf6be87641b270148bae1cc29ae4317791bc3145d2fe0335387`。精确文件记录见 [artifact.json](release/1.0.0/artifact.json)。
- 真实团队测试请选择你授权的模型。6585 的默认模型是本地固定响应测试夹具。可在隔离实例中自行配置授权模型，或使用另一已配置的 WorkSwarm 实例；不需要导入任何其他实例的凭据。

## 正例

进入本专家团的团队会话，发送下列提示。使用全新目录，避免覆盖任一既有结果。

```text
使用「木料定尺下料复核专家团」v1.0.0 进行真实团队人工测试。
我已确认案例的整数毫米尺寸、材质规格、两端修边与每件锯缝。只读：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/timber-cut-list-review-team/tests/fixtures/verified-pairing.json

仅允许在下列尚不存在的目录保存成员独立报告与交付；若已存在就停止：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/timber-cut-list-review-team/.local/manual-positive-1/
只读原案例并用实际 build_team/create_task 依次委派 stock-analyst、planner、verifier。保留各成员完成回执。
请实际使用安装包的 cut-workflow。库存员生成 stock.json，规划员依库存报告生成 plan.json，复核员从原案逐件独立验算生成 review.json。
亲自运行 deliver 到该目录下尚不存在的 delivery/。列出文件路径、原案摘要、每块余料、复核结果和实际成员回执。
不要联网、修改输入、改变占量、操作设备或发布。完成后等待我确认人工测试结果。
```

期望 `verified`，B1、B2 各使用 2,391 mm，每块余 9 mm。打开实际的 layout.html，展开和收起库存明细，确认首尾修边、零件、锯缝、余料与 CSV 四行一致。检查复核说明与输入快照，保留实际成员活动和回执。

## 负例

用同样的流程把案例换成 `/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/timber-cut-list-review-team/tests/fixtures/one-mm-over.json`，工作目录改为尚不存在的 `/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/timber-cut-list-review-team/.local/manual-negative-1/`。两块各有 2,390 mm 可用。独立复核应确认无可行分配，给出两块各差 1 mm 的最佳近似情况，CSV 仅有表头。

本版人工测试已于 2026-11-20 由用户确认，见 [人工测试确认](USER_TEST_CONFIRMATION.md)。复测请记录精确版本与摘要，并保留当前版本专家团、实际成员交接、正例排样图和负例结果的原始截图。

## 隔离实例管理

本实例由该团队 tests/host_integration.py 启动。要停止 6585 实例，调用：

```bash
/Users/IDLE_And_R/Downloads/Huawei/jiuwenswarm/local-only/connector-import/venv/bin/python -B   "/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/timber-cut-list-review-team/tests/host_integration.py" stop --runtime "/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/timber-cut-list-review-team/.local/host-final-positive"
```

在全新的团队 .local 目录里按 prepare、start、check 建立新实例。prepare 指向现有宿主目录和解释器，check 指向精确原生 ZIP。在已有端口仍被占用时，使用 prepare 的 --port-offset。保留当前测试和证据目录。
