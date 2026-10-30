# 第三方来源与修改说明

资讯晨报助手改编自 shangjian2023 的 dsh-rss-daily 0.7.0：
https://github.com/shangjian2023/dsh-rss-daily/tree/a6c2d71238f03af3f3dd8cf1ac0033000de45d02 。

原版权：Copyright (c) 2026 shangjian2023。适用许可：MIT；完整原文及免责声明随包保留于 `licenses/dsh-rss-daily/LICENSE`。未发现上游独立 NOTICE，不虚构额外声明。

2026-10-27 修改：从 py/daily.py 改编标题指纹、中文双字组/Jaccard 去重和 fetch/finalize/confirm 工作流；参考 mcp/server.py 接口，重写成无第三方运行依赖的中文 WorkSwarm MCP/Skill。补充公开 HTTPS 限制、证书强校验、来源 ID 绑定、原子状态、独立演示数据及未确认稿件保护。不包含原 DSH 面板、定时器、webhook、newsflash 事件地址构造、证书验证降级、feedparser 或 mcp SDK。

`data/sources.json` 选用上游清单中的少数派、Solidot、Hacker News 公开订阅地址。运行时取得的新闻内容不因代码采用 MIT 就自动获得再分发许可；仅供用户阅读标题/短摘要并访问原文，不随插件分发新闻全文。

包内演示文本为本次验证创建的合成测试材料，清楚标为演示，不是实时新闻。不分发上游图标、字体或站点页面资源，不表示原作者或新闻来源对本改编背书。
