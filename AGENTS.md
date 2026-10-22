# 插件维护：审查、开始制作、提交

本仓保存团队已经开发、测试的 Skill / SwarmSkill / Plugin 源码和可提交给 Agentic Hub 的 ZIP。总控为 Song Haoran。每次任务先完整阅读本文件，按用户当前指令选择流程；不要把候选调研、研究样包、脚手架或只有代码的结果记为已交付插件。

| 流程 | 触发方式与执行角色 | 完成后到哪里 |
| --- | --- | --- |
| 一、审查（Review） | 用户要求筛选或审查候选，由 candidates agent 执行 | 更新候选去重结论并给出可选项，等待用户选定 |
| 二、开始制作（Build） | 用户明确选定并要求“开始迁移/开发某插件” | 立即登记认领和任务，制作测试包，等待用户明确确认本版本测试结束 |
| 三、提交（Submit） | 用户明确确认当前版本测试结束，且已知阻断问题已解决 | 推送、PR 合入 ZIP、提交 Hub、补齐证据和最终验收 |

**流程边界。** 审查结论不自动触发制作；选定插件不代表测试结束；AI 自测或 CI 通过不代表用户测试结束。用户对当前测试包的明确结束确认就是进入提交流程的依据，无须在无变化时重复索取同一确认。确认前制作流程停在可测试的本地包，不自动 push、创建交付 PR、合入、发布 Release 或提交 Hub。规则、文档、工具、CI 等纯仓库维护 PR 不需要插件用户测试确认。

**追踪范围。** `Development Tasks` 与关联 `Progress Reports` 只记录具体插件资产的开发和修改，包括新增、移植、功能改造、修复和升级。流程一只维护 `Plugin Candidates` 的审查信息，不创建开发任务或虚构进展汇报。纯仓库维护只在 GitHub PR 记录变更、验证与审查，不创建插件任务、汇报或 pending 同步记录，也不登记候选或资产。混合 PR 只登记实际插件变更；补充同一资产的交付证据继续关联原任务。

