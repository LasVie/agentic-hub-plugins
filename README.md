# Agentic Hub 插件交付仓

保存团队已开发、测试的 Skill / SwarmSkill / Plugin 源码与发布 ZIP。AI 维护者先阅读 [AGENTS.md](AGENTS.md)。

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

`check` 只验证来源记录和本仓固定格式；每个真实插件还必须有自己的功能测试。MIT / Apache-2.0 的许可保留、署名、修改声明及授权不明时的处理，按 [AGENTS.md](AGENTS.md#许可与分发要求) 执行。第三方材料保留各自适用许可；本项目自身的统一许可证仍待总控决定，不能由 AI 默认选定。

维护流程分为三步，详细要求见 [AGENTS.md](AGENTS.md)：

1. **审查（candidates agent）**：先跳过已确认重复、已被认领、已立项或已交付的候选，再对照历史和新增 Skill / Plugin 等能力。发现完整重复立即回填查重结论、关联资产和依据；未认领且无任务的重复项标为 `Excluded`。待核重叠不冒充已确认重复。本阶段只维护候选审查，不创建开发任务。
2. **开始制作（用户选定后）**：先同步候选认领与原开发任务，再做来源审查、格式适配和功能测试，交付本地测试包、安装步骤及版本/哈希。任务使用 `Ready for Testing` / `User Testing`。等待用户明确确认当前包测试结束，确认前不 push、开交付 PR 或提交 Hub。
3. **提交（用户明确测试结束后）**：在关联进展汇报记录用户确认和测试包版本/哈希，问题解决后设 `Ready for Submission` / `Submitting`，再推送、PR 合入 ZIP、清理分支、同步台账、提交 Hub 和补齐两类截图。最终总控验收通过且全部交付条件满足后才设 `Completed` / `Delivered`；用户测试结束不等于最终验收。

`Development Tasks` 与关联 `Progress Reports` 只追踪具体插件的开发和修改。纯规则、文档、工具、CI 等仓库维护只在 GitHub PR 留痕，不创建插件任务、汇报或候选/资产记录，也不适用插件用户测试门槛。本仓维护 PR 同样在合入后清理对应临时分支。

认领、转派、多个任务与历史升级按[候选负责人、立项与交接](AGENTS.md#候选负责人立项与交接)维护；他人的认领不能被覆盖。任务表保留现有简化列，用户测试确认写入关联的 `Progress Reports`，两类截图仍分别存放。

在线追踪表统一使用英文页签、字段、状态与描述。维护者写入新记录时同样使用英文，保留 ID、成员姓名、链接和原始来源文件名；字段映射见 `tracking/tracker.json`。
