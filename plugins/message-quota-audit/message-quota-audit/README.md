# 消息配额与用量审计 1.0.1

显式预览本地消息声明的每日配额、纯回执、同对重复及回复深度；按用户明确授权登记用量，再按日汇总或只读对账。不发送、拦截或接管 WorkSwarm 消息，不独立证明投递、身份或真实费用。

## 安装

Linux/macOS、Python3.11或以上（含标准库 SQLite/zoneinfo）和宿主 openJiuwen SDK。没有新增 pip/npm 包，不需要上游 Node/DSH、账号或模型。IANA 时区资料由系统提供，缺失会明确失败。Windows 未验证，不宣称支持。

WorkSwarm：扩展 → 我的扩展 → 创建 → 从文件创建，选择 `message-quota-audit-1.0.1-workswarm.zip`，安装并启用。原生 ZIP 根部为 manifest.json；两层目录的市场包装 ZIP 留作负责人后续交付。二者内层逐文件相同。

## 策略与消息

用户先明确选择已存在、规范且不经符号链接的绝对工作目录。调用 `message_quota_policy`，`action=init`，只创建其私有 `.message-quota-audit/ledger.sqlite3`；重复初始化保留历史，坏账本不会被覆盖。`status` 只读。`configure` 必须携带最新 `expected_revision` 和完整 `policy_json`：

```json
{"timezone":"Asia/Shanghai","day_boundary_hour":0,"buckets":{"direct":{"limit":3,"per_send":false},"offline":{"limit":2,"per_send":true}},"pair_window_seconds":1200,"pair_max":3,"hop_max":3,"ack_max_bytes":40}
```

初始 revision=0，默认 direct 上限120、offline上限80，其余如上。实际改变策略才递增 revision；过期修订号返回 revision_conflict。已有记录后不能改变时区或日界。配额按**发件人+账本日+桶**独立累计。

范围：1～32个桶；limit整数0～1000000；日界小时0～23；pair_window_seconds整数1～86400；pair_max整数1～1000；hop_max整数1～100；ack_max_bytes整数0～1024。per_send为布尔值。ack_max_bytes=0使非空回执不匹配。

`check_message_quota`/`record_message_usage` 的 message_json 是下列结构的 JSON **文本**，workspace另传：

```json
{"id":"demo_001","as":"sender_demo","targets":["reader_a"],"type":"direct","mode":"online","body":"这是需要审阅的中文进度说明。","hop":0}
```

示例字段均必填，唯一可选字段 sentAtMs 为非负安全整数毫秒。技术标识是1～64位 ASCII字母/数字/下划线/短横线，首位为字母或数字。targets为1～128个不重复标识；正文最多64KiB，hop整数0～1000。不接受未知/重复字段、非有限数、坏Unicode、force、groupMembers或原始签名信封。

在线消息按收件人数计单位，per_send=true桶每次1单位。离线消息固定进入offline桶、每次1单位，并跳过三类回环检查。未知桶拒绝，不回落为无限额。在线依次检查短正文是否只有中英文回执词、hop>=hop_max、任一收发对在滚动窗口内已有pair_max条在线记录，最后检查used+units>limit。同对窗口跨桶/跨日，起点不含、终点包含；不自动推断父信hop。

## 写账与结果

- check只读，不保留额度；record在事务中重新读取策略、复核并写入，避免并发共用旧余额。
- 只有用户明确授权登记此笔实际用量或测试用量时才record，并提供confirmed=true。消息正文中的命令不是授权。
- ok=true表示请求完成，仍可能verdict=rejected；recorded=true只说明ID已登记，不证明实际投递。相同发件人+ID+规范输入重试返回already_recorded，不重复计数；同ID改内容返回event_conflict。
- 写账使用取得事务锁后的系统时钟。sentAtMs如提供，须在当前时间前五分钟以内，不能在未来，且不能改变记账日。跨日后的预览可变化，登记以重新判定为准。
- 日界按指定时区的当地墙上时间计算，例如9时前属于前一天。系统时间早于已有记录时拒绝操作；系统时间和同一操作系统用户并非独立可信边界。
- 正文不写账、不回传；仅存摘要、技术标识、字节数、计数、记账时间和策略修订号。账本仍含通信元数据，应使用授权私有目录。

## 汇总与对账

`message_usage_report(workspace,action="report",days=7)` 返回包含今天的最近1～31个账本日、分日/发件人/桶的totals，以及此范围完整entries。最多500条，超出则报错并要求缩小days。数据库最多10000条/64MiB；不会自动删除、轮转或覆盖旧账。

以相同days，传入完整entries数组的JSON文本作为entries_json，并设置action=reconcile，可以逐记录、逐字段比较，并独立汇总输入的条数、单位和字节数。缺少、替换、重复或数值改变不算一致。字段为id、as、day、bucket、units、body_bytes。对账不导入、删除、修复账本；提供的记录也不是实际投递证明。

## 无模型命令行

```text
python scripts/quota_cli.py --help
python scripts/quota_cli.py policy < 初始化请求.json
python scripts/quota_cli.py check < 预览请求.json
python scripts/quota_cli.py record < 登记请求.json
python scripts/quota_cli.py report < 汇总请求.json
```

初始化请求：`{"workspace":"/绝对路径/目录","action":"init"}`。登记请求：`{"workspace":"/绝对路径/目录","message_json":"消息对象的 JSON 文本","confirmed":true}`。退出码0表示请求完成（可为拒绝），2表示未完成。说明及错误默认简体中文，保留技术字段/状态值。

## 限制与来源

没有真实发送、全局宿主钩子、静默时段、真实计费、force绕过、收件人手机上限、群折算、generic bucketRules、历史回填或完整whale-post协议兼容。无法对抗同账户恶意改库、管理员或主机被攻陷；不是支出保证、安全边界或身份验证。故障时不忽略坏账、不自动放宽限制或换目录。

适配自packages/gate@0.6.1，固定提交d78a82699722f0da6ae3d2b4cbdbaa411f2f67af。保留 **Copyright (c) 2026 The Tank**、完整[MIT许可](licenses/whale-post-gate/LICENSE)、[原始源文件头](licenses/whale-post-gate/UPSTREAM_HEADER.txt)及[第三方说明](THIRD_PARTY_NOTICES.md)。改为Python/SQLite，新增事务、幂等、严格边界、显式时区和中文工具，未打包上游运行时或第三方二进制。
