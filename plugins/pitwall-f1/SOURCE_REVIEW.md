# 来源与查重审查 — F1 赛事数据助手

Owner: Nguyen Trung Dung. Reviewed 2026-11-06, Asia/Singapore.
Task AH-20261106-pitwall-f1; Candidate CAND-CLD-299 (earlier retired task AH-20261030-pitwall-f1 is historical only).
Mapping: Pitwall F1 -> F1 赛事数据助手 -> pitwall-f1; repo:agent-plugin:pitwall-f1.

## 任务与差异

- 关联历史/新增资产 ID：无。候选的 2026-10-30 查重（Asset Ledger 与开发任务中无 F1/赛车赛事数据接口）结论保持；2026-11-06 开工时复查，Asset Ledger 与相关任务/PR 仍无等价资产。
- 范围变更：原选择移植上游全部 77 个工具。2026-11-06 实测上游的 71 个工具依赖 F1 官方计时流（livetiming.formula1.com，直接请求与 FastF1 均返回 401/403；FastF1 v3.9.0 发行说明称 2026-10 起官方数据接口强制登录，需要 F1 TV Access 及以上账号），其余 6 个只依赖 Jolpica。用户 2026-11-06 选择“移植 6 个 Jolpica 工具 + 新写 OpenF1 原生工具”，不要求账号。
- 复用与独立实现结论：Jolpica 部分 ported（MIT，已核实）；OpenF1 部分 native（见 NATIVE_DESIGN.md）。上游的 6 个 Jolpica 工具合并为 4 个（车手积分榜、车队积分榜和总积分榜合并为 `f1_championship_standings`，能力不变），另有 8 个 OpenF1 原生工具，共 12 个。

## 材料与授权证据

| 实际使用路径/材料 | 上游 URL 与固定提交/版本 | 适用许可与覆盖范围 | 许可文件及 SHA-256 | 复制/修改情况 |
| --- | --- | --- | --- | --- |
| `pitwall.py` 的 `CIRCUIT_NAME_MAP` 对照表（Git blob f5210d815ad65f8f05588c81e2807f6f584c5089） | https://github.com/darshjoshi/pitwall-f1 @ 04d65d386d96b85362e2eec37f39ca9018b13ee3（1.0.0） | MIT，Copyright (c) 2026 Darsh Joshi；根目录 LICENSE 覆盖仓库全部文件，文件无单独版权头 | `licenses/pitwall-f1/LICENSE`，SHA-256 44a481b6b6a342037e8f4071f32df9515db040afbc987d1c17436f8a9bf82b7c，与上游固定提交 LICENSE（Git blob df791326850d02ef05980815abef9c63743f8d96）逐字节一致 | 对照表原样复制到 `tools/pitwall_tools.py`，另增中文别名表（独立编写） |
| `pitwall.py` 中 `get_historical_results`、`get_championship_standings`、`get_driver_standings`、`get_constructor_standings`、`get_race_winners_history`、`get_track_record` 的 Jolpica 请求路径思路 | 同上 | 同上 | 同上 | 重写为结构化中文输出；修改取数规则（见下） |
| OpenF1 八个工具、校验、限流、缓存、错误处理、中文输出、`SKILL.md`、README | 无上游 | 本团队原创；NATIVE_DESIGN.md | 不适用 | 无复制 |

代码、提示词、文档、图标、字体、数据、依赖分别核查：

- 代码：仅上述两项来自上游；上游 FastF1 工具（约 47 个）、官方计时流静态工具（12 个）、SignalR 实时工具（16 个）、绘图、`decompressor.py`、`merger.py`、`signalr_client.py`、`topics.py` 均未复制。
- 提示词/文档：上游 `skills/f1/SKILL.md` 与 README 未复制，本包的 SKILL.md 和 README 独立编写。上游 README 的非官方免责声明要求已在本包 README、SKILL.md 和 THIRD_PARTY_NOTICES.md 中以自己的文字保留。
- 图标/图片/字体：上游 `assets/` 的图片和插件图标未使用；本包没有图标、图片、字体或二进制文件。
- 数据：不随包分发任何赛事数据；运行时匿名访问 Jolpica-F1 与 OpenF1。MIT 许可不授予这两个服务的使用权。
- 依赖：本包只用 Python 标准库和宿主 openjiuwen SDK，不打包依赖。上游的 mcp、fastf1、pandas、numpy、matplotlib、aiohttp、websockets 等均不使用。

## 取数规则与上游的差异（修改摘要）

