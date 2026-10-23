---
name: environment-inspector
description: 主动观测本机系统、标准位置工具链和 TCP 监听端口，保存与比较快照，提供中文筛选界面；不结束进程、不读取密钥。
---

# 本机环境探针

默认使用简体中文。先确认用户指定的现有工作目录，调用 `environment_inspector` 的 help/status；写入时携带最新 expected_revision。用户想操作界面时调用open_ui，展示一个带中文标签的链接，提醒仅在本机使用，不要复制短期凭据到共享记录。

- status：读取已保存观测快照。
- probe：expected_revision；主动执行只读本机标准位置工具 --version 与 lsof TCP监听观测。失败保持unavailable，不代表系统没有服务。
- compare：before_id, after_id；比较两份不同的已保存快照，端口不可观测时不推断增减。
- export_snapshots：导出已保存快照，不读取密钥/配置文件/用户名/设备名/网卡地址。

只根据真实工具返回报告成功。不要把未观测当不存在、把保存草稿当验收、把记录证据当自动评审，也不要调用本插件未提供的宿主操作。原始工作文件或 Git 状态不可擅自改动。只读观测本机操作系统、标准位置工具版本与TCP监听端口，明确区分可用、未观测与失败，保存及比较快照。不会结束进程、修改系统、读取密钥或配置文件。仅当前macOS已验证，Linux与Windows不作已测试保证。
