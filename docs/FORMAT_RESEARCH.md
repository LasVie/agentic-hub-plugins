# Agentic Hub 包格式调研

核对日期：2026-10-22。调研只读取 ZIP 和官方文档/校验代码，没有运行样包或提交新资产，也没有把他人的样包作为团队成品收进本仓。

## 实际下载样包

完整事实记录见 [samples.json](research/samples.json)，包含来源、固定公开版本、下载文件列表、文件数、大小和 SHA-256。四份文件均通过 Hub artifact API 返回的 SHA-256 核对。

| 类型 | 名称 | 版本 | 文件条目 | 原生入口 | 包内许可证文件 |
| --- | --- | --- | ---: | --- | --- |
| Skill | wechat-article-delivery | 1.0.0 | 15 | 根级 SKILL.md | 有 LICENSE、NOTICE.md 及上游 MIT 文本 |
| Skill | swarmskill-creator | 2.0.0 | 17 | 根级 SKILL.md | 未找到；需再核查上游 |
| Plugin | pr-quality-check | 1.0.0 | 12 | 根级 manifest.json，package_type=plugin | 未找到；需再核查上游 |
| Plugin | spanner | 1.0.0 | 9 | 根级 manifest.json，含 skills 和 tools | 未找到；需再核查上游 |

“包内未找到”不是“确定没有授权”，也不是“允许复用”；这里只记录检查结果。公众号样包声明按材料区分 Apache-2.0 与 MIT，说明不能仅看一个顶层许可证名就推断所有文件的许可。

## 下载载荷与发布包装

官网下载得到的四份 ZIP 均为原生载荷，根上没有 plugin.yaml。网页发布 Skill 时选择技能目录，前端生成市场包装；发布 Plugin 时可以上传原生包，也可以上传包装包。不能把“下载 ZIP 根布局”直接等同于“发布市场外壳”。

本仓统一产出明确的市场包装 ZIP：`<slug>/plugin.yaml` 加 `<slug>/<slug>/` 内层载荷；Skill 内层入口为 SKILL.md，Plugin 内层入口为 manifest.json。保留原生源码以便 Skill 网页选择目录。市场外层不放 tests、SOURCE_REVIEW、tracking 或任意第二个载荷目录；这些开发资料在仓内单独保存。需要随包的 LICENSE/NOTICE 等材料放入内层。

Plugin 的外层 runtime.type 为 agent-plugin，内层 package_type 为 plugin、id 等于外层 name、版本完全一致。Skill 和 SwarmSkill 的外层 runtime.type 都是 skill；SwarmSkill 由 kind 和 roles 决定。名为 swarmskill-creator 的样包本身就是普通 Skill，因此不能按名称猜类型。

Hub 对部分 capability 文件采用宽松结构校验；本仓更严格，声明的文件必须存在，并单独执行实际功能测试。样包中的历史 version 写法也不能覆盖本仓统一的 x.y.z 交付约定。

## 官方依据

以下均固定到官方仓库提交 `0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a`：

- [Agent 资产开发规范](https://github.com/openJiuwen-ai/skillhub/blob/0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a/docs/zh/5.%20开发指南/Agent资产.md)
- [Agent 资产发布步骤](https://github.com/openJiuwen-ai/skillhub/blob/0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a/docs/zh/4.%20用户指南/Agent资产发布.md)
- [Skill 布局与 frontmatter 校验](https://github.com/openJiuwen-ai/skillhub/blob/0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a/marketplace/plugins_market/validation/types/skill.py)
- [Plugin 的 manifest、身份与版本校验](https://github.com/openJiuwen-ai/skillhub/blob/0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a/marketplace/plugins_market/validation/types/agent_asset.py)
- [包装外层限制](https://github.com/openJiuwen-ai/skillhub/blob/0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a/marketplace/plugins_market/validation/types/wrapped_asset.py)
- [网页 Skill 打包器](https://github.com/openJiuwen-ai/skillhub/blob/0036e5e8493cfadb4ea2d56e10c7c0edc4dd950a/frontend/src/utils/buildSkillPublishZip.ts)

当前已核对的 Hub 通用限制：ZIP/累计解压 512 MiB、条目数 1000、预检压缩比 50；图标如有为合法 PNG 且不超过 5 MiB；名称/展示名/描述/标签还受字段长度约束。本仓额外将 ZIP 限制为 95 MiB，并使用确定性不压缩成员以避免压缩比误报。本地校验器不是 Hub 全部内容安全规则的完整复刻，最终仍以平台实际响应为准。

后续平台格式改变时，应一起更新此文、模板、打包器与契约测试；不能只改文件扩展名或凭旧样包继续发布。
