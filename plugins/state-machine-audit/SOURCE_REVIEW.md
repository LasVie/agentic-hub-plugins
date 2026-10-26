# 来源与适配审查

任务 `AH-20261026-state-machine-audit`；候选 `CAND-DSH-214`；负责人 Cai Zhenze。
名称映射：`AmethystLuna/logicprobe` → **状态机行为审计** → `state-machine-audit`。
内部ID `repo:agent-plugin:state-machine-audit`。用户于2026-10-26明确批准有限状态机审计范围；候选/原任务认领已写入实时表并回读，当前制作阶段。

## 差异和范围

模式 `ported`，许可结论 `verified`，适用于下列实际移植范围。Archify `repo:agent-plugin:archify-graph-tools@1.0.0` 仅验证/渲染结构化图谱，不探索守卫和变量配置；Process Workbench `repo:agent-plugin:process-workbench@1.0.0` 记录实际执行证据，不搜索假设行为。既有代码审查 `2e67d9c04b7a42db9fbd51b4e2df5392@1.0.0`、API契约检查 `0a2a5f70f4aa42d4a3982215cfd89351@1.0.0` 不提供本输入/动作/反例输出。Main的备份候选275及原工作区/分支/运行状态不属于此任务。

## 固定来源和材料

- 上游 https://github.com/AmethystLuna/logicprobe ，固定 `e1b5ac4a426c43878863092bc79387700a8189cb`，package.json版本1.4.2；与原研究记录npm1.4.1区别保留。
- 完整递归树、根LICENSE/package.json/README、Python引擎导入/守卫/更新/探索/不变量/主入口、模型schema与样例已检查。根MIT全文版权为 `Copyright (c) 2026 Amethyst Luna`，没有观察到嵌套LICENSE或NOTICE。
- `audit-upstream` 在固定材料目录上找到MIT候选证据；该自动结果仍为unknown，当前verified是人工逐项阅读实际许可和范围后的结论。

|实际材料|固定上游路径|用途/修改|许可与随包证据|
|---|---|---|---|
|`runtime/audit.py`|`tools/python/logicprobe-engine.py`（SHA256 `c56f5ac0159c9dc83a1af6ea46b2dff7e0febc22f26136c8d8e101e65ab615cd`）|守卫/fallback/更新语义和BFS搜索片段改写；严格有限子集，不复制或运行完整引擎|MIT全文 `licenses/logicprobe/LICENSE`，SHA256 `e22255c214b26dcc8eb5827f277db869d67c1e97dbdc08e7aae367eecfbe8148`|
|模型协议与中文说明|`skills/logicprobe/references/dsh-model-schema.md`（SHA256 `de2a5cc715252aba2cd1355e6c584da372c066771b436c72a68276cc5c469c0b`）|保留技术字段，独立中文描述有限子集；新增终态/有限域/重复更新严格约束|同一根MIT覆盖；第三方声明随包|
|原文件头|Python文件开始至import前|全文逐字保留，单独声明其描述的是上游而非本包范围|`licenses/logicprobe/UPSTREAM_HEADER.txt`|
|包装/SDK工具/用例|本次适配|闭合校验、只读路径与实际字节哈希确认、中文工具和虚构订单例子|没有额外第三方媒体或数据复用|

上游README中的Superpowers方法学提示、其它完整技能、启动钩子、Web界面、图标、截图、字体、benchmark与测试夹具不进入本包；没有对此类材料作概括授权结论。实际例子为本次虚构中文订单模型。无第三方运行依赖随包；Python标准库来自用户环境，openJiuwen SDK由宿主提供。无网络/账号/外部求解器/付费模型调用。不存在Apache材料或NOTICE要求；未改变或猜测新增代码的统一许可。

## 正确性修正与真实局限

上游S2只查静态出边、S3用图SCC、某些守卫枚举采样最多201个整数，Python不变量搜索预算耗尽可返回无违例。不能继承这些结果的广泛保证。本适配独立闭合校验后精确逐配置探索、检查真实启用迁移；上限/越域始终标覆盖未完成，不把未搜索分支判通过。只支持never-states与event-before-state，不自动从源码抽模；模型本身须经用户明确确认并绑定字节哈希。反例为BFS首个最短事件迹；报告展示省略与搜索未完成分开处理。

## 最终ZIP审查（2026-10-26）

