---
name: route-replay
description: 不导入规划器，逐时刻检查网格路径与费用。
---
# 独立回放复核

先运行 `scripts/replay.py audit-model --case 原始案例绝对路径 --output 新独立模型审查JSON绝对路径`，仅从原始案例检查意图、模型局限与规则。此阶段不读取候选；用 notes/ issues 分开记录说明/真正疑问。独立记录保存并交接后，再运行 `scripts/replay.py review --case 同一案例 --model-report 先前独立报告 --plan 规划员实际候选 --output 新最终复核JSON`。这会核对每步运动、障碍、停留、同格、换边、费用与摘要。语义审查额外发现的问题放 issues，不能用说明隐藏冲突。回放器不证明搜索穷尽或最优性。

使用宿主已有命令工具及 Python 3.10+，相对于本技能定位脚本；参数用实际绝对路径。只写用户授权的新文件，不覆盖旧证据。报告使用简体中文。
