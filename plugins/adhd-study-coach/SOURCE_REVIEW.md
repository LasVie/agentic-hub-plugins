# 来源与查重审查 — ADHD 学习教练

Owner: Nguyen Trung Dung. Reviewed 2026-11-06, Asia/Singapore.
Task AH-20261106-adhd-study-coach; Candidate CAND-CLD-288.
Mapping: ADHD Study Coach -> ADHD 学习教练 -> adhd-study-coach; repo:agent-plugin:adhd-study-coach.

## 任务与差异

- 关联历史/新增资产 ID：无。开工时（2026-11-06）按名称、描述、标签和范围检索 Asset Ledger（854 行）以及 Development Tasks（开工前 69 个任务行），没有 ADHD、间隔重复、闪卡或学习进度卡类资产，也没有同名或同功能的开发任务。
- 最接近的已有资产及差异：
  - 学习力发展师团队技能（SwarmSkill）：多角色的学习评估、方法设计和落实辅导；没有 ADHD 针对性设计，没有间隔复习排期，没有可保存的进度卡或确定性计算。
  - llm-learning-tutor-team（SwarmSkill）：只讲 LLM 与 AI Agent 基础。
  - K12学业成长教练团（SwarmSkill）、小学课程辅导团队、亲子学习陪伴团（Expert Team）：面向中小学生、老师和家长的多角色方案。
  - 边做边学编程助手（Plugin，learning-output-style）：真实编程任务中的学习式指导。
  - 共享记忆（Plugin）：SQLite 事实与偏好记忆，不涉及学习排期。
  这些都不是“单个学习搭档 + 热身复习 + 间隔排期 + 可复制的进度卡”，因此不构成完整功能覆盖；本审查是按名称和描述的比对，没有安装试用这些资产。
- 复用与独立实现结论：技能说明 ported（上游 MIT，已核实）；三个进度卡工具为 native（见 NATIVE_DESIGN.md）。上游没有任何可执行代码。

## 材料与授权证据

| 实际使用路径/材料 | 上游 URL 与固定提交/版本 | 适用许可与覆盖范围 | 许可文件及 SHA-256 | 复制/修改情况 |
| --- | --- | --- | --- | --- |
| `agents/adhd-study-coach.md`（Git blob a2287fe5ccce6891e575dbd98df2519090f8fdac）和 `claude-ai-skill/adhd-study-coach/SKILL.md`（Git blob 5670b9b1dc456ce55d28e4f5d6a88289c50ff947）的教练说明文字 | https://github.com/itsAalaa7/adhd-study-coach @ eec04896c443b76d34546698905ec0911fa3f17f（`plugin.json` 版本 0.2.0） | MIT，Copyright (c) 2026 Aalaa Fahiem；根目录 LICENSE 覆盖仓库全部文件，文件无单独版权头 | `licenses/adhd-study-coach/LICENSE`，SHA-256 d9487d7e75e16293408fe8556dc940f400c0d6e7fbeed42a7d149a5be43fd748，与上游固定提交 LICENSE（Git blob b0ed61b8356ec0529ba1ca429dc38074ca34e688，LF 换行，1069 字节）逐字节一致，已用 `git cat-file blob` 取原始字节比对 | 译为简体中文并改写为 `skills/adhd-study-coach/SKILL.md`（见下） |
| 三个进度卡工具、中文进度卡格式、校验与错误处理、README | 无上游 | 本团队原创；NATIVE_DESIGN.md | 不适用 | 无复制 |

代码、提示词、文档、图标、字体、数据、依赖分别核查：

