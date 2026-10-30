# 离线分子结构工作台测试记录（已确认人工测试版本 1.0.1）

- 日期：2026-10-28；负责人：Cai Zhenze。
- Candidate ID：CAND-EXT-002；Task ID：AH-20261028-molecule-structure-lab。
- 当前结论：2026-10-30，Cai Zhenze 明确确认 1.0.1 人工测试完成并通过，授权第三阶段。开发验证与用户原始证据分别记录。
- 以下保留 1.0.0 失败及 1.0.1 开发复测历史；最新结论见末尾人工测试确认。历史 dist 文件和失败包保留在原工作区，不作为当前发布材料。
- 环境：macOS arm64；Python 3.12.14；openJiuwen 0.1.19；Node.js 24.19.0（源与提取包）/ 22.23.3（宿主安装包）；RDKit 2026.09.1；Codex 内置浏览器（Chromium）。

## 实际执行

`MOLECULE_WORKBENCH_NODE=<已有Node绝对路径> <宿主venv>/bin/python -B plugins/molecule-structure-lab/tests/test_core.py`

13 项测试全部通过，包含真实 WASM 描述符/匹配、无查询与不匹配区分、普通氢规范化、未知原子/未指定键拒绝、SMARTS 通配语法、非法/中文/超限输入、缺少 Node、禁止 fetch 的本地引擎执行、工作区与符号链接、外部状态保护、启动/复用/停止、Host/Origin/路径访问限制和确认参数。

`tests/test_sdk.py --payload <插件载荷目录> --output <报告路径>` 使用真实 SDK 的 manifest loader、resolver 和 BuildContext，验证两个原生 Tool、一个 Skill、Tool.invoke/stream、分析/错误及本插件独立服务生命周期。源目录验证已通过；最终安装载荷的结果见随附 sdk-verification.json。

实际浏览器操作已验证：

