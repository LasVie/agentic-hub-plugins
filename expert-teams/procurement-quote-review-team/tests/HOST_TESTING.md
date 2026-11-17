# 宿主集成测试边界

单独执行宿主 SDK / `register_group.py --validate-only` 时，应将进程工作目录设置为本团队 `.local/` 下的专用验证目录，并设置独立数据路径。实际 SDK 的日志初始化可能在当前目录创建 `logs/`；仅设置数据目录不会改变这个日志位置。不要让验证日志落在仓库根目录或其他人的工作区。构建中两次只读加载产生的日志已移入本团队 `.local/loader-validation-logs/` 保留。

`host_fixture.py` 只为测试启动独立 WorkSwarm 数据目录和本机脚本化模型端点；不在交付包中。它从宿主原生工作区模板初始化配置，不复制其他实例的模型配置或凭据。默认端口为 HTTP 6515、WebSocket 29515、Agent 28515、Gateway 30515、测试模型 6516；任何端口占用都停止启动。

`test_host_integration.py` 通过真实 WebSocket 管理接口导入、安装并查询 AgentGroup。显式 `--run` 只允许连接本测试实例，发起实际团队任务和真实包内脚本调用。模型响应由夹具预先编排，因此只能验证成员创建、委派、工具调用、任务完成和文件交付，不能证明模型理解、采购判断质量、自然语言遵循、真实独立审查效果或优于单专家。

测试代码、准备步骤和夹具不得加入原生 ZIP。原有 `6411` 实例及其模型设置不参与脚本化聊天。人工测试需使用真实模型、独立检查原始输入与输出、验证四个成员实际参与，并由用户确认；模型调用费用须事先授权。

命令示例（将占位路径替换为本机实际路径）：

```text
<宿主Python> -B tests/host_fixture.py prepare --host <JiuwenSwarm目录> --runtime <新的隔离目录>
<宿主Python> -B tests/host_fixture.py plan --host <JiuwenSwarm目录> --runtime <隔离目录> --payload <解压的原生包目录> --case <合成案例JSON> --installed-payload --scenario excluded-uncertainty
<宿主Python> -B tests/host_fixture.py start --host <JiuwenSwarm目录> --runtime <隔离目录>
<宿主Python> -B tests/test_host_integration.py --native <原生ZIP> --runtime <隔离目录> --run --record tests/records/1.0.1/host-excluded-uncertainty.json
<宿主Python> -B tests/host_fixture.py stop --runtime <隔离目录>
```

启动前必须在隔离目录准备 `plan.json`，记录本次合成测试中各角色执行的显式命令和交付路径。不得填入真实账号数据或模型服务密钥。每个测试使用新目录，失败证据保留，不自动删除、重置或冒称通过。

`--installed-payload` 先用解压包生成合成案例摘要，但成员实际命令指向管理接口随后安装的真实专家团 Skill 脚本；开始聊天前必须完成导入和安装。技术、商务和复核角色各自先执行原始案例检查，再写入已知合成评估；夹具不会把预编排评估冒称独立模型判断。

仅在同一隔离实例中执行导入查询、未开始聊天且已安装包逐文件字节相等时，可使用 `--reuse-installed` 复用安装。已有交付或事件记录时 `--run` 会拒绝重跑，避免把旧结果误算为本次成功。管理 RPC 结果、真实模型请求/工具返回、成员任务完成状态与文件结果分别保存在隔离目录；`host-result.json` 明确记录脚本化判断来源及 `human_testing_passed: false`。不得把原始请求日志或测试实例状态加入交付 ZIP。

已完成的真实执行可使用 `--reuse-installed --verify-recorded-run` 重新检查保留的请求、工具返回与文件绑定，不再发起聊天或模型请求。这个模式会标记为记录回读，不伪装成新一轮执行。正式摘要见 `records/host-integration.json`；失败尝试留在 `.local/host-smoke-1`，早期预检查包成功记录留在 `.local/host-smoke-2`，最终包实际运行证据留在 `.local/host-final`。早期夹具曾在建队前创建任务；修正为宿主要求的 `build_team` 顺序后通过。最终包的技能加载返回为渲染后的目录说明，测试断言也据实际返回修正；这些只改变测试代码，没有改变交付 ZIP。

## v1.0.1 范围与未知项回归

