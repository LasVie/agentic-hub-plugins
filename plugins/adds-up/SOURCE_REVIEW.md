# 来源与查重审查 — 文档数字核对

Owner: Nguyen Trung Dung. Reviewed 2026-11-13, Asia/Singapore.
Task AH-20261113-adds-up; Candidate CAND-CLD-292.
Mapping: Adds Up -> 文档数字核对 -> adds-up; repo:agent-plugin:adds-up.

## 任务与差异

- 关联历史/新增资产 ID：无同类。开工时（2026-11-13）按名称、描述和标签检索 Asset Ledger（872 行，其中 2026-10-23 之后登记 263 行）和 Development Tasks（开工前 78 个任务行），关键词包括 grim、add up、arithmetic、totals、percentage、numerical conflict、数字、加总、合计、核对、勾稽、对账、一致性、百分比、banknote 等，没有“核对文档里的合计、百分比、日期、公式范围是否对得上”的资产，也没有同类开发任务或已认领候选。候选的既有审查结论（2026-10-22，Partial Overlap - Extend Existing Capability）成立：与下列资产部分重叠，但各缺一块能力。
- 最接近的已有资产及差异：
  - evidence-digest（Skill，3cbddcad49f1496a90d20f7af5acca3a@1.0.0）：提取带位置的证据并报告“同一定义下的数字冲突”；不做合计与分项、百分比与个数、星期与日期、时长、公式范围、GRIM 这些确定性检验，也没有读 Office/PDF 文件的工具。
  - corporate-finance-analysis（Plugin，fa6d49332f7c4eb7bdae8697f114f24a@1.0.0）：企业现金流、估值和勾稽模型，输入是财务模型，不是对任意文档做数字一致性核对。
  - 月结差异核对、科研双源数据对账、多表合并与对账（Skill）：分别核对试算平衡表、两份 CSV 的逐条规则对账、多表合并，都是针对指定数据结构的对账，不读 Word/PPT/PDF，也不做文字里的百分比、日期、时长检验。
  - 自一致性校验（Skill）：比较同一问题的 N 个回答是否互相矛盾，不是文档数字。
  这些都不是“多种文件格式 + 合计/百分比/日期/公式范围/GRIM 的确定性检验”，因此不构成完整功能覆盖；本审查是按名称、描述和标签的比对，没有安装试用这些资产。上游自身也把“引用已有的证据提取与冲突检验入口”和“新增的算术、日期、单位、公式检验”分开，本包保持这个分工，不替代 evidence-digest。
- 复用与独立实现结论：规则、数字解析和文件提取逻辑为 ported（上游 MIT，已核实）；两个原生工具的封装、输入校验、并发保护、输出截断为 native（见 DESIGN.md）。

## 材料与授权证据

| 实际使用路径/材料 | 上游 URL 与固定提交/版本 | 适用许可与覆盖范围 | 许可文件及 SHA-256 | 复制/修改情况 |
| --- | --- | --- | --- | --- |
| `skills/check/scripts/adds_up.py`（Git blob e4cf7d0f2351a7f49ce96dad0d487667b213e27c，122101 字节，SHA-256 4b62934a07eae6c73b661661fe967a76d2e227a0595fac48e35adb71a938f20a） | https://github.com/Aphro4266/adds-up @ 501af9e40e709780849cbedfd73af45d1eb7c6bd（2026-10-24；`plugin.json` 版本 0.2.0） | MIT，Copyright (c) 2026 Murat Matur；根目录 LICENSE 覆盖仓库全部文件，该文件没有单独版权头 | `licenses/adds-up/LICENSE`，SHA-256 8e64120969b71eee850ba6cfccf0245dd0c72cb7c8118dc7665f38a37c00b501，与固定提交 LICENSE（Git blob 9f1615b1aabc1df5a22b62aa0a1ddf8b86afa477，LF，1068 字节）逐字节一致，已用 `git cat-file blob` 取原始字节比对 | 移植为 `tools/adds_up.py` 前半部分；按 tests/port/port_core.py 的 123 处精确替换改动，其余保持原样（实测约 88.2% 的上游行原样保留） |
| `skills/check/SKILL.md`（Git blob 021aabf7c1da37825260408d281132dca3498835）与 `skills/check/references/checks.md`（Git blob 0cd1c3bf0e19384706ddd48c7bc8e6fd4b9b5446） | 同上 | 同上 | 同上 | 译为简体中文并改写为 `skills/document-number-check/SKILL.md` 和 `references/checks.md`，并为中文材料增补若干项 |
| 两个原生工具封装、输入校验、并发保护、输出截断、README、测试、示例文件 | 无上游 | 本团队原创；DESIGN.md | 不适用 | 无复制 |

代码、提示词、文档、图标、字体、数据、依赖分别核查：

- 代码：上游脚本只用 Python 标准库；`tests/port/port_core.py` 记录了全部改动。上游测试 `tests/test_adds_up.py` 没有复制，本包的测试（`tests/test_adds_up.py`）为独立编写，但参考了上游测试想要覆盖的规则范围。
- 提示词/文档：只改编上述技能说明与检查类别，并参考上游 `README.md`（Git blob 3594d96eec2e0fc54161bc776d49657a8b54a22f）里的功能描述；本包 README 独立编写。
- 图标/图片/字体：上游 `.claude-plugin/icon.png` 未使用；LICENSE 写的是对“软件”的授权，图标这类品牌图形的授权范围不明确，所以不复用。本包没有图标、图片、字体或二进制文件。
- 数据：不随包分发任何数据；工具只读用户指定的文件，不联网、不写文件、不保存内容。示例文件（`tests/fixtures/manual/`）为本团队编写，不在 ZIP 内。
- 依赖：只使用 Python 标准库和宿主 openjiuwen SDK，不打包依赖；PDF 文字提取需要环境里已有 pdfplumber 或 pypdf（可选，没有时工具明说）。

