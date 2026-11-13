# 来源与查重审查 — 网页无障碍检查

Owner: Nguyen Trung Dung. Reviewed 2026-11-13, Asia/Singapore.
Task AH-20261113-a11y-enforcer; Candidate CAND-CLD-251.
Mapping: A11y Enforcer: WCAG Accessibility Checker -> 网页无障碍检查（拟定名称，待用户确认） -> a11y-enforcer; repo:agent-plugin:a11y-enforcer.

## 任务与差异

- 关联历史/新增资产 ID：无同类。开工时（2026-11-13）按名称、描述和标签检索 Asset Ledger（872 行）、Development Tasks 和候选认领，关键词包括 accessib、wcag、contrast、a11y、aria、axe、lighthouse、无障碍、对比度，没有“对界面代码做确定性 WCAG 标记扫描并给出文件、行号、成功标准编号”或“可调用的对比度计算”的资产，也没有同类开发任务或已认领候选。候选的既有审查结论（2026-10-30，Partial Overlap - Extend Existing Capability）成立：与下列资产部分重叠，但各缺一块能力。
- 最接近的已有资产及差异：
  - wcag-audit-team（SwarmSkill，3fda724704c741a3b4b6d014753b0423@1.0.0）：五个角色按 WCAG 2.1 的 POUR 原则做合规审计，是多角色审阅流程；没有读代码文件的确定性扫描，也没有对比度计算工具，标准版本是 2.1 而不是 2.2。
  - 前端交付准入规则（Skill，885747d67e69453689a311422b9bdf34@1.0.1）：变更范围、状态归属、异步竞态、无障碍和交付前验证的通用规则，其中无障碍只是一项原则性要求，不扫描代码。
  - 设计交付团队（SwarmSkill，f29d2a1aede84adfa128ec2e78f4efac@1.0.0）：设计评审、无障碍检查、交接文档和前端实现的多角色流程，面向设计交付，不扫描代码。
  - 配色主题与色板交付（Skill，8978dad9e5cc4dd4a560f3dc624aca35@1.0.0）：从参考图提取色板并交付两两对比度证据；对比度是色板交付的一部分，不是对已有界面代码的检查，也不是可对任意颜色对调用的工具。
  - 视觉内容创意简报团队（SwarmSkill，e641421e624842a0930f6230421e9611@1.0.0）和 Scientific Visualization（Skill）：创意简报和科研图表里提到无障碍，与界面代码检查无关。
  这些都不是“静态扫描 HTML/JSX/TSX/Vue/Svelte/Astro 标记 + 对比度计算工具”，因此不构成完整功能覆盖；本审查是按名称、描述和标签的比对，没有安装试用这些资产。本包定位为代码层面的扫描与对比度工具，与 wcag-audit-team 这类审计流程互补，不替代它。
- 复用与独立实现结论：扫描规则和对比度算法为 ported（上游 MIT，已核实）；有界匹配与时间上限函数、两个原生工具的封装、输入校验、错误处理和报告格式为 native（见 DESIGN.md）。

## 材料与授权证据

