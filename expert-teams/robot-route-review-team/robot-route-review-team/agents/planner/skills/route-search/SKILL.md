---
name: route-search
description: 在严格限额内使用CBS规划小型离散网格同步路径。
---
# 同步路径搜索

运行 `scripts/planner.py --case 冻结案例绝对路径 --map-report 地图员实际报告绝对路径 --output 新候选JSON绝对路径`。先读取地图员报告；有 issues 先停止并交接。`found` 是未经独立复核的候选；`infeasible_within_horizon` 仅指当前有限时域；`search_limit` 是未完成，不得改写为无解。路径到达终点后永久停留，成本为各机器人首次到达步数总和；最多一次有证据的修正，不改规则。

使用宿主已有命令工具及 Python 3.10+，相对于本技能定位脚本；参数用实际绝对路径。只写用户授权的新文件，不覆盖旧证据。报告使用简体中文。
