# Windows Toolkit — current and historical confirmation

## Current Chinese 1.0.1: user testing confirmed

Owner **Nguyen Trung Dung**; Task `AH-20261023-dsh-win-toolkit`;
Candidate `CAND-DSH-019`; Chinese display name **Windows 本机工具箱**.
Confirmation report: `RPT-20261023-dsh-win-toolkit-usertest-101`.

> These are the new screenshot verification for the 1.0.1 version, confirm and proceed

Received in the current conversation on 2026-10-23. Verification observed at
17:43:10 Asia/Singapore; exact message sent time and message permalink are
unavailable, so neither is invented. The user explicitly identifies the new
screenshots as 1.0.1 verification and instructs us to proceed. This supersedes
the earlier pending record for the LF rebuild. Existing merge authorization is
reused. The original 1.0.0 confirmation and images remain historical evidence.

- Tested native ZIP: `test-packages/windows-toolkit-1.0.1-native.zip`.
- Native SHA-256: `18c6b8d439992404bb308ac37084405a92869d38523c64d473dbf42d499421d4`.
- Canonical ZIP: `releases/agent-plugin/windows-toolkit/1.0.1/windows-toolkit-1.0.1.zip`.
- Canonical SHA-256: `844450ba04d52481dbdb762eb515ddca4fcea179a1191f82d33f8a0a90b874a4`.
- All six native payload files match source and canonical ZIP exactly, use
  UTF-8/LF, and retain the pinned MIT license. Only line endings and
  manifest.version changed from 1.0.0; Python AST is unchanged.
- Current source and separately extracted native read-only direct checks: 7/7
  each PASS. Clipboard write/notification were not repeated by the agent during
  repair; they are exercised in the user's new frontend evidence below.

## Seven new original PNGs for 1.0.1

Stored in `test-evidence/1.0.1/` under their original filenames. All seven local
originals were visually matched against the conversation images. Copies retain
the exact source bytes, dimensions and hashes, without recompression or editing.
`originals.json` records identity, package hashes and evidence scope. No
credentials or private content requiring redaction were visible in these images.

| Original filename | Visible evidence | Bytes | Dimensions | SHA-256 |
| --- | --- | ---: | --- | --- |
| `Screenshot 2026-10-23 173831.png` | win_hosts_list: completed tool call; hosts path, 21 total lines, no custom mappings | 56158 | 1227×597 | `e216e6cc4f807f19f6480be3a01e6d0a71a8e1e89aa16dc0456e32a5346d7adb` |
| `Screenshot 2026-10-23 173843.png` | win_netdiag: github.com:443, DNS 20.205.243.166, TCP OPEN | 44239 | 1178×532 | `23c672e1d440e2c5f31493f4b2d40cf347203e1cc450280dd9c30f352bd0f187` |
| `Screenshot 2026-10-23 173854.png` | win_netdiag: 127.0.0.1:1, TCP CLOSED | 38577 | 1147×497 | `12f829622545799af399a49a5eebfd191dd924b8eee04e8bdf7f2dc01fd9f561` |
| `Screenshot 2026-10-23 173904.png` | win_notify: completed tool call; assistant reports Notification / 67676767; OS popup itself not shown | 35167 | 1167×455 | `8863e7cfd80d5412d3711d6d133a1a409187a30dc3fc73b57704812977ad3639` |
| `Screenshot 2026-10-23 173918.png` | win_clipboard_write: completed tool call; assistant reports 67676767, 8 characters | 29925 | 1042×467 | `5628182a030ac26b9c8804296f03de7f34add848131ca15635c41715433878c5` |
| `Screenshot 2026-10-23 173929.png` | win_clipboard_read: completed tool call; current text is Read what is on my clipboard, not the earlier numeric value | 26968 | 1192×482 | `f8ba9c3bcfcfcc4c99e4637a68f1c805245fedbb57f8803e3f10e85f79bed047` |
| `Screenshot 2026-10-23 173938.png` | Plugins panel: Windows Toolkit enabled; clipboard-read conversation visible behind panel | 46617 | 742×537 | `03c134e63cbb747f3f7d5734dbf491c3f005317abc58c7c1ced9247505d1c21e` |

The visible conversation runs from 17:35 to 17:38 on 2026-10-23. It shows
completed tool calls for all five tools, an enabled plugin, the 21-line hosts
result, and both open/closed network results. Hosts and external-netdiag inputs
contain Chinese; clipboard/notification inputs use English and numeric text.

Evidence limits: the UI renders the English locale name **Windows Toolkit**;
none of the images shows a version/hash, so version association relies on the
user's explicit confirmation above. The clipboard read returns the newly copied
prompt text rather than `67676767`; no uninterrupted write/read round trip is
claimed. Notification completion appears in the conversation, but the OS popup
itself is not photographed. Raw result panels are collapsed; no independent raw
backend event trace is claimed. Chinese clipboard round-trip coverage comes
from the original direct-tool test, not these new screenshots.

No known blocking issue remains in the performed checks. PR CI and permanent
image-link verification are required before merge. Project Lead acceptance and
Hub operations remain separate and pending.

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
