---
name: rehearsal-dependencies
description: 核实负责人、容量和流程依赖
---
# 核对流程与负责人

在团队已授权的工作目录运行 Python 3.10 或以上的随包命令。具体脚本目录为组包根目录下 skills/rehearsal-evidence/scripts。

命令为 `python3 -B plan.py map`，使用脚本绝对路径。传入 --input 与 --output。检查依赖、负责人、来源位置和待澄清事项。交给主理人和离线作业设计员。不要推断字段。

引用文件必须实际存在，使用不存在的输出子目录，记录退出码和产物摘要。失败时如实返回，不覆盖证据。
