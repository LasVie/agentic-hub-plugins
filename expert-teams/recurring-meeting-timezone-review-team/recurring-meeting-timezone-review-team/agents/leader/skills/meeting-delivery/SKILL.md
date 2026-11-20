---
name: meeting-delivery
description: 核对原始输入、规划和独立报告，处置分歧后交付。
---

运行本角色的 tools/deliver.py。请用 skill_tool 取得本技能真实路径，从技能目录回到本成员根目录找到 tools；工作区中的同名文件不是随包脚本。
先核对收到真实梳理、规划、独立基线和独立比对文件。用 python3 -B 执行，提供 --input、--intake、--baseline、--plan、--review、--output 的绝对路径，交付目录须全新。
只有实际命令成功且 review.md、meetings.csv、audit.json 存在才交付。使用宿主现有文件交付工具或报告真实可读路径。它检查一致性；各时段可仍有会撞到窗口或待澄清。
