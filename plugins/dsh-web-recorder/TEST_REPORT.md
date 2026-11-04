# 网页会话记录器 1.0.3：当前版本测试记录

日期：2026-11-04（Asia/Singapore）。负责人仍为 Siu Lok Yin；原 Task / Candidate ID 保持不变。

本次变更：用户可见说明、Skill、工具诊断和报告中文化；机器标识、参数结构与原生实现边界保持不变。下面旧版本记录完整保留，仅作历史，不能确认本次中文包。

## 2026-11-04 当前精确包：真实 WorkSwarm GUI 两阶段记录与纠正

用户明确委托 Agent 使用本地已打开的 WorkSwarm 测试导入和 prompt、留存原图及进行 PR/Hub 工作，并要求保留负责人、不要反复询问。根 Agent 按授权实际操作并目视当前 GUI 结果。本轮为 **AI 受委托测试**，`human_performed_testing=false`；没有虚构用户本人测试、最新口头通过、平台提交或最终验收。

- 精确 native SHA-256 `6bafe91b1e0f14b924ae2f08f28e4b0049f1bf70efa0ad190e69b9a175233dba` 通过 WorkSwarm 原生界面导入，实际 toast 成功；详情显示网页会话记录器 1.0.3。实际安装的四个运行文件独立只读哈希核对，与冻结源码/原生包/规范包完全相等。
- 实际宿主：**WorkSwarm 桌面 0.2.8、内嵌 Python 3.12.13、随宿主 aiohttp 3.13.5**，模型 `gpt-6.1-sol`。浏览器为任务目录中的 Google 官方 Chrome for Testing 157.0.8103.38，独立临时资料，不使用私人浏览器会话。该环境不同于下方开发验证的隔离 0.2.9b1 / Python 3.11.17 / aiohttp 3.14.5。
- 真实会话 `web_1a1a5573525_73417e2b087b`，记录 `session_id=c00d12dca9b0`。第一阶段实际 `web_record_start` 后返回会话并等待操作；受委托 Agent 在本轮 localhost 合成页面输入、点击本地请求和定位链接，再由第二阶段实际 `web_record_status` / `web_record_stop` 查询并停止。没有用静态日志替代宿主调用。
- 原生记录时间为 `2026-11-04T14:55:30` 至 `2026-11-04T15:20:22`；中间包含 CUA 选择应用延迟造成的长等待，不当作性能基准。live UI 三轮显示 20.01 / 49.49 / 16.33 秒；原生导出摘要显示 20.16 / 49.52 / 16.36 秒，分别保留为真实观察，不拼成虚构精确耗时或原生工具延迟。

| 原始文件实际计数 | 结果 |
| --- | --- |
| 总事件与序号 | 25 条，`seq` 连续 1–25，首条是首页 GET 请求 |
| 点击 / 输入 / 更改 | 4 / 9 / 1 |
| 提交 | 0；本轮不声称验证了提交事件 |
| 导航 | 3 条，包含同文档导航；不是 3 次新页面请求 |
| 网络 | 8 条记录 = 4 条 request + 4 条 response，不是 8 次请求 |
| 输入隐私 | 最后一条 `value_len=12`；合成输入正文在 events/report 均不存在，输入事件没有值正文字段 |
| 停止结果 | `active=false`、`phase=completed`，两份输出真实存在 |

### 保留首次总结错误与真实纠正

第一次停止后，模型以 `read_file offset=1` 读取零起行文件，跳过了第一条记录，误称 JSONL 缺少 seq1、只有 24 条/7 条 network，与报告不一致。这是读取偏移引起的模型总结错误，不能写成首次总结全部正确，也不是原始事件丢失。

根 Agent 独立完整解析原始文件后，要求从 `offset=0` 重读。模型明确撤回缺首条、24 条及 7 条 network 的说法；纠正后的表述与实际 25 条、连续 1–25、8 条 network 一致。工具 trace 中真实参数名是 `offset`，不混写为不存在的 `start_line`。纠正没有改写 `report.md`、`events.jsonl` 或 `state.json`，没有补写事件。

- 原始 `events.jsonl`：4286 字节，SHA-256 `bea32883986441f6b27947c766189ff9f3726c9e3004a0cebed4dbbc0bcccd5b`。
- 原始 `report.md`：2497 字节，SHA-256 `f84f3785ac1160ae9aa4f1ec13c92c0fae126427e035279a9a34047ac0c11d41`。

原文输出的独立复核与复制均保持这些哈希。清理按实际观察记录：根 Agent 已停止自有 fixture 会话 `27131`，端口 52939/53085 关闭；worker `82106` 当次为 `<defunct>`，表示已结束执行但等待宿主回收，不声称 PID 当时消失，也不处理用户会话或其他服务。