市场包 `releases/agent-plugin/state-machine-audit/1.0.0/state-machine-audit-1.0.0.zip`，SHA-256 `0219fb71c2cb3f879640a434491b8ff9d1cf318718e066a328ed313fa8cb8964`；原生测试包 `plugins/state-machine-audit/test-packages/state-machine-audit-1.0.0-workswarm.zip`，SHA-256 `0caa0a0fc9653e8e90b13b0ddfe43a14c06a1da0c2039fce0b84bdd3a070aa4b`。市场包外层只有plugin.yaml与同名内层目录，原生包manifest位于根。

已分别抽取到 `dist/state-machine-audit/1.0.0/extracted-canonical/` 与 `extracted-native/`。14个原文件/市场包/原生包/实际安装目录的载荷哈希一致；没有测试、开发缓存或调试日志混入运行载荷。MIT完整版权、许可、免责声明与固定上游LICENSE逐字节相等，哈希符合provenance；原文件头与上游原始前缀逐字节一致，第三方声明注明实际移植及修改范围。所有载荷可严格UTF-8读取。JSON技术字段、API名及原始法律文本保留；README/技能/工具说明/人类可读结果和错误均为简体中文。中文有效与拒绝流程已在源目录、两种抽取包及实际宿主SDK中执行；见TEST_REPORT.md和package-verification.json、host-verification.json。

实际功能测试不等于用户确认；本任务仍在本地Build，等待当前中文1.0.0包的人工测试及原始截图。没有push、PR、Hub提交或发布，也没有作新的统一许可决定。

## 1.0.1 提交前修正（2026-10-26）

用户已明确确认1.0.0人工测试完成通过并提供12张原始截图，原件及哈希已保留；逐图审查指出inspect缺少初始状态，源码复核确认。1.0.1在inspect报告中直接返回模型 `init`，避免按状态数组顺序猜测，更新版本和中文确认说明。核心实际差异仅VERSION与新增init字段，探索算法/语义/限制及六个模型不变。新增回归把四个模型的状态顺序反转，验证真实初始状态、完整字节哈希和输入只读。

许可范围/固定上游不变。14个载荷中5个文件变化（README、manifest、runtime/audit.py、Skill说明、工具说明）；examples、MIT/原文件头、THIRD_PARTY_NOTICES逐字节不变。1.0.0的原始两种ZIP不覆盖，当前source版本为1.0.1。

1.0.1市场ZIP `releases/agent-plugin/state-machine-audit/1.0.1/state-machine-audit-1.0.1.zip`，SHA-256 `9280fb9d391e31136c66f7b088524309e03a257d03ce1a3e833c8bc70e21f212`；原生ZIP `plugins/state-machine-audit/test-packages/state-machine-audit-1.0.1-workswarm.zip`，SHA-256 `0846461cbb98e2c08398e65df2f8dffac55c96431d883f22867ffc66e05015cb`。两包已分别抽取，14文件与source哈希完全一致，许可证原文/文件头再次核对精确一致。实际安装/测试证据见当前TEST_REPORT.md。

依据AGENTS Phase2规则4/8返回原任务Build；已保存的1.0.0确认不能视为1.0.1确认。等待当前1.0.1人工完成及适用原始截图；未push/开PR/merge/Hub操作。

## 当前1.0.1人工确认与提交前复核

Cai Zhenze于2026-10-26明确确认当前1.0.1人工测试完成并通过，提供5张当前原始PNG；完整原件/尺寸/摘要见evidence/1.0.1/originals.json及USER_TEST_CONFIRMATION.md。截图显示四个模型均实际返回init=待支付、完整模型与哈希确认，以及真实审计/反例/死端/越域/上限与拒绝结果。已知初始状态输出缺陷已修复并经人工复测；没有剩余阻断。此前1.0.0证据和ZIP保存在本地ignored dist/state-machine-audit/history及原任务历史，避免将已取代包作为首次交付。

本次提交仅当前已确认1.0.1源码、测试/许可/安装文档、必要构建与公开夹具准备脚本、实际功能/包装/宿主记录、5个当前原始截图及摘要、原生ZIP和市场ZIP/artifact.json。所有包内字节和两种ZIP哈希保持上述测试值，原MIT/文件头/声明完整；无未满足分发条件。外层测试/确认说明更新不改变载荷。GitHub交接之后仍须等待Song Haoran接受；不执行Hub、Release或Asset Ledger操作。