## 改动与上游的差异（修改摘要）

- 增加中文支持（合计/小计/平均/其中等标签，“2026年3月5日”日期，星期三/周三，“共 14 周”时长，全角百分号和括号，“N 人中有 n 人占 p%”，“从 12% 升至 15%，增长 3%”，年份/月份标签不当数字，“总计划”不当合计），英语、德语、土耳其语、法语、西班牙语的识别全部保留。
- 全部输出改为简体中文；位置标签和线索类型名保持上游写法。
- 新增安全上限和 XML 声明拒绝（见下节）。
- 命令行入口改为可调用函数；新增两个原生工具、输入校验、并发保护（上游规则用全局变量 STATS、FMT 记录当前文件，同一时刻只允许一个调用）、输出截断和错误处理。
- 技能说明从“运行上游脚本”改为调用两个原生工具；报告用语固定为中文（错误、冲突、待确认）。

## 静态安全审查（上游脚本，2026-11-13）

- 只导入 argparse、collections、csv、datetime、decimal、io、json、os、re、sys、xml.etree.ElementTree、zipfile；没有 `eval`、`exec`、`subprocess`、网络模块、`pickle`、`ctypes`。`compile` 的匹配全部是 `re.compile`。
- 只读文件（`open(path, "rb")`、`zipfile`），写入只发生在标准输出；PDF 库在 `try: import` 中可选导入。
- 发现的缺口及本包的处理：没有文件大小、压缩包条目数和解压后大小上限（改为 50 MB、5000 个、单条目 80 MB、总计 300 MB）；用标准库 XML 解析器读取不受信任的文档，可能遭遇实体展开（改为拒绝含 DOCTYPE 或 ENTITY 声明的 XML，正常 Office 文档不含这两种声明）；规则靠全局变量保存状态（加锁）。这些都有对应测试（`tests/test_adds_up.py` 的 Safety 与 ToolWrapper）。
- 没有直接运行上游仓库里的测试代码：它来自下载的未审查来源，运行前先做了上述静态审查，之后只对已审查、已移植进本仓库的副本运行本团队自己的测试。

## 服务条款与独立限制

- 无外部服务、无账号、无网络访问。
- 商标/署名：本包不是上游作者发布或认可的版本——README 明确写明，THIRD_PARTY_NOTICES.md 写明不授予上游名称、图标或商标的权利、也不表示上游作者认可本插件；保留 Murat Matur 的版权与 MIT 全文。不使用上游图标。
- 效果：本包只列出算术线索并帮助核对，不能替代审计，不保证文档里没有别的错误。
- 专利、商标和服务条款：移植与独立实现都不构成对这些权利的自动豁免；本审查没有对它们作出结论。

## 最终 ZIP 许可复核

复核对象：`releases/agent-plugin/adds-up/1.0.0/adds-up-1.0.0.zip`（SHA-256 082de326fe91a49fd163fc22e09cb1f05441ba5ac4765104f9666ee8b8dcc055，182166 字节）及其内层载荷；原生测试包 `test-packages/adds-up-1.0.0-native.zip`（SHA-256 55fecb1b36179c77e24ee18c8077f2459a2beaace21b833d8ef720a7b2fd205f，181108 字节）。复核日期 2026-11-13，已解压后逐项检查：

- 包装 ZIP 的内层载荷 7 个文件，与经用户测试的原生测试包逐文件、逐 SHA-256 一致（包装只多出外层 `plugin.yaml`）。
- `provenance.json` 的 `license_evidence` 指向的 `licenses/adds-up/LICENSE` 存在于 ZIP 内，SHA-256 与记录一致（8e64120969b71eee850ba6cfccf0245dd0c72cb7c8118dc7665f38a37c00b501，1068 字节，LF，无 CR）；含 “Copyright (c) 2026 Murat Matur” 和完整的授权声明、免责声明；与上游固定提交 LICENSE 的原始 Git blob（9f1615b1aabc1df5a22b62aa0a1ddf8b86afa477）逐字节一致。
- 三个复用路径 `tools/adds_up.py`、`skills/document-number-check/SKILL.md`、`skills/document-number-check/references/checks.md` 都在 ZIP 内，且被 `THIRD_PARTY_NOTICES.md` 逐条列出（上游路径、Git blob、复用方式、修改摘要）。
- `THIRD_PARTY_NOTICES.md` 含上游 URL、固定提交、版权声明、许可文件路径与哈希、复制范围、修改摘要、未复用清单和授权范围说明。上游没有 NOTICE 文件，所以没有需要保留的 NOTICE（MIT 本身不要求）。
- MIT 不要求在文件里写修改通知；本仓库约定的修改摘要放在 `THIRD_PARTY_NOTICES.md`，`tools/adds_up.py` 的文件头也写明了来源与改动。上游文件没有版权头可保留。
- ZIP 内没有图标、图片、字体、编译缓存或可执行文件；上游图标未使用。
- 本次未发现未满足的许可条件。尚未解决的事项（不构成许可障碍）：上游的商标和名称未获授权，也未使用；专利等其他权利没有作出结论。

`check`、`check-repo`、CI 和 Hub 接受上传都不能代替上述内容复核；本复核是人工逐项核对。