十张 JPEG 原图、原生长 PNG、AX trace 与原始会话输出原字节保存在 `test-evidence/20261104-zh-1.0.3/`，清单见 `GUI_TEST_RECORD_1.0.3.json` 与同目录 `evidence.json`。这些是同一流程的不同视图，不是十一项独立测试。长图 `jiuwenswarm-share-20261104-152641.png` 为 2250×12183、1879841 字节、SHA-256 `3511affcfaab92d7dbc70793039ddff04d33ea4549da60384cb9b0ad81146c36`，从本轮 Downloads 原字节复制并实际查看，包含首次错误与完整纠正，未经裁切、缩放或重压缩。

本轮仅更新包外交付报告/证据及 artifact 的报告哈希；四文件 payload 与两个 ZIP 冻结字节未变。完整 1.0.2 历史记录及旧包保留。当前没有 push、创建新 PR、合并或提交 Hub；永久 PR 原图附件与真实 CI 必须在后续实际交付时验证。

## 独立开发功能与 SDK 验证（非本轮 GUI 环境）

环境：macOS 26.6 arm64，WorkSwarm 0.2.9b1 原有宿主 Python 3.11.17、aiohttp 3.14.5。未安装或修改 Python 环境。系统未安装 Chrome、Edge 或 Chromium，初次测试准确返回中文依赖错误；随后按用户委托授权从 Google 官方 Chrome for Testing 目录下载 157.0.8103.38 mac-arm64，仅置于本任务隔离目录，不安装系统、不修改默认浏览器、不读取已有用户资料。

官方来源：`https://googlechromelabs.github.io/chrome-for-testing/`，该页面链接的官方 JSON 给出下载地址 `https://storage.googleapis.com/chrome-for-testing-public/157.0.8103.38/mac-arm64/chrome-mac-arm64.zip`。实际下载 196562867 字节，本地 SHA-256 为 `3406b38b52b7d341d74450eb7b369be038c9fec9894c8b8a9e9e9f97333caf2f`。此哈希为实际下载字节计算值，不冒称官方独立提供了预期 SHA-256。浏览器与其代码不进入插件 ZIP。

普通 Codex 执行沙箱内，浏览器在端点建立前以 SIGABRT 退出；经自动审批允许在该外层沙箱外执行本地测试后成功。Chrome 自身沙箱保持启用，没有添加 `--no-sandbox`。两项测试只使用独立临时浏览器资料和 `127.0.0.1` 合成页面，没有外部账号、API 密钥、业务数据或付费模型。

| 当前真实测试 | 结果 |
| --- | --- |
| `tests/test_web_recorder.py`：真实 CDP 点击、输入与导航 | 退出 0；9 项断言通过 |
| 实际事件计数 | 点击 1、输入 1、导航 2、网络 8，共 12 条 |
| 首个文档 GET、响应及 `/api/data` 请求 | 实际捕获并核对 |
| 中文 Markdown 时间线与稳定 JSON 事件代码 | 已写出并核对 |
| 输入隐私 | 只含 `value_len=5`，没有输入值字段 |
| `tests/test_cross_process_session.py` | 三个独立进程的开始、查询、停止均成功；状态持续存在，两份输出真实生成 |

当前原始开发日志见 `FUNCTIONAL_TEST_1.0.3.log`、`CROSS_PROCESS_TEST_1.0.3.log`。`test-evidence/dsh-web-recorder-1.0.3-functional.png` 是真实无头浏览器通过 CDP 原生捕获的开发补充截图，已实际查看，中文名与 1.0.3 清晰；它不是 WorkSwarm GUI 导入/提示测试，也不是用户本人测试证据。

真实 SDK 已从源码、输出副本与原生 ZIP 新解压目录装载 manifest 并验证路径，解析到三个工具和一个中文 Skill；真实 `Tool` 实例、中文未知会话诊断和中文报告渲染均通过。源码、原生包、规范包与输出副本的四个运行文件逐字节一致。

- 当前原生包 SHA-256：`6bafe91b1e0f14b924ae2f08f28e4b0049f1bf70efa0ad190e69b9a175233dba`
- 当前规范包 SHA-256：`a1f12e93ec1f3779a18eb8a386d0d83ef5714aa6a25f8a673425c34538e50673`
- 原生开发截图：756×413 PNG，25727 字节，SHA-256 `e0b03345c3af133dd69bfa2b22fcf642670b77a359b0befe1f56f6d43195ed6b`，未经编辑。

上午开发阶段的 GUI 待完成状态已由本轮实际结果更新，不补造用户亲测或新口头通过。旧版首文档限制与旧修复文字矛盾处，以各轮真实结果为准；接入前已完成的请求仍无法恢复。


## 2026-11-04 仓库验证范围

使用现有 Python 的 `-S` 隔离视图，仅只读加载仓库固定依赖 PyYAML 6.0.3，全仓单元测试 603 项通过、122 项因可选依赖跳过；没有安装或修改环境。两款当前包另用完整真实 WorkSwarm SDK 验证并实际实例化所有声明工具。

