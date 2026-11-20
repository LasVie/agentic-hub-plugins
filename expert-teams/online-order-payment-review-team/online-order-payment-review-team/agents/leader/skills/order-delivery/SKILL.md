---
name: order-delivery
description: 根据真实独立核验回执生成中文摘要、核对表和审计记录
---

等三名成员的原始回执。用当前原始资料重新核对回执关联，再运行：

`python3 -B <脚本> deliver --source <原始目录> --as-of <日期> --baseline <baseline.json> --proposal <matches.json> --verification <verification.json> --out <全新交付目录>`

确认 review.md、reconciliation.csv 和 audit.json 齐全才报告交付。给出差额、需要回查的原行和文件路径，保持未入账不等于已收到。
