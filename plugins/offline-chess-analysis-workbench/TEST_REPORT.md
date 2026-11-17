# 离线国际象棋分析工作台 1.0.1：复测记录

日期：2026-11-16（Asia/Singapore）；负责人 Cai Zhenze；候选 `CAND-EXT-015`；原任务 `AH-20261113-offline-chess-analysis-workbench`。

## 先前用户验收与当前状态

用户明确确认 1.0.0 人工测试完成并通过，七张原始截图已逐字节保存并记录摘要。见 `USER_TEST_CONFIRMATION.md` 与 `evidence/user-testing-1.0.0/index.json`。这是真实历史验收，不是 AI 自测。图片展示运行中 WorkSwarm 四次真实工具调用、安全复用、不同局面引擎搜索、将死和回放；并非每项下载或文件选择器操作的独立截图证据。

交付前发现生成解析器的 Peggy MIT 许可/署名漏项，因此返回 Build。1.0.1 增加两份原始上游文件、补充出处并更新版本；第三方运行时及对应源码未修改，功能范围未变。1.0.0 两个原包保留不变；历史测试报告和审查记录留在 `test-packages/history/1.0.0/`，其旧结论已由当前补充记录纠正。新包尚未获用户完成确认，不据历史截图声称 1.0.1 通过。

## 已实际执行：修正版

- 13 项 Python 生命周期回归通过，包括旧版本 1.0.0 的完整运行记录在任何联系/启动前被拒绝且保持原样；外国安装保护、确认门、启动/复用/停止、并发与真实空闲退出仍通过。仅操作任务自有临时测试服务。
- 9 项 UI/模型测试通过，禁止字符串代码生成；含 FEN/PGN、合法变化、中文拒绝、失效、取消/故障恢复及生产 10 秒看门狗的受控替身测试。
- 9 项真实引擎/规则测试通过，禁止字符串代码生成；perft 20/400/8902、王车易位、吃过路兵、四种升变、真实 Qg7#、合法三变化及真实搜索取消/恢复。31 项独立测试全部通过。
- 第三方 JS、WASM、NNUE 和全部对应源代码与旧包逐文件比较；原始引擎 Emscripten 6.0.9 重建结果仍适用，未重复宣称重新编译。新 Peggy LICENSE 和 AUTHORS 与锁定上游字节一致；具体许可/源码路径和摘要见 provenance、source-audit。

## 历史证据的适用边界

`host-verification.json`、`sdk-verification.json`、`browser-verification.json`、`package-verification.json` 和 `tests/records/content-security.json` 明确属于 1.0.0；不将其版本改写成 1.0.1。1.0.0 的实际 Chrome 测试已覆盖合法/非法移动、将死及三变化回放、教学 PGN、编辑/设置失效、中文错误、取消/恢复和四个真实下载（独立解析），相同计算代码的这些结果继续作为历史回归证据。

隔离宿主为未修改的 WorkSwarm 0.2.5.beta1 / SDK 0.1.19，另有公共 SDK 0.1.20 历史结果；独立 SDK 调用不等于聊天调度。1.0.0 运行中聊天路径由本次用户截图证实。模型调用与付费调用均为零；未改宿主或其他插件。完整 WorkSwarm 0.2.8、Linux 与同模型基线 A/B 仍未验证；Windows 生命周期不支持。新包的用户宿主与浏览器操作仍待人工。

## 当前包、解包和安装检查

