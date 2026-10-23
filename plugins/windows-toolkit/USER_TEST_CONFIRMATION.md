# Windows Toolkit — current and historical confirmation

## Current LF rebuild: 1.0.1

Owner Nguyen Trung Dung; task `AH-20261023-dsh-win-toolkit`; candidate `CAND-DSH-019`.
Chinese display name: **Windows 本机工具箱**.

- Native ZIP: `test-packages/windows-toolkit-1.0.1-native.zip`.
- Native SHA-256: `18c6b8d439992404bb308ac37084405a92869d38523c64d473dbf42d499421d4`.
- Canonical SHA-256: `844450ba04d52481dbdb762eb515ddca4fcea179a1191f82d33f8a0a90b874a4`.
- Source/native/canonical payloads now match exactly and use LF; license unchanged.
- Changed bytes: CRLF normalization and manifest.version only. Python AST and
  all other normalized payload bytes match the tested 1.0.0 package.
- Agent repair validation: 7/7 real source checks and 7/7 extracted checks pass.
- **Current-package user test completion: pending.** No new user quote or manual
  test is invented. Existing merge authorization is preserved; do not ask again
  for the same merge permission after the changed-package gate passes.

The seven original PNGs and [PR evidence comment](https://github.com/LasVie/agentic-hub-plugins/pull/42#issuecomment-6361186996)
are preserved for the original 1.0.0 test. No screenshot shows a version or hash.
The same visible workflow and locale names remain applicable functionally, but
association with the rebuilt 1.0.1 requires the user's explicit confirmation.
Source/license review and automated checks do not replace that confirmation.

The user clarified in the continuation conversation that the successful tests
were for the Chinese 1.0.0, then requested the 1.0.1 ZIP path. That clarification
is not recorded as completion confirmation for 1.0.1. The exact new native path
and hash were supplied; current-version confirmation remains pending.

Evidence correction after inspecting all seven images: the hosts and external
netdiag prompts contain Chinese. Clipboard/notification examples use English
and numeric text. No image demonstrates a Chinese clipboard write/read round
trip. The older blanket statement that all UI inputs were English/numeric is
too broad; the original file is retained as historical evidence below and in
`USER_TEST_CONFIRMATION_1.0.0.md`.

## Historical user confirmation: original 1.0.0

- 任务 ID：AH-20261023-dsh-win-toolkit
- 候选 ID：CAND-DSH-019
- 中文展示名：Windows 本机工具箱
- 版本：1.0.0
- 宿主：WorkSwarm 0.2.7，本地 Windows 安装
- 测试包：`test-packages/windows-toolkit-1.0.0-native.zip`
- 测试包 SHA-256：`0e6acdcc1df0ebcb4cece362c928467ee2ee600cd578addf8696f2c7f535fb32`

## 用户确认

> "Tested on workswarm 0.2.7 locally, confirmed working"

- 确认人：Nguyen Trung Dung
- 确认时间：2026-10-23 16:31（Asia/Singapore），消息在本会话内收到
- 证据来源：当前会话；无消息永久链接，故不虚构 URL

## 原始截图

用户提供的原始 PNG 保存在 `test-evidence/`，未重新压缩。工作区副本经 SHA-256 核对与用户提供文件一致。

| 截图 | 内容 | 字节数 | 尺寸 | SHA-256 |
| --- | --- | ---: | --- | --- |
| `ws-hosts-list-20261023-1627.png` | `win_hosts_list` 调用，`RESULT DONE` | 23822 | 1176×487 | `86d2b57de3b38387d6a78cf1214a52d9e8c2269ed7c2edb464a29607c5e91e86` |
| `ws-netdiag-open-20261023-1628.png` | `win_netdiag` github.com:443 → DNS `20.205.243.166`，TCP **OPEN** | 26133 | 1117×462 | `79e112592e5c3d74d14654ddbc35f3af83414d3d08ffa644c7708330c550974a` |
| `ws-netdiag-closed-20261023-1628.png` | `win_netdiag` 127.0.0.1:1 → TCP **CLOSED** | 26362 | 1093×487 | `eb384947dc653eeeb4c2db52fc8b00cc1af72f5a7a67386eb6d42ba1816bc7ae` |
| `ws-clipboard-write-20261023-1629.png` | `win_clipboard_write` 写入 `67676767`（8 字符） | 22472 | 1107×416 | `8ecaee338c4f33775cf4df0ac51c98e54a553a9c97ac0307855ae06ddaf522d1` |
| `ws-notify-20261023-1629.png` | `win_notify` 弹出标题与正文均为 `67676767` 的通知 | 22851 | 1133×405 | `4bbe2ffd0a1be54d184ffda5fc094ad82bbcbbb173b58935349a44d1ed4143a5` |
| `ws-plugin-enabled-20261023-1638.png` | Plugins 面板显示 **Windows Toolkit** 开关为开启状态 | — | 983×784 | `846fd06c81c57af48a884b2aa08ddcf91ff3554874028425954acd83758dc188` |
| `ws-clipboard-read-20261023-1647.png` | `win_clipboard_read` 读回剪贴板内容 `6666677777`（10 字符），助手同时指出与先前写入值不同 | 22124 | 1083×493 | `6010f84f4775e840987fc70249fdf453405c83218c9f23e83c32eac68059c1d5` |

注：`ws-hosts-list-*` 与 `test-evidence/` 实际文件名一致。

## 证据覆盖与缺口（如实记录）

**已证明：**

- 插件在 WorkSwarm 0.2.7 中成功加载并启用（Plugins 面板开关为开启）
- **全部五个工具**在真实宿主中完成调用并返回结果：`win_hosts_list`、`win_netdiag`、`win_clipboard_read`、`win_clipboard_write`、`win_notify`
- `win_netdiag` 同时验证了可达（`github.com:443` → OPEN）与不可达（`127.0.0.1:1` → CLOSED）两种相反结果
- `win_clipboard_read` 真实读回剪贴板文本 `6666677777`（10 字符），证明读取路径可用
- 助手主动指出读回值与先前写入值 `67676767` 不同，说明返回内容来自真实实时剪贴板，而非回显或缓存
- 工具调用耗时 2.67s–9.39s，属合理区间

**未证明 / 缺口：**

- 截图为局部裁剪（约 1100×490），未包含插件版本号 1.0.0、详情页或完整工具清单
- `win_hosts_list` 截图底部被裁切，hosts 内容与行数不可见，仅见 `RESULT DONE`
- 用户界面测试中输入均为英文与数字；中文往返仅由直接工具测试证明（`中文测试 端口工具箱`、`ZIP 包内中文往返测试`），未在宿主 UI 中复现
- 非 Windows 宿主（`POWERSHELL_MISSING`）路径未实测
- 剪贴板读回值与写入值不同属预期行为：期间剪贴板被其他程序改写，非缺陷

## 边界

- 本确认为用户测试完成，**不等于** Project Lead 验收，也不表示已提交或通过 Hub 审核。
- 上述缺口不影响已记录的确认范围，但若后续需要以中文渲染与读取往返作为验收依据，应补充对应截图。
