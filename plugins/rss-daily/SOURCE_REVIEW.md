# 来源、功能差异与再分发审查

2026-10-27；负责人 Wang Jie；候选 CAND-DSH-266；任务 AH-20261027-rss-daily。名称映射：shangjian2023/dsh-rss-daily → 资讯晨报助手 → rss-daily。内部 ID：`repo:agent-plugin:rss-daily`。

## 规则、登记与功能范围

已阅读工作区流程复盘全文和最新 main d3b325f 的完整 AGENTS.md。开发目录是独立 Git worktree `agentic-hub-plugins-rss-daily`，不更改 Annotate 或 fools-errand 工作目录，不在未取得当前包用户测试确认前提交或推送 PR，不操作 Hub。

实施前已在原共享表按 Candidate ID 核对无认领和任务，登记 Planned / Wang Jie / AH-20261027-rss-daily，并创建 Researching / Plugin / New Asset 任务，实际回读一致后才克隆源码。已有 RSS 工具 blogwatcher `24ad7d8aea5a4ac08683ae8a92c04ec9` e7bda4f 提供订阅更新和已读管理；不重新制作其通用订阅 CLI。与 newsletter-growth-team `6cda66d3f34048eab98a194179ff3c47` 1.0.0、竞争情报监测团队技能 `47dc6a921d3b4a6d939f5d5526ed44c1` 1.0.0 相比，本范围新增实际候选证据绑定、中文编排落稿、用户确认后消费条目和可恢复的发布状态，不是写作提示词或信息收集计划。已有订阅监测仍是既有能力入口，本包只处理日报工作流这一增量。

## 固定来源与许可

上游 https://github.com/shangjian2023/dsh-rss-daily ，0.7.0，提交 `a6c2d71238f03af3f3dd8cf1ac0033000de45d02`。研究副本保留于工作区 upstream/dsh-rss-daily，未执行原项目安装脚本。根 LICENSE 是完整 MIT 文本，版权 `Copyright (c) 2026 shangjian2023`；未发现子目录单独许可证或 NOTICE。不能把 README 的生产质量宣传当作本次验证结果。

| 材料 | 实际使用与变化 | 覆盖及随包位置 |
| --- | --- | --- |
| py/daily.py | 改编 tokenize、Jaccard 标题近似去重、标题指纹，以及 fetch/finalize/confirm 分阶段工作流；不复制完整 1255 行实现 | 根 MIT，runtime/engine.py；完整许可 licenses/dsh-rss-daily/LICENSE |
| mcp/server.py、mcp/README.md | 参考四阶段工具接口与用户确认约定；改为标准库 stdio 传输，不分发第三方 mcp SDK | 根 MIT，runtime/server.py 和中文 Skill；修改摘要见 THIRD_PARTY_NOTICES.md |
| py/sources.default.json | 选用少数派、Solidot、Hacker News 的公开 RSS 地址事实，非原文内容；限制数量并允许明确配置 | 根 MIT 的清单部分；data/sources.json |
| README 和编辑规则 | 中文改写用途、证据要求和操作限制，明确模型不等于事实核查器 | 根 MIT；包内 README、Skill 和第三方声明 |
| 图片、字体、页面组件、DSH/Cordis 实现 | 不复用、不打包、不依赖 | 排除 |
| feedparser、mcp、npm 依赖 | 不分发、不运行；XML/HTTP/状态及传输仅使用 Python 标准库 | 无新增第三方运行依赖；不把开发环境或模型作为再分发内容 |
| 实际新闻文本、站点服务 | 不随代码包预抓取或再分发文章；运行时只取公开订阅标题/摘要及原链接 | MIT 不授予站点内容、商标或服务的额外权利；遵守来源限制，不绕过登录或访问控制 |

完整 MIT 原文与免责声明按字节保留，SHA-256 `b3d60c37bbcb0c53c5eda5d884574e0b2f48b8f85f2307becb5689e80d88a2da`；保留原作者和来源，记录本次修改，不新增虚构版权、不暗示原作者背书。provenance 记录实际覆盖文件、固定来源和许可证据，不声称重新许可整个团队仓库。

## 安全及适配取舍

上游有 TLS 验证失败后关闭验证重试的路径，另有 newsflash `/e/{id}` 链接拼接，且 issue #8 报告相关链接 404。本包不移植这两条路径：始终校验证书，只接受公开 HTTPS RSS/Atom，来源链接来自解析到的实际 feed，不合成第三方事件地址。该取舍不是宣称上游问题已修复。

移植保留实际抓取、时效过滤、同批及确认历史去重、模型编辑、来源绑定落稿和明确用户确认的闭环。DSH 原生面板、后台定时、webhook/微信投递和“零上下文”客户端插播不属于本轮交付，不伪装成在 WorkSwarm 可用。没有第三方账号、密钥或依赖安装步骤；宿主仍须有 Python 3.9+。示例是独立演示材料，不能冒充真实新闻。

## 验证状态

源代码分别在 Python 3.9.6 与 3.11.17 通过 43 项功能测试；最终 ZIP 的实际解压载荷在系统 Python 3.9.6 通过相同 43 项，并通过独立 MCP JavaScript SDK 的 27 条含实网断言。三个公开源实际返回解析成功，各取最多两条，得到六条候选；没有以演示材料冒充真实新闻。完整命令、原始计数及 WorkSwarm 创建器拒绝 MCP 的检查边界见 TEST_REPORT.md。

规范交付包 `releases/agent-plugin/rss-daily/1.0.0/rss-daily-1.0.0.zip`，SHA-256 `1253b65bb649ae2839dc8bc31c14d723c02468f7403af1bc27496ac05e2754ad`。工作区原生测试包 `local-tests/rss-daily/1.0.0/rss-daily-1.0.0-workswarm.zip`，SHA-256 `2f8815b00cb46c6907de62781c0574b2ee4c58e70aecaafbeb98bf73dc247588`。两者实际运行载荷与源码逐字节一致，共十三个文件；二者仅外层结构不同。规范归档包含仓库要求的 plugin.yaml，原生包以 manifest 插件目录导入宿主。

完整 MIT 已从最终原生包解压核对，仍为 `b3d60c37bbcb0c53c5eda5d884574e0b2f48b8f85f2307becb5689e80d88a2da`，与 provenance 和固定上游一致。内层含完整许可、修改说明与来源，无额外 SDK/图标/字体或第三方实现混入。许可审查只覆盖上述实际使用材料，不扩展到各网站文章版权或宿主验收。

中文包 1.0.0 在开发交接时冻结并等待用户实测。2026-10-27 17:56 UTC+8，Wang Jie 提供当前包九张 WorkSwarm 测试截图并要求核对正确后提交 PR；已核对安装载荷十三文件与原生/规范包一致，结果符合既定流程。确认与原图清单另见 USER_TEST_CONFIRMATION.md、evidence.json。许可及最终 ZIP 均未因补充证据而改变，可以进入 GitHub 提交阶段；尚无负责人最终验收，不操作 Hub。