- 代码：上游仓库只有 Markdown、JSON、SVG、HTML 和一个压缩包，没有任何可执行代码；`tools/study_card.py` 为本团队独立编写。
- 提示词/文档：只改编上述两份教练说明。上游 `README.md`、`RESEARCH.md`、`SECURITY.md`、`CHANGELOG.md`、`universal/`、`integrations/`、`docs/` 网站和 `claude-ai-skill` 压缩包均未复制，本包 README 独立编写。`RESEARCH.md` 只以链接指向，没有随包分发。
- 研究出处：上游教练说明和 `RESEARCH.md` 引用了多篇论文（如 Roediger & Karpicke 2006、Dunlosky et al. 2013）。本包只保留“作者 年份”的引用，没有复制论文内容，也**没有逐条核实**这些出处。上游自己说明 `RESEARCH.md` 由 AI 辅助检索整理，2026-09-26 做过一轮核对并修正了若干数字，建议在引用前自行核实；`SKILL.md` 已把相关表述改为“上游项目称”，并要求教练被问到时说明这是上游的说法。
- 图标/图片/字体：上游 `.claude-plugin/icon.svg` 和网站图片未使用；本包没有图标、图片、字体或二进制文件。
- 数据：不随包分发任何数据；工具不联网、不读写文件、不保存任何内容。
- 依赖：只使用 Python 标准库和宿主 openjiuwen SDK，不打包依赖。

## 改动与上游的差异（修改摘要）

- 全文译为简体中文。保留环节 0–4 的结构、评分与改期规则、教学规则（分块、先示范再撤、一次一题、合意的困难、时间外化、65% 底线、绝不羞辱等）、反思五问、闪卡格式和“这科学吗”的回答。
- 上游有两种记忆方式：Claude Code 版把数据写在插件数据目录里（需要 Read/Write/Bash/PowerShell 工具和 `${CLAUDE_PLUGIN_DATA}`），claude.ai 版用可复制的进度卡。本包只采用进度卡：不读写文件，不依赖特定宿主的工具。
- 上游让模型自己写进度卡和算日期；本包改为三个原生工具读写卡片、计算到期日和间隔，并严格校验。进度卡由英文改为中文固定格式；去掉上游的“gap in days”字段，改用“间隔天数”。
- “不稳”的改期：上游只写“间隔不变、很快再复习”，本包具体实现为“间隔不变、明天再复习”，这是本团队的解读。
- 新增：不是临床工具、不诊断的边界说明；“上游项目称”的出处声明；工具返回的日期来源提示。去掉：上游面向 Claude Code 的 `model`、`color`、`tools` 头字段和数据目录说明。

## 服务条款与独立限制

- 无外部服务、无账号、无网络访问。
- 商标/署名：本包不是上游作者发布或认可的版本，README 和 THIRD_PARTY_NOTICES.md 已写明；保留 Aalaa Fahiem 的版权与 MIT 全文。
- 医疗与效果：本包是学习辅助，不是临床工具，不诊断、不治疗，也不承诺提高成绩；`SKILL.md` 要求被问到诊断时拒绝并建议咨询专业人士。
- 专利、商标和服务条款：独立实现不构成对这些权利的自动豁免；本审查没有对它们作出结论。

## 最终 ZIP 许可复核

- 原版权/署名及文件头保留位置：`THIRD_PARTY_NOTICES.md`；`licenses/adhd-study-coach/LICENSE`；`tools/study_card.py` 头部注明规则来源与固定提交。上游文件没有单独的版权头可保留。
- THIRD_PARTY_NOTICES.md：`adhd-study-coach/THIRD_PARTY_NOTICES.md`，逐项列出来源、版权人、复用范围、修改摘要和未复用内容。仅有一个上游。
- MIT 许可全文路径：`adhd-study-coach/licenses/adhd-study-coach/LICENSE`（完整文本含免责声明）。
- 上游 NOTICE：无（上游仓库没有 NOTICE 文件，2026-11-06 核对固定提交文件清单：.claude-plugin、.gitignore、CHANGELOG.md、LICENSE、README.md、RESEARCH.md、SECURITY.md、agents、claude-ai-skill、docs、integrations、universal）。
- Apache-2.0 修改文件显著声明：不适用（上游为 MIT）。
- 品牌素材、数据、依赖、服务条款：见上节；无品牌素材、数据集或打包依赖。
- 解包检查命令、文件清单与哈希核对结果：见 TEST_REPORT.md 的包身份与解包核对部分（native ZIP 与 canonical ZIP 内层文件逐一比对 SHA-256）。
- AI 结论：技能说明 verified（MIT 覆盖已核实，逐字节比对了随包 LICENSE）；进度卡工具 original。待解决：上游研究出处未逐条核实（见上文）；没有已知的授权阻塞。
