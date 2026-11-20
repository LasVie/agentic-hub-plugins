---
name: rehearsal-scenario
description: 按冻结证据推进两种模拟情景
---
# 推进情景

在团队已授权的工作目录运行 Python 3.10 或以上的随包命令。具体脚本目录为组包根目录下 skills/rehearsal-evidence/scripts。

命令为 `python3 -B simulate.py`，使用脚本绝对路径。传入 --input、--map、--fallback、--restart 及 --output。只在基线已交付且两份计划冻结后运行。向核验员交接完整轨迹和情景条件。

引用文件必须实际存在，使用不存在的输出子目录，记录退出码和产物摘要。失败时如实返回，不覆盖证据。
