---
name: rehearsal-review
description: 先锁独立基线，再核对每个工作项
---
# 建立并核对独立记录

在团队已授权的工作目录运行 Python 3.10 或以上的随包命令。具体脚本目录为组包根目录下 skills/rehearsal-evidence/scripts。

命令为 `python3 -B verify.py baseline / compare`，使用脚本绝对路径。先运行 baseline，仅传入 --input、--output，给主理人基线路径和摘要。收到正式独立复盘任务后另行运行 compare，传入 --map、--fallback、--restart、--baseline、--trace、--input、--output。报告缺项、重复或不一致，不修改其他成员证据。

引用文件必须实际存在，使用不存在的输出子目录，记录退出码和产物摘要。失败时如实返回，不覆盖证据。
