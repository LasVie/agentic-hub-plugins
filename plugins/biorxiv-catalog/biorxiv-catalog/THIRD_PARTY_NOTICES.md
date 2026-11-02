# 第三方来源与许可

连接配置来源：Anthropic 的 knowledge-work-plugins/bio-research。
固定版本：2574e29377c7173d0cecffef29a6ecbd7f8ccb5d。
上游：https://github.com/anthropics/knowledge-work-plugins/tree/2574e29377c7173d0cecffef29a6ecbd7f8ccb5d/bio-research

`connection.json` 改编自上游 `.mcp.json`，仅保留 bioRxiv 服务，删除其他连接，并添加修改说明。修改者 Nguyen Trung Dung，日期 2026-11-02。该上游文件没有单独的版权头。适用 Apache-2.0 完整原文位于 `licenses/anthropic-bio-research/LICENSE`；保留上游作者与项目身份。根目录和 bio-research 目录没有单独 NOTICE；这里不编造上游 NOTICE。

中文工具卡、适配器、说明和测试为本仓库适配工作。MCP Python SDK（MIT）、jsonschema（MIT）及其依赖由宿主环境单独安装，不在此 ZIP 中分发；openjiuwen 由宿主提供。

远端后端、论文、摘要、图片、字体、模型和数据库未打包。论文各有许可字段；上游连接文件的 Apache 许可不覆盖论文内容、服务、数据或商标。该插件不是 bioRxiv、medRxiv 或 Anthropic 的官方产品或背书。
