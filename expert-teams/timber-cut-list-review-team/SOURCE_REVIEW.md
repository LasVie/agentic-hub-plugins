# 来源、许可与复用审查

- Timber Cut List Review Team → 木料定尺下料复核专家团 → `timber-cut-list-review-team`。
- 任务 `AH-20261119-timber-cut-list-review-team`，Cai Zhenze，Candidate Not Applicable，原生实现。
- [Gilmore 与 Gomory，Operations Research 9(6), 849–859 (1961)](https://pubsonline.informs.org/doi/10.1287/opre.9.6.849) 提供下料问题背景。[Google OR-Tools 装箱文档](https://developers.google.com/optimization/pack/bin_packing) 提供容量约束参考。[MetaGPT，ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html) 提供分步交接的研究背景。仅引用公开概念，不复制论文、实现、示例、数据、提示词或媒体，不声称已验证协作优势。
- 运行时为新写的 Python 标准库实现、中文说明、离线 HTML 及合成数据。没有第三方素材进入运行时，第三方版权、许可副本或 NOTICE 不适用。源材料的再分发许可未据引用扩大。
- 测试与打包复用本库 `expert-teams/robot-route-review-team/tests/{build_package,host_integration}.py` 在 `8c0c29b6a7a7fcf197946e49ca828888b0e1c05e` 的机制，按团队修改标识、端口和验收断言。测试适配留在外层，沿用该库权利状态。
