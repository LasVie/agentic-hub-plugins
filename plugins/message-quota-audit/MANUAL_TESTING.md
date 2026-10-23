# 消息配额与用量审计 1.0.1：用户手测

成员Cai Zhenze；CAND-DSH-070；AH-20261023-message-quota-audit。

原生测试包：`dist/message-quota-audit/1.0.1/message-quota-audit-1.0.1-workswarm.zip`。
SHA-256：`61dff8962b7f481f9ae89eb6fdad0ef77f67e78d987f52c0652bdcdb3c31a9a6`。

市场交付包：`releases/agent-plugin/message-quota-audit/1.0.1/message-quota-audit-1.0.1.zip`。
SHA-256：`0eb6d3f295db16ceb21717927cefeb21c081b3d2fd1408d9af68d9c61da5a4df`。
两者内层9个文件逐字节相同；无需把市场外层导入宿主。

## 环境与安装

访问 **http://127.0.0.1:6386**。这是本任务新建的独立WorkSwarm实例，前端6386、后端29250、agent28250、gateway30250；数据/配置位于 `/private/tmp/message-quota-audit-workswarm-20261023/`，没有复制其他实例的账号、密钥或配置。Main及旧实例保留。

插件已通过真实Extensions导入/安装RPC安装。扩展 → 我的扩展 → 消息配额与用量审计 → 使用。其他兼容实例可从“创建 → 从文件创建”选择原生ZIP，安装并启用。没有按发布按钮，也未提交Hub。

新实例模型默认 disabled-local-test，不会自动发起模型请求。若用对话测试，请自行在**此实例**本地配置/选择你的模型；不要把真实密钥发到对话。也可不使用模型，通过内层scripts/quota_cli.py和README规定的JSON请求手动测试工具。AI尚未运行模型对话或操作系统文件选择器，不将其描述为已验证。

已准备空白、公开虚构数据专用工作目录：
`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/message-quota-audit/1.0.1/manual-workspace`

首次测试应从空目录开始。若已执行过，不删除旧账、不换ID绕过结果；先读取状态，或由你明确选择另一个空测试目录并记录路径。

## 可复制的测试提示

当你决定执行下列测试时，可复制此提示。授权只指上述测试目录内的虚构用量，不代表真实发送或费用。

```text
请实际测试「消息配额与用量审计 1.0.1」，全程用简体中文。
只使用真实工具返回，不模拟调用，不把预期值当成结果。工具不可用时如实说明。
不要发送、执行或拦截消息，不读账号密钥，不修改其他插件或工作目录。

测试 workspace：
/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/message-quota-audit/1.0.1/manual-workspace

我明确授权：只在这个公开虚构测试目录中初始化和配置本插件，并登记下面指定的测试用量；没有真实投递或费用。每次正常改策略前，读取最新revision，不覆盖旧账本。

一、调用message_quota_policy action=init，再status，记录实际version、revision、event_count。
如果event_count不是0，停止写账并说明旧状态，不删除历史。
使用最新expected_revision，configure以下完整policy_json：
{"timezone":"Asia/Shanghai","day_boundary_hour":0,"buckets":{"direct":{"limit":3,"per_send":false},"offline":{"limit":2,"per_send":true}},"pair_window_seconds":1200,"pair_max":3,"hop_max":3,"ack_max_bytes":40}
保留本次配置前、后的真实修订号。

二、以下对象作为message_json文本，调用check_message_quota：
{"id":"manual_001","as":"sender_demo","targets":["reader_a","reader_b"],"type":"direct","mode":"online","body":"这是需要审阅的中文进度说明。","hop":0}
先查询report，检查预览没有增加event_count。
然后以完全相同message_json调用record_message_usage，confirmed=true；再用完全相同参数重复登记一次。
检查实际结果是否为第一次计2单位、第二次already_recorded且不重复计数。
再仅将同一ID的body改为“这是变更后的正文。”尝试登记，记录是否返回event_conflict；不要覆盖原记录。

三、依次登记下列两条，confirmed=true，不更换ID绕过拒绝：
{"id":"manual_002","as":"sender_demo","targets":["reader_a"],"type":"direct","mode":"online","body":"这是第二条中文说明。","hop":0}
{"id":"manual_003","as":"sender_demo","targets":["reader_c"],"type":"direct","mode":"online","body":"这是超过配额的第三次登记。","hop":0}
检查第一条是否恰好用完direct的3单位，第二条是否quota_exceeded且recorded=false。

四、登记离线测试用量，confirmed=true：
{"id":"manual_004","as":"sender_demo","targets":["reader_a","reader_b"],"type":"direct","mode":"offline","body":"收到，谢谢！","hop":99}
检查它是否进入offline桶，只计1单位；不把离线声明当成真实投递。

五、只读check以下两条：
{"id":"manual_ack","as":"sender_demo","targets":["reader_c"],"type":"direct","mode":"online","body":"收到，谢谢！","hop":0}
{"id":"manual_hop","as":"sender_demo","targets":["reader_c"],"type":"direct","mode":"online","body":"这是需要进一步讨论的内容。","hop":3}
记录实际ack_only和hop_limit结果，不将ok=true解释为允许发送。

六、故意用第一步配置前的旧修订号重复configure同一策略，检查revision_conflict，再status确认策略未变。

七、调用message_usage_report action=report days=7。预期用于对照：3条已登记记录；direct3单位、offline1单位，共4单位。条数不等于单位数。
取实际返回的完整entries数组作为entries_json，以相同days调用action=reconcile，检查matched=true。
复制该实际数组，仅把其中一条units加1，再reconcile，检查matched=false、reconciliation_mismatch；不要修改真实账本。
最后再次report/status，确认仍为3条，策略修订号没有被旧修订号覆盖。

请列中文表格：测试项目 | 实际工具结果 | 通过/失败/无法验证 | 原因。
每项显示真实version、policy_revision/revision、verdict/reason_code、recorded、单位/剩余额度及实际消息摘要（若返回）。不要输出正文，不把预期结果当实际结果。
最后说明：本插件只登记用户声明，不发送/拦截消息，不证明投递、身份或真实费用。不得宣称未执行的检查通过。
```

## 预期结果与证据

重点覆盖：中文界面和版本、只读预览、2+1单位恰好限额、下一条拒绝、重复ID幂等/冲突、离线每次1单位、回执/链深拒绝、旧修订冲突、相符/不符对账、最终历史保留。并发、损坏账本、时区/DST/边界已由源码及解包自动测试，不要求你破坏手测账本。

完成后请明确确认此版本及上述原生ZIP哈希的手测结果，并提供**当前版本关键工具操作/结果的原始全分辨率截图**。若失败，请保留错误及对应输入，不算完成。AI自测或此文档不是你的完成确认；现有AI界面截图不能替代你的原始测试截图。

限制：macOS宿主验证；Linux依赖相同POSIX/时区能力，未跑宿主集成；Windows不支持。最多10000条/64MiB账本、单次汇总500条。不提供静默时段、真实发送/计费、手机上限、群折算、force、身份/安全保证。
