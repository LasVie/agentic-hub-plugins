---
name: rehearsal-fallback
description: 冻结离线登记限额和待办路径
---
# 冻结离线作业

在团队已授权的工作目录运行 Python 3.10 或以上的随包命令。具体脚本目录为组包根目录下 skills/rehearsal-evidence/scripts。

命令为 `python3 -B plan.py fallback`，使用脚本绝对路径。传入 --input、--map 及 --output，记录共享人员限额、各流程限额和超限路径。交给复工切换规划员和情景演练员。

引用文件必须实际存在，使用不存在的输出子目录，记录退出码和产物摘要。失败时如实返回，不覆盖证据。