| 项目 | 观察结果 |
| --- | --- |
| 阿司匹林 + 苯环 SMARTS | 13 原子、13 键；平均分子量 180.159；TPSA 63.6；首个匹配原子 4–9，图中六个原子高亮 |
| 改为乙醇并重新分析 | 3 原子、2 键；平均分子量 46.069；苯环不匹配 |
| 修改输入但未重算 | 旧结果标记失效，两个导出按钮禁用 |
| 无 SMARTS | 清楚显示未执行子结构查询，与没有匹配区分 |
| 非法 SMILES C1CC / SMARTS [ | 实际中文错误；旧结果不能导出 |
| C* / C~C | 实际返回 unsupported_atom / unsupported_bond，不生成误导描述符 |
| SVG / JSON 下载 | 两个实际文件已下载；SVG UTF-8 元数据与 JSON 相同，中文名称正确；SVG 包含可显示的结构路径和高亮 |
| 错误后重新分析 | 可恢复正常结果，无须重启宿主 |

发现并修复的开发问题：未修改的上游 Embind 绑定需要 Worker 内动态生成函数，故仅本插件 Worker 响应开放对应 CSP 指令；主页面仍禁止字符串求值。SVG 原有编码声明与新增中文元数据不一致，导出已改为显式 UTF-8 并实际下载复核。未知原子和未指定键现明确拒绝。

## 宿主和包验证

隔离宿主 `/private/tmp/state-machine-audit-workswarm-20261026`，源码提交 `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`。前端 6392、后端 WebSocket 29290 及前端代理 `/ws` 的 ping/pong、config.get 和扩展列表均实际通过。仅导入和安装本插件；没有付费模型调用。安装后的配置及既有插件字节对比、载荷 SDK 测试和 ZIP 提取结果见本目录验证 JSON。

运行 `python tools/asset_release.py check plugins/molecule-structure-lab` 与 `pack`；市场 ZIP 和原生 ZIP 应具有逐文件一致的内部载荷，原始上游 JS/WASM 和许可材料散列必须一致。最终 ZIP 路径和 SHA-256 见 MANUAL_TESTING.md 与 releases 下 artifact.json。

## 已知边界与尚未验证事项

- 仅验证上述 macOS / SDK / Chromium 环境；Windows 不支持；其他浏览器和宿主版本未验证。
- 没有实际切断整机网络；资源均来自插件自身回环服务，Node 引擎在 fetch 禁用条件下实际通过。不宣称已完成全系统网络抓包或断网测试。
- 没有调用付费模型做会话 A/B；原生工具真实解析/调用已验证，用户仍需验证其当前会话中的工具发现与使用。
- 浏览器超时/取消、长期运行及移动端布局未做完整人工压力测试；不据此宣称已验证所有平台或极端输入。
- SMARTS 只返回首个匹配；不统计全部匹配、不额外强制手性。索引对应 RDKit 规范化后的图；普通显式氢可能被移除。
- 描述符不表示药效、毒性、真实物质安全或实验结论。本插件没有反应预测、三维构象或合成规划。
- 2026-10-28 首次交付时尚无用户人工测试确认，状态曾为 Ready for Testing；现状以下方失败复测记录为准。

最终实测：原生 ZIP 11,201,681 字节、市场 ZIP 11,207,708 字节；60 个载荷文件完全一致。提取包与安装包的真实 SDK 测试均通过。原生扩展 API import/install 成功，界面“我的扩展”可见；已安装状态 connected。32 个既有插件文件及宿主配置 SHA-256 完全不变。最终安装包页面再次成功运行阿司匹林并实际下载 SVG/JSON；UTF-8 元数据一致，6 个高亮原子。系统默认 python3 缺少 PyYAML，未安装新依赖；改用宿主已有 venv 后 check/pack 通过。宿主当前模型为 disabled-local-test，未进行模型会话测试。


## 2026-10-29—30：首次人工失败调查与安装隔离复测（历史记录）

**用户人工测试结论仍为失败，等待复测；未标记通过。** 原始截图按字节保存在 `dist/molecule-structure-lab/1.0.0/failure-evidence-20261029/`，摘要清单为 `originals.json`。本轮继续原任务 `AH-20261028-molecule-structure-lab`，不新建任务，不执行 GitHub 或 Hub 交付。

实际失败会话 `web_1a186519d4d_e94cefdd7b69` 的日志证实：调用发生在 6393 宿主，其安装根为 `.research/ebook-workswarm-20261027/data/agent/workspace/plugins/plugin_packages/local/molecule-structure-lab`；旧人工目录中的 `server.json` 则记录 `/private/tmp/state-machine-audit-workswarm-20261026/data/agent/workspace/plugins/plugin_packages/local/molecule-structure-lab`（6392 隔离安装）。记录的结构、UID 和权限有效，但不是调用方的安装根。`read_state` 在连接服务或创建进程前检查 `root`，所以两次实际调用返回 `invalid_runtime`。这是跨安装测试目录交接错误；没有发现必须修改载荷的插件缺陷。

旧记录、旧服务及 Main 环境均保留；旧记录 SHA-256 仍为 `eb0141092187c5734545c48551b09efc456f13d0da583f51113089f58166b828`。新目录只供 6392 安装使用：`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/molecule-structure-lab/1.0.0/manual-workspace-6392-retest-20261029`。

本轮验证严格区分调用层级：

| 项目 | 实际结果与边界 |
| --- | --- |
| 已安装插件的 SDK Tool.invoke | 使用真实 SDK manifest loader/resolver 解析 6392 已安装载荷；独立进程调用 `molecule_workbench`，只读 status、经授权 start、重复 start 安全复用和运行 status 通过；真实返回本机 URL |
| 运行中 WorkSwarm 会话调度 | **仍未验证**。此宿主未发现无模型原生工具执行接口，模型为 disabled-local-test；没有付费模型调用或配置修改。用户明确选择“Leave running-host verification pending”。独立 SDK 调用不作为运行宿主验证 |
| 启动环境 | 首次受执行沙箱限制的 SDK 尝试返回 server_failed，仅留下本轮自己的空锁文件；在获准的回环网络执行环境中，同一载荷成功启动。没有覆盖旧记录或降低所有权检查 |
| 浏览器与实际返回地址 | 从 SDK 实际返回的 URL 打开正常浏览器。阿司匹林 13 原子/13 键、amw≈180.159、TPSA≈63.6；首个苯环匹配 4–9，真实结构高亮 |
| 编辑失效 | 修改 SMILES 和 SMARTS 后旧结果失效，导出禁用；乙醇重算成功，苯环不匹配；清空查询明确显示未设置查询 |
| 错误和恢复 | invalid_smiles、invalid_smarts、unsupported_atom、unsupported_bond 均显示中文原因且旧结果不可导出；CCO + SMARTS `*` 恢复成功，首个原子索引 [0] |
| 实际下载 | SVG、JSON 均实际下载并保留；SVG UTF-8 元数据与 JSON 完全相等，含 6 个高亮原子。SVG SHA-256 `9f6ca33d0931a813649d979c4017e3f24696a8ccd01e4f3adc30f3eed90a4a1d`；JSON SHA-256 `3c54b22a8c10e8ee15a36e21f8ae024dd2505364c978ee5e76e09b579b7c1c7f` |
| 外来安装保护回归 | 扩展现有测试，非法记录及结构有效但 root 属于另一安装的记录，各执行 status/start/stop：6 个子场景均拒绝，字节、inode、权限、文件集合不变，没有联系、创建或停止服务 |
| 针对性检查 | 3 项相关回归测试通过；asset_release.py check 通过。复用未受影响的引擎/许可/SDK验证，不宣称重新执行所有旧测试 |
| 包身份 | 源、6392 安装载荷、原生 ZIP 和市场 ZIP 的 60 个内部文件全部逐字节一致；两个 ZIP 未重建、版本未改 |

新服务在长时间空闲后按原设计退出；2026-10-30 再次通过同一已安装 SDK 工具启动并安全复用，实际新地址重新打开且引擎就绪。当前地址/原始返回仅保存在本机 `dist/molecule-structure-lab/1.0.0/current-retest-service.json`，不把临时令牌地址写入交付载荷。开发浏览器截图不是用户测试通过证据。

本轮仅更新包外 `MANUAL_TESTING.md` 及其 dist 副本、此测试记录、既有针对性回归、`retest-verification.json` 和关联记录；删除了错误的固定历史 URL 与直接导入旧安装模块的操作指南。未改宿主、SDK、依赖、其他插件或内层载荷。`artifact.json` 仅同步本记录的摘要；ZIP SHA-256 保持原值。任务保留 Integration Testing，候选保留 Planned；等待用户复测与后续运行宿主验证，不能进入 Phase 3。


## 2026-10-30：再次失败与真实运行宿主证据核对

**用户再次报告人工测试失败；整体人工测试仍未通过。** 本次仅修正包外交接说明和证据分类，没有发现需要改动插件载荷的缺陷。原始失败截图保存在 `dist/molecule-structure-lab/1.0.0/failure-evidence-20261030/`；`originals.json` 保存原图 SHA-256，`host-tool-events.json` 保存逐次工具调用及原始返回（SVG 以摘要索引，完整原始内容仍在宿主历史中）。

- 用户提供的 Downloads/Huawei 原生 ZIP 为 11,201,681 字节，SHA-256 `55e943a1fe105ff0ce3dc210cb83ed85fd1e30b4300af0a5018271df59da637b`，与保留包完全相同，ZIP 内没有 server.json 或人工 workspace。
- 10:39 失败会话 `web_1a18aacc138_89c9adc8fc81` 实际来自 6393 的 `.research/ebook-workswarm-20261027` 安装。history.jsonl 第 4 行载入该安装的 Skill，第 10–11 行对 6392 专用 workspace 调用 status 并返回 invalid_runtime。虽然提示词写了 6392，实际调度没有转移到 6392。
- workspace 内 server.json 结构、UID、0700 目录权限有效，root 为 `/private/tmp/state-machine-audit-workswarm-20261026/data/agent/workspace/plugins/plugin_packages/local/molecule-structure-lab`；记录 SHA-256 `d058f422c3c77ce26ed0701040aa17ff0c2e84d50b49594e11c285817b85dcea`。没有改写记录、root、权限或停止服务。
- 新发现并核验的 6392 用户会话 `web_1a18a9fa5e0_323a0bc973a6` 已于 10:24:48—10:24:57 实际执行四次工作台工具调用：status stopped、start 成功、第二次 start 安全复用、status running。后三次原始返回包含同一端口 62821 的完整 URL。会话界面已实际打开并与原始返回核对。
- provenance：该会话 history.jsonl 第 10–11、15–16、21–22、26–27 行分别为四次调用/返回；gateway.log 第 25249–25251 行的 WebSocket origin 为 http://127.0.0.1:6392，同一连接在第 27107–27119 行绑定该会话。full.log 第 7647、7714、7721、7729 行分别记录会话建立、harness 分发、用户请求的模型选择和 worker 分发。因此这是真实运行宿主调度，不是独立 SDK harness。这里只读取用户既有历史；本轮代理未发起模型调用。
- 八次 analyze_molecule 真实结果均为 1.0.0：阿司匹林13原子/13键、苯环首匹配4–9；乙醇无匹配；空查询；invalid_smiles、invalid_smarts、unsupported_atom、unsupported_bond；最后 CCO/SMARTS * 成功恢复，首匹配0。结果详见上述证据 JSON。
- 已从真实返回地址重新打开工作台，1.0.0 / RDKit 2026.09.1 就绪。复用此前未受影响的交互、高亮、输入失效、错误恢复和真实 SVG/JSON 下载开发验证，不冒称本轮重复执行或用户人工通过。

以上证据更新此前“运行宿主调度待验证”的历史结论：这次指定 6392 安装的发现、调用、启动、安全复用及实际 URL 已证实。其他安装的兼容性不能据此推定；6393 对外来 workspace 的拒绝保持。此前默认模型禁用状态不能覆盖用户后来请求的模型选择；本轮未改配置或调用模型。

交接改为直接提供成功的 6392 会话链接和单独的分子工作台链接，明确要求在地址栏核对宿主；相同 ZIP 不代表运行记录可跨安装复用。旧目录和本轮目录均保留，不需重新安装 ZIP。两个 ZIP、60 个内层载荷和版本不变。仅更新包外 MANUAL_TESTING.md/dist 副本、此报告、retest-verification.json 和 artifact.json 的报告摘要；复用已通过的六个外来记录拒绝子场景。仍为 Phase 2 / Integration Testing / Planned；等待用户浏览器复测、明确完成确认及当前适用原始截图。


## 2026-10-30：1.0.1 修复从 WorkSwarm 点击链接被拒绝的问题

**当前等待用户自行导入 1.0.1 并复测；没有用户测试通过确认。** 11:02 三张原始截图按原字节保存在 `dist/molecule-structure-lab/1.0.0/navigation-failure-20261030/`。新证据证实一个真实插件缺陷，修正前述“没有发现载荷缺陷”的历史结论，但不改变外来安装运行记录必须拒绝的结论。

根因：1.0.0 的服务器对全部路径统一拒绝 `Sec-Fetch-Site: same-site/cross-site`。正常点击 WorkSwarm 会话里的另一端口链接也会携带该标记，因此服务成功启动后，入口页面仍返回“仅接受本机同源请求”。此前地址栏直接打开的开发检查没有覆盖这一导航方式。

最小修复仅在本插件 `tools/server.py`：允许当前随机令牌下精确 `/web/index.html` 入口的、无 Origin、带用户激活标记的顶层 GET 导航；必须同时为 `navigate`、`document` 和 `Sec-Fetch-User: ?1`。Host 仍必须精确匹配回环地址及端口。资源、健康/控制接口、POST、HEAD、嵌入式加载、无用户激活、错误 Origin/Host/令牌、查询与路径穿越不因此放宽。运行记录所有权检查未改。其他载荷修改仅为 1.0.1 版本标签与中文安装说明；没有改动宿主、SDK、依赖或其他插件。

| 本轮实际检查 | 结果及证据边界 |
| --- | --- |
| 旧版故障复现 | 新导航回归在 1.0.0 的两个合法导航场景实际失败（403，而预期 200）；1.0.1 通过 |
| 核心测试 | 14 项全部通过：真实 RDKit WASM、启动/复用/停止、外来安装拒绝、中文错误及新增导航正负场景 |
| 包验证 | check / pack 通过；原生 ZIP、市场 ZIP、源及已安装载荷的 60 文件逐字节相等；两个包均已提取。全部 vendor/许可/源材料与 1.0.0 相同，复用有效许可审计 |
| 本插件升级 | 先保存旧安装及运行记录，再通过旧安装的真实 SDK 工具确认并停止该插件自己的服务；记录字节未变。通过 WorkSwarm 原生 plugin_packages 卸载、import_local、install 接口安装 1.0.1；其他插件与宿主配置字节不变 |
| 用户上传界面 | 自动化未完成原生文件选择器，不能记为“手动上传界面已通过”。实际导入使用该界面对应的受支持原生接口；没有改写宿主文件 |
| 已安装 SDK | loader/resolver、两个 Tool / 一个 Skill、invoke/stream、分析、错误及 status/start/reuse/status/stop 全部通过；这是独立 SDK 调用，不冒充模型会话调度 |
| 普通 Chrome 实际点击 | 从另一回环端口的明确开发链接页面点击工具真实返回 URL，成功加载 1.0.1 与 RDKit 2026.09.1；不是直接粘贴地址或伪造 WorkSwarm 会话 |
| 浏览器功能 | 阿司匹林13原子13键、苯环原子4–9真实高亮；编辑失效并禁用导出、乙醇无匹配、空查询区分、四种非法输入及 CCO/* 恢复全部通过 |
| 实际下载 | SVG/JSON 实际保存到 Downloads 并复制到本轮 dist；独立解析确认两者元数据完全相等。下载事件等待器曾超时，文件检查证实实际下载成功；不把事件超时写为未下载 |
| 运行宿主会话与人工测试 | 1.0.0 的用户真实调用证据保留；**1.0.1 的用户自行上传→会话调用→点击链接完整链仍等待复测**。没有付费模型调用，也没有替用户宣布人工通过 |

维护证据索引：`navigation-verification-1.0.1.json`。原始结果在 `dist/molecule-structure-lab/1.0.1/` 下的 `package-verification.json`、`host-upgrade-verification.json`、`installed-sdk-verification.json`、`browser-verification.json`、`browser-service-sdk-results.json` 和 `downloads-verification.json`。开发截图不是用户通过证据。

原生 ZIP SHA-256：`7fe3bcf1390a25ff484d49cf4eb5c681c1ea76001d3d3aa37810bf2af72b0f8a`。
市场 ZIP SHA-256：`f42697463babe8275f41b9b640add46c0473f08ddb5a9ad70844710a95ae828a`。

原 1.0.0 两个 ZIP、用户失败截图、运行记录及历史报告均保留。未处理任何未知服务或 Main 环境。新的人工目录为空，不使用开发 SDK 服务记录。复测应自行在当前安装导入原生包，并使用 MANUAL_TESTING.md 中的实际工具流程；不依赖开发者已启动的临时 URL。候选仍 Planned；原任务更新为 Ready for Testing，仅表示新修复包已准备好。Phase 3 仍被当前版本人工确认和原始证据门槛阻止。

后续回归规则：本插件所有浏览器入口改动必须覆盖真实用户点击跨端口链接，不能只用无来源 HTTP 请求或地址栏导航代替；不要通过放宽控制接口或安装身份检查修复入口问题。


## 2026-10-30：用户确认 1.0.1 人工测试完成

Cai Zhenze 在当前 Main 2.0 对话明确表示：“I confirm manual testing of 离线分子结构工作台 1.0.1 is complete and passed.” 用户同时提供五张原始截图并授权 Phase 3。消息没有可用永久链接，不编造链接或精确确认时刻。截图文件时间为本地 14:47:33—14:48:19。

- 原生 ZIP SHA-256：`7fe3bcf1390a25ff484d49cf4eb5c681c1ea76001d3d3aa37810bf2af72b0f8a`。
- 市场 ZIP SHA-256：`f42697463babe8275f41b9b640add46c0473f08ddb5a9ad70844710a95ae828a`。
- 两包及当前源目录的 60 个运行载荷文件逐字节一致；确认后未改变载荷、名称、版本或 ZIP。
- 原图按原始字节保存在 `test-evidence/1.0.1/`；`originals.json` 记录原文件名、尺寸、字节数及 SHA-256，没有缩放、重压缩或修改。
- 图 1 展示实际 WorkSwarm `status → start → start → status`，全部返回 1.0.1；首次无记录、随后启动、重复安全复用，URL 一致，没有 `invalid_runtime`。这补足之前仅独立 SDK 验证的宿主调用证据。
- 图 2 展示空输入中文错误；图 3—5 展示浏览器中的阿司匹林高亮、乙醇不匹配及苯高亮和描述符，页面均标记插件 1.0.1。
- 用户整体测试通过是用户确认；截图没有单独展示下载完成或逐项编辑过程，不把导出按钮当作下载证据。1.0.1 的实际下载与编辑失效等开发验证见 `navigation-verification-1.0.1.json`，不混同两种证据。
- 已知阻塞：无。1.0.0 外来安装目录冲突通过新安装专用工作区处理；导航缺陷由 1.0.1 修复并复测。既有失败证据、外来服务和运行记录保留；所有权校验未绕过。
- 独立交付复核：60 个载荷文件、47 条许可证据、5 条复用文件散列及 48 个上游/许可材料均匹配，无阻塞发现。复用未变动的功能验证；交付时再次运行格式及确定性打包检查。
- 原始任务与报告：`AH-20261028-molecule-structure-lab` / `RPT-20261029-molecule-structure-lab-retest`。候选继续 Planned；GitHub 交付后等待 Song Haoran 验收，不代表 Hub 提交或 Completed。
