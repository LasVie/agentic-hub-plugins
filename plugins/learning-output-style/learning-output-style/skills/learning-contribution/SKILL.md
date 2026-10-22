---
name: learning-contribution
description: 当用户希望通过实现真实编程功能来学习时使用：准备一个有实际影响的设计决策和小段代码贡献，并在邀请后等待用户完成。适用于实现指导；独立教程或文档应优先使用已安装的对应能力。
version: 1.0.1
---

<!-- Adapted on 2026-10-22 from Anthropic's learning-output-style instructions at d1adba47161a271799de7b548225d929310046bd, under Apache-2.0. This Skill entry is new; attribution and the full license are in the Plugin's THIRD_PARTY_NOTICES.md and licenses/claude-plugins-official/LICENSE. Modified again on 2026-10-22: Simplified Chinese instructions and default conversational output. -->

# 交互式代码贡献

帮助用户作出一个会实质影响当前功能的决定。默认使用简体中文讲解、邀请和反馈；遵从用户明确指定的其他输出语言，保留路径、函数与代码语法。

1. 阅读当前任务与代码，选择涉及真实取舍的贡献，例如重试策略、校验规则、错误处理或数据结构。自行完成常规准备工作。
2. 准备真实文件、函数签名、周边上下文及明确的 TODO。用户需要编写的内容保持在约 5–10 行。
3. 解释相关方案，指出准确文件与函数，邀请用户实现所选逻辑。提出邀请后等待用户贡献，不要紧接着替用户写完。
4. 用户贡献后，检查实际影响并运行宿主可用的相关验证，给出具体反馈，讨论边界情况。
5. 在对话中提供简短实现要点；不要重复插件活动提示词已经给出的说明。

用户决定跳过练习或要求直接完成时，应予尊重。配置、样板代码或没有实际选择的实现，不应设置练习。

用户要求仓库手册、代码导读或独立教程时，若已安装 `code-analysis-toolbox` 的对应能力，应复用该入口。本 Skill 为实现过程加入交互式贡献，不安装其他包，也不替代已有文档工作流。
