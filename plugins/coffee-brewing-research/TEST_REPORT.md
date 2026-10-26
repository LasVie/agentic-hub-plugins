# 咖啡选豆与冲煮 1.0.0 — 实际验证记录

Task AH-20261026-coffee-brewing-research；Candidate CAND-CLD-134；负责人 Nguyen Trung Dung。
初始基线 main `68e231af7fe3a6fdc34c2983fcf19167309ce0aa`，独立分支 `port/coffee-brewing-research-20261026`。

## 环境与测试边界

2026-10-26 使用现有 WorkSwarm 虚拟环境的 Python、实际 openJiuwen 原生 Tool/ToolCard、MCP SDK、httpx、jsonschema。
SDK 来自本机已安装的编辑式宿主源码，实际版本随 host-verification.json 记录。
不更改或重启用户正在使用的 jiuwenswarm 服务，不新增模型、账号或密钥。
单元用例只模拟远端传输边界；另有实际公开服务和真实 DeepAgent/SkillUseRail/Runner 验证。

## 已完成的本地契约验证

- 原生 SDK **15/15** 用例通过，根发现入口 **3/3** 通过（其中一个在新解释器中实际执行这 15 项）。
- 覆盖八卡中文/DIRECT/唯一性、全工具路由、美元预算/limit/枚举/数组/空白/非有限数字、价格上下界、
  中文原样输入、额外私密字段及错误包装在联网前拒绝、原始日期/空值/零/配方和热度依据保留、
  空结果、真实错误、模式变化、限流等待、超时/取消、无自动重试、错误脱敏和流式结果。
- 初次文档测试误要求“私密”字面词，已有说明实际写“不发送完整会话”等具体禁止项；修正测试判断后通过。
  没有通过篡改运行行为隐藏失败。根测试入口已隔离，避免其他仓库测试修改 SDK 日志单例影响用例。

## 实际服务诊断

初始化与工具发现证实远端 **1.0.2 / 2025-03-26 / 八工具**，与上游集成 1.0.0 分开记录。
本地适配器的检索、档案、相似与推荐先成功。
首次比较使用检索刚返回的真实 ID，服务却返回其中一个 ID 未找到；保留原始失败记录
`.research/coffee-brewing-research/live-source-id-failure.json`，不声称该次比较通过。
另一次明确诊断改用两条记录的**实际完整原名**，比较成功；不是适配器自动重试或隐式替换输入。
此为已观察到的远端 ID 解析限制，原因未进一步推断。Skill/README 和用户指南说明原名用法及诚实错误报告。

目录还会在 espresso 分类返回 `pods_only=true` 的胶囊，因此 Skill 明确保留 formats、pods_only 与 brew_methods，
不能把胶囊当整豆或默认用于 V60。未通过改写返回数据掩盖该情况。

完整八工具、真实宿主、提取包与最终哈希验证完成后在下方追加实际结果；本段不预先声称待执行项目通过。

## 用户测试与交付

Nguyen Trung Dung 于 2026-10-26 在当前会话明确回复 **“Confirmed working”**，同时提供本版本八张截图。
已找到八张对应原始 PNG、逐一查看核对，并无损复制至 evidence/1.0.0；原名、尺寸和哈希见 evidence.json。
确认关联本报告同一 1.0.0 原生与外层 ZIP，二者哈希及八个运行文件均保持不变。
确认 Report ID：RPT-20261026-coffee-brewing-research-confirmed-100。
图像实际覆盖启用、Skill 读取、多项工具完成及本地拒绝；若干截图未显示完整原始结果，搜索图仅显示 Skill 调用，
错误图显示 ok:false 但截断完整错误代码/提示。保留这些证据限制，不虚构手工原始输出验证。
前端会话成功由用户明确确认；独立 SDK/公开服务/宿主验证分别记录。不声称实际 Hermes CLI 模型会话已测试。
完整材料已收集，可进入提交；PR、图像永久链接和实际 Linux CI 必须在合并前验证。

## 最终实际结果

- 源码与提取原生 ZIP：真实 SDK 各 **15/15**，根发现入口各 **3/3 PASS**。
- 源码八个不同工具均有真实公开服务成功记录；不是一次全绿批次。首次 ID 比较失败已保留，
  实际完整原名比较成功；后续查询遇到真实 429，适配器保留 Retry-After 且未自动重试。
  等待后仅完成余下工具，八项覆盖记录见忽略目录 live-coverage.json。
- 提取包检索/档案两项先成功，配方查询遇到限流；等待后单独配方调用成功，共三个关键查询均有成功记录。
  不将首次限流伪装成查询成功。
- 实际中文 query=巧克力、limit=1 的查询成功返回 1 条实际记录，保留中文成功提示；
  适配器没有翻译/替换输入或伪造咖啡。price_min=30、price_max=20 在联网前返回中文 INVALID_ARGUMENTS。
- 源码及提取包均使用实际 **DeepAgent + SkillUseRail + Runner**：八个 DIRECT 工具对主智能体可见，
  真实注册资源中的目录查询成功，额外中文私密字段本地拒绝，九项引用（八工具和一个 Skill）卸载，运行文件字节不变。
  没有模拟模型、智能体、加载器或执行真实模型调用。host-verification.json 记录实际 SDK 版本。
- **8 个运行文件**源码/原生/外层/提取字节一致，UTF-8、LF、无 BOM；安全路径、ZIP CRC、完整 MIT 原文核对通过。
- Native SHA-256：`f7b178268153b8075460d5ba6e1ae1f72ab8e2dd1106576596eb54f2e916bb4b`。
- Canonical SHA-256：`974eacf436ce73b99571e03c30b41877b6a7318609bf73f5b84badfc8ecd31ea`。
- `asset_release.py check-repo`：**36 assets / 45 ZIPs PASS**。未重新运行完整 Windows 仓库套件，不声称全绿；
  Build 阶段未运行 GitHub CI；后续提交仍须通过实际 Linux CI。
- 中文名称、说明、schema、Skill、错误和原样中文查询已验证；用户已明确确认前端当前版本工作并提供八张原始截图；未进行实际 Hermes 模型会话。
- 实际源服务响应、限流/失败和诊断日志仅保存在忽略的 .research，未打包或分发目录结果。

当前版本用户完成确认和八张原始截图已收集，可进入 Submit；实际 PR/图像链接/CI 验证记录随后通过 PR 和 tracker 补充。已知上游 ID、限流、胶囊/器具限制均写入中文指南。