- 原生测试 ZIP：`test-packages/offline-chess-analysis-workbench-1.0.1-workswarm.zip`；SHA-256 `e8baa13cb6eaead5702f122bb861dd5280b10dc1137150e52af759bf0ffc79f7`。
- 规范 ZIP：`releases/agent-plugin/offline-chess-analysis-workbench/1.0.1/offline-chess-analysis-workbench-1.0.1.zip`；SHA-256 `581bf7dccb464218a48a6a5d3ebfcd7c3386ef3685aa7a03a65b8e580daea513`。
- 两个 ZIP、源码及解包目录的 209 份有效载荷逐文件相等；两个新增 Peggy 文件及其余 20 份许可证据的摘要全部核对；所有第三方运行时和对应源码与旧包不变，其他七条差异仅许可说明和版本标识。记录：`tests/records/1.0.1-package-verification.json`。
- 仓库脚本预检对源码及两个 ZIP 的 63 份 JS 均为零命中；锁定官方校验器 `content_security.py`（提交 `c8ee4ef44be0453470114aa5a19f4e1017462907`）扫描每个 ZIP 的 78 份脚本为零命中。没有混淆、拆分或改名规避规则；这不是实际 Hub 提交结果。
- 未修改的独立 WorkSwarm 0.2.5.beta1 实例 `http://127.0.0.1:6483/` 通过受支持的导入/安装/显示接口升级至 1.0.1，209 份安装文件与原生包完全相等。旧安装先逐文件核对并完整备份，原有不活动运行记录保留；没有停止已有服务。前端、后端与代理/直接 WebSocket 检查通过，宿主源码、模型配置及其他插件不变。记录：`tests/records/1.0.1-host-verification.json`。
- 安装载荷经公共 SDK 0.1.19 和独立 SDK 0.1.20 解析工具/中文 Skill，确认门、status、start、安全复用、流式返回、停止、HTTP 和无动态执行 CSP 均通过；单独 SDK 0.1.20 自测服务已正常停止。SDK 进程测试不等同运行中聊天调度；后者仍需用户重测。记录：`tests/records/1.0.1-sdk-verification.json`。
- Chrome 正常地址栏打开当前安装 SDK 工具真实返回的 URL，页面显示 1.0.1，真实搜索得到 `Qg7#`（深度 245，20,522 节点，111 ms），回放到 g7 并显示黑方被将死。编辑 FEN 立即清除旧分析并禁用四类导出；非法六字段输入显示中文 `invalid_fen`；恢复教学 PGN 后实际搜索得到 `d3`（深度 17，581,061 节点，3 秒）。一次自动选择器等待超时，后续重新读取页面确认搜索实际完成，未把等待超时隐瞒成通过结果。
- 实际点击浏览器导出的 FEN/PGN/JSON/SVG 均已保留并独立计算摘要。FEN 30 字节、PGN 145 字节、JSON 2,682 字节、SVG 6,951 字节；JSON 版本 1.0.1，三条 PV 的 SAN/FEN 逐步合法；FEN/PGN 对应原始分析局面，SVG 与 JSON 所记回放一步的当前棋盘字节一致，不混淆两种局面。记录：`tests/records/1.0.1-download-verification.json`；真实下载在 `tests/records/1.0.1-browser-downloads/`；页面记录 `tests/records/1.0.1-browser-verification.json` 与 `tests/records/1.0.1-browser-qa.jpg` 是 AI 工程验证，不是用户原图或人工完成确认。

仓库结构检查 `python tools/asset_release.py check-repo` 通过：77 份源码资产、93 份发行 ZIP。结构检查不等同功能或人工验收。任务已在原始云端记录恢复为 Ready for Testing，1.0.1 报告 `RPT-20261116-offline-chess-analysis-workbench-ready-101`；1.0.0 用户确认报告保持独立。

## 人工重测

按 `MANUAL_TEST.md` 手动上传新的原生 ZIP、启用 1.0.1，在新的空目录通过真实 `chess_workbench` 获取当前 URL。检查页面版本、实际搜索/将死/回放、编辑失效、错误恢复和四类下载。请明确确认新包版本及摘要并提供适用的原始截图。

仅标准国际象棋；单局主线至多 512 半回合，Hash 32 MiB、单工作线程、至多 10 秒和三变化。Hash 不是整个进程内存限制；有限搜索不证明全局最优或实际胜负。FEN 不包含未提供的重复历史。无联网对弈、账户、书库、残局库或 Chess960。候选保持 Planned，任务待重新测试；不推送、建 PR、合并、发布或操作 Hub。

## 当前版本人工确认（2026-11-17）

Cai Zhenze 明确确认「离线国际象棋分析工作台 1.0.1」人工测试完成并通过，并授权进入 Phase 3。准确原生包摘要 `e8baa13cb6eaead5702f122bb861dd5280b10dc1137150e52af759bf0ffc79f7`；规范包摘要 `581bf7dccb464218a48a6a5d3ebfcd7c3386ef3685aa7a03a65b8e580daea513`。六张新原始全分辨率截图逐字节保留，见 `evidence/user-testing-1.0.1/index.json` 和 `USER_TEST_CONFIRMATION.md`。此前待人工事项现由用户完成确认覆盖，不将旧 AI 自测改写为用户测试。运行中 WorkSwarm 工具四次真实调用及版本/安全复用由新截图直接支持；浏览器截图展示新版本真实搜索、局面编辑、将死及升变后局面。图片不单独证明每项下载或文件选择器操作；完整通过结论来自用户明确确认。

1.0.1 的已知交付阻塞项为无；保留有限搜索和平台兼容范围声明。既有1.0.0原包与证据不变。源码、载荷、包装和ZIP未因记录确认而改变。进入 GitHub 交付；Project Lead acceptance 仍待 Song Haoran，未宣称 Hub 上传、提交、发布或官方目录登记。上文历史「待人工」状态保留原日期上下文，以本节最新确认及实时原任务记录为准。

交付取舍：1.0.0 的包、原图和旧工程记录仅在本任务本地保留，不随本次首次 GitHub 交付发布；前述旧路径均为本地历史记录。当前交付保留准确历史摘要和许可修正原因，实际提交1.0.1的当前证据，避免发布已有已知署名缺口的旧包。
