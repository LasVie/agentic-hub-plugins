---
name: meeting-planning
description: 展开固定本地周会，计算 UTC、参与者本地起止与窗口冲突。
---

从 skill_tool 返回的本成员技能路径定位 tools/plan.py。运行 python3 -B，传入 --input 原始案例、--intake 梳理回执及 --output 全新规划文件的绝对路径。
梳理回执通过且主理人确认核验员已从原始输入完成独立基线后再运行。报告时区指纹、实际期次、第一处冲突和真实文件路径。不存在或重复的本地时刻需要人确认，禁止自主移动或挑选偏移。
