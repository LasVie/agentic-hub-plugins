# 插件交付仓维护步骤

本仓保存团队已经开发、测试的 Skill / SwarmSkill / Plugin 源码和可提交给 Agentic Hub 的 ZIP。总控为 Song Haoran。每次任务先完整阅读本文件；不要把研究样包、脚手架模板或仅提交代码的结果标为已交付插件。

## 1. 开工：查重、来源检查、登记任务

1. 读取 [在线追踪表](https://docs.google.com/spreadsheets/d/12MqKOUOb49c9-i4KF_lii5A2TbmsoeJBF9kCwBIO4eM/edit)。先读取实时页签、表头、已有任务 ID 和下拉选项，不能根据旧列号直接覆盖。
2. 在“资产总账”同时检索历史和新增记录，比较用途、输入输出、适用边界和依赖。重叠时扩展已有资产；在 `SOURCE_REVIEW.md` 记录关联资产 ID 与差异。不能仅靠名称判重。
3. 更新“开发任务”的一行：任务 ID、任务名称、组件类型、历史或新增、负责人、状态、依赖任务。任务 ID 复用已有记录；新建时使用 `AH-YYYYMMDD-<slug>` 并检查唯一性。未指定负责人填写“待分配”，不得猜测账号；组件类型使用实时下拉值。开始工作填“调研中”或“开发中”。同一任务后续更新原行，不追加重复任务。
4. 自动核查来源：定位实际上游 URL 和固定提交/版本，检查根许可证、子目录许可证、文件头、素材及依赖声明。可执行 `python tools/asset_release.py audit-upstream <上游目录>` 收集文件哈希和候选许可；结果只是检测证据，AI 必须继续核对许可覆盖范围及实际使用方式，写入 `SOURCE_REVIEW.md` 和 `provenance.json`。
5. “公开仓库”“可下载”“网页页脚 Apache-2.0”“有一个 license 字段”均不能单独证明单项资产可以搬运。证据不足填 `unknown`，不得改成“已开源”或复制进交付 ZIP。
6. 获得明确可复用依据后，采用 `mode: ported`，记录固定来源、实际复制路径和随包携带的许可证据，并完成下列许可与分发要求。本仓自身采用什么许可证仍由总控另行决定，不能由 AI 默认选定。
7. 授权不明或不允许搬运时，采用 `mode: native`：只从公开功能说明、用户需求及获授权的输入输出建立 `NATIVE_DESIGN.md`；独立写代码、提示词、文档、图标和测试。不要把原代码交给 AI 翻译、改变量名或改写后声称原创。记录已接触的材料；若开发上下文已包含不得复用的实现，交接功能规格给未接触该实现的开发者/新 AI 上下文，而不是假称已完成独立实现。功能相似不等于已获得其他权利的许可，存在疑问须如实交总控判断。
8. 来源不清不阻止独立需求设计和本仓工具维护，但必须阻止有问题材料进入 ZIP。缺少追踪表权限时保存本地 `tracking/pending/` 同步记录并报告，不能声称已经更新云表。

### 许可与分发要求

以下维护要求经总控确认，核对日期为 2026-10-22；适用于 Skill、SwarmSkill 和 Plugin。以实际许可原文、覆盖材料和预期用途判断，不能只按仓库名或 SPDX 标签自动放行。

1. **逐项核查范围。** 在 `SOURCE_REVIEW.md` 记录上游地址、固定提交/版本、权利人原有声明、复用及修改路径、每项适用许可和分发条件。代码、提示词、文档、图标、字体、数据、依赖分别检查；代码开源不自动授权品牌素材、第三方数据或 API 服务。混合许可逐项满足；双许可需记录实际选择，不能随意删去 `AND` 中的义务或臆造 `OR` 选择权。
2. **MIT。** 复用或分发相关软件的副本或实质部分时，保留原版权声明和许可声明。本仓统一随包保留完整上游 MIT 文本（含免责声明），并保留原有文件头；链接、SPDX 字段和新版权声明不能替代原声明。记录修改内容是本仓追踪约定，不声称是 MIT 独立要求。依据：[MIT 原文](https://opensource.org/license/mit)。
3. **Apache-2.0。** 按第 4 条向接收者提供许可证副本；对修改过的文件作显著修改声明；分发衍生源码时保留适用的版权、专利、商标和署名声明。如果上游发行包带有 NOTICE，随包保留其中适用的署名内容；没有上游 NOTICE 时如实记录“无”，不要伪造。新增团队署名不能替换上游声明，也不能把 NOTICE 写成改变许可证条款的文件。第 6 条不授予一般商标使用权，不得因此宣称官方背书。依据：[Apache-2.0 第 4、6 条](https://www.apache.org/licenses/LICENSE-2.0.txt)。
4. **其他或不明许可。** 其他许可证、单独授权、附加限制或兼容性疑问按实际原文检查，不能套用 MIT / Apache 结论。公开但没有许可，或许可未覆盖实际复用材料时，保持 `permission_status: unknown`，阻止这些材料进入源码交付与 ZIP；可以取得明确授权，或按第 1 节独立开发。没有找到许可证不等于已证明闭源，更不等于允许复制。依据：[GitHub 的无许可证说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)。
5. **随包材料。** 对 `ported` 资产，本仓要求在内层载荷提供 `THIRD_PARTY_NOTICES.md`，列明上游、固定版本、原作者/权利人声明、适用文件、许可和修改摘要；许可原文放在 `licenses/<upstream>/LICENSE`，上游适用 NOTICE 放在同目录。多个上游分别保存，保留原文件头及其他适用声明，不能只在本仓网页或 PR 附链接。Apache 的修改文件声明仍需在修改文件上落实，集中修改摘要不能替代它。此目录和汇总文件名是本仓约定，不是许可证统一规定。
6. **发行前复核。** 解包最终 ZIP，核对所有复用路径是否有相符的许可及声明、修改声明是否齐全、`license_evidence` 的路径与哈希是否匹配实际随包文件；`SOURCE_REVIEW.md` 记录检查结果和 ZIP 内路径。PR 明列已落实事项与待解决项，任一必要条件未满足则不合入该资产。`audit-upstream`、`check`、CI 和“Hub 接受上传”都不能替代这一步内容审查。

本政策没有为整个仓库、团队原创部分或上游材料统一改换许可证。AI 不得猜测版权归属、抹去上游作者、替总控作出新的再许可决定；独立实现也不能被描述为对专利、商标或服务条款等其他权利的自动豁免。

## 2. 固定包装格式：Skill 与 Plugin 不同

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

## 3. 收尾：先合入 ZIP，再补证据和同步

1. 创建分支与 PR，提交源码、实际测试记录、来源审查、发布 ZIP 和 artifact.json。主分支只接收经过测试的资产；不直接推送插件到 main。PR 应写明任务 ID、功能差异、源许可检查结果、ZIP 路径/哈希和测试结论。确认 PR 的实际 `merged` 状态及合并提交；“push 成功”“PR 已打开”不等于合入。
2. PR 合入后，向用户明确提示：请上传本次真实插件的**测试截图**（显示版本、关键操作与结果），以及**最终 Agentic Hub 提交截图**（显示资产名、版本、提交结果/审核状态）。可在 PR 上传附件或上传到团队可访问的 Drive，再把真实链接分别写入任务表两列。不能伪造截图、拿样图代替、把日志或 PR 链接当成截图；截图需避免泄露密钥和私人数据。
3. 提交 Hub：Skill 网页选择解包后内层 `<slug>/<slug>/` 技能目录，由网页包装；Plugin 上传发布 ZIP。也可按当时官方 CLI/API 提交包装 ZIP。若 Skill 网页重新包装，不假设整包 ZIP 哈希相同，应比对载荷文件清单/哈希及版本。最终提交使用与合并版本一致的内容。
4. **立即同步资产总账**：只在 PR 已合入且实际功能测试通过后登记新资产；按资产 ID 更新已有资产，或追加一行，首列选择“新增资产”。原历史资产做版本升级仍保留“历史资产”，不要更改其历史归属。字段映射见 `tracking/tracker.json`；同步名称、类型、分类、用途、标签、范围、发布者、版本、来源链接和登记日期。Hub 发布前，来源链接用实际合并 PR/交付路径；不能编造 Hub 链接或写“已发布”。
5. 新资产尚无 Hub ID 时，仓内稳定 ID 使用 `repo:<type>:<slug>`，明确这是内部 ID，不是 Hub 分配 ID；取得 Hub ID 后另在交付记录中保存并把来源链接更新为真实 Hub 详情页，稳定内部 ID 不反复更换。历史 Hub 记录继续使用原 ID。先匹配已有关联 ID / 来源 URL，再查名称和功能，避免为同一资产追加第二行。
6. **同步开发任务**：在原任务行填写实际合并 PR、两种截图链接和当前状态。缺 PR 合入或任一截图时保持进行中/验收中，并在进展汇报写清欠缺项。Hub 显示“审核中”只能记录“已提交待审核”，不能写已发布。若任务验收要求上架，需等审核通过；若只要求提交，可按约定验收，不虚构最终上架。
7. **总控验收**由 Song Haoran 的明确结论填写；AI 不得自行设为“通过”。达到本任务约定的交付目标、PR 已合入、两份证据真实可访问、总控验收通过后，才把状态设为“已完成”、填写实际完成日。对未满足条件的任务只更新真实进度。
8. **同步进展汇报**：追加有日期和关联任务 ID 的记录，列出已完成、下一步、阻塞/待补证据、真实 PR/证据和需总控决定的事项，不覆盖他人的历史汇报。
9. 每次写入后回读目标单元格，核对任务 ID、资产 ID、链接及状态。不得用本地历史快照覆盖多人协作表。没有相应连接/权限时报告未同步项并保留 pending 文件；不能编造同步成功。

纯维护规范或工具变更属于“协作建设”：可以提交维护 PR、登记任务和汇报；不登记为插件资产，也不要求虚构插件 ZIP 或 Hub 截图。本仓初始化属于这一类。
