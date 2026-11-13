# 测试报告 — 文档数字核对 1.0.0

Owner: Nguyen Trung Dung. Tested 2026-11-13, Asia/Singapore.
Task AH-20261113-adds-up; Candidate CAND-CLD-292.
Package under test: native ZIP `test-packages/adds-up-1.0.0-native.zip` (见文末的最终哈希记录)。

## 环境

- Windows 11 家庭中文版 10.0.26100；Python 3.11.9（虚拟环境 `D:/jiuwen_repos/outputs/pitwall-build/venv`）；openjiuwen 0.1.20.post1；pydantic 2.14.3。
- 环境里装有 pdfplumber，没有 pypdf（PDF 路径因此用 pdfplumber 测试，pypdf 路径没有测）。
- 没有调用任何模型（`model_calls: 0`）。没有在 WorkSwarm 前端里对话测试（`frontend_conversation: not performed`），那一步留给用户手工测试。

## 1. 自动测试（`tests/test_adds_up.py`）

命令（在仓库外的目录运行，避免 SDK 把日志写进仓库）：
`python -B -m unittest discover -s <仓库>/plugins/adds-up/tests -v`
结果：**61 个测试全部通过**（4.8 秒）。测试对象是插件载荷里的真实文件 `adds-up/tools/adds_up.py`。覆盖：

| 类别 | 内容 |
| --- | --- |
| 数字解析 | 千分位与小数逗号、`¥` `￥` `元` `人民币`、括号负数、全角百分号；“2026年3月5日”“1月”“5日”等不当作数；“2025年”“2025年度”是年份标签 |
| 中文表格规则 | 合计、总计、共计、总额、汇总、销售合计、小计、平均分、其中、合计列、全角百分号的税率行、占比列；“总计划”不当作合计；年份表头和月份标签列不求和；错误信息是中文 |
| 英文、德文标签回归 | Total、Summe 仍然能触发 |
| 中文正文规则 | 星期在日期后或前（星期三/周三/星期天）、不存在的日期、时长（周/天/个月、结束早于开始）、日号不当作时长、“N 人中有 n 人，占 p%”、“n/N（p％）”、“从 12% 升至 15%，增长 3%”；英文句子仍然有效 |
| GRIM | 百分比和平均值的相符与不可能，中文结论，最接近的可能值 |
| 文件 | CSV、Markdown、最小 docx（表格与正文）、最小 xlsx（SUM 少算、文本数字是原因、隐藏工作表）、最小 pptx、真实的中文 PDF（pdfplumber）、不支持的格式、不存在的文件、损坏的压缩包、渲染标题是中文 |
| 安全 | 文件过大、压缩包条目过多、单条目过大、总量过大都被拒绝；含 DOCTYPE 或 ENTITY 的 XML 被拒绝；工具不在目录里写任何文件 |
| 原生工具封装 | 工具卡片（名称、中文描述、必填项、不接受多余字段）；11 种非法 files 参数和 9 种非法 GRIM 参数都返回 `INVALID_ARGUMENTS`；`ALL_FILES_FAILED`；部分文件失败时仍返回其余文件；报告截断与提示；`max_rows` 与 `all_rows`；4 个并发调用结果互不串扰 |
| 包内容 | manifest、asset.json、技能 frontmatter、LICENSE 哈希与 provenance 一致、载荷里没有缓存文件 |

## 2. 仓库格式检查

- `python tools/asset_release.py check plugins/adds-up`：`format_ok: true`。
- `python tools/asset_release.py preflight plugins/adds-up/adds-up`：扫描 0 个 JavaScript 文件，0 个已知动态执行特征。

## 3. 原生 ZIP 与宿主检查（真实 DeepAgent / Runner / SkillUseRail，没有模型）

