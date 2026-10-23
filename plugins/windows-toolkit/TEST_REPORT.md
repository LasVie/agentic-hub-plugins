# Windows Toolkit 1.0.1 — LF rebuild validation

Task `AH-20261023-dsh-win-toolkit`; candidate `CAND-DSH-019`; owner Nguyen Trung Dung.
Date: 2026-10-23, Asia/Singapore. Current Chinese display name: **Windows 本机工具箱**.

Current package status: **Ready for Testing**. The original 1.0.0 user confirmation
is historical; explicit completion confirmation for the rebuilt 1.0.1 is pending.
The seven original screenshots remain unchanged and document the original test.
No current-version frontend test, CI success, merge or lead acceptance is claimed.

| Current archive | SHA-256 |
| --- | --- |
| `test-packages/windows-toolkit-1.0.1-native.zip` | `18c6b8d439992404bb308ac37084405a92869d38523c64d473dbf42d499421d4` |
| `releases/agent-plugin/windows-toolkit/1.0.1/windows-toolkit-1.0.1.zip` | `844450ba04d52481dbdb762eb515ddca4fcea179a1191f82d33f8a0a90b874a4` |

The original failed PR42 head `8f21e91505e0f3689d8b46496c22809cd5af0feb`
reproduces `current source and release ZIP differ` in a clean LF checkout.
Its manifest is 4,221 source bytes with zero CRLF pairs, versus 4,338 ZIP bytes
with 117 CRLF pairs. Five non-license payload files have the same newline-only
mismatch; the license already matches. This is an asset packaging defect, not
evidence that clean origin/main or test_playground is broken.

Version 1.0.1 was built from LF source because the packer refuses to replace a
different archive under an existing version. Original 1.0.0 archives are retained
unchanged for audit. All six native payload files now match source, native ZIP
and canonical ZIP byte-for-byte. There are seven canonical entries including
the marketplace wrapper. Every payload file is UTF-8/LF. Relative to the tested
1.0.0 payload, only CRLF-to-LF normalization and manifest.version changed; Python
AST comparison and exact normalized-byte comparisons pass. The complete original
MIT license retains SHA-256 `e7f61d728785dac8cc772f416f5d33fa618b35d141b972cf7d41b21bbfd873a6`.

New direct tests use the real Tool classes in the existing Windows host venv:

- Source: **7/7 PASS**; independently extracted native package: **7/7 PASS**.
- Checks: hosts content/line-count shape; actual loopback TCP OPEN then CLOSED
  or TIMEOUT; invalid port; missing host; clipboard read shape; declared classes.
- Clipboard write and notification were not repeated in this repair run. Their
  original test evidence remains historical, and runtime logic is unchanged.
- `python -B -m unittest discover -s tests -p test_playground.py -v`: **4/4 PASS**
  in this LF checkout. No clean-main failure is inferred from a bad local clone.
- Package contract, deterministic rebuild and clean-checkout verification are
  recorded in `LF_REBUILD_REPORT.md` and `packaging-repair-verification.json`.

Run `python -B tools/asset_release.py pack plugins/windows-toolkit`, then
`python -B plugins/windows-toolkit/build_native_test_package.py`. Scoped Git
attributes retain LF for this asset's text files and preserve PNG/ZIP bytes.
No runtime function, Skill wording or locale display name was changed.
`display_name.en = Windows Toolkit` is normal host locale rendering, not a
Chinese-package compliance gap.

## Historical 1.0.0 direct test report (preserved)

测试日期：2026-10-23（Asia/Singapore）。任务 `AH-20261023-dsh-win-toolkit`；候选 `CAND-DSH-019`。

环境：Windows 11（原生），PowerShell 5.1.26100.9711，Python 3.12.6，OpenJiuwen 0.1.16 宿主 venv。无外部服务、无账号、无网络依赖（DNS/TCP 测试仅使用本地回环监听）。

