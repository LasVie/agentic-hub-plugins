---
name: windows-toolkit
description: 读取与写入 Windows 剪贴板、弹出系统通知、读取 hosts 文件，并对任意主机做 DNS 解析与 TCP 端口诊断；仅支持 Windows。
---

# Windows 本机工具箱

默认使用简体中文。本插件在 Windows 宿主机上提供 5 个专用工具，所有用户输入都以 Base64 跨 PowerShell 边界传递，不拼接命令行。

## 何时使用

- 用户想把刚复制的内容交给助手处理，而不是粘贴进对话 → `win_clipboard_read`
- 用户明确要求把某段文本放到剪贴板 → `win_clipboard_write`
- 长任务结束，需要提醒用户 → `win_notify`
- 怀疑域名被本机映射或需要确认 hosts 内容 → `win_hosts_list`
- 怀疑网络不可达，需要区分 DNS 故障与端口不通 → `win_netdiag`

## 工具

| 工具 | 作用 | 写操作 |
| --- | --- | --- |
| `win_clipboard_read` | 读取当前剪贴板文本；为空时返回 `empty: true` | 否 |
| `win_clipboard_write` | 用给定文本替换剪贴板内容 | 是，须用户明确要求 |
| `win_notify` | 弹出约 6 秒后自动关闭的通知 | 是，会占用桌面 |
| `win_hosts_list` | 只读读取 hosts 文件内容与行数 | 否 |
| `win_netdiag` | DNS 解析 + TCP 端口测试，返回 `OPEN` / `CLOSED` / `TIMEOUT` | 否 |

## 使用纪律

1. 先只读、后写入：需要诊断时优先 `win_hosts_list` 与 `win_netdiag`。
2. 写入类工具仅在用户明确要求时调用；不要用通知代替正常回复。
3. `win_netdiag` 的 `TIMEOUT` 表示在 5 秒内未完成握手，不等于端口关闭；报告时区分二者。
4. `DNS_FAILED` 表示解析失败，不要在此情况下推断端口状态。
5. 只根据工具真实返回报告结果；工具返回 `ok: false` 时如实说明错误码与消息，不要猜测成功。

## 限制

仅支持 Windows 10/11，依赖 `powershell.exe`（PowerShell 5.1+）。不修改 hosts，不结束进程，不读取密钥或凭据，不修改网络配置。非 Windows 宿主会返回 `POWERSHELL_MISSING` 错误。
