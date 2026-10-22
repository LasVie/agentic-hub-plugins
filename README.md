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

交付顺序：开工登记与查重 → 来源检查/独立实现 → 功能测试与打包 → PR 合入 ZIP → 用户提供测试和 Hub 提交截图 → 同步 Asset Ledger、Development Tasks 和 Progress Reports。Hub 提交和审核通过分开记录。

“Development Tasks”及关联“Progress Reports”只追踪具体插件资产的开发和修改，包括新增、移植、改造、修复和升级。规则文档、通用模板、打包工具、CI 等纯仓库维护只在 GitHub PR 留痕，不登记插件任务、不更新 Plugin Candidates 或 Asset Ledger；混合 PR 只登记实际插件变更。

来自候选页的任务使用稳定候选 ID 关联，立项、转派和收尾时同步候选与任务的负责人。仅认领仍为“To Evaluate”，建立任务后为“Planned”，全部交付条件及总控验收通过后才为“Delivered”。具体规则见 [候选负责人、立项与交接](AGENTS.md#候选负责人立项与交接)。

在线追踪表统一使用英文页签、字段、状态与描述。维护者写入新记录时同样使用英文，保留 ID、成员姓名、链接和原始来源文件名；字段映射见 `tracking/tracker.json`。
