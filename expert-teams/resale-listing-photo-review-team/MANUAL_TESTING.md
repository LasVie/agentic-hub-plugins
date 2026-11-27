# 二手商品上架照片复核专家团 v1.0.0 人工测试

1. 使用 `test-packages/resale-listing-photo-review-team-1.0.0-native.zip`，在 WorkSwarm「我的专家 → 专家团 → 创建 → 上传文件创建」导入。核对安装版本 1.0.0，选择已经启用本机文件图片读取的视觉模型。本轮使用合成照片，可授权模型读取。
2. 从安装后的专家团启动新会话，发送下面的提示。输出目录必须全新。遇到现成目录请将末尾的序号改为下一未用值。
3. 确认团队在实际任务面板有整理员和独立复核员两个完成任务。两位成员均须看到四张照片，封存各自的意见。打开最终 `delivery/checklist.html`，核对 C01 照片通过，主图为 `camera/front.jpg`，后续顺序为划痕近照 `camera/right-scratch.png`、充电器 `camera/charger.png`。D02 应暂缓，并要求补拍钻头收纳盒与电钻同框。若视觉模型看不清或两位成员的依据无法对应，保留待确认，提供实际现象。
4. 请明确告知此 ZIP 的人工测试是否完成且通过。请提供能看清版本、两位成员的任务和最终清单的原始截图。

## 可直接发送的合成案例

```text
请使用已安装的「二手商品上架照片复核专家团」v1.0.0 进行真实团队测试。先核对安装版本。

授权读取以下合成商品说明与照片目录，并允许当前已选的 WorkSwarm 视觉模型查看这四张合成照片。
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/resale-listing-photo-review-team/tests/fixtures/products.json
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/resale-listing-photo-review-team/tests/fixtures/photos/

只从源目录读取，不修改文件或权限。只授权在以下全新目录存储本轮脚本输出与真实任务回执。若目录已存在，请停止。
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/expert-teams/resale-listing-photo-review-team/.local/manual-test-v100-1/

使用安装版共享技能。预检后创建两个真实团队任务。整理员、独立复核员分别用 read_file 查看同样的四张原照和商品说明，两人各自封存意见、向主理人单独交接。在两份意见封存前不要互相查看结论。核对实际任务状态及回执后交付。请报告逐款状态、主图和详情照片顺序、补拍或待确认事项，及两份任务回执和 checklist.html 的绝对路径。不要发送或发布照片。完成后等待我确认人工测试。
```
