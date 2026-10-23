# 第三方来源与修改说明

本包含有来自 **dsh-whale-post / packages/verify** 的适配材料。上游：
https://github.com/deepsleepAquarium/dsh-whale-post/tree/d78a82699722f0da6ae3d2b4cbdbaa411f2f67af/packages/verify

- 版本：0.6.1；固定提交以上述完整哈希为准，不将不同的发布标签提交混为一谈。
- 原有版权：**Copyright (c) 2026 The Tank**。
- 许可：MIT；完整原文（含条件与免责声明）保留在 [licenses/whale-post-verify/LICENSE](licenses/whale-post-verify/LICENSE)。上游无适用 NOTICE。
- `runtime/verifier.py` 适配自 `index.js`：保留完整原始文件头（历史接口说明），固定字段顺序、UTF-8 正文摘要、解码十六进制密钥的 HMAC、字段与白名单检查、关闭时明确未校验。
- `README.md` 参考并适配上游 README 的功能说明，改为简体中文宿主流程，纠正白名单对象为发件人。
- 2026-10-23 的修改：转为 Python 标准库，加入受限基础协议、严格 JSON/Unicode/类型与大小检查、安全文件访问、专用密钥、明确白名单、原子修订号策略。删除共享密钥回落、可选 bus/Cordis、提醒和消息传输功能。
- 原生宿主适配、技能与测试是本次新增材料；不对仓库自有新增材料擅自作统一再许可决定。

没有复制图标、字体、媒体、模型、外部数据集、第三方依赖二进制或用户凭据。Python 标准库和 openJiuwen SDK 由运行环境提供，未捆绑；Node 仅用于开发验证，不是运行依赖。
