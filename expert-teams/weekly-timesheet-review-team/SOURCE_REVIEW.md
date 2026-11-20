# 来源与许可复核

2026-11-20，Cai Zhenze 已批准独立开发。本项目没有对应候选行或外部移植源。命名映射为 Weekly Timesheet Review Team → 每周工时记录复核专家团 → `weekly-timesheet-review-team`。功能范围基于当前对话批准的输入、计算和交付要求。

- Toggl Track 帮助中心的 [Detailed report](https://support.toggl.com/en-us/article/detailed-report-k9bzy2/) 仅说明逐条工时表是常见输入。未复制其代码、模板、文档文字、标识或数据，未调用其账户或接口。
- 仓库 `2f9e4759dc05b92f7aa5aea8389497ab21c7ea79` 的专家团指南与洗衣团队已交付的测试机制用于原生清单、安装 Skill 和真实任务交接验证。复用的仓库构建与测试机制只存在于开发测试路径，实际使用见 `provenance.json`。
- 工时代码、角色内容、文档、样例及视觉样式均独立编写。包内脚本使用 Python 标准库，无捆绑第三方程序、资产、字体、素材或数据。宿主所配置的模型另由用户授权。
- 官方 SkillHub CLI 固定在 `c8ee4ef44be0453470114aa5a19f4e1017462907`，只用于构建验证，未随包分发。没有需要随包附带的第三方许可或 NOTICE。未为仓库原生代码作新增许可决定。