额外在完整 SDK 环境发现运行 608 项、61 项跳过时，有两个无关资产的 `assertWarns` 触发 SDK 的延迟模块属性错误：`offline-backup-recovery` 与 `offline-ebook-reader` 测试访问 `openjiuwen.core.foundation.store.__warningregistry__` 后抛出 `ModuleNotFoundError`。无需插件代码的 SDK-only 复现也触发同一错误。这次完整 SDK 全仓运行未通过，原始失败日志保留，不冒称全绿；CI 依赖隔离视图与两款当前包 SDK/功能测试结果分别记录。

`asset_release.py check-repo` 通过：63 项源码资产、75 个版本 ZIP。没有修改这两款之外的插件代码。

## 历史记录（原文保留）

# Functional Test — dsh-web-recorder 1.0.2

Test date: 2026-10-23 (Asia/Singapore). Task AH-20261023-dsh-web-recorder; candidate CAND-DSH-172.
Passing here means development functionality plus repository packaging checks only. It is **not** Hub submission/publication, host-install approval, or Project Lead acceptance.

## Environment & repeatable commands
macOS Darwin arm64; Python 3.11.15 (OpenJiuwen `~/agent-core/.venv`); aiohttp 3.13.3; Google Chrome 155.0.8059.86.
No API keys, business data, cloud deployment, or paid calls. The test serves a local `http.server` page on 127.0.0.1 and launches headless Chrome in a throwaway `--user-data-dir`.

```bash
# functional test (drives a real headless Chromium over CDP)
~/agent-core/.venv/bin/python plugins/dsh-web-recorder/tests/test_web_recorder.py

# repository format / packaging checks
python tools/asset_release.py check plugins/dsh-web-recorder
python tools/asset_release.py pack plugins/dsh-web-recorder
python tools/asset_release.py check-repo
```

Raw output of the functional test is saved to `FUNCTIONAL_TEST.log` (host connector-pool INFO lines stripped; it does not replace real user screenshots).
The previous 1.0.1 automated screenshot is retained as historical development evidence only. Version 1.0.2 changes session persistence and requires fresh WorkSwarm confirmation.

## What the test exercises
A local page with an input, a button (whose click issues `fetch('/api/data')`), and a link. Over CDP the test performs a genuine `input` event, a genuine `click` (triggering the network request), and a history `pushState` + `popstate` navigation, then stops the session.

## Actual results — PASS
All assertions passed (process exit 0):

| Check | Result |
| --- | --- |
| click captured (>=1) | PASS |
| input captured (>=1) | PASS |
| navigation captured (>=1) | PASS |
| network captured (>=2) | PASS |
| events.jsonl non-empty (>=4) | PASS |
| report.md contains timeline | PASS |
| network event includes `/api/data` | PASS |

In-process run counts: `click=1, input=1, navigation=2, network=8` (12 events total).

Representative captured timeline (from a run):

```
| 1 | network    | GET http://127.0.0.1:.../ [Document] |
| 2 | network    | ← 200 text/html http://127.0.0.1:.../ |
| 3 | navigation | load → http://127.0.0.1:.../ |
| 4 | input      | input#field[name=field] (len=5) |
| 5 | click      | button#go "Go" |
| 6 | network    | GET http://127.0.0.1:.../api/data [Fetch] |
| 7 | network    | ← 200 application/json http://127.0.0.1:.../api/data |
| 8 | navigation | popstate → http://127.0.0.1:.../next |
```

`web_record_start` → `web_record_status` → `web_record_stop` all returned `ok: true`; outputs `report.md` and `events.jsonl` were written to the session output directory.

The rerun also verified the test targets the page whose `location.href` matches the fixture URL instead of relying on unordered CDP target enumeration. A lifecycle defect was fixed so `keep_browser_open=true` no longer deletes the retained browser's temporary profile directory.

The initial-document-request race noted in 1.0.1 is resolved in 1.0.2: new targets auto-attach paused (`waitForDebuggerOnStart`) until Network/Runtime/binding/init-script are installed and then resume, and a page opened via the `url` parameter is reached by navigating the already-instrumented initial page rather than `Target.createTarget`. The first document GET/response is now captured (timeline rows 1–2 above).

Version 1.0.2 adds a detached recorder worker and file-backed registry/state/result protocol. `tests/test_cross_process_session.py` invokes start, status, and stop in three separate Python processes and verifies the active session survives, navigation/network events remain visible, and both output files are produced.

## Known issues / limitations
- The first document request of a page opened via the `url` parameter may precede per-page network instrumentation; the recommended flow (start, then browse, or `attach_url`) captures everything. Documented in README.
- Chromium-family browsers only (CDP). Firefox/WebKit unsupported.
- A browser must already be installed on the host; none is downloaded.

## Scope statement
This report covers functional behavior and repository packaging only. It is not a legal license conclusion, not Hub acceptance, and not Project Lead acceptance.
