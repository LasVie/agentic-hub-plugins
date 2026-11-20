# 人工测试 · 日常洗衣分批复核专家团 v1.0.0

- [原生安装 ZIP](test-packages/laundry-load-review-team-1.0.0-native.zip) SHA-256 `5a5ee96e6a2705d73a09ed7d6358acbd5a77b8209662bd5f5384145c119560bb`。
- [规范包装 ZIP](release/1.0.0/laundry-load-review-team-1.0.0.zip) SHA-256 `487147dce54755e37fef5a9f4fec37a350042a0814642aafa5b1718a97b5ce7d`。

1. 打开有授权模型的 WorkSwarm。选择「专家管理 → 我的专家 → 专家团 → 创建 → 上传文件创建」，类别为「专家团」，上传原生 ZIP。检查 v1.0.0 和主理人、规划员、独立护理复核员。
2. 按下方提示词进行真实团队测试。核对任务回执顺序：复核员独立初核 → 规划员生成候选 → 同一复核员核对候选 → 主理人交付。初核任务只读取原案。
3. 打开 `checklist.html`。预期 11 件均有交代。3 批可机洗（5 件浅色上衣用标准 40°C；3 件深色运动衣用轻柔 30°C；新红衣单独用轻柔 30°C）。运动上衣悬挂晾干，短裤允许低温烘干。围巾仅手洗，标签不清的新衣待确认。档案状态 `reviewed_with_holds`。
4. 可选负例：复制样例到另一路径，只在副本中删除 `gentle30` 程序，使用另一个新输出目录。预期只有浅色批次可以继续，深色运动衣与红衣显示无相容程序。
5. 请保留显示版本、真实任务交接及中文清单的原始截图，并确认本版测试是否通过。

[隔离 WorkSwarm 预览](http://127.0.0.1:6811/) 已通过本地管理接口装入精确原生 ZIP。默认模型为固定响应夹具。验证实际协作时，请在自己有授权模型的 WorkSwarm 导入，或在隔离预览自行配置并选择有授权的模型。可直接查看 [工程合成案例清单](.local/workswarm/artifacts/delivery/checklist.html)。

## 可直接粘贴的合成案例提示词

```text
请使用已安装的「日常洗衣分批复核专家团」v1.0.0 进行真实团队测试。只读以下已授权合成案例：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/laundry-load-review-team/tests/fixtures/mixed-basket.json

仅授权在如下全新目录写入报告和交付，若已存在请停下：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/laundry-load-review-team/.local/manual-test-v100-1

先委派复核员从原案保存独立初核和实际回执，再委派规划员；完成后委派同一复核员校验候选，再交付。请运行已安装的脚本，核对摘要并给出真实任务回执、每批程序、干燥去向、待处理项和 checklist.html 绝对路径。不得联网、改写原案或操作机器。完成后等待我确认。
```

## 隔离服务

在本仓库根目录运行以下命令查看或停止本任务预览。

```sh
team="$PWD/expert-teams/laundry-load-review-team"
py="$PWD/../jiuwenswarm/local-only/connector-import/venv/bin/python"
"$py" -B "$team/tests/host_integration.py" status --runtime "$team/.local/workswarm"
"$py" -B "$team/tests/host_integration.py" stop --runtime "$team/.local/workswarm"
```
