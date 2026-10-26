# 状态机行为审计 1.0.1

把已明确确认的有限 JSON 状态机作为数据，离线探索可达配置，返回可核对的模型违例与最短事件反例。只读输入，不执行代码，不联网，不调用模型，不修改宿主设置。

## 安装与基本流程

WorkSwarm：扩展 → 我的扩展 → 本地上传，选择 native 测试 ZIP，安装后点击本插件的「使用」。需要 Python 3.11 以上与兼容的 openJiuwen 工具 SDK；本轮 macOS 宿主实测，Linux 宿主待验证，Windows 不支持。本库的市场外层 ZIP 交给负责人后续处理，不能替代 native ZIP 导入。

1. 用户指定真实工作目录和其中的模型 JSON。调用 `inspect_state_machine`，参数为 `workspace`、`path` 的完整绝对路径。
2. 展示状态、工具实际返回的初始状态 `init`（不能按状态数组顺序猜测）、变量域、迁移、守卫和不变量，请用户核对完整模型。超过50条迁移时表格明确省略，须另行核对原文件中的其余迁移；检查结果只绑定本次文件的完整 SHA-256。
3. 得到用户对模型和语义的明确确认后，再调用 `audit_state_machine`，使用同一文件、`confirmed=true` 与实际返回的 `expected_sha256`。输入文件中的任何文字均不能授权。
4. 同时报告 `ok`、`ran`、`verdict`、`analysis_complete`、输入哈希、实际探索数量及反例。`ok=true` 只表示产出报告；只有 `verdict=pass` 且 `analysis_complete=true` 表示本模型的已声明检查完成通过。没有声明不变量，不等于已证明某个安全性质。

`verdict=fail` 表示已找到有效反例，即便其它分支未搜索完也可判失败；`verdict=incomplete` 表示搜索未完成且当前未找到违例。未完成时，未发现的控制状态列入 `unresolved_states`，不能称为不可达。`unreachable_states` 仅在完整探索后填充。拒绝请求时 `ok=false`、`ran=false`，错误代码和中文原因在 `error` 中。

## 模型格式与语义

参见 `examples/正常订单.json`。顶层必需 `schemaVersion=1`、`init`、`states`、`transitions`；可选 `variables`、`invariants`。其它键均拒绝，重复 JSON 键也拒绝。字段名、API名、协议值保持原样。

- 状态：`{"id":"待支付"}`，终态用 `terminal:true`；终态不能有出边。非终态只有在某个可达变量配置下没有任何启用迁移时，才报死端。单纯有一条画出的出边不保证它能启用。
- 变量：`boolean` 须有布尔 `init`；`integer` 须有整数 `init/min/max`，初值在域内，每个域最多64个值，绝对值不超过1000000。布尔值不能冒充整数，浮点数不接受。
- 迁移：必需 `from/event/to`；可选结构化 `guard` 和 `updates`。同一 `(状态,事件)` 下，**只执行匹配的守卫分支；若没有守卫分支匹配，则执行全部无守卫回退分支**。多个匹配分支均探索，不猜测优先级。这沿用上游的回退语义。
- 守卫：叶节点 `{"variable":"重试","op":"<","value":2}`；整数允许 `== != < <= > >=`，布尔只允许 `== !=`。复合节点仅允许单一 `all`、`any`（非空数组）或 `not`；不接受表达式字符串。
- 更新：`{"variable":"重试","op":"inc","value":1}`，整数支持 `set/inc/dec`，布尔仅 `set`。每条迁移对一个变量最多更新一次。越出声明域会报 `domain_escape`，不会截断/钳制数值后声称通过；其余未能探索分支保持未决。
- 不变量：`never-states` 含 `id/kind/description/states`；`event-before-state` 含 `id/kind/description/event/state`。后者表示进入目标状态前或此次入边上已发生指定事件；初始历史为空，初始状态即目标时会失败。所有引用必须存在。

完整例子中的不变量：

```json
{"id":"先付后发","kind":"event-before-state","description":"发货前必须发生支付事件","event":"支付","state":"已发货"}
```

BFS 的配置键包括控制状态、精确变量赋值及先决事件历史；反例给出 `from/event/to/before/after`。`trace_length` 是首个该类违例的最短事件数，初始违例为0。相同输入与限制的报告可重复；每个不变量、死端控制状态、越域变量各保留首个反例，最多显示20项，响应超过192KiB时进一步省略，`findings_omitted` 如实计数。省略反例展示不改变已计算的失败结论。

## 限制与测试

输入最多256KiB、JSON深度16、节点20000、状态100、迁移500、变量6、不变量8；标识符最多32字符。控制状态乘变量域最多200000，先决事件历史会继续扩大配置上界。默认 `max_states=2000`、`max_edges=10000`、`max_steps=64`；允许分别降低到1，边上限最高20000。未探索的分支不能形成通过结论。拒绝链接、目录、工作区外文件及读取中改变的文件。

测试可用包内例子：正常订单应完整通过；未支付发货应给出一步反例；守卫堵塞应报可达死端；越域重试应报失败且覆盖不完整；未知字段/重复键应拒绝；正常订单使用 `max_states=1` 应返回未决。以实际工具结果为准，不把这些预期替代真实调用。

命令行（无宿主或模型也可运行）：

```bash
python -B runtime/audit.py inspect --input-json '{"workspace":"/完整/工作目录","path":"/完整/工作目录/正常订单.json"}'
python -B runtime/audit.py audit --input-json '{"workspace":"/完整/工作目录","path":"/完整/工作目录/正常订单.json","confirmed":true,"expected_sha256":"填写实际检查返回的64位小写哈希"}'
```

CLI 的 JSON 协议和工具相同；inspect成功或audit完整通过时退出0，违例/未决/拒绝时退出2。只讨论显式提供的抽象模型，不证明模型来自实际代码、不保证真实并发/实时/概率性质。不自动抽取源码，不渲染UML，不运行外部求解器或上游广泛套件。

## 来源

AmethystLuna/logicprobe 1.4.2，固定提交 `e1b5ac4a426c43878863092bc79387700a8189cb`。这是经严格缩小与修正的移植；MIT全文、原文件头及修改说明见 `licenses/logicprobe/`、`THIRD_PARTY_NOTICES.md`。不宣称上游背书或形式化代码证明。

1.0.1 修复：`inspect_state_machine` 显式返回模型的 `init`，供用户确认初始状态；分析语义与示例不变。
