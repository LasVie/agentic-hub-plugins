---
name: notice-delivery
description: 从真实核验回执生成可转发的每周清单
---

已收到两份独立摘录和后续核验回执时，运行：

`python3 -B <脚本> deliver --source <原始通知.json> --baseline <baseline.json> --draft <draft.json> --receipt <verification.json> --out <全新交付目录>`

确认 checklist.md、changes.csv 和 audit.json 齐全。给出实际路径、自原文核实的待办、被替换的安排和仍需询问的事项。