| 实际使用路径/材料 | 上游 URL 与固定提交/版本 | 适用许可与覆盖范围 | 许可文件及 SHA-256 | 复制/修改情况 |
| --- | --- | --- | --- | --- |
| `a11y-enforcer/skills/a11y-enforcer/scripts/a11y_scan.py`（Git blob 798293a064dc58015fb86bcc4d5e22808a49559a，10571 字节，SHA-256 610e7ac63235bd1577d1f62d7812bea77e25872530fba9ad543cda97e5b4f87f）和 `.../scripts/contrast.py`（Git blob d71961c8cd2d8f0f184ddfd1f8e351b68a0c6530，2669 字节，SHA-256 4e8a80bef217860874b87ed696b776c82166eea8537bd9fe2e89a280e52b98f0） | https://github.com/petrovicistefan/claude-code-plugins @ 0b19c0dd919c2b5e0b992fb1610ef2ca427a357f（2026-10-07；`plugin.json` 版本 1.0.0） | MIT，Copyright (c) 2026 Stefan Petrovici；`a11y-enforcer/LICENSE` 覆盖该目录全部文件，两个脚本都没有单独版权头；仓库根目录 LICENSE 开头同为 MIT 和 Stefan Petrovici（只核对了开头） | `licenses/a11y-enforcer/LICENSE`，SHA-256 5f434c88921e448707dc3b7983a41364721fdbec7468735c26dba2200f183d04，与固定提交 `a11y-enforcer/LICENSE`（Git blob b723472340e31da4d4c4452bb6e21a893e04f480，LF，1073 字节）逐字节一致，已用 `git cat-file blob` 取原始字节比对 | 合并移植为 `tools/a11y_enforcer.py` 中“移植自上游”的一段；按 `tests/port/build_tool.py` 的精确替换改动，其余保持原样（实测约 83.8% 的上游行原样保留） |
| `a11y-enforcer/skills/a11y-enforcer/SKILL.md`（Git blob e742f7dfb50f4eab9ca1e8e968dbad8e6586af9e）与 `README.md`（Git blob 7c294748da687d7d5d9d9b54c4c1cb47a191515c）中的规则清单 | 同上 | 同上 | 同上 | 译为简体中文并改写为 `skills/web-accessibility-check/SKILL.md`，规则清单扩写为 `references/rules.md`，并为中文页面增补若干项 |
| 两个原生工具封装、有界匹配函数、输入校验、错误处理、README、测试、示例文件 | 无上游 | 本团队原创；DESIGN.md | 不适用 | 无复制 |

代码、提示词、文档、图标、字体、数据、依赖分别核查：

- 代码：上游两个脚本只用 Python 标准库；`tests/port/build_tool.py` 记录了全部改动并在任何一处替换不精确匹配固定提交时停止。固定提交的 `a11y-enforcer` 目录里没有测试文件，本包测试（`tests/test_a11y_enforcer.py`）为独立编写。
- 提示词/文档：只改编上述技能说明与规则清单；本包 README 独立编写。上游 README 末尾的作者介绍、联系方式和 logo 链接没有复用。
- 图标/图片/字体：上游 `.claude-plugin/icon.png`（Git blob 1eacc2571d12258f4d13d66ab5260d7c23c8eeea，78886 字节）未使用；LICENSE 写的是对“软件”的授权，图标这类品牌图形的授权范围不明确，所以不复用。本包没有图标、图片、字体或二进制文件。
- 数据：不随包分发任何数据；工具只读用户指定的文件，不联网、不写文件、不保存内容。示例文件（`tests/fixtures/manual/`）为本团队编写，不在 ZIP 内。
- 依赖：只使用 Python 标准库和宿主 openjiuwen SDK，不打包依赖。
- 提交历史：只取得了固定提交这一个浅克隆提交（作者 Stefan Petrovici），没有核查完整提交历史，也没有核查是否有其他贡献者；`plugin.json` 和 LICENSE 都只署 Stefan Petrovici。

## 改动与上游的差异（修改摘要）

- 全部输出改为简体中文（20 条规则的说明、对比度结论、颜色解析错误）；规则名、WCAG 编号和“错误/警告”两个级别保持上游写法。
- 增加中文识别：链接文字里的“点击这里、点这里、这里、了解更多、查看更多、更多、详情、点击查看、链接”也按“链接文字没有说明去向”提示。
- 有界匹配和时间上限：标签匹配限定在 8000 字符窗口、`<label>` 匹配限定在 2000 字符、查找结束标签最多向后看 20000 字符；每个文件 10 秒、一次调用 60 秒的时间预算；单个文件超过 1 MiB 不扫描；一次调用最多 3000 个文件、总计 200 MiB（见下节）。正常大小的文件结果与上游一致，有测试逐个标签比对。
- 文件夹遍历：扩展名不区分大小写，跳过符号链接；显式指定的文件只接受上游支持的扩展名。
- 对比度：`rgb()`/`rgba()` 数值超出范围时拒绝，而不是默默算出一个结果。
- 去掉命令行入口（`argparse`、`main`、`sys.exit`）和 `--json` 写文件的选项，两个脚本合成一个模块；新增两个原生工具、输入校验、错误处理和报告格式。
- 技能说明从“运行上游脚本”改为调用两个原生工具；只在用户要求修复时才改代码。

