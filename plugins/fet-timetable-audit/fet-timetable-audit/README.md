# 课表校验与导出 1.0.0

离线读取 FET 课表输入与已有活动安排，检查引用、工作量和时间冲突，并按教师或学生组导出 CSV/JSON。无需 FET 求解器、OR-Tools、账号或外部服务。

## 安装与启用

需要 Python 3.11+ 和支持原生 Plugin 的 WorkSwarm/openJiuwen 宿主。当前 WorkSwarm 中打开“扩展 → 我的扩展 → 创建 → 从文件创建”，选择交付说明中的 **workswarm.zip 测试包**。市场包装 ZIP 留作后续交付；两个包的运行载荷相同。

导入后检查名称和版本，通过“使用”在新 Agent 对话中启用插件，确认三个工具可用。文件必须使用后端可以访问的绝对路径；浏览器本机路径未必适用于远程后端。

| 工具 | 必填参数 | 结果 |
| --- | --- | --- |
| `inspect_fet` | `path` | 网格、引用、教师/学生工作量、问题和检查边界 |
| `verify_fet_timetable` | `fet_path`、`solution_path` | 已安排/未安排活动、时间冲突、越界和已支持的不可用时段 |
| `export_fet_timetable` | `fet_path`、`solution_path`、`format`、`output_path` | 新的 UTF-8 CSV/JSON 文件、行数、SHA-256 和校验结果；可选 `teacher`、`students` 精确名称筛选 |

`solution_path` 是含活动 Id、Day、Hour、Room 的 FET 风格活动 XML（通常为 `*_activities.xml`），不是 HTML/PDF 或课表截图。导出目录须已存在，不能经过符号链接；文件必须尚不存在且扩展名与格式一致。两个筛选条件同时提供时取交集。导出不修复冲突、不修改输入，请先阅读校验结果。

## 示例

```text
请调用 inspect_fet 检查 /绝对路径/示例学校.fet，再用 verify_fet_timetable
对照 /绝对路径/无冲突课表.xml。用中文显示实际返回的版本、问题和未检查范围。
不要把“未发现已检查范围内的问题”说成完整课表可行性证明。
```

```text
请用 export_fet_timetable 导出同一课表：teacher="张老师"，format="csv"，
output_path="/绝对路径/张老师课表.csv"。显示实际行数、文件位置和 SHA-256。
如果文件存在则停止，不覆盖。
```

`ok: true` 只代表操作完成，仍需检查 `passed`、`issues` 和 `bounded_coverage`；导出的检查结果位于 `verification`。冲突是有效检查结果，不等于工具执行失败。工具或文件不可用时应如实报错，不能编造结果。

## 范围与限制

- 仅接受本地普通 UTF-8 XML（每文件至多 8 MiB），拒绝网址、符号链接、设备/FIFO、DTD 与实体声明，并限制节点、深度、活动数量和展开工作量。
- Duration 和工作量表示**时段数量**，不保证等于钟表小时。学生不可用时段按年级/班级向小组继承。
- 实施基本时间检查和权重 100% 的教师/学生不可用时段。软约束、未支持的时间约束和空间约束列为未检查；不校验教室容量/冲突，不证明全部 FET 规则或最优性。
- 不生成、求解、优化或修复课表。`passed` 不代表完整可行性证明。
- CSV 对可能被表格软件执行为公式的文本加前导单引号；JSON 保留原始文本。字段键/协议值保留英文，说明和数据支持中文 UTF-8。
- 核心不联网、不调用模型；宿主如使用模型解释结果，仍按宿主自身配置处理对话。

## 来源

无需模型的检查入口：`python scripts/audit_cli.py --help`。可直接运行 `inspect` 或 `verify`，读取中文 JSON 结果；退出码 0 表示已检查范围无问题，1 表示发现问题，2 表示输入错误。此入口无需宿主 SDK。

基于 nispa/fet-claude-skill 1.2.1 的三个 MIT Python 模块，固定提交 `beb2e1193665deb68b8f29d7617e7bb972573d95`，经合并、修复和适配。完整许可见 `licenses/fet-claude-skill/LICENSE`；范围与修改见 `THIRD_PARTY_NOTICES.md`。不含 FET 求解器，不代表其作者官方背书。
