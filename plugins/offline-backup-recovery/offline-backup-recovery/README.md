# 离线备份与恢复 1.0.0

为用户明确指定的稳定目录创建本地 ZIP 备份，保存文件清单与 SHA-256，校验后预览恢复计划，并在取得授权后恢复到**尚不存在的新目录**。支持普通二进制/文本文件、中文路径、嵌套目录及空目录。不覆盖现有文件或目录。

## 安装

环境：macOS/Linux、Python≥3.11、兼容的 WorkSwarm 原生 Plugin 宿主及其现有 openJiuwen SDK。插件核心仅用 Python 标准库，无 pip/npm、Node、tar、账号、网络服务或模型调用。Windows 未支持。

在 WorkSwarm「扩展 / Extensions」导入同版本 `offline-backup-recovery-1.0.0-workswarm.zip` 并启用，确认显示「离线备份与恢复」、版本1.0.0、1个技能与3个工具。原生兼容 ZIP 与市场包装 ZIP 的内层载荷完全相同；较早宿主需要原生 ZIP。

## 工具

| 工具 | 主要参数与行为 |
|---|---|
| `create_directory_backup` | `source_dir`、`archive_path`、`confirmed=true`；用户明确授权复制目录并创建新的 `.zip`；父目录已存在，输出在源目录之外。 |
| `inspect_directory_backup` | `archive_path`，可选 `expected_sha256`；只读验证格式、全部成员、清单及摘要。 |
| `restore_directory_backup` | `archive_path`、`target_dir`；默认 `mode=preview`，仅返回清单，不写入。恢复需要 `mode=restore`、`confirmed=true` 及先前真实返回的摘要 `expected_sha256`。 |

所有路径均为不含 `.`、`..`、空段的真实绝对路径，不经过符号链接。请选择具体数据目录，不选择根目录或整个用户主目录。输出目标的父目录必须已存在。恢复目标即使是空目录也会拒绝；需另选新名字，不能擅自清理旧目标。

推荐顺序：停止源目录的写入 → 明确授权创建 → 保存返回的 `archive_sha256` → 使用此值校验 → 预览新目标 → 用户确认后恢复 → 对比文件数量、内容和摘要。不要把文档示例或预期值冒充实际返回结果。

## 结果与限制

- 成功和业务错误均返回当前 `version=1.0.0`、`ok`；失败看 `error.code` 与中文说明。`ok=true` 不表示来源可信、在线应用一致或人工测试完成。
- 成功结果包含 `archive_sha256`、`archive_bytes`、`file_count`、`directory_count`、`total_bytes`、`integrity_verified`。校验/预览返回完整有界 `entries`。预览为 `writes_performed=false`；恢复成功为 `true`。
- 仅支持本插件 `offline-backup-recovery/v1` 格式：非压缩、非加密 ZIP、结构化清单、普通文件与目录。不能导入通用 ZIP、DSH 原始 tar 备份或其他产品快照。
- 最多1000个文件/目录（不含清单）、深度20、单文件16MiB、合计64MiB、归档80MiB、清单512KiB。拒绝链接、硬链接、设备/FIFO、危险或重复路径、控制字符、冒号、反斜线以及未列入清单的成员；超限失败而非静默截断。
- 备份保留文件字节与目录结构，不保留原权限、属主、时间戳、扩展属性或稀疏布局。新目录权限0700，新文件0600；可执行位不恢复。未加密、不自动脱敏，显式选定目录中的敏感文件也会复制，请自行保管归档与摘要。
- SHA-256用于一致性比较，不能认证来源或抵御同时改写归档和清单的人。与另行保存的可信摘要比较可发现归档变化。仅恢复校验通过的明确归档，不执行其中内容。
- 读取时检查文件/目录变化，但不提供文件系统原子快照或数据库事务一致性。请关闭写入者；不是整个在线 WorkSwarm/数据库迁移工具。不能抵御同一操作系统用户的恶意并发修改，路径检查也不是操作系统沙箱。
- 恢复在完整校验后排他创建新目录，再逐文件写入并复核；写入期间其他进程可能看到未完成目标。失败时仅尝试清理本次创建且身份未变的目录；无法安全清理会返回 `partial_output`，应人工检查。突然断电/强制终止可能留下临时文件或未完成目标，不会自动删除历史。

常见错误：`confirmation_required`（需要明确授权）、`output_exists`（另选目标）、`integrity_mismatch`（摘要不符）、`invalid_archive`（格式不支持/内容损坏）、`unsafe_path` / `unsafe_file`（危险路径或链接）、`size_limit`（超限）、`source_changed`（停止并发写入再试）、`filesystem_error`（检查权限/路径/空间）、`partial_output`（人工检查失败新目标）。

没有自动备份、自动清理/保留策略、原地恢复、同步、升级安装、会话修复、凭据搜集或后台服务。

## 无模型命令行

在内层目录运行 `python3 -B runtime/backup.py --help`。子命令为 `create`、`inspect`、`restore`，用 `--input-json` 提供与工具相同的 JSON 参数。退出码0表示成功，2表示失败。默认说明、结果和错误使用中文。

来源与原始完整 MIT 许可见 `THIRD_PARTY_NOTICES.md`、`licenses/dsh-backup/LICENSE`。
