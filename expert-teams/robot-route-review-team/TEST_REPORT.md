# 多机器人路径规划复核专家团 1.0.0 测试记录

2026-11-17；任务 `AH-20261117-robot-route-review-team`；负责人 Cai Zhenze；Candidate Not Applicable。
状态：Build，等待用户对当前包人工测试及原始截图；没有人工通过记录。

## 已完成的功能验证

- Python 3.10 源码 34 项定向回归通过；对精确原生 ZIP 解压的相同 34 项也通过。原始输出：`tests/records/source-tests.txt`、`extracted-tests.txt`。
- 会车位案例由真实CBS计算，独立回放 `route_valid`，到达步数合计7、最晚4。14个固定种子的小实例与独立联合状态 Dijkstra 对照一致；另测3机器人、4方轮换、静止目标。
- 负例包括同格、反向换边、穿墙/跳步、错误起终点、到达后离开、永久终点占用、遗漏机器人、非法数值、篡改代价、陈旧案例/地图/模型/计划、报告分歧、真实模型问题、信息说明、不覆盖与符号链接拒绝。完整有限时域搜索与高层/低层限额停止分开验证。
- 全流程通过实际 CLI 写入/序列化/读回五份证据并交付中文 HTML、CSV、JSON、说明和输入快照；逐一复核所有交付摘要，测试 HTML 数据转义、UTF-8 和 CSV 行数。
- JSON Schema 自检及5份实际宿主输入/报告通过；跨字段/身份/摘要/路径语义由运行时严格检查，不由 Schema 单独证明。见 `tests/records/schema-validation.json`。
- 现有 Node 对提取的 viewer 脚本 `--check` 通过；实际浏览器 file: URL 被安全策略拒绝，没有绕过。HTML视觉、动画与下载交互尚待人工检查。见 `viewer-check.json`。

## 正式打包与实际加载

原生23个文件；根 `package_type: agent_group`，Leader+3名成员均为完整 `agent_template`；规划/回放私有技能分别仅挂载到该成员，root共享 `route-workflow`。无宿主文件、模型配置、缓存、凭据、测试代码或第三方实现进入包。

官方 `openjiuwen-agentichub 0.0.1` CLI，固定来源 `c8ee4ef44be0453470114aa5a19f4e1017462907`：干净staging的 `validate`、`pack` 均通过。实际宿主 creator `register_group.py --validate-only` 返回 `RESULT: PASS (4 agents)`，并使用真实 SDK `load_agent_group_package_bundle`。运行时安装23文件与原生 ZIP/source逐字节一致。CLI/包格式检查不替代路径功能或团队合作验证。

动态JS preflight 对payload、原生与规范ZIP通过；平台扫描器报告0个`.js`文件，不能据此声称扫描了HTML内联脚本。内联脚本另行语法检查与安全转义测试；不存在动态执行或外部资源引用。

原生 SHA-256：`ab0cc094891ebd6ae5ee4ea5efa14e0f49b7961b3ddedddc5a5bfd923ae7be89`。
规范包装 SHA-256：`447d455cba0c4652090af5f30ebde75acafd041e9f2fc1c4031bf4376e77a22c`。
确切打包清单和审查/报告摘要见 `release/1.0.0/artifact.json`。

## 真实宿主通道（固定本机响应，非真实模型判断）

JiuwenSwarm checkout `local/connector-import`，提交 `fa91394e42a7af731424222db82b02351e694de9`，保留其已有本地改动。本资产不修改宿主、依赖、其他团队或模型设置。专用6555/6556/28555/29555/30555端口、全新本团队状态、固定本机响应，不拷贝其他实例凭据。4轮各自保留请求/事件/工具返回；精确PID停止自己的进程后再运行下一轮。

| 实际宿主案例 | 最终交付 | 独立回放 | 已观察边界 |
| --- | --- | --- | --- |
| 会车位正常输入 | reviewed | route_valid | 合计7/最晚4，真实任务与文件交接 |
| 在专用候选副本注入中心格碰撞 | blocked | route_invalid | 顶点冲突被发现，不被导出为通过 |
| 原始模型审查保留真实结构化问题 | blocked | route_valid | 路径合法也不能消除未决建模问题 |
| 高层展开限额1 | search_limit | no_route_to_verify | 无虚构路径，不称无解 |

每轮验证四个真实成员、五个任务阶段、共享/私有Skill读取、实际命令退出、完成回执、真实上游交付以及快照摘要；复核员先保存只含原始模型的审查，再接收规划候选，文件时间顺序一致。`tests/records/host-evidence-index.json` 及各轮摘要保存精确包摘要与结果；原始数据在 `.local/host-*/`。加强交接断言后只回读已有执行，没有重放完成的聊天。

固定响应证明实际宿主调度/工具/文件通道，不证明自然语言遵循、语义独立、盲审、真实建模质量、团队优于同预算单专家或用户验收。真实模型合作效果待用户自行授权测试；没有发起付费调用。

## 人工界面与待测事项

本机6555前端访问成功、WebSocket/RPC实际工作；观察到「我的专家→专家团」原生四成员详情、中文README、版本1.0.0与上传文件创建对话框。6411人工入口HTTP200及WebSocket管理接口工作，精确23文件通过支持的import_local/install安装；浏览器刷新后确认原生四成员、v1.0.0、中文说明与原采购团同时可见。自动文件选择器超时，完整GUI上传未验证；管理RPC安装不算GUI上传或用户测试。默认模型仍为disabled-local-test，未修改配置、未调用真实模型。

初次安装后的磁盘检查误用了历史research数据根而找不到目录；安装已成功，未重复导入。依据实际6411进程dotenv中的数据根纠正只读检查后，23文件完整匹配原生ZIP。实际安装位于既有JiuwenSwarm local-only/connector-import/data/domain/.agent_teams/agent_groups/local/，属于支持的运行态安装而非源代码改动。详见manual-host-import.json。宿主git diff字节摘要前后相同，其他资产/验收记录未更改。

人工入口与说明见 `MANUAL_TESTING.md`；HTML视觉/播放/暂停/滑块与真实模型语义审查未验证。用户须核对模型、成员任务、独立复核、路径/CSV及负例后明确确认，并提供原始截图。任何包内字节或最终ZIP变化都需重建并重新确认。未提交、推送、创建PR/Release或操作Hub；项目负责人验收及Asset Ledger均未改变。

模型成本：正例固定响应使用29次本机协议请求，费用为零；这不是实际模型用量测量，不能据此承诺单专家对照优势或固定成本。真实模型与用户人工测试仍待另行授权/操作。
