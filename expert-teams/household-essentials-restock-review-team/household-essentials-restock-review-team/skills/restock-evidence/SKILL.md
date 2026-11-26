---
name: restock-evidence
description: 用本地脚本登记库存、独立核验补货方案并交付文件。
---

# 补货证据

脚本在本组包的 `skills/restock-evidence/scripts/restock.py`。使用用户授权且已核对的实际包路径。命令如下，以 `python3 脚本绝对路径` 开头。每个 `--out` 都是不同且尚不存在的目录，父目录应存在。

| 执行人 | 参数 | 回执 |
| --- | --- | --- |
| 核对员 | `intake --source 原始JSON --out 登记目录` | `intake.json` |
| 核验员 | `baseline --source 原始JSON --out 基线目录` | `baseline.json` |
| 主理人 | `plan --intake 登记JSON --out 方案目录` | `proposal.json` |
| 核验员 | `verify --source 原始JSON --baseline 基线JSON --proposal 方案JSON --out 核验目录` | `verification.json` |
| 主理人 | `deliver --source 原始JSON --baseline 基线JSON --proposal 方案JSON --verification 核验JSON --out 交付目录` | `shopping-list.md`、`restock.csv`、`audit.json` |

用原生任务及消息记录真实工具输出、回执路径和失败原因。成员应读取自己的技能。先完成独立基线，再发送方案。不要手写工具回执或忽略返回错误。待定或未知信息依原始输入保留给用户核实。估计按日使用、不补填缺失数值；不执行采购。
