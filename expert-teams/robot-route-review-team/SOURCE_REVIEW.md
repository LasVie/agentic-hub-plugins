# 来源、许可与复用审查

- 原始研究名：Multi-Robot Path Planning Review Team（独立设计）。
- 中文交付名：多机器人路径规划复核专家团；slug：`robot-route-review-team`。
- 任务：`AH-20261117-robot-route-review-team`；候选：Not Applicable；模式：native。

## 功能参考，不分发参考材料

1. Stern 等，2019，*Multi-Agent Pathfinding: Definitions, Variants, and Benchmarks*，固定版本 [arXiv:1906.08291v1](https://arxiv.org/abs/1906.08291v1)。参考问题定义、冲突种类与目标差异；不复制正文、图、数据或代码。论文材料分发权限未据此扩大。
2. Sharon 等，2015，*Conflict-based search for optimal multi-agent pathfinding*，[DOI 10.1016/j.artint.2014.11.006](https://doi.org/10.1016/j.artint.2014.11.006)。参考高层冲突分支/低层时空路径的公开算法概念；本包独立写作 Python 实现。2026-11-17 出版商网页重查返回 403，复用 Phase 1 的书目/摘要证据，不绕过访问限制、不分发论文。
3. [whoenig/libMultiRobotPlanning](https://github.com/whoenig/libMultiRobotPlanning/tree/4c75fa20c435c440d8b6bd6dc81668ddc7296ba0)，提交 `4c75fa20c435c440d8b6bd6dc81668ddc7296ba0`。根 MIT 许可明确 Copyright (c) 2017 whoenig，固定文本已核验；只查看 README/许可证以评估 C++14/CMake/Boost/yaml-cpp 依赖。本包不复制或改编任何上游实现、提示词、图片、基准或文档，不捆绑这些依赖。该提交较旧，不称其积极维护。
4. [MetaGPT，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)，参考结构化中间交接的公开思想；未复制框架代码或提示词，不据发表结果声称本团队优于单专家。

## 实际复用

仓库自身 `expert-teams/procurement-quote-review-team/tests/build_package.py` 的正式 CLI 打包/ZIP 检查机制，以及 `expert-teams/logic-grid-puzzle-team/tests/host_integration.py` 的隔离本机宿主管理/脚本化模型测试模式，在本团队 tests 内改编。固定仓库基线 `4e190253f00b2a1d65fdc657161a67fecde15a48`。不改原文件，不复制业务算法。继承原仓库权利状态；不猜测所有权或重新许可。

运行时代码、中文角色/技能、HTML/CSS/JS、合成案例与测试为本次原生编写；仅依赖 Python 3.10+ 标准库及宿主已有 AgentGroup/文件/命令工具。没有外部媒体、字体、数据集、网络服务或商标图形。未引入有权利不明的材料；原生实现不构成对专利、商标或其他权利的自动豁免。仓库统一许可由项目负责人决定。

包内 `来源与边界.md` 保留引用和实际复用说明；第三方实现分发集合为空，因此无伪造的上游 NOTICE。打包后的逐文件清单、路径、类型与字节校验记在 `release/1.0.0/artifact.json` 和 TEST_REPORT.md。
