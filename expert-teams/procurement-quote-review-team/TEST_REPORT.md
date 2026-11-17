# 测试记录：采购报价比选复核专家团 v1.0.1

任务：`AH-20261116-procurement-quote-review-team`；负责人：Cai Zhenze。日期：2026-11-17。阶段为 Build / Ready for Testing；**v1.0.0 人工测试发现问题，v1.0.1 尚待人工复测，不作通过声明**。

## 实际故障与根因

独立检查了 `.local/manual-review-20261117-1/` 的技术、商务、复核员独立初评和正式复核、输入快照及实际生成的 evaluation.json/HTML，并用原 v1.0.0 ZIP 的原脚本复现。原案例摘要为 `5403d27cda57fdb0d235f3489ef409f1ae388d755f31edad0ef27850e5ca362d`；甲乙交期符合、质量各 4/5；丙交期 30 天超过必备上限 14 天，双方均判 fail，丙质量双方均 unknown/null。成本 5800/4400/1700 CNY 无争议。

两个本地原因叠加：旧报告只有字符串 issues，成功复算说明与能力边界也被当成全局阻断；脚本又把所有 unknown 全局阻断，未先区分明确排除报价与仍参与比较报价。实际输出含八条澄清、没有评审冲突、没有排名。旧的脚本化正例使用丙质量 5 分及空 issues，未覆盖真实失败条件。不是已确认的宿主安装或算术故障。

原始 v1.0.0 ZIP、artifact.json 保持原路径与原摘要；旧构建记录、实际失败报告/交付快照和四张用户原始图片及索引保存在 `evidence/1.0.0/`。`reproduction.json` 保存原脚本复现结果。旧 `.local` 会话资料未覆盖。图片是旧版失败证据，不是本版通过证据。

## 最小修正与兼容性

- 成员报告改为显式 schema 2：notes 为信息说明；issues 必须指定 global/offer 范围、eligibility/evaluation 类别及必要的有效报价标识。严格 JSON Schema 与运行时检查一致；不自动猜测、迁移旧字符串报告。
- 先检查全部报告覆盖、摘要、原文归属和引文，再判资格。对同一必备要求双方明确 fail 且没有资格未知/冲突的报价明确排除并保存理由。资格未知、单方失败、其他必备分歧或资格问题仍阻断。
- 仅已确认排除报价的非必备评价未知、评分分歧或费用缺口降为可见警示；全局问题及未排除报价的重要缺口/分歧继续阻断。排除不豁免错误引文、过期摘要、缺失条目或无效报告。
- 保留原 `weighted-min-cost-v1` 公式、权重、精度与并列规则，最低成本只从合格报价计算。没有硬编码 B/A 顺序，没有补写丙质量分。
- Leader、三名成员、共享 Skill、输入契约及 HTML/CSV/JSON/Markdown 中文输出同步更新，分开显示资格、阻断、警示与说明；保留独立初评、后续复核、最多一次有据修正和源快照。
- 案例 schema 仍为 1，原案例及三份原文字节不变。运行时仍只依赖 Python 3.10+ 标准库及既有 AgentGroup/文件/命令工具，不增加依赖、服务或宿主改动。

## 受影响的定向回归

命令：`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s expert-teams/procurement-quote-review-team/tests -p test_quote_review.py -v`。

源码与精确新 ZIP 解压脚本各 **51 项通过**。覆盖原失败报告显式适配、信息说明保留、已排除报价评价缺口/分歧、真正全局及资格阻断、合格报价评分/成本不一致、单方必备失败、其他必备未知、过期/伪造引文、完整条目与严格 schema、旧版拒绝、原有路径/并发/不覆盖/快照/转义防护。未跑与此改动无关的其他资产或全库套件。最终解压结果见 `tests/records/1.0.1/extracted-functional-tests.json`。

`member-reports-v2/` 是原失败报告的明确格式适配：仅重新分类说明/问题，保留原判断、原文引文、摘要、成本和原报告哈希映射；不是新模型或人工评审。实际新脚本计算：B 技术分 80、综合分 88、第一；A 技术分 80、综合分约 78.3448275862、第二。C 明确因 delivery 排除；质量仍 unknown/null，三条质量警示和五条说明保留，无阻断。输出不是硬编码。

JSON Schema Draft 2020-12 自检通过，三份适配报告通过、12 个结构负例被拒绝；证据 `schema-verification.json`。使用已安装开发环境的验证库，未安装或打包该依赖。运行时继续自行检查引文、摘要、条目、数值与问题相关性。

另有原创反例 `tests/fixtures/eligible-quality-unknown/`：只改乙质量原文为未提供可核对说明，新摘要 `aaedb26f0ff05d29f262cb66505517ee3f6b3a10d6d1d33a862427557dd8f8eb`。乙仍可满足交期但评分缺口影响甲乙结果，必须待澄清、无排名；不能沿用原案例 4 分。

## 精确包、格式与来源

