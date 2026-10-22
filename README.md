# Agentic Hub 插件交付仓

保存团队已开发、测试的 Skill / SwarmSkill / Plugin 源码与发布 ZIP。AI 维护者先阅读 [AGENTS.md](AGENTS.md)。

Shared Google Sheets tracker: [open and edit](https://docs.google.com/spreadsheets/d/12MqKOUOb49c9-i4KF_lii5A2TbmsoeJBF9kCwBIO4eM/edit?usp=sharing). Anyone with the link can edit (verified 2026-10-22). Update the existing workbook in place using a configured connector or an available browser; link sharing does not configure connector/API authentication. See [tracker access instructions](AGENTS.md#shared-google-sheets-tracker-access).

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

维护流程分为三步，详细要求见 [AGENTS.md](AGENTS.md)：

1. **审查（candidates agent）**：先跳过已确认重复、已被认领、已立项或已交付的候选，再对照历史和新增 Skill / Plugin 等能力。发现完整重复立即回填查重结论、关联资产和依据；未认领且无任务的重复项标为 `Excluded`。待核重叠不冒充已确认重复。本阶段只维护候选审查，不创建开发任务。
2. **开始制作（用户选定后）**：先同步候选认领与原开发任务，再做来源审查、格式适配和功能测试，交付本地测试包、安装步骤及版本/哈希。任务使用 `Ready for Testing` / `User Testing`。等待用户明确确认当前包测试结束，确认前不 push 或开交付 PR。
3. **提交（用户明确测试结束后）**：在关联进展汇报记录用户确认和测试包版本/哈希，问题解决后设 `Ready for Submission` / `Submitting`，再推送、PR 合入 ZIP、清理分支、在 PR 上传测试原图并将证据链接同步到开发任务、汇报及关联候选，交给总控验收。Agentic Hub 的提交、发布和对应截图由 Song Haoran 本人负责，不属于成员及其 agent 的交付步骤或完成门槛。测试证据齐全、总控明确验收且 GitHub 交付条件满足后才设 `Completed` / `Delivered`；用户测试结束不等于最终验收。

**资产总账更新时点**：PR 合入后先同步开发任务、汇报和候选，不新增或更新 `Asset Ledger`。Song Haoran 完成 Agentic Hub 提交并提供可核验的成功凭据后，才新增资产或更新对应版本；`Submitted - Pending Review` 已满足提交成功条件，无需等待审核通过或公开发布。总账入账独立于成员的 GitHub 交付验收。

`Development Tasks` 与关联 `Progress Reports` 只追踪具体插件的开发和修改。纯规则、文档、工具、CI 等仓库维护只在 GitHub PR 留痕，不创建插件任务、汇报或候选/资产记录，也不适用插件用户测试门槛。本仓维护 PR 同样在合入后清理对应临时分支。

认领、转派、多个任务与历史升级按[候选负责人、立项与交接](AGENTS.md#candidate-ownership-project-initiation-and-handoffs)维护；他人的认领不能被覆盖。任务表保留现有简化列，用户测试确认写入关联的 `Progress Reports`，两类截图栏只填 PR 中原图的证据链接；Hub 截图栏保留给总控后续提供的证据，缺少时不阻塞成员交付。新增任务必须纳入原表格范围并继承下拉选项、日期格式与换行。

在线追踪表统一使用英文页签、字段、状态与描述。维护者写入新记录时同样使用英文，保留 ID、成员姓名、链接和原始来源文件名；字段映射见 `tracking/tracker.json`。
