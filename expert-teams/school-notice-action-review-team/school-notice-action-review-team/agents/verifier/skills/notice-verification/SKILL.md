---
name: notice-verification
description: 先凭原始通知建独立基线，再验证两份摘录并报告差异
---

先只接收原始通知。独立枚举事项、适用对象、截止时间和订正关系。逐份生成自己的摘录文件，运行：

`python3 -B <脚本> baseline --source <原始通知.json> --extraction <核验员摘录.json> --out <全新基线目录>`

保存基线并完成原生任务，交回 baseline.json 路径和实际回执。随后新任务才读取分析员初稿，运行：

`python3 -B <脚本> verify --source <原始通知.json> --baseline <baseline.json> --draft <draft.json> --out <全新核验目录>`

用原始通知复核漏项、相对日期、班级和变更范围。交付 verification.json 和争议原行。程序比对一致仍须保留未决条目；不得通过改写基线抹除分歧。
