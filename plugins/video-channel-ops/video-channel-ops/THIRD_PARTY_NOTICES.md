# 第三方来源和修改说明

## ai-youtube-os

- 来源：https://github.com/channelroom-studio/ai-youtube-os
- 固定版本：a4eb2f9838e99b26060a236ef2196a18bf38bc7a（插件 0.1.4）
- 版权：Copyright (c) 2026 Channelroom Studio
- 许可：MIT，完整原文见 licenses/ai-youtube-os/LICENSE

涉及文件：

- `runtime/media.py` 改编自上游 `plugins/ai-youtube-os/scripts/render.py` 与 `scripts/preflight.py`（文件头已注明修改）。
- `runtime/templates/channel.json`、`state.json`、`OPERATIONS.md` 译自上游 `templates/` 同名文件，并按本插件工具名调整。
- `runtime/engine.py` 中的频道目录结构与每日流程约定改编自上游 `commands/new-channel.md`、`commands/daily.md`（文件头已注明修改）。
- `skills/video-channel-ops/SKILL.md` 改编自上游 `skills/channel-operations/SKILL.md` 与三个命令说明（韩语译为简体中文并改写为工具调用流程）。

修改摘要：由 Claude Code 插件（命令 + 技能 + 脚本）改写为 WorkSwarm 原生 Python 工具；全部文本改为简体中文；防重复制作、job ID 记录、“上传尝试不等于完成”与授权确认改为工具强制；新增指标记录与到期提醒、Windows 路径映射、路径越界保护；默认时区改为 Asia/Shanghai；未包含上游 README 中的外部指南、模板与付费服务链接，以及上游图标。工具封装、README 与测试为本适配新写。

未声明上游作者认可本适配。YouTube 是 Google LLC 的商标，本插件与 Google 无关。
