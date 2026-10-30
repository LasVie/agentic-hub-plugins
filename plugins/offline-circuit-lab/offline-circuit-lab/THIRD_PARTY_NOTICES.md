# 第三方来源与许可

本插件「离线电路实验室」v1.0.0 的有界 RLC 数值计算部分改编自 **CircuitJS1**。这是功能范围有限的离线适配版，不是完整 CircuitJS1，也不代表原作者提供认证或背书。

- 上游项目：<https://github.com/pfalstad/circuitjs1>
- 固定源代码版本：`e952e788a4135a693bfd4cee7883f9b3314e3e76`（所检查的应用版本字符串为 `5.0.3ts`）。
- 改编代码：`runtime/solver.py`。
- 原始作者声明（保留原文）：`Copyright (C) Paul Falstad and Iain Sharp`。
- 许可证：**GNU General Public License, version 2 or (at your option) any later version**，即 `GPL-2.0-or-later`。
- 完整原始许可证：`licenses/circuitjs/LICENSE`；内容为上游 `COPYING.txt` 的逐字节副本。
- 完整已选原始源文件：`licenses/circuitjs/upstream/ResistorElm.ts`、`CapacitorElm.ts`、`Inductor.ts`、`SimulationManager.ts`。这些文件保留完整原始署名与许可头，供来源核验，不由本插件执行。

## 改动说明

2026-10-28：将已选线性电阻、电容、电感伴随模型、修正节点分析盖章及稠密 LU 求解过程适配为 Python 标准库实现；新增有界输入、中文错误、零初始状态、首步后向欧拉、后续梯形积分、浮置/冲突/病态检查及残差和节点电流守恒校验。工具/API 的直流计算把电容视为开路、电感视为理想短路，不添加虚构漏电。

本插件没有复制完整编辑器、图标、字体、图片、示例电路库、稀疏矩阵库、压缩库或其他可选器件实现；不需要上游 Node/npm 构建。随包原始文件中的依赖引用保留原貌，但对应依赖实现未复制、未运行。具体改编行号及文件摘要见插件仓库的 `SOURCE_REVIEW.md` 与 `provenance.json`。

## 分发与无担保

改编的数值代码继续受上述 GPL 条款约束。分发时应保留署名、许可、修改说明，并提供相应源代码；本包已包含可读的 Python 与网页源代码。此声明不将仓库其他资产统一重新许可，不授予上游商标或未复用材料的权利。宿主已经安装的 SDK 未由本插件重新分发或修改。

以下保留原始许可声明的含义与原文；完整条款以随包许可证为准：

> CircuitJS1 is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 2 of the License, or (at your option) any later version.
>
> CircuitJS1 is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

软件不提供任何担保。本版仅用于理想线性电路的学习和数值对比；结果不能代替真实硬件测量、安全验证或工程认证。请减小步长复核数值收敛性。
