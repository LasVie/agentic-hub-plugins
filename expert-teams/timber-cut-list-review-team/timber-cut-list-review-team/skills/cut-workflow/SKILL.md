---
name: cut-workflow
description: 以原始库存、占量和零件需求进行真实交接、独立复核及中文排样档案交付。
---

# 定尺下料复核

使用宿主给出的已安装技能目录，脚本为其中的 scripts/cut_list.py。显式授权只读案例路径与每个新输出路径。运行 Python 3.10+，建议使用 -B。

| 操作 | 文件参数 |
| --- | --- |
| inspect | --case 原案 --output 新库存报告；可重复 --note 或 --issue |
| plan | --case 原案 --stock 库存报告 --output 新候选 |
| verify | --case 原案 --stock 库存报告 --plan 候选 --output 新复核报告 |
| deliver | --case 原案 --stock 库存报告 --plan 候选 --review 复核报告 --output 新交付目录 |

每一步使用实际文件。只提供文件路径、摘要和真实状态。除非用户明确给出变动依据，复核员不得编辑库存或候选。搜索限额与无解分开。未通过复核时，交付档案仅用于解释发现，CSV 无可用下料行。
