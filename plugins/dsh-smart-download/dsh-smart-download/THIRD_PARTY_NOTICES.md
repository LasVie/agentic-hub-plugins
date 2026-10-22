# Third-Party Notices

## dsh-smart-download

- Upstream: https://github.com/LeiSureYu/dsh-smart-download
- Version: 1.4.6
- Revision: `e80a6574407fed44a8ad6efde3a789bce119beeb`
- Copyright: Copyright (c) 2026 dsh-smart-dl contributors
- License: MIT; full text in `licenses/dsh-smart-download/LICENSE`
- Applies to: the ported download behavior, tool documentation and implementation in this payload

Modifications: replaced DeepSeek Harness Cordis/web integration, progress UI, Node.js subprocess orchestration and optional platform-specific aria2 packages with standalone OpenJiuwen Python tools. Added private-network protection, atomic output handling, conservative resume metadata, status persistence and built-in range workers.


## 中文运行版本 1.0.1（2026-10-22）

将 README、实际 Skill、展示元数据、工具说明与可读错误中文化。保留上述原始许可、版权与署名；完整 MIT 许可字节不变。校验错误使用专用内部异常，保留 `CHECKSUM_MISMATCH` 错误码；状态网址隐藏凭据与查询参数，无效网址返回结构化错误。仅对插件自有状态目录强制设置目录权限，保留用户既有下载目录权限，临时元数据文件继续使用 0600 权限。未添加第三方实现、依赖、图像、字体或数据，不改变上游身份与发布者。
