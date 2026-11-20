---
name: rehearsal-delivery
description: 冻结范围、落实交接、处理分歧及最终交付
---
# 汇总并交付

在团队已授权的工作目录运行 Python 3.10 或以上的随包命令。具体脚本目录为组包根目录下 skills/rehearsal-evidence/scripts。

命令为 `python3 -B deliver.py`，使用脚本绝对路径。变量 S 为随包 scripts 路径。传入 --input、--map、--fallback、--restart、--baseline、--trace、--review 和 --output。核对实际分派与成员回执后运行。交付以脚本结果为准。

引用文件必须实际存在，使用不存在的输出子目录，记录退出码和产物摘要。失败时如实返回，不覆盖证据。