## 静态安全审查（上游脚本，2026-11-13）

- 只导入 argparse、json、os、re、sys（a11y_scan.py）和 re、sys（contrast.py）；没有 `eval`、`exec`、`subprocess`、网络模块、`pickle`、`ctypes`。
- 读文件：`open(path, encoding="utf-8", errors="replace").read()`，没有大小上限；写文件：只有 `--json` 选项会 `open(a.json, "w")` 写出问题清单——本包去掉了该选项，工具不写任何文件。其余输出到标准输出。
- 发现的缺口及本包的处理：
  1. 正则回溯：`TAG_RE` 对整个文件匹配，大量未闭合的标签会使耗时随文件长度二次方增长。用自己写的一次性探测脚本（不运行上游脚本）在上游的正则上实测：2 万字符的畸形输入，`<div a=b ` 重复耗时 2.2 秒，`<a b={` 重复 8.2 秒，`<img ` 重复 7.6 秒，`<label ` 重复 5.6 秒；10 万字符的同类输入在 5 分钟内没有跑完。`inner_text` 查找结束标签、`label_for` 收集也有同样的向后整段扫描。本包改为有界窗口和时间预算（见修改摘要），并有测试：6 万次 `<div a=b ` 的畸形文件在 1 秒预算下被丢弃并说明，同一调用里的正常文件仍被扫描。
  2. 没有文件大小上限（改为 1 MiB），没有文件数量和总大小上限（改为 3000 个、200 MiB）。
  3. 文件夹遍历会读取符号链接指向的文件（改为跳过符号链接）。
- 没有直接运行上游仓库里的脚本：它来自下载的未审查来源，运行前先做了上述静态审查，之后只对已审查、已移植进本仓库的副本运行本团队自己的测试。

## 与上游行为一致、已知的限制（保留，不当作缺陷修改）

- 行内样式的 `outline: none` 在 `.html`、`.vue`、`.svelte`、`.astro` 文件里会被“行内样式”和“CSS 文本”两项检查各报一次。
- 属性名一律转小写比较，所以 JSX 的 `onClick`、`tabIndex` 也能识别；组件（大写开头标签，`Image`、`NextImage` 除外）里的问题看不到。
- 一个标签超过 8000 个字符、花括号嵌套超过两层的属性，可能识别不到。
- 对比度只识别 `#rgb`、`#rgba`、`#rrggbb`、`#rrggbbaa`、`rgb()`、`rgba()` 和 20 个基本英文颜色名；`hsl()` 等不识别，会明确报“无法识别的颜色”；背景色的透明度被忽略。
- 这些限制已写进 README 和 `references/rules.md`。

## 服务条款与独立限制

- 无外部服务、无账号、无网络访问。
- 商标/署名：本包不是上游作者发布或认可的版本——README 明确写明，THIRD_PARTY_NOTICES.md 写明不授予上游名称、图标或商标的权利、也不表示上游作者认可本插件；保留 Stefan Petrovici 的版权与 MIT 全文。不使用上游图标和作者介绍。
- 效果：本包只做静态扫描和对比度计算，没有发现问题不等于符合 WCAG，也不能替代审计。
- 专利、商标和服务条款：移植与独立实现都不构成对这些权利的自动豁免；本审查没有对它们作出结论。WCAG 是 W3C 的标准，本包只引用成功标准编号，不复制标准原文。
