# 用户测试完成与原始截图

成员 Cai Zhenze；CAND-DSH-070；AH-20261023-message-quota-audit；消息配额与用量审计1.0.1。

用户在当前独立Codex会话明确确认：
> I confirm manual testing of 消息配额与用量审计 1.0.1 is complete and passed. Use my attached screenshots and proceed to Phase 3 under the latest AGENTS.md, keeping it isolated from Main.

收到/核对观察时间：2026-10-23 17:22:53 Asia/Singapore；原消息发送时间未提供，不虚构消息链接。截图文件名时间为17:19:10/19/28/37，画面内会话时间16:50～16:51；仅按可见来源记载，不把文件名当消息时间。

原生手测ZIP SHA-256：61dff8962b7f481f9ae89eb6fdad0ef77f67e78d987f52c0652bdcdb3c31a9a6。
市场ZIP SHA-256：0eb6d3f295db16ceb21717927cefeb21c081b3d2fd1408d9af68d9c61da5a4df。

当前源码、两个ZIP及安装目录的9个文件哈希与手测交付记录完全一致。只新增外层确认/截图/交付记录，不修改已测试载荷。最新版AGENTS blob e6e315918b1d948ba37bd2a3312c55c05a254d97与本地相同；交付门槛材料齐备，无已知阻塞问题，负责人最终验收仍待后续。

## 原图

四个原始全分辨率PNG原字节复制到evidence/user-test-1.0.1-01.png至04.png；尺寸、字节数、SHA-256、原文件名和收取路径见evidence/originals.json。无缩放、重压缩、剪裁或重绘。检查未发现账号密钥或不相关私人内容；画面中的本地路径及公开虚构输入是本次授权测试材料。

01～02为完整测试要求；03～04为实际完成汇总，显示1.0.1、revision0→1、预览未写账、2+1单位达到direct限额、超额拒绝、重复ID幂等/冲突、离线1单位、回执/链深拒绝、旧修订拒绝和相符/差异对账。最终3条记录共4单位，正文byte数42/30/18。

只读核对本地手测数据库：revision1，manual_001/002/004单位2/1/1、byte数42/30/18；manual_001摘要fadf49b958d5416552a475d94eda4ee481196332967fb6f41a0589a4e8563bea与原图一致。没有修改或重新执行用户账本操作。截图是用户提供的对话/工具结果汇总，不冒充独立逐事件原始后端日志；用户明确完成确认是单独证据。

## 后续

在获准的交付PR正文/专用评论嵌入这些原始PNG，核对远端字节、显示与永久评论链接后回填Test Screenshot；不能以裸PR或本地路径替代。GitHub交付后保留Awaiting Acceptance/Planned，等待Song Haoran接受；不操作Hub，不提前登记Asset Ledger。
