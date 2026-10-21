# Agentic Hub 插件交付仓

保存团队已开发、测试的 Skill / SwarmSkill / Plugin 源码与发布 ZIP。AI 维护者先阅读 [AGENTS.md](AGENTS.md)。

- `skills/<slug>/`：技能源码、打包 metadata、来源审查。
- `plugins/<slug>/`：插件源码、manifest、来源审查。
- `releases/<type>/<slug>/<version>/`：经测试后通过 PR 合入的 ZIP、SHA-256 和载荷清单。
- `templates/`：开发脚手架，不能作为已有成品统计。
- `tracking/tracker.json`：同一份在线追踪表的页签及字段映射；维护时仍须读取实时表头。
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

交付顺序：开工登记与查重 → 来源检查/独立实现 → 功能测试与打包 → PR 合入 ZIP → 用户提供测试和 Hub 提交截图 → 同步资产总账、开发任务和进展汇报。Hub 提交和审核通过分开记录。