- `f1_historical_results`：上游对 `…/results.json?limit=30` 取 30 条成绩行；2026-11-06 实测 2024 年该请求只覆盖 2 站（共 30 行，第 2 站被截断，来源总计 479 行），所以仅年份的查询只能看到开头两站。本包改为：年份+赛站返回该站前十；年份+车手返回整季每站成绩；其他组合返回分站冠军（最多 100 条，超出时警告）。
- `f1_race_winners_history`：上游对每一年各发一次请求并静默吞掉失败；本包用一次 `circuits/<id>/results/1.json` 请求取全部冠军，再取最近 N 个有比赛的赛季，没有失败被吞掉。
- `f1_circuit_fastest_lap`（上游 `get_track_record`）：上游把上一赛季的最快圈标成“全时赛道纪录”，口径不实。本包改名并明确“这是该年份比赛的最快圈，不是历史纪录”，并允许指定年份。
- 赛道解析：保留上游别名表；未命中时用 Jolpica 赛道列表按名称、城市、国家匹配，多个匹配时返回 AMBIGUOUS_CIRCUIT，不挑第一个。

## 服务条款与独立限制

- Jolpica-F1（https://api.jolpi.ca/ergast/f1）：Ergast 的社区延续，匿名访问，2026-11-06 实测返回 200。本包间隔 0.3 秒、每分钟 60 次，不自动重试。
- OpenF1（https://api.openf1.org/v1）：官网（https://openf1.org/ ，2026-11-06 查阅）说明免费版包含 2023 年起全部历史场次、无需认证、每秒 3 次/每分钟 30 次，并标注为个人使用；实时数据需要付费赞助。本包只读取历史数据，限制在每分钟 28 次、间隔 0.4 秒，达到上限报错而不重试，并在每次结果和 README 中提示“个人使用、勿批量抓取或商业化”。分发本插件不改变 OpenF1 的使用条款；商业或大规模使用需用户自行向服务方取得授权。待解决：向项目负责人说明该“个人使用”标注，是否影响 Hub 公开分发由其判断。
- 商标：F1、FORMULA 1 及相关标志属 Formula One Licensing B.V.。本包不含标志，仅在说明文字中以事实性方式提及，并声明“非官方、无关联”。
- 专利、商标和服务条款：独立实现不构成对这些权利的自动豁免；本审查没有对它们作出结论。

## 最终 ZIP 许可复核

- 原版权/署名及文件头保留位置：`tools/pitwall_tools.py` 头部注明改编来源与固定提交；`THIRD_PARTY_NOTICES.md`；`licenses/pitwall-f1/LICENSE`。上游文件没有单独的版权头可保留。
- THIRD_PARTY_NOTICES.md：`pitwall-f1/THIRD_PARTY_NOTICES.md`，逐项列出 Pitwall F1 的来源、版权人、复用范围、修改摘要和未复用内容。仅有一个上游。
- MIT 许可全文路径：`pitwall-f1/licenses/pitwall-f1/LICENSE`（完整文本含免责声明）。
- 上游 NOTICE：无（上游仓库根目录没有 NOTICE 文件，2026-11-06 核对固定提交文件清单：.claude-plugin、.gitignore、.mcp.json、LICENSE、README.md、assets、decompressor.py、merger.py、pitwall.py、pyproject.toml、signalr_client.py、skills、tests、topics.py、uv.lock）。
- Apache-2.0 修改文件显著声明：不适用（上游为 MIT）。
- 品牌素材、数据、依赖、服务条款：见上节；无品牌素材、数据集或打包依赖。
- 解包检查命令、文件清单与哈希核对结果（2026-11-06）：native ZIP（63131 字节，SHA-256 8d5c293156423fba68f1ae5e2c7bf554fe33d3d62e65f39f188a6f2b06cb1178）解包后共 6 个文件：README.md、THIRD_PARTY_NOTICES.md、licenses/pitwall-f1/LICENSE、manifest.json、skills/pitwall-f1/SKILL.md、tools/pitwall_tools.py，无缓存、隐藏文件、符号链接或二进制。canonical ZIP（63948 字节，SHA-256 f3567f21daf21b317f4059457a804a874ef6ffd9b718f80d080a587f29e5225a）内层 6 个文件与源码、native ZIP 逐文件 SHA-256 一致（`tests/test_pitwall_f1.py` 与 artifact.json 的 payload_sha256 核对）；LICENSE 的 SHA-256 与 provenance.json 记录及上游固定提交 LICENSE 一致。别名表与上游 `CIRCUIT_NAME_MAP` 经 AST 逐项比较完全相同（63 项）。
- AI 结论：Jolpica 部分 verified；OpenF1 部分 original。待解决：OpenF1“个人使用”标注对公开分发的影响，交项目负责人判断。