旧版 `records/host-integration.json`、`.local/host-final`、人工运行记录和原始 ZIP 都保留为 v1.0.0 证据，不用于证明 v1.0.1。新版使用两个全新运行目录，依次停止各自精确记录的进程后再复用测试端口：

1. `--scenario excluded-uncertainty`：三个真实成员各自执行安装包脚本并保存 `schema_version: 2` 报告；技术与复核均保留丙的交期 `fail`、质量 `unknown/null`、丙范围的评估问题，各角色另有明确的说明 `notes`。真实完成回执将这些边界传给复核员；实际 `deliver` 应保留说明和警告，并按既定规则得到乙、甲排序，丙不参与基准。
2. `--scenario eligible-uncertainty`：仅在新的私有合成输入副本，将乙来源第 5 行改为“技术质量等级：未提供可核对的质量说明。”，保留交期和费用行，重新运行实际 `inspect` 得到摘要；不修改原始夹具。技术与复核报告一致保留合格乙报价的质量 `unknown/null` 与乙范围的评估问题。实际交付必须 `clarification_required`，无排名；不能因为修正了丙的处理而忽略真正影响可比报价的未知项。

每轮均重新核对当前 ZIP 摘要、四成员 AgentGroup、共享 Skill 加载、真实安装脚本路径、三份报告与交付快照字节一致、完成回执、说明保留和实际排名边界。摘要分别存入 `records/1.0.1/host-excluded-uncertainty.json` 与 `host-eligible-uncertainty.json`。预编排的角色报告与文字判断始终是夹具；真实宿主调用不等于模型语义判断或人工验收通过。

上游说明实际通过复核员认领任务时的工具返回交接，断言检查这个真实返回，不把任务正文或最终角色 JSON 代替交接证据。测试等待 Leader 的 `deliver` 工具成功回执再结束，避免仅看到中途创建的 HTML 就提前报告成功。首轮说明交接断言曾误查用户消息字段；已依据真实工具返回修正，并回读保留执行，不重放已完成模型调用。

后续专门增加两阶段复核协议检查，保留上述早期单阶段运行作为运行通道证据，不据此证明“先独立后对照”。新夹具有四项实际任务：技术、商务、无上游依赖的 `fixture-verifier-independent`，以及依赖前三项的 `fixture-verifier-review`。独立任务只运行原始案例检查并先保存 `verifier-independent.json`；复核任务实际读取这个文件及两份初稿，保存三文件 SHA-256 清单后写最终复核。夹具控制技术/商务完成回执等到独立任务完成，便于验证独立记录前没有收到上游总结；这不是宿主盲审隔离保证。新摘要为 `records/1.0.1/host-independent-positive.json` 与 `host-independent-negative.json`。检查真实任务依赖、独立完成与复核开始顺序、文件时间、实际读取文件摘要和原始记录保留；固定判分仍不证明语义独立。

最终以 `host-independent-source-positive.json` 和 `host-independent-source-negative.json` 为准：独立快照的说明明确为“仅依据原始来源形成，尚未读取技术或商务初稿”，不在独立阶段写入对初稿的一致性结论；实际复核阶段读取三份文件后才形成最终记录。上述较早两阶段记录仍保留，但其独立夹具说明曾过早复用“初稿一致”的预置文字，现按 `host-evidence-index.json` 标为已被替代。索引保存当前与旧证据摘要，不改写旧执行历史。切换实例时先等待精确拥有的进程完成停止；启动端口仍占用时拒绝复用。没有因端口/就绪失败重放已完成的聊天。

宿主本地导入接口拒绝同名/同标识覆盖，未发现原地更新接口。现有 `agent_groups.uninstall` 会移除定义并保留团队显示身份，但共享 Skill 的原路径会改变，不能据此保证旧会话可复现。本轮先检查 6411：没有本团旧会话，用户截图中的原团队会话位于另一个 6393 实例。完整备份本团原安装文件与旧 ZIP 后，通过授权的原生管理接口 uninstall → import_local → install 更新 6411；核对既有会话 ID 和历史摘要未变、16 个安装文件等于精确新 ZIP。见 `records/1.0.1/manual-host-upgrade.json`。6393、原始人工报告及旧 ZIP 未改动。升级不修改宿主源码、不直接写安装目录、不触发模型；用户须新建本版会话复测，不保证旧版会话可在新定义下复现。
