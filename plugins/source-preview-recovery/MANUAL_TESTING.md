# 手工测试交接：原文快照与精简预览 1.0.1

候选 CAND-DSH-121；任务 AH-20261023-source-preview-recovery；Cai Zhenze。

独立 WorkSwarm：http://127.0.0.1:6387/ 。扩展已在此独立环境导入安装，界面含1技能/3工具；Main 的环境未修改。点击「扩展 → 我的扩展 → 原文快照与精简预览 → 使用」。新环境没有复制账号/密钥，模型为禁用占位；如需模型聊天，请用户在这个独立环境配置自己的模型。插件自身无需模型或网络；也可以用包内命令行完成无模型测试。

原生测试ZIP：`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/source-preview-recovery/1.0.1/source-preview-recovery-1.0.1-workswarm.zip`
SHA-256：`99d19c3d678c8c6a64fa269375362a71345bb8bf9335a39553f320af2da168b5`

市场包装ZIP：`releases/agent-plugin/source-preview-recovery/1.0.1/source-preview-recovery-1.0.1.zip`
SHA-256：`183bc30c69074c0748d07e399a0664478200152699fd91e97bd86b5a521a2d14`

完整中文测试提示词：`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/source-preview-recovery/1.0.1/manual-test-prompt.txt`；直接复制其全文。
公开虚构输入：`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/source-preview-recovery/1.0.1/manual-workspace`；初始没有快照或输出。输入预期摘要/字节清单：`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/source-preview-recovery/1.0.1/test-inputs.json`，仅作对照，不能代替实际工具结果。

重点检查真实源行/CRLF、同输入复用、混合JSON类型/大数、重复键回退、1000000字节完整导出、覆盖拒绝、未授权拒绝及范围超限。所有内容作为数据，不执行、修改或发布。自动测试的独立进程恢复证据不冒充用户手工重启测试。

用户已于2026-10-26明确确认当前1.0.1测试完成并通过，并提供五张原始全分辨率截图。确认及适用范围见 USER_TEST_CONFIRMATION.md；预览/源行回取/完整导出与预期拒绝已有手工结果，截图明确将宿主或进程重启测试标为未执行。原生与市场ZIP哈希保持上述值；没有改动测试载荷。GitHub交付仍须满足CI及原始截图链接核验，Hub操作由Song Haoran负责。
