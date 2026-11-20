# 人工测试 · 分时用电账单复核专家团 v1.0.0

- 安装：[原生 ZIP](test-packages/tou-bill-review-team-1.0.0-native.zip)，SHA-256 `8281f525470dfa86164f444cead9f7320fdd5c779283f64b5791c0f3d142ec9e`。
- [规范 ZIP](release/1.0.0/tou-bill-review-team-1.0.0.zip) SHA-256 `f184969266e41f8f1110ab64f057c3c90c608a19d90102d6ce4e7a55ac87efc6`。

1. 打开已配置授权模型的 WorkSwarm，选择「专家管理 → 我的专家 → 专家团 → 创建 → 上传文件创建」，保持「专家团」，上传原生 ZIP。确认已安装 v1.0.0，显示主理人、电表读数核查员、分时费率计算员及独立费用复核员。
2. 使用下方合成案例发送测试指令。确认真实组员任务与回执。独立复算报告必须先于候选文件生成。
3. 打开生成的 `review.html`。账单应为 1.00 CNY，复算 0.80 CNY，差额 0.20 CNY。`intervals.csv` 的 18:00 应为 `off_peak`，峰段与非峰段各 2 kWh。确认 HTML、CSV、JSON、三份原件副本及原始回执对应，参阅 `artifact.json`。
4. 如需核查阻断，将三文件复制到另一个授权目录，从副本 CSV 去掉 18:00 的数据行，使用新的输出目录。预期报告「缺少读数」，停止给出核验金额。原例及上轮档案不得改动。
5. 请保留当前版本、真实成员交接和最终 HTML 金额的原始截图，并确认本版测试是否通过。

[隔离预览](http://127.0.0.1:6705/) 已用相同原生包安装，可检查团队界面与固定响应工程记录。该预览的默认模型只用于固定响应夹具。自行验证语义协作时，用已配置且获授权模型的 WorkSwarm 导入测试 ZIP，或先在隔离实例的设置中自行配置获授权的模型后选用它。可直接打开 [已生成的合成案例 HTML](.local/workswarm/artifacts/delivery/review.html)。

## 合成案例提示词

```text
请使用已安装的「分时用电账单复核专家团」v1.0.0 真实运行团队任务。只读以下已授权的合成案例目录：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/tou-bill-review-team/tests/fixtures/two-hour

仅允许在以下全新目录生成报告；如目录已存在，请停下：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/tou-bill-review-team/.local/manual-test-v100-1

冻结三份原件。请实际委派电表核查与独立复算并使用已安装的脚本，先保存原案独立复算报告及其任务回执，再派费率成员计算候选。核验三个真实成员的回执之后运行交付。展示 18:00 的分段、账单与复算金额、差额、复核状态和 review.html 绝对路径。不要联网、改写原件、付款或自行确认人工测试。
```

## 隔离服务

从项目根目录运行，供查看或停止本任务的隔离预览。其他既有实例有独立数据与端口。

```sh
team="$PWD/expert-teams/tou-bill-review-team"
py="$PWD/../jiuwenswarm/local-only/connector-import/venv/bin/python"
"$py" -B "$team/tests/host_integration.py" status --runtime "$team/.local/workswarm"
"$py" -B "$team/tests/host_integration.py" stop --runtime "$team/.local/workswarm"
```