- 原生 ZIP：`test-packages/procurement-quote-review-team-1.0.1-native.zip`，89785 字节，SHA-256 `b6292e0650856a100bb9dd82713a5f683ac64f33c1a3cdd3ad1e7622de35638a`。
- 规范包装 ZIP：`release/1.0.1/procurement-quote-review-team-1.0.1.zip`，41307 字节，SHA-256 `32adc9970b6c6095983c6cd9134a624714d9847c6f3027b961fb619ee429df39`。
- 16 个运行文件在源码、原生包和规范包逐字节一致。原生根 manifest.json 的 package_type 为 agent_group；包装 runtime.type 为 agent-group。包内没有测试数据、旧截图、报告、模型夹具、凭据、日志或开发缓存。
- 官方 CLI `openjiuwen-agentichub 0.0.1`，固定源 `c8ee4ef44be0453470114aa5a19f4e1017462907`，对干净暂存执行 validate/pack 通过；复建不改变已保存 ZIP。未使用不支持 Expert Team 的插件 packer。路径、类型、大小、压缩比、源包一致性及不覆盖检查通过；复用旧有八项归档负例。
- Finder 创建的普通 `.DS_Store` 保留在磁盘，打包器忽略它；符号链接和其他不安全类型仍拒绝。归档内容不允许该元数据。
- 新精确两包 JS preflight 均为 0 JS 文件、0 匹配，仅说明本地已知检查结果，不代表所有平台审批。
- 实际宿主 Python 对最终原生 ZIP 解压内容执行官方 `agent-group-creator/scripts/register_group.py --validate-only` 通过，实际 load_agent_group_package_bundle 加载四个 AgentTemplate。来源审查仍为 native 原创，没有新第三方复用。完整负载/来源/报告摘要由 `release/1.0.1/artifact.json` 记录。

旧包不变：原生 SHA-256 `ae9ae241de65459f7268f2a2dd43a38d41e3065c5c34c87ed9426fc817fb1cdb`；规范 SHA-256 `570f2120093565da3025e786454e9cc6bbae4c46a5c592835d5a3413b60c308f`。

## 实际宿主交接验证：有界脚本化夹具

宿主版本 `fa91394e42a7af731424222db82b02351e694de9`，SDK 来源 `f3f8f576164cc405c046e43079c8ad00ee17f0c4`，使用现有 Python 3.13 环境。独立状态、HTTP 6515、WebSocket 29515、Agent 28515、Gateway 30515、本机脚本化模型 6516；不复制真实模型凭据、不调用外部/付费模型、不改宿主或其他资产。

两次最终运行均从精确新原生 ZIP 真实导入/安装并通过真实宿主聊天/团队/命令链路，每次 262 条实时事件：

1. `host-independent-source-positive.json`：原案例，最终 reviewed、B/A 排名、C 质量未知和警示保留。
2. `host-independent-source-negative.json`：上述乙资料缺口反例，最终 clarification_required、无排名、C 仍排除并保留警示。

每次均验证：Leader build_team；技术/商务各自加载共享 Skill、运行实际已安装脚本并完成任务；复核员无依赖的第一任务只读原文形成独立记录，未收到初稿摘要；第二任务依赖三个已完成任务并实际读取技术、商务及独立记录，保存各文件 SHA-256 交接清单；正式复核完成后 Leader 执行 deliver。成员 shell 与交付均退出 0；持久化报告、HTML、两个 CSV、JSON、Markdown 与源快照一致。复核员独立记录的说明明确为未读初稿，未将预置数据冒充模型推理。

`host-evidence-index.json` 保留先前四次通道/顺序检查及其哈希和被后续证据取代的原因。先前单阶段复核没有证明独立初评顺序；本轮两阶段实测补足该检查。启动监听和切换实例释放端口曾有就绪竞争，仅发生在导入/聊天前；夹具增加有界本机就绪/自有进程退出等待，没有放宽业务断言或修改包。

这些是真实宿主执行及文件交接证据；所有判断来自确定性合成模型夹具，**不能证明真实模型的独立语义判断、中文遵循、抗提示注入、优于单专家或人工验收**。两个场景并非两个真实模型评审。

## 人工环境与未验证项

复用 <http://127.0.0.1:6411/>，只通过受支持的管理接口卸载/导入/安装本团。原已安装 v1.0.0 文件先备份，原 ZIP/历史输出不动；该实例既有会话 ID 与历史摘要保持不变。实际安装 16 文件等于新 ZIP，四成员、Skill、1.0.1 中文详情已由浏览器核对，见 `manual-host-upgrade.json`。用户原 6393 会话未改动。

6411 当前默认模型为 disabled-local-test；用户需自行选择已授权的可用模型，或在原已配置实例用原生上传入口安装本包。未改模型设置，未声称 GUI 文件选择/上传或真实模型复测通过。文件 URL 浏览器安全限制未绕过；HTML 内容/转义/一致性已有测试，真实浏览器渲染和人工语义检查留给用户。

人工步骤见 MANUAL_TESTING.md：新会话、新输出目录、真实三成员及两阶段复核，检查 B/A 排名与 C 排除/未知披露，再检查乙资料缺口仍阻断。须取得新版本两种精确 ZIP 的明确通过确认和原始截图后才可进入 GitHub 交付。

当前没有新的人工通过确认；没有同模型同工具同预算的单专家对照。实际记录不等于供应商真实性或正式采购合规认证。分支 feat/procurement-quote-review-team，基线 293e6ef8cc34286af0937d0be14e61b8ddedc230；已安全 fetch，更新的 origin/main 对适用规则无变化，未丢弃分支/并行工作。全部本轮实现/测试/文档/包位于本团队目录，未提交、推送、创建 PR、合并、Release 或执行 Hub 操作。
