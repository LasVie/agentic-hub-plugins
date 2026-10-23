# Windows 本机工具箱（windows-toolkit）

让助手直接使用 Windows 本机能力：读取剪贴板、弹出通知、查看 hosts 文件、诊断某个主机的端口连通性。

## 功能

| 工具 | 说明 |
| --- | --- |
| `win_clipboard_read` | 读取当前剪贴板文本 |
| `win_clipboard_write` | 写入剪贴板文本 |
| `win_notify` | 弹出系统通知（约 6 秒自动关闭） |
| `win_hosts_list` | 只读读取 hosts 文件 |
| `win_netdiag` | DNS 解析 + TCP 端口测试 |

## 适用场景

- 你刚复制了一段内容，希望助手直接读取，而不是再粘贴一次
- 长任务结束时希望收到系统提醒
- 某个站点打不开，希望区分是解析问题还是端口不通

## 安装

在 WorkSwarm 中导入本插件目录（或发布 ZIP），启用后即可在会话中使用上述工具。安装后建议先执行一次只读检查：

- 问“帮我读一下 hosts 文件里有哪些自定义映射”，应调用 `win_hosts_list`
- 问“检查 127.0.0.1 的 1 端口是否可达”，应调用 `win_netdiag`

## 环境要求

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10 / 11 |
| PowerShell | 5.1 或更高（系统自带即可） |
| 权限 | 无需管理员：hosts 为只读，剪贴板与通知为当前用户级操作 |
| 其他 | 无需账号、无需网络服务、无需额外运行时 |

## 安全设计

所有用户输入都先编码为 Base64，在 PowerShell 内部解码使用，从不拼接进命令行字符串，因此剪贴板内容或主机名无法注入命令。脚本以 `-NoProfile -NonInteractive` 方式运行。

## 限制

- 仅 Windows 可用；非 Windows 宿主会返回 `POWERSHELL_MISSING`。
- 不修改 hosts、不结束进程、不读取密钥或凭据。
- `win_netdiag` 的 `TIMEOUT` 只表示 5 秒内未完成握手，不代表端口关闭。

## 来源与许可

本插件为 MIT 许可的上游 `dsh-win-toolkit@0.1.3` 的 WorkSwarm 原生移植版本。上游版权与许可全文保留在 `licenses/dsh-win-toolkit/LICENSE`，来源与复用范围见仓库内 `provenance.json` 与 `SOURCE_REVIEW.md`。
