# 截图外发脱敏复核专家团 v1.0.0 人工测试

任务 `AH-20261126-screenshot-redaction-review-team`，负责人 Cai Zhenze。本轮只用两张合成 PNG。

1. 打开 WorkSwarm「我的专家 → 专家团 → 创建 → 上传文件创建」，导入 `test-packages/screenshot-redaction-review-team-1.0.0-native.zip`。核对名称、v1.0.0 以及主理人、截图脱敏员和独立像素复核员三个角色。需要已有 Swift 命令行工具的 macOS。
2. 向团队发第一次测试指令。由脱敏员用已安装工具本机扫描，并保存 `scan.json` 与真实任务回执。
3. 按团队返回路径，在本机浏览器打开安装包内的 `confirm.html`，选 `scan.json` 与两张合成 PNG。将 `image-01` 保持暂缓。只检查并确认 `image-02`，遮盖客户邮箱，给底部报错文字标记保留框。若本机未识别邮箱，拖动手画完整遮盖框。保存 `approval.json`，将确认文件移到本轮新工作目录，向团队发第二次指令。
4. 核对脱敏员生成候选、独立复核员执行复核、主理人交付。预期 **1 张通过，1 张暂缓**。只有 `share/image-02.png` 可供最后检查。邮箱所在像素为不透明黑色，底部报错清楚，`image-01` 不在 share/，原始 PNG 不变。
5. 通过后保存真实任务回执和中文版清单的原始截图，并明确确认人工测试结果。截图只用本次合成数据。

## 第一次测试指令

```text
请使用已安装的「截图外发脱敏复核专家团」v1.0.0 测试本机截图脱敏。先核对版本。
授权只读以下合成 PNG 目录：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/screenshot-redaction-review-team/tests/fixtures/screenshots/
仅在以下尚不存在的目录保存工具、缓存、报告与结果。若已有目录，请停止：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/screenshot-redaction-review-team/.local/manual-test-v100-1/
用现有宿主真实团队任务。请先由截图脱敏员用安装包的脚本进行 email 类别本机扫描。输出 scan.json、确认页面和任务回执的绝对路径。在我提供 approval.json 路径之前停止。原图和识别文字不得读入模型或发送到其他服务。
```

## 第二次测试指令

```text
我已在本机检查合成原图和确认框，image-01 暂缓、image-02 已确认。
授权只读该确认文件：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/screenshot-redaction-review-team/.local/manual-test-v100-1/approval.json
请让同一脱敏员用真实任务生成候选，再让独立复核员逐像素复核。主理人核对回执后交付。用已安装的脚本，保持首次授权的路径和新输出约束。报出通过和暂缓的编号、真实任务回执路径、最终 checklist.html 和 share/ 路径。不发送任何文件。完成后由我确认人工测试结果。
```
