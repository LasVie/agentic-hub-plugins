# 设计说明 — 文档数字核对

Owner: Nguyen Trung Dung. Written 2026-11-13. Task AH-20261113-adds-up; Candidate CAND-CLD-292.

## 组成

- `adds-up/tools/adds_up.py`：一个文件，前半部分是移植的上游规则与文件提取逻辑（`process`、`render`、`grim`、`check_table`、`check_prose`、各类 `extract_*`），后半部分是本团队独立编写的两个原生工具。宿主按文件加载工具类，所以不拆成多个模块。
- `adds-up/skills/document-number-check/`：中文技能说明与检查类别，指导通读、确认线索、重算和写报告。
- `tests/port/port_core.py` 和 `tests/port/wrapper_tail.py`：生成 `tools/adds_up.py` 的两个来源（`python -B -I port_core.py <上游 adds_up.py 的 Git blob> core.py`，再 `cat core.py wrapper_tail.py`）。port_core.py 里每处替换都要求与固定提交精确匹配，不匹配就停止，所以改动范围可核查。

## 两个工具

### `adds_up_extract`

输入：`files`（1 到 10 个本机文件路径）、`max_rows`（1 到 500，默认 60）、`all_rows`（默认 false）。
行为：对每个文件调用移植的 `process()`，得到内容、线索、规则覆盖统计和说明；用中文的 `render()` 合成 `report_text`。只读，不写文件、不联网。
输出：`ok`、`tool`、`message`（给模型的中文提示：线索只是候选、要重算、不用外部事实）、`report_text`、`files`（每个文件的错误、线索数、说明数、规则覆盖）、`lead_count`、`truncated`。
错误：`INVALID_ARGUMENTS`（参数不合法）、`ALL_FILES_FAILED`（所有文件都没读成，附每个文件的原因）、`INTERNAL_ERROR`（不暴露堆栈）。个别文件读不了时 `ok` 仍为 true，该文件在 `files` 里带 `error`。
限制：单个文件 50 MB；Office 压缩包最多 5000 个条目，单条目解压后 80 MB，总共 300 MB；含 DOCTYPE 或 ENTITY 声明的 XML 被拒绝；报告超过 80000 个字符会截断并写明（`truncated` 为 true）；调用互斥执行（上游规则使用模块级全局状态）。

### `adds_up_grim`

输入：`n`（1 到 1000000 的整数）、`value`（按文档写法填的非负数，百分比可带 `%` 或 `％`）、`kind`（`percent` 或 `mean`）。
行为：调用移植的 `grim()`，判断是否存在整数个数（百分比）或整数总和（平均值）使其四舍五入后等于所报值；给出最接近的可能值。
输出：`consistent`、`decimals`、`matching_counts_or_totals`、`nearest`、`result_zh`（中文结论）。
错误：`INVALID_ARGUMENTS`（n 不是整数、value 不是数、百分比超过 100、kind 不对、多余字段）。

## 中文支持的边界（与上游规则的关系）

- 增加的是“标签与句式识别”，没有改任何算术判断。新增识别：合计/总计/总额/共计/汇总/小计/平均/均值/其中；“2026年3月5日”“星期三/周三/礼拜三”；“共 14 周/天/个月”；全角百分号与括号；“N 人中有 n 人，占 p%”“n/N（p%）”；“从 12% 升至 15%，增长 3%”；“2025年”、“1月”等标签不当作数字。
- 没有做：中文大写金额检验、“万/亿”换算、没有年份的中文日期、农历、句子里的增长率与同比环比（这些由技能指导通读时核对）。规则没有触发不等于没有问题。

## 为什么不是“纯技能”

上游本身就是一个技能加一个脚本，技能让模型在有代码工具时运行脚本。本包把脚本的两个入口做成宿主直接可见、可调用的原生工具：不依赖宿主有没有代码执行工具，参数有校验，错误有结构，输出是中文，并且能被自动测试。技能保留“通读、确认线索、重算、写报告”这部分只有模型能做的工作。