- 构建：`python tests/make_native_zip.py`，确定性 ZIP，7 个条目，181108 字节。
- 解压后逐字节与源载荷比对：一致。
- 对解压后的载荷运行 `tests/host_checks.py`（`--fixtures tests/fixtures/manual`）：
  - 两个工具 `adds_up_extract`、`adds_up_grim` 以直接可见（`direct`）的方式加载，描述含中文；技能目录被加载。
  - 经 Runner 注册的工具调用：缺 `files` 被拒（`INVALID_ARGUMENTS`）；多余字段被拒；不存在的文件返回 `ALL_FILES_FAILED` 且信息为“找不到这个文件”；GRIM 的 `n: 0` 被拒。
  - 经 Runner 对中文示例文件的真实调用：
    - `销售明细.csv`：1 条线索（合计显示 840，上面各行之和 830）。
    - `正确的预算.csv`：0 条线索（对照）。
    - `预算表.xlsx`：6 条线索（`SUM(B2:B4)` 只算到第 4 行漏掉 B5，文本形式的 18000 是 E5、C6 偏低的原因，E6 合计周围互相对不上，等等）。
    - `项目报告.docx`：6 条线索（星期四不是星期三；91 天约 13 周不是 14 周；156/240 = 65.0% 不是 62%；12% 到 15% 是 25% 相对变化；2026年2月30日不是日期；培训费 15 x 480 = 7,200 不是 7,400）。
    - `季度汇报.pptx`：1 条线索（2026年2月30日）；“三季度收入比二季度增长 12%”规则不检验，要靠技能通读（按表算是 9.6%）。
    - 多文件（含一个不存在的文件）：前两个正常，第三个带错误。
    - GRIM：n=25、平均 3.47 不可能（最接近 3.48）；n=12、33.3% 相符（4 个）。
  - 卸载后工具和技能都消失；载荷与示例文件的哈希在检查前后不变。
- 结果记录：`host-report.json`（`model_calls: 0`，`payload_unchanged: true`，`fixtures_unchanged: true`）。

## 4. 没有测、或测得不够的部分

- 没有在 WorkSwarm 前端里用真实模型对话：模型是否会在合适的时候调用工具、是否按技能写出符合格式的中文报告、会不会漏掉规则看不到的问题（句子里的增长率、正文与表格的对照），要靠用户手工测试（`MANUAL_TESTING.md`）。
- 示例 docx、xlsx、pptx 是用最小 OOXML 手工生成的，只验证了本工具能读；没有用 Word、Excel、PowerPoint 打开过。
- 没有用 pypdf 测试 PDF；pdfplumber 路径只测了单页纯文字的中文 PDF，没有测有表格线的 PDF、扫描件和多页大文件。
- 没有测过真实世界里的大文件（接近 50 MB 的文件、很大的工作表）的耗时。
- 没有运行上游仓库自带的测试（来源未审查的下载代码，见 SOURCE_REVIEW.md）。本包的测试是独立编写的；因此“与上游行为一致”只靠“规则代码 88.2% 的行保持原样”和上面的回归测试来支撑。
- 上游的计数口径：“规则覆盖了什么”里的“行内计算：4/4 相符”这类数字沿用上游的统计方式，同一表里有线索时也可能显示全部相符；它说明规则看了多少个关系，不是说没有线索。

## 5. 运行中的警告（非阻塞）

- SDK 在隔离宿主检查里报：`Failed to load description from …/SKILL.md: 'NoneType' object has no attribute 'fs'`（本团队已交付的其他插件在同一检查里有同样的警告）；技能目录仍然被加载并在卸载时移除。技能能否在 WorkSwarm 里被模型发现，要靠用户手工测试确认。
- SDK 报 `No module named 'redis'`（在线训练 rail 不可用），与本插件无关。
- pdfplumber 在读取手工 PDF 时报 `Could not get FontBBox from font descriptor`：手工 PDF 的字体描述不全，不影响文字提取。

## 6. 最终哈希记录（2026-11-13）

| 产物 | 文件 | 大小 | SHA-256 |
| --- | --- | --- | --- |
| 原生测试包（交给用户测试） | `test-packages/adds-up-1.0.0-native.zip` | 181108 字节 | 55fecb1b36179c77e24ee18c8077f2459a2beaace21b833d8ef720a7b2fd205f |
| 规范包装包（准备交付） | `releases/agent-plugin/adds-up/1.0.0/adds-up-1.0.0.zip` | 182166 字节 | 082de326fe91a49fd163fc22e09cb1f05441ba5ac4765104f9666ee8b8dcc055 |

两个包的 7 个内层载荷文件逐文件、逐 SHA-256 一致；`tools/adds_up.py` 的 SHA-256 为 4f40c9fa566a09ebe66dbaecee301201cf3e0a47ddc9d341e1842a27b99b7fc8。上述自动测试和宿主检查都是针对这套字节。用户测试之后如果载荷、名称或本地化有任何改动，需要重新构建、重新测试并重新确认。
