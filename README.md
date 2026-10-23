# Agentic Hub 插件交付仓

保存团队已开发、测试的 Skill / SwarmSkill / Plugin 源码与发布 ZIP。AI 维护者先阅读 [AGENTS.md](AGENTS.md)。

Shared Google Sheets tracker: [open and edit](https://docs.google.com/spreadsheets/d/12MqKOUOb49c9-i4KF_lii5A2TbmsoeJBF9kCwBIO4eM/edit?usp=sharing). Update the existing workbook in place using a configured connector or an available browser; link sharing does not configure connector/API authentication. See [tracker access instructions](AGENTS.md#shared-google-sheets-tracker-access).

- `skills/<slug>/`：技能源码、打包 metadata、来源审查。
- `plugins/<slug>/`：插件源码、manifest、来源审查。
- `releases/<type>/<slug>/<version>/`：经测试后通过 PR 合入的 ZIP、SHA-256 和载荷清单。
- `templates/`：开发脚手架，不能作为已有成品统计。
- `tracking/tracker.json`：同一份在线追踪表的页签及字段映射，含 Plugin Candidates；维护时仍须读取实时表头。
- `docs/FORMAT_RESEARCH.md`：实际下载样包与官方格式依据。

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/asset_release.py audit-upstream /path/to/authorized-upstream
python tools/asset_release.py check skills/my-skill
python tools/asset_release.py pack skills/my-skill
python tools/asset_release.py check-repo
```

`check` 只验证来源记录和本仓固定格式；每个真实插件还必须有自己的功能测试。MIT / Apache-2.0 的许可保留、署名、修改声明及授权不明时的处理，按 [AGENTS.md](AGENTS.md#licensing-and-distribution-requirements) 执行。第三方材料保留各自适用许可；本项目自身的统一许可证仍待总控决定，不能由 AI 默认选定。

维护流程以 [AGENTS.md](AGENTS.md) 为准：

1. **入口与筛选**：AI 先读规则，采集或复用用户明确提供的成员姓名，再辅助筛选候选；跳过他人认领、已立项、已交付及已证明重复的项目，回填新查重结论。用户选定前不认领、不创建开发任务。
2. **用户选定后制作**：先更新负责人、候选认领和关联开发任务，再审查固定来源、开源许可及实际复用范围；允许复用的进行适配，许可不明或不允许搬运的按原生开发规则处理。测试包和最终交付包都必须是中文版。可按实际功能重新起中文展示名，新资产可在打包前选择合规 slug；记录原名、新名和 slug 对应关系，保持已建立的追踪 ID。
3. **用户测试与收齐材料**：提供中文测试包、安装步骤、版本和哈希，等待用户明确测试完成且问题解决，随后主动索要缺失的测试截图原图。源码、中文 ZIP、许可材料、功能测试记录、用户确认和截图全部齐全后才设 `Ready for Submission`；此前保持本地制作，不 push 或开交付 PR。
4. **PR 交付与验收**：材料齐全后 push、创建 PR，并在创建时附上已收齐的截图原图；核验图片及永久链接，回填测试截图栏。中文最终包必须与用户确认的测试包一致；改名、中文化或其他包变更后须重测确认。功能测试、CI、许可审查和截图链接都通过后再合入、清理分支、同步开发任务/汇报/候选，交给 Song Haoran 验收；他上传对应版本的有效 Hub 提交截图即视为 `Accepted`，无需再口头确认，按实际截图上传日期填写完成日期。满足成员交付条件后才设 `Completed` / `Delivered`。

**取消与释放**：任何实际取消都删除 `Development Tasks` 对应整行，不保留 `Cancelled` 任务。取消原因是 WorkSwarm 适配或许可障碍时，候选改为 `Excluded / Unassigned`；没有账号、个人条件或以后再做时改为 `To Evaluate / Unassigned`。从候选的活跃任务链接中移除已取消 Task ID，将真实原因和旧 ID 保留在候选备注/历史汇报中；历史取消记录不继续占用插件。重新认领使用新 Task ID；同一候选的其他在研任务及已交付资产保留。

**资产总账更新时点**：`Asset Ledger` 只收录官方 Agentic Hub 公开目录中实际存在的资产及版本。PR 合入、提交成功凭据、仅本人可见的详情页或 `Submitted - Pending Review` 截图都不能单独作为入账依据；核对真实 Hub ID、名称及公开版本后才新增或更新。误录的非目录资产从总账移除，保留开发任务、候选和 PR 证据。现有官方资产的未公开升级保留原公开版本。

**验收与新名称**：Song Haoran 提供对应版本的有效 Hub 提交截图后，回填 PR 证据链接和 `Project Lead Acceptance = Accepted`，无需再要求同一次验收的口头确认；其余 GitHub 交付门槛通过后设 `Completed` / `Delivered`，`Completed Date` 使用实际验收/截图上传日期（Asia/Singapore）。补录使用原证据日期并记录本次同步时间。截图本身不代表官方目录已收录。`Development Tasks / Final Plugin Name` 记录实际中文展示名，有官方名称后与之核对，保留原名映射及稳定 ID。

`Development Tasks` 与关联 `Progress Reports` 只追踪具体插件的开发和修改。纯规则、文档、工具、CI 等仓库维护只在 GitHub PR 留痕，不创建插件任务、汇报或候选/资产记录，也不适用插件用户测试门槛。本仓维护 PR 同样在合入后清理对应临时分支。

认领、转派、多个任务与历史升级按[候选负责人、立项与交接](AGENTS.md#candidate-ownership-project-initiation-and-handoffs)维护；他人的认领不能被覆盖。任务表保留现有简化列，用户测试确认写入关联的 `Progress Reports`，两类截图栏只填 PR 中原图的证据链接；Hub 截图栏保留给总控后续提供的证据，缺少时不阻塞成员交付。新增任务必须纳入原表格范围并继承下拉选项、日期格式与换行。

在线追踪表统一使用英文页签、字段、状态与描述。维护者写入新记录时同样使用英文，保留 ID、成员姓名、链接和原始来源文件名；字段映射见 `tracking/tracker.json`。
