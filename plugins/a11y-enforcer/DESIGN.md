# 设计说明 — 网页无障碍检查

Owner: Nguyen Trung Dung. Written 2026-11-13. Task AH-20261113-a11y-enforcer; Candidate CAND-CLD-251.

## 组成

- `a11y-enforcer/tools/a11y_enforcer.py`：一个文件，由三段组成：文件头部（本团队编写的有界匹配与时间上限函数 `iter_tags`、`collect_label_for`、`read_source`），中间是移植的上游规则（`scan_file`、`iter_files`、`parse_color`、`ratio`、`verdict` 等），末尾是本团队独立编写的两个原生工具。宿主按文件加载工具类，所以不拆成多个模块。
- `a11y-enforcer/skills/web-accessibility-check/`：中文技能说明和规则一览，指导先扫描、再算对比度、再读代码补查扫描看不到的部分、最后分级汇报。
- `tests/port/header.py`、`wrapper_tail.py`、`build_tool.py`：生成 `tools/a11y_enforcer.py` 的来源（`python -B -I build_tool.py --upstream <两个上游 Git blob 所在目录> --out <输出文件>`）。`build_tool.py` 校验上游 blob 的 SHA-256，每处替换都要求与固定提交精确匹配一次，不匹配就停止，所以改动范围可核查。

## 两个工具

### `a11y_scan`

输入：`paths`（1 到 10 个文件或文件夹路径）、`errors_only`（默认 false）、`max_issues`（1 到 500，默认 100）。
行为：展开路径（文件夹按字典序遍历，跳过 node_modules、dist、build 等目录、隐藏目录和符号链接），对每个文件调用移植的 `scan_file()`，汇总问题；`report_text` 是中文报告，`issues` 是结构化列表（file、line、rule、wcag、level、message）。只读，不写文件、不联网。
输出：`ok`、`tool`、`message`（给模型的中文提示：静态扫描的盲区、没有发现问题不等于合规）、`report_text`、`summary`（扫描文件数、错误数、警告数、按规则计数，覆盖全部问题）、`issues`（最多 `max_issues` 条）、`issues_truncated`、`skipped`（没扫描的路径及原因）、`scan_complete`。
错误：`INVALID_ARGUMENTS`、`ALL_PATHS_FAILED`（所有路径都找不到）、`NO_FILES`（没有支持的文件）、`NO_FILES_SCANNED`（找到了文件但都没能扫描）、`INTERNAL_ERROR`（不暴露堆栈）。个别文件超过大小、超时或读不了时 `ok` 仍为 true，该文件出现在 `skipped` 里，并且 `scan_complete` 在超时或超过数量/时间上限时为 false。
限制：单个文件 1 MiB；每个文件 10 秒、一次调用 60 秒；一次调用最多 3000 个文件、总计 200 MiB；一个标签 8000 字符、`<label>` 2000 字符、结束标签查找 20000 字符。没有全局状态，调用可以并发。

### `a11y_contrast`

输入：`pairs`（1 到 50 个对象，每个只含 `foreground` 和 `background`，各最长 64 个字符）。
行为：对每一对调用移植的 `parse_color()`、`ratio()`、`verdict()`；带透明度的前景色按背景色混合，背景色的透明度被忽略并在 `notes` 里说明；显示值四舍五入到两位，达标按精确值判断，两者不一致时在 `notes` 里说明。
输出：`ok`、`tool`、`message`、`report_text`、`pairs`（每对的 ratio、ratio_exact、aa_normal、aa_large、aaa_normal、aaa_large、ui_components、result_zh、notes，或 error）、`all_aa_normal`。
错误：`INVALID_ARGUMENTS`、`INVALID_COLOR`（所有颜色都无法识别）。个别颜色无法识别时 `ok` 仍为 true，该项带 `error`。

## 中文支持的边界

- 增加的是中文输出和“链接文字意思不明”的中文词表，没有改任何规则的判断条件。
- 没有做：对中文文案本身的检查（例如 alt 文本写得好不好）、对运行时渲染结果的检查。这些由技能指导读代码和用浏览器工具补查。

## 为什么不是“纯技能”

上游本身就是一个技能加两个脚本，技能让模型在有代码工具时运行脚本。本包把两个脚本做成宿主直接可见、可调用的原生工具：不依赖宿主有没有代码执行工具，参数有校验，错误有结构，输出是中文，上游对畸形输入的二次方回溯有了上限，并且能被自动测试。技能保留“读代码补查、给出最小修改、分级汇报”这部分只有模型能做的工作。