**语言与身份。** 同一[在线追踪表](https://docs.google.com/spreadsheets/d/12MqKOUOb49c9-i4KF_lii5A2TbmsoeJBF9kCwBIO4eM/edit)使用 `Overview`、`Asset Ledger`、`Plugin Candidates`、`Development Tasks`、`Progress Reports`、`Members`。用途、范围、标签、备注、任务名称、进展正文和状态均用英文；保留稳定 ID、实际姓名、URL、版本、日期及原始来源文件名。历史展示名采用官方英文标识，不据此重命名上游包。`tracking/tracker.json` 提供字段和流程映射，每次仍须读取实时表头、下拉选项和目标行，按 ID 更新；写前回读、写后核对，不用旧快照覆盖他人的进度。没有连接或权限时报告未同步项；实际插件任务可保留 `tracking/pending/` 记录，不能声称已更新云表。

## 流程一：审查（candidates agent）

### 先过滤，再比较功能

1. 先读 `Plugin Candidates` 的 `Candidate ID`、`Candidate Status`、`Owner`、`Duplicate Check`、`Related Assets and Differences`、`Linked Development Task IDs`、`Notes`。先根据已有结论和认领过滤，再读取相关资产详情或下载上游材料。
2. **已确认重复直接跳过。** `Duplicate Check = Already Covered`，或备注已有明确的完整功能覆盖结论时，本轮不重新审查、不下载重复样包、不进入推荐清单。保留现有结论和关联资产 ID。`Same Name - Review Needed`、`Functional Overlap - Review Needed`、`Not Checked` 只是待核状态，不能冒充已确认重复。
3. **已被选定直接跳过。** 常规筛选跳过已有明确 `Owner`、已有用户选定/认领记录、已关联开发任务或 `Candidate Status = Planned / Delivered` 的候选；同样跳过 `Deferred / Excluded`。用户明确要求继续本人任务、交接、重新审查或新增差异功能时，按相应记录定向处理。其他人的认领不被覆盖，不为同一候选另开重复任务。
4. 对剩余候选，在 `Asset Ledger` 同时检索历史和新增资产，重点跨 Skill、SwarmSkill、Plugin 对照业务功能，其他类型有相关能力也纳入。比较输入对象、关键动作、输出、适用范围、排除项及依赖；同名、同品牌、不同作者、不同包装或接入方式都不能单独作为重复或新增依据。先用分类/功能标签缩小范围，再看相关详情；资料简略时保留待核结论。
5. **发现重复当轮回写。** 完整覆盖填 `Already Covered`，在 `Related Assets and Differences` 写已有资产 ID、版本及具体覆盖原因，在 `Notes` 追加审查日期、候选版本/来源和比较依据。对本轮未认领、未关联任务的完整重复项，按用户授权将 `Candidate Status` 设为 `Excluded`，保留原始调研、来源和历史记录。若写前发现已被认领或进入任务，跳过认领/状态变更，保留对方工作，报告该冲突。
6. 部分重叠填 `Partial Overlap - Extend Existing Capability`，列出复用已有入口与实际新增的边界，建议扩展已有资产；不按完整重复排除。确认有独立功能填 `Confirmed New Capability`；信息不足使用对应的待核选项并写清缺口。不能把未查到同名解释为已经完成查重。
7. 结果回读确认后，汇总“已确认重复而跳过、已认领而跳过、待核、可供选择”及候选 ID。本阶段不认领、不创建开发任务、不制作包。没有新范围或新版本证据时不重复审查已判重复的候选；用户明确重新打开的项目才检查相关变化。

审查记录用英文，例如：`Reviewed YYYY-MM-DD; candidate <version/ref>; compared <Asset ID>@<version>; outcome <Duplicate Check>; reason <input/action/output/scope comparison>.` 不编造已阅读的版本或审查日期。

## 流程二：开始制作（用户选定后）

### 先认领和登记，再开始实现

1. 用户说“开始迁移/开发 <候选>”后，先按 `Candidate ID` 回读当前结论、负责人、认领和任务关联。已确认完整重复则指出已有资产并跳过；其他人的项目默认跳过，只有明确交接/重新指派后继续。用户指定新增差异功能时回到流程一核对该差异，不能换包装重做同功能。
2. 在开始代码制作前，更新候选的 `Owner`、`Candidate Status = Planned`、`Linked Development Task IDs`，在 `Notes` 追加用户选定日期、范围和依据；同步创建或复用 `Development Tasks` 的任务 ID、`[Candidate ID] <Task Name>`、`Component Type`、`Change Type`、`Owner`、`Status`、`Dependencies`。新任务 ID 使用 `AH-YYYYMMDD-<slug>` 并核对唯一性。未知负责人保留 `Unassigned`，仍以 `Planned`、关联任务 ID 和选定备注表明已被选中；不得根据 AI 账号或 PR 作者猜测负责人。
3. 写前再次核对认领。尽量同批更新候选和任务，再回读两边 ID、负责人、状态；若并发认领冲突，保留已确认的指派，报告冲突，不继续制造重复实现。若只有一边写成功，先修复关联并核对，再开始制作。开始时填 `Researching` 或 `In Development`，之后一直更新原行。
4. 审查已完成的候选不从头重跑全目录；开工只核对已有关联资产和审查后新增/变更的相关能力，避免遗漏新交付资产。无对应候选的独立开发需求注明 `Not Applicable`，不编造候选行。

### 来源核查和原生开发

1. 定位实际上游 URL 和固定提交/版本，核对根许可证、子目录许可证、文件头、素材及依赖。可执行 `python tools/asset_release.py audit-upstream <上游目录>` 收集哈希和候选许可；AI 仍需检查许可覆盖范围和实际用法，写入 `SOURCE_REVIEW.md` 与 `provenance.json`。
2. 公开仓库、可下载、网页页脚 Apache-2.0 或单个 license 字段都不能单独证明所用材料可搬运。证据不足保持 `permission_status: unknown`，禁止有问题材料进入交付源码或 ZIP。按实时选项填写候选 `License Review`，具体结论和证据追加到 `Notes` 和 `SOURCE_REVIEW.md`，保留原调研许可快照。
3. 明确可复用时采用 `mode: ported`，记录固定来源、实际复制路径及随包许可证据，落实后面的“许可与分发要求”。本仓自有代码的统一许可证仍由总控另行决定。
4. 授权不明或不允许搬运时采用 `mode: native`：只从公开功能说明、用户需求和获授权输入输出建立 `NATIVE_DESIGN.md`，独立写代码、提示词、文档、图标和测试。不能把不可复用实现交给 AI 翻译、改变量名或改写后声称原创。记录已接触材料；上下文已包含不可复用实现时，把功能规格交给未接触实现的开发者/新 AI 上下文。独立实现不能被描述为对专利、商标或服务条款的自动豁免；疑问如实交总控判断。
5. 来源不清不阻止独立需求设计和仓库工具维护，但有问题材料不得进入交付。审查跨任务复用的是固定来源的证据，最终使用范围和 ZIP 仍需复核。

### 做成我们的格式，交给用户测试

1. 从模板按后面的固定格式制作 Skill / SwarmSkill / Plugin；保留源码和实际依赖，生成可供目标宿主安装、运行的测试包。可创建本地分支和本地提交保存工作；此阶段不 push、开交付 PR、合入或上传 Hub。
2. 执行格式检查、资产自身功能测试和打包；解包最终测试 ZIP 验证运行内容、声明路径和许可文件。提供用户可访问的测试 ZIP/内层 Skill 目录、版本、SHA-256、依赖环境、安装步骤、关键操作、预期结果及已知问题，不以包装器测试替代资产功能测试。
3. 包可供测试时设任务 `Status = Ready for Testing`；用户开始测试后设 `User Testing`。在 `Progress Reports` 写测试包版本/哈希、验证结果、下一步及欠缺证据，候选仍为 `Planned`。邀请用户提供真实测试截图，并在任务的 `Test Screenshot` 保存实际链接；不伪造截图或用日志代替。
4. **用户测试确认是明确的阶段门槛。** 等用户明确表示当前任务/版本“测试结束”或“测试通过，可以提交”，且已知阻断问题已解决，才设 `Ready for Submission` 并进入流程三。AI 自测、CI、下载包、开始测试、上传一张截图或含糊反馈都不等于结束确认；“测试结束但有问题”仍回到制作修复。无需为同一份有效确认重复提问。
5. 在原任务关联的 `Progress Reports` 追加英文确认记录：`User test confirmation: <faithful English rendering>; confirmed by <actual user>; date/time <time>; Task ID <id>; version <version>; ZIP SHA-256 <hash>; known blocking issues <none/resolved details>; evidence/source <actual conversation reference if available>.` 保留用户原消息的可核查依据；没有消息链接时注明当前对话，不编造 URL。测试截图单独留在证据列，不能代替确认。
6. 确认只覆盖用户实际测试的版本和包哈希。此后改变源码载荷、包装或最终 ZIP 时，回到制作/测试并取得对新包的结束确认；仅调整仓库维护文档且测试包未变不使确认失效。用户测试确认不等同于最终 `Project Lead Acceptance = Accepted`。

### 候选负责人、立项与交接

- 候选和任务按稳定 ID 关联，所有关联任务 ID 都保留；多人协作保留一个明确候选主负责人，其他协作者写备注。只分配负责人、未开始制作时仍可为 `To Evaluate`，但常规候选筛选已跳过该认领。
- 以总控明确指派或已确认任务分工为准。候选有负责人则承接给对应任务；候选未分配而任务已有确认指派时同步回候选。两边都未分配则保留 `Unassigned`。
- 负责人不同时核对最近明确指派/交接；没有依据时保留原值并报告冲突，不覆盖。明确转派后同步两边，并在原任务关联汇报写原负责人、新负责人、日期和依据。拆分子任务不自动改变候选主负责人。
- 候选状态与任务进度分开维护。首次制作至提交待验收均为 `Planned`；`Delivered` 只表示约定的首次交付条件全部满足。升级另建或关联适当任务，保留历史交付标记。`Deferred / Excluded` 依据明确决定；流程一对未认领完整重复项的排除是已获授权的例外。单个任务取消不自动排除整个候选。

## 流程三：提交（用户明确测试结束后）

### 先核对确认，再提交 PR 与 Hub

1. 回读原任务及用户测试确认，核对 `Task ID`、版本、最终 ZIP SHA-256、未解决问题和当前负责人。没有针对当前包的有效确认就留在流程二，不猜测、不补写历史确认。已有 PR/合入的历史任务不撤销历史记录；尚未完成的 Hub 提交或后续新版本仍需满足本次阶段门槛，不重新提交已合入的相同 ZIP。
2. 确认有效后设任务 `Submitting`。按最新 main 创建或更新本次来源分支，推送源码、实际功能测试记录、来源审查、ZIP 和 artifact.json，创建交付 PR；不直接把插件推到 main。PR 写任务/候选 ID、功能差异、固定来源与许可检查、测试确认关联汇报 ID、版本和 ZIP 哈希。用户已按本流程明确确认本包测试结束时，正常继续后续步骤，无须重复索取相同的提交许可。
3. 检查最终 ZIP 与确认包一致、适用许可和声明齐全、资产测试/CI 通过且无未解决阻断问题，再合入。确认 PR 实际 `merged` 状态与合并提交；push 成功、PR 已打开和 CI 通过都不等于已合入。按本节的分支清理要求立即清理对应临时分支。
4. PR 合入后提示用户补齐真实 `Test Screenshot` 和最终 `Agentic Hub Submission Screenshot`；截图分别显示版本/关键操作/结果，以及资产名/版本/提交结果或审核状态。可上传到 PR 或团队可访问的 Drive，分别回填两列真实链接；不得拿日志、PR URL 或样图当截图，避免暴露密钥和私人数据。
5. 按约定提交 Hub：Skill 网页选择解包后的内层 `<slug>/<slug>/` 目录由网页包装；Plugin 上传合并的发布 ZIP；也可按当时官方 CLI/API 提交。需要用户在网页完成的步骤则交付明确指引并等待真实结果，不声称已提交。Skill 网页重新包装时比较载荷清单/哈希和版本，不假定外层 ZIP 哈希相同。提交内容与已确认、已合并的载荷一致。

### 同步台账与最终验收

1. **合入后同步 Asset Ledger。** 只在 PR 实际合入且功能测试通过后登记新资产；按关联 ID 更新已有记录或追加一行 `New Asset`，同步名称、类型、分类、用途、标签、范围、发布者、版本、来源和日期。历史资产升级保留 `Historical Asset`。Hub 发布前用真实合并 PR/交付路径作为来源，不编造 Hub 链接或发布状态。
2. 无 Hub ID 时稳定内部 ID 使用 `repo:<type>:<slug>`，明确不是 Hub ID。实际 Hub ID 另记 delivery.json，取得后把来源更新为真实详情页；内部 ID 保持稳定，历史 Hub ID 继续保留。先匹配关联 ID/来源，再看名称和功能，避免重复登记。
3. **同步任务、候选和汇报。** 原任务填写实际合并 PR、两类截图及真实状态；候选回填负责人、关联任务 ID、实际查重/许可结论和备注中的合并版本、资产 ID、Hub 状态。欠证据、尚待 Hub 目标或总控验收时设 `Awaiting Acceptance`，首次交付候选仍为 `Planned`，不填完成日。Hub 审核中只记 `Submitted - Pending Review`，不能冒称已发布。新汇报保留日期、任务/候选 ID、已完成、下一步、阻塞及需总控决定事项，不覆盖历史记录。
4. **最终总控验收单独记录。** Song Haoran 明确验收后才填 `Project Lead Acceptance = Accepted`。只有功能测试和用户测试结束确认有效、PR 合入、两份真实证据可访问、约定 Hub 提交/发布目标达成、总控明确验收、台账与关联记录同步并回读核对后，才将任务设为 `Completed`、填实际完成日，将对应首次交付候选设为 `Delivered`。只要求提交与要求上架分别按约定判断；测试结束不代替最终交付验收。
5. 后续升级和拆分任务保留原交付与认领历史；多任务的整项候选交付按约定完整范围判断。写后核对候选 ID、任务 ID、资产 ID、负责人、链接和各页状态。纯仓库维护走维护 PR，不要求插件 ZIP、两类截图或插件验收，不向任务和汇报登记。

### PR 合入后删除开发分支（所有 PR 适用）

1. 插件开发、修改和纯仓库维护的 PR 合入后，立即清理本仓对应的临时来源分支；不必等待插件截图、Hub 审核或总控验收。先确认 PR 的实际 `merged` 状态及合并提交，再核对来源仓库、分支名和最新 head SHA；只有分支仍停留在该 PR 已合入的 head，且没有其他未合入 PR 使用它作为来源或目标分支时，才删除。
2. 仓库启用 GitHub 的“Automatically delete head branches”时，仍须确认本次来源分支已删除；未自动删除则由有权限的维护者手动删除并核实结果。权限不足或分支保护阻止清理时，在该 PR 记录分支名和原因，不能声称已经删除。
3. 保留 `main`、仓库默认分支及明确保留的长期或受保护分支。若来源分支在合入后出现新提交，或仍被其他未合入 PR 依赖，保留并在 PR 说明待处理事项；不删除其他贡献者 fork 中的分支，不强制删除本地未合入的工作。
4. 后续修改从最新主分支新建开发分支，不复用已合入的旧分支。交付和追踪链接使用实际 PR、合并提交或主分支发布路径，避免依赖即将删除的开发分支 URL。此清理规则同样适用于维护 PR，但不因此向插件追踪表新增记录。

## 许可与分发要求

以下维护要求经总控确认，核对日期为 2026-10-22；适用于 Skill、SwarmSkill 和 Plugin。以实际许可原文、覆盖材料和预期用途判断，不能只按仓库名或 SPDX 标签自动放行。

1. **逐项核查范围。** 在 `SOURCE_REVIEW.md` 记录上游地址、固定提交/版本、权利人原有声明、复用及修改路径、每项适用许可和分发条件。代码、提示词、文档、图标、字体、数据、依赖分别检查；代码开源不自动授权品牌素材、第三方数据或 API 服务。混合许可逐项满足；双许可需记录实际选择，不能随意删去 `AND` 中的义务或臆造 `OR` 选择权。
2. **MIT。** 复用或分发相关软件的副本或实质部分时，保留原版权声明和许可声明。本仓统一随包保留完整上游 MIT 文本（含免责声明），并保留原有文件头；链接、SPDX 字段和新版权声明不能替代原声明。记录修改内容是本仓追踪约定，不声称是 MIT 独立要求。依据：[MIT 原文](https://opensource.org/license/mit)。
3. **Apache-2.0。** 按第 4 条向接收者提供许可证副本；对修改过的文件作显著修改声明；分发衍生源码时保留适用的版权、专利、商标和署名声明。如果上游发行包带有 NOTICE，随包保留其中适用的署名内容；没有上游 NOTICE 时如实记录“无”，不要伪造。新增团队署名不能替换上游声明，也不能把 NOTICE 写成改变许可证条款的文件。第 6 条不授予一般商标使用权，不得因此宣称官方背书。依据：[Apache-2.0 第 4、6 条](https://www.apache.org/licenses/LICENSE-2.0.txt)。
4. **其他或不明许可。** 其他许可证、单独授权、附加限制或兼容性疑问按实际原文检查，不能套用 MIT / Apache 结论。公开但没有许可，或许可未覆盖实际复用材料时，保持 `permission_status: unknown`，阻止这些材料进入源码交付与 ZIP；可以取得明确授权，或按流程二的独立开发要求。没有找到许可证不等于已证明闭源，更不等于允许复制。依据：[GitHub 的无许可证说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)。
5. **随包材料。** 对 `ported` 资产，本仓要求在内层载荷提供 `THIRD_PARTY_NOTICES.md`，列明上游、固定版本、原作者/权利人声明、适用文件、许可和修改摘要；许可原文放在 `licenses/<upstream>/LICENSE`，上游适用 NOTICE 放在同目录。多个上游分别保存，保留原文件头及其他适用声明，不能只在本仓网页或 PR 附链接。Apache 的修改文件声明仍需在修改文件上落实，集中修改摘要不能替代它。此目录和汇总文件名是本仓约定，不是许可证统一规定。
6. **发行前复核。** 解包最终 ZIP，核对所有复用路径是否有相符的许可及声明、修改声明是否齐全、`license_evidence` 的路径与哈希是否匹配实际随包文件；`SOURCE_REVIEW.md` 记录检查结果和 ZIP 内路径。PR 明列已落实事项与待解决项，任一必要条件未满足则不合入该资产。`audit-upstream`、`check`、CI 和“Hub 接受上传”都不能替代这一步内容审查。

本政策没有为整个仓库、团队原创部分或上游材料统一改换许可证。AI 不得猜测版权归属、抹去上游作者、替总控作出新的再许可决定；独立实现也不能被描述为对专利、商标或服务条款等其他权利的自动豁免。

## 固定包装格式：Skill 与 Plugin 不同

本仓采用“原生目录 + 确定性市场包装 ZIP”。参考依据及 4 个实际下载样包见 [格式调研](docs/FORMAT_RESEARCH.md)。这是本仓的交付约定；服务端支持部分更宽松的历史格式，不代表本仓应该放宽测试要求。

### Skill / SwarmSkill

源码：`skills/<slug>/asset.json`、`provenance.json`、`SOURCE_REVIEW.md`，及 `skills/<slug>/<slug>/SKILL.md`。`SKILL.md` 使用 UTF-8，YAML frontmatter 的 `name` 与目录名一致、`description` 非空；slug 为小写字母开头、小写字母/数字/单连字符，最长 64 字符。仓内版本统一 `x.y.z`；若 frontmatter 声明 version，须与 asset.json 相同。

```text
<slug>-<version>.zip
└── <slug>/
    ├── plugin.yaml            # runtime.type: skill
    └── <slug>/
        ├── SKILL.md           # Skill 原生入口；无需 manifest.json
        ├── scripts/           # 可选
        ├── references/        # 可选
        └── assets/            # 可选，及必要的来源/许可文件
```

SwarmSkill 仍是 `runtime.type: skill`，但 frontmatter 需 `kind: swarm-skill` 和至少两个不重复的 `roles[].id`，并在 asset.json 标为 `swarmskill`。不能通过名称是否含 swarm 判断类型。

### Plugin

源码：`plugins/<slug>/asset.json`、`provenance.json`、`SOURCE_REVIEW.md`，及 `plugins/<slug>/<slug>/manifest.json`。

```text
<slug>-<version>.zip
└── <slug>/
    ├── plugin.yaml            # runtime.type: agent-plugin
    └── <slug>/
        ├── manifest.json      # Plugin 原生入口；package_type: plugin
        ├── README.md
        ├── skills/<skill>/SKILL.md
        └── tools/             # 可选，也可有 rails、mcps 等实际需要的能力
```

manifest 的 `id = asset.json.name = plugin.yaml.name`，三个版本相同，`package_type = plugin`。根 manifest 禁止 `persona`、`agent_card`、`model`、`subagents`、`memories`、`rubrics`；不要混用宿主 Extension / Claude marketplace 的包格式。所有声明的 Skill、tool、rail、MCP 文件必须实际存在，路径不得越界。Hub 有些声明缺文件也能通过结构校验，本仓仍必须验证并做功能测试。

### 两类共同要求

- 从 `templates/` 复制脚手架到 `skills/` 或 `plugins/`，填写真实 metadata、作者、来源和独立设计；模板本身不计资产。
- 执行 `python tools/asset_release.py check <资产目录>`；再运行该资产自己的测试，记录环境、命令、结果、失败案例及依赖，不能用本仓包装器测试替代插件功能测试。
- 执行 `python tools/asset_release.py pack <资产目录>`，ZIP 与 `artifact.json` 写入 `releases/<type>/<slug>/<version>/`。ZIP 只装运行载荷和市场外壳；测试、任务表、开发缓存不塞进外壳。来源及许可文件如需随包携带，应放在内层载荷中。
- 市场外层只放 `plugin.yaml`、可选 `icon.png`、唯一同名内层目录。版本不可默默覆盖，所有本地引用、SHA-256 和归档路径需可核对。本仓 ZIP 上限为 95 MiB，以适应 GitHub 单文件约束；更大的资产交总控选择交付方式。
- `audit-upstream` 与本地校验不等于法律结论、真实运行成功或 Hub 已审核通过。下载的 4 个样包只用于静态调研，不运行、不作为本团队成品提交。