测试方式：**直接工具测试**。解压测试 ZIP 后，加载包内 `tools/windows_toolkit.py` 的真实 `Tool` 子类，通过其公开 `invoke()` 入口调用，等同于宿主注册后的调用路径；不经过任何模拟层。

## 交付给用户测试的包

| 项目 | 值 |
| --- | --- |
| 测试包 | `plugins/windows-toolkit/test-packages/windows-toolkit-1.0.0-native.zip` |
| ZIP SHA-256 | `0e6acdcc1df0ebcb4cece362c928467ee2ee600cd578addf8696f2c7f535fb32` |
| 版式 | 原生包：`manifest.json` 位于 ZIP 根目录，无 marketplace 外层 |
| 包内文件 | `manifest.json`、`README.md`、`THIRD_PARTY_NOTICES.md`、`licenses/dsh-win-toolkit/LICENSE`、`skills/windows-toolkit/SKILL.md`、`tools/windows_toolkit.py` |

市场包装 ZIP（Hub 提交用，**不是** WorkSwarm UI 安装包）：`releases/agent-plugin/windows-toolkit/1.0.0/windows-toolkit-1.0.0.zip`，SHA-256 `18ce196c8bfa65ce65bc0d560f064643ba9122ffd96f8f43f12c27166880262f`，版式为 `windows-toolkit/plugin.yaml` + `windows-toolkit/manifest.json`。

命令：

```bash
"D:/Python 3/python.exe" plugins/windows-toolkit/tests/test_windows_toolkit.py --allow-write
```

结果：**PASS**，11/11 项通过，退出码 0。解压测试 ZIP 后的独立复测：**PASS**，7/7 项通过。

| 检查项 | 结果 |
| --- | --- |
| `win_hosts_list` 返回内容与行数 | PASS |
| `win_netdiag` 对本地监听端口返回 `OPEN` | PASS |
| `win_netdiag` 监听关闭后返回 `CLOSED`/`TIMEOUT` | PASS |
| `win_netdiag` 拒绝越界端口（`BAD_INPUT`） | PASS |
| `win_netdiag` 拒绝缺失主机（`BAD_INPUT`） | PASS |
| `win_clipboard_read` 返回文本与空标记 | PASS |
| `win_clipboard_write` 替换剪贴板内容 | PASS |
| 写后读回与写入内容一致（含中文） | PASS |
| `win_notify` 弹出系统通知 | PASS |
| `win_notify` 拒绝缺失正文（`BAD_INPUT`） | PASS |
| manifest 声明的 5 个工具类均存在于模块 | PASS |

## 测试中发现并修复的真实缺陷

**PowerShell 5.1 输出编码缺陷。** 初次运行时剪贴板写后读回得到 `windows-toolkit ????? 2026-10-23`：Windows PowerShell 5.1 按当前 OEM 代码页输出 stdout，Python 端按 UTF-8 解码导致所有非 ASCII 字符变成 `?`。修复方式是在每个脚本前注入 `[Console]::OutputEncoding` 与 `$OutputEncoding` 的 UTF-8 设置。修复后中文写读往返一致。该缺陷只影响非 ASCII 文本，ASCII 路径不受影响，因此若不测试中文将无法发现。

**初版缺少可安装的测试包。** 初版只产出 market 包装 ZIP，其 `manifest.json` 位于内层目录，直接导入 WorkSwarm 会被判定缺少 manifest。已按 AGENTS.md 第 83 条补充原生测试包（`manifest.json` 置根），并解压后独立复测通过。

## 只读与写入分离

按交付规则，只读工具默认执行；剪贴板写入与通知属于桌面写操作，需在获得用户明确同意后以 `--allow-write` 运行。本次两项写入测试均在用户明确同意后执行。

## 边界

- 本测试为**直接工具测试**，不等于用户在 WorkSwarm UI 中的实际操作验证，也不构成 Hub 提交或 Project Lead 验收。
- DNS/TCP 仅验证了本地回环端口，未验证真实外网主机可达性。
- 非 Windows 宿主路径（`POWERSHELL_MISSING`）未在本次运行环境中实测。
