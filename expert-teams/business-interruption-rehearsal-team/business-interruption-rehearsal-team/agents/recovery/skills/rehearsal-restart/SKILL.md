---
name: rehearsal-restart
description: 冻结复工门槛、顺序和回填规则
---
# 冻结复工切换

在团队已授权的工作目录运行 Python 3.10 或以上的随包命令。具体脚本目录为组包根目录下 skills/rehearsal-evidence/scripts。

命令为 `python3 -B plan.py restart`，使用脚本绝对路径。传入 --input、--map、--fallback 及 --output，解释写入、快照、批准及复工顺序，将计划交给演练员。

引用文件必须实际存在，使用不存在的输出子目录，记录退出码和产物摘要。失败时如实返回，不覆盖证据。
