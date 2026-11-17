---
name: modeler-workflow
description: 枚举全部合法配对，报告无解、唯一解或多解，并生成不含答案的学习者原文。
---

使用宿主已有的命令执行工具运行 Python3；从本技能文件定位成员根目录（../..），不能假定当前工作目录或硬编码安装路径。所有参数路径均加安全引用。脚本不是命令注册承诺，先检查工具确实可用。
# 完整计数

运行 `python3 <成员根>/tools/model.py --input <model.json绝对路径> --output <新的建模目录>`。检查 JSON 输出和退出码，读取生成的 model-report.json、learner.json。枚举所有合法配对；只能使用真实 solution_count。把 learner.json 路径及哈希交回 Leader。不要篡改失败结果或删线索凑出唯一解；需要修订则报告具体情况。
