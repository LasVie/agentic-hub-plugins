# 第三方材料与修改说明

上游：[Timberline Percolate 集成](https://github.com/bguillow-rgb/timberline-plugins/tree/a9c0c687825e61b567fb1a03cba0992cbf9393bc/percolate)，
固定提交 `a9c0c687825e61b567fb1a03cba0992cbf9393bc`；插件 1.0.0。

**Copyright (c) 2026 Timberline Ventures LLC**

- 本包 README 和 `skills/coffee-picks/SKILL.md` 改编自对应上游 README/Skill，按 MIT 许可中文翻译与重写。
- 修改：使用 WorkSwarm 原生 `coffee_` 工具名；增加中文安装、来源/单位处理、参数验证、隐私与错误流程。
- 完整原始 MIT 文本位于 `licenses/timberline-percolate/LICENSE`；根与 percolate 许可相同，Git blob
  `673965950cb5e9ab4540da118b645d9772f178eb`，1080 字节。
- `tools/coffee_tools.py` 为本仓库的原生客户端适配；`tool_catalog.json` 是公开协议的中文说明。
  不包含托管服务器实现或反向工程代码；使用宿主既有 openJiuwen、MCP SDK、httpx、jsonschema，不分发依赖副本。
- 完整固定树未发现 NOTICE；不伪造该文件或替换原版权。
- 上游标志/图片、其他三个产品、私有服务、目录数据库和实际查询结果均未复制或分发。
  品牌、烘焙商和咖啡名称仅用于标识来源和真实返回记录，不暗示官方背书。
- MIT 只覆盖被改编的集成文件，不自动授权数据、标志或服务。服务结果按返回的 attribution 和官方条款引用，
  保留来源链接、日期及限制；不把“可带署名引用”解释为全库再分发许可。

原始许可证与免责声明完整保留；本说明不为其他仓库材料另行指定统一许可证。
