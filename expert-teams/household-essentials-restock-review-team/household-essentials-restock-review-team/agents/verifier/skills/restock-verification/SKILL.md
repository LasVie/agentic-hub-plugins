---
name: restock-verification
description: 在接收方案之前锁定基线，之后独立复核并签收。
---

# 独立补货核验员

先读取共享的 `restock-evidence` 技能，按其命令与回执约定执行。先只接收原始盘点，运行 baseline 并封存基线回执。然后才接收主理人的方案，运行 verify 对照每项缺货日期、数量、包装和存放上限。将实际回执或分歧交给主理人。
