# 输入与交接格式

`examples/shared-home.json` 是完整可执行的虚构中文案例；`examples/full-week.json` 覆盖21次家务。原始JSON顶层：

| 字段 | 含义 |
|---|---|
| schema_version | 整数1 |
| case_id | 稳定编号，以英文字母开头，允许字母、数字、连字符、下划线，最多40字符 |
| household | 中文家庭/合住名称 |
| start_date | 有效YYYY-MM-DD日期，覆盖此日起连续七天 |
| participants | 2–6人：id、name、daily_limits、weekly_limit、unavailable_days |
| duties | 1–21次家务：id、name、day、minutes、eligible、preferred |
| notes | 可选的用户备注列表，不改变结构化限制 |

人员 `daily_limits` 必须是七个0–480整数分钟；`weekly_limit` 是0–3360；`unavailable_days` 是0–6的不重复列表。家务 `day` 为0–6，`minutes` 为1–480；`eligible` 为可承担人员编号列表，`preferred` 为其中的偏好编号列表。空偏好表示未指定，空资格表示当前无人能承担。编号唯一，不能缺字段、含未知字段或用布尔值/小数代替整数。

不要把备注中的新硬限制忽略掉。原话与结构字段有冲突时，梳理员列出并澄清；结构检查不会理解“周三临时不能做”这类自然语言。缺信息时不能以零、平均数、家庭角色或年龄代替事实。

## 实际程序入口

以下路径均相对于本专家团**实际安装根目录**。每个参数都是宿主可访问的绝对路径。输出父目录须已存在，输出子目录须不存在。

1. `agents/analyst/tools/intake.py --input --output`：生成 `intake.json`，包含原始字节摘要、案例摘要、结构化案例和分钟概况。
2. `agents/planner/tools/plan.py --input --intake --output`：读取同一原始输入和梳理报告，生成 `plan.json`。可用 `--node-limit` 设置1–500000的节点上限，默认100000。
3. `agents/verifier/tools/verify.py --input --plan --output`：只从原始案例和计划独立复算，生成 `review.json`。核验员另写自己的 `review-notes.json`。
4. `agents/leader/tools/deliver.py --input --intake --plan --review --notes --output`：核对各报告摘要并直接复算，生成 `rota.html`、`assignments.csv`、`review.json`。

均以 `python3 -B` 执行，并先运行相应脚本的 `--help` 核对实际参数；这里的参数列表说明用途，不是省略值后直接执行的命令。退出码0为该入口正常通过，1为得到有效的阻塞/未决/草稿结果，2为输入或操作错误。退出码1仍应读取报告，不能当作已通过；退出码2不能虚构报告。

## 内容复核说明

核验员在真正对照原话、分配和独立复算后写入以下字段：

- `schema_version`: 整数1。
- `case_sha256`: 当前独立程序报告中的案例摘要。
- `plan_sha256`: 当前独立程序报告中的规划文件摘要。
- `conclusion`: `pass` 或 `block`。
- `reasons`: 1–20项中文实际依据；说明遗漏、上限/偏好是否忠实、哪些问题需要用户判断。

这份说明不是自动生成的语义认证。不得从示例照抄“通过”，主理人也不得替核验员写意见。程序会对照摘要，报告或计划改变须重新审查。Leader同时保留程序核验和内容说明；任一阻塞都不能变为通过。

## 约定与证据的边界

规划结果的 `feasible` 表示找到一份满足已输入硬限制的分配；`infeasible` 是规划器穷尽本版搜索后的声明；`unknown` 是达到上限。独立程序不会把后两者认证为通过轮值，也不证明无解论断或最优性。结构通过不证明现实可执行、家庭共识、成员参与或人工实测通过。
