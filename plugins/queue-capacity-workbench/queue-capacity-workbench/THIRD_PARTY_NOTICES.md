# 第三方声明

本插件使用 **SimPy 4.1.2**，源代码版本 `f43816490c6f76f336ad6e457d3cab9f386894af`，官方项目 https://gitlab.com/team-simpy/simpy ，官方分发 https://pypi.org/project/simpy/4.1.2/ 。

Copyright (c) 2013 Ontje Lünsdorf and Stefan Scherfke (also see AUTHORS.txt)

`vendor/simpy/` 与 `vendor/simpy-4.1.2.dist-info/` 为官方通用 Python wheel 的完整、未修改文件。采用 MIT 许可；完整许可与免责声明在 `licenses/simpy/LICENSE`，wheel 原有许可亦保留。上游许可称 AUTHORS.txt，匹配版本源分发实际名称为 AUTHORS.rst；原文件随包保留在 `licenses/simpy/AUTHORS.rst`。源分发与 wheel 未包含单独 NOTICE 文件，不虚构该文件。

SimPy 无第三方运行依赖；仅使用已有 Python 标准库。上游构建工具 setuptools/setuptools_scm 不随本插件分发，也不在运行时安装。

本仓自有工具适配、队列模型、界面与示例独立编写；私有目录生命周期与固定文件 HTTP 传输基于本仓 solid-mesh-workbench 的维护代码进行适配。没有复制上游文档示例、品牌图标、字体、数据集、第三方脚本或前端依赖。未修改 SimPy 原文件；本插件不代表上游官方产品或背书。仓库自有代码的统一许可由项目负责人决定，此声明不重授上游许可。
