# 域名续费比价 1.0.0 — 本地验证

Task AH-20261026-domain-renewal-research；Candidate CAND-CLD-138；Nguyen Trung Dung。
基线主分支 341277d；2026-10-26，Asia/Singapore。

## 已完成的实际验证

- 原生适配器单元/契约测试 **15/15 PASS**，真实 openJiuwen/MCP 类型，只有单元用例替换传输边界。
- 源码实际原生 Tool.invoke → 公共 MCP 服务 **11/11 PASS**：价格筛选、注册商、缓存批量证据、
  后缀报价、估算、搜索链接、命名指导、历史、表单说明、名称比较和一次 example.com 检查。
- 使用 IANA example 名称，无私密项目名称、无凭据、无购买、无模型调用。
- 可选 Radar 未调用；其数据有独立非商业条款。单元测试覆盖接口和许可/未知值原样保留，不声称实时 Radar 数据已验证。
- **真实 DeepAgent + SkillUseRail + Runner 资源管理器通过**：完整 manifest 加载，12 个原生卡片在
  面向模型的工具清单中可见且为 direct；已注册工具执行真实三条报价查询；中文私密额外字段在联网前拒绝；
  13 个资源引用（12 工具 + 1 Skill）卸载成功，打包源码字节未变。
- 环境：Windows，宿主现有 Python；openJiuwen 0.1.19（editable 源码）、MCP SDK 1.29.0、jsonschema 4.26.0。
- 远端观察：Cheapest Domains API/MCP 1.12.0，协议 2025-11-25；固定集成来源仍为 0.11.0。
- 当前回应保留部分覆盖、来源日期、价格样本、unknown/null、retryAfterSeconds；不自动重试。

源码命令：

```text
python -B -m unittest discover -s tests -p test_domain_renewal_research.py -v
python -B plugins/domain-renewal-research/tests/live_checks.py --payload <source-payload> --report <private-local-report>
python -B plugins/domain-renewal-research/tests/host_checks.py --payload <source-payload> --report <private-local-report> --live-price
```

实际公共响应与宿主日志保存在忽略的 .research/domain-renewal-research 中，不随 ZIP 分发。
最终包哈希、逐文件比较、提取包复测和仓库检查在 package-verification.json 中记录。

## 仍待用户验证

初始 Ready for Testing 时用户确认与截图尚未收到；2026-10-26 后续确认及原始证据已补齐，见文末及 USER_TEST_CONFIRMATION.md。
未声称已完成前端对话、ZIP 文件选择器或内嵌 MCP App 渲染，也未调用真实模型。
源码宿主验证证明工具绑定与实际执行，不代替用户的完整会话验收。
Hub 操作由 Song Haoran 负责；未创建交付 PR、推送、发布或登记 Asset Ledger。

## 最终提取包与仓库检查

- Native SHA-256：`af6ef3967d0dcb88739abf6bf0df5e88e4eb39f98477b536386d0e93159b0d26`。
- Canonical SHA-256：`532fefbc5aa7a94fa08ad76270ad9d491e8f4ffe7fac12713a3e4b1c6945a82c`。
- 原生、外层及源码 **8 个文件逐字节相同**，UTF-8/LF、无 BOM；两包 CRC、路径安全、声明类和完整许可核对通过。
- 提取原生 ZIP 后，真实 SDK **15/15** 适配器/契约测试通过；公开服务核心查询 **3/3 PASS**。
- 提取包 **真实 DeepAgent/SkillUseRail/Runner** 再次通过：12 个原生工具在模型侧清单中可见、中文额外字段拒绝、
  注册资源中的实际价格查询成功、全部插件引用卸载、提取文件哈希不变。没有模型调用。
- SDK 用例在新的 Python 子进程中运行，避免其他仓库测试对 SDK 日志单例的污染；没有改动产品代码或宿主日志配置。
- `asset_release.py check-repo`：本分支 **35 资产 / 44 ZIP PASS**；独立 LF 基线 **34 / 43 PASS**。
- 广泛 Windows 测试不声称全绿：不含本端口的独立 main341277d 为 290 测试、62 failures、75 errors、60 skips；
  本分支 293 测试具有**相同的失败/错误标题集合**（62 failures、75 errors、60 skips），没有新增失败标题。
  新增根测试是 2 个包元数据检查及 1 个隔离宿主测试入口，后者实际执行 15 个测试。
  既有测试包括拒绝 Windows 的 source-preview-recovery 路径和 agent-letter 测试硬编码的 `/private/tmp` SDK 日志目录。
  原始广泛测试产生的 11 个新日志污染错误已通过本端口测试进程隔离解决；保留原日志，不归咎于产品实现。
- 不声称 clean main 的 check-repo/test_playground 失败，也没有修改其他插件来通过检查。
- CUA 当前 apps=0、browsers=0：中文名称、帮助、错误和模型可见 schema 已做真实 SDK 检查，实际前端渲染/文件选择器仍待用户。

`package-verification.json` 记录全部字节哈希和摘要；`host-verification.json` 记录实际宿主结果。
私有本地原始响应、基线和日志保留在忽略的 .research/domain-renewal-research，不随运行包分发。
初始构建状态为 Ready for Testing；后续当前版本用户确认和原始截图已收到，交付状态见 USER_TEST_CONFIRMATION.md 与 PR。

## 2026-10-26 用户确认与原始截图补充

Nguyen Trung Dung 在当前会话明确表示 “Confirmed for chinese version, can you port the English version too, if that is necessary”。
该确认关联此前提供、哈希未变的中文 1.0.0；不复用其他插件确认。七张已提供的截图在 Windows Screenshots 目录找到原始文件，
逐张查看后逐字节复制到 evidence/1.0.0，哈希、原名、尺寸和证据边界见 evidence.json。
画面可见插件启用、注册商/续费比较/估算/缓存查询/命名表单调用；部分返回在裁剪范围外，不据此声称原始结果全部可见。
参数拒绝截图显示智能体替换了输入，最终 INVALID_ARGUMENTS 不在画面内，因此不将它计为该手工用例通过。
准确中文参数在真实 SDK 测试中独立验证拒绝；目前无已确认的适配器故障。
仅更新外围证据、报告和发布记录，运行文件、版本、原生及外层 ZIP 均未改变。
English prompts added outside runtime; explicit English responses are supported by the existing Skill rule. English UI and optional Radar remain untested.
