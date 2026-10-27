# 第三方来源和修改说明

## dsh-persona-switcher

- 来源：https://github.com/yupaoa/dsh-persona-switcher
- 固定版本：563854472ae7fe3b2e96f6cbcb53428d3af81e1c（npm dsh-persona-switcher@0.3.1）
- 版权：Copyright (c) 2026 yupaoa
- 许可：MIT，完整原文见 licenses/dsh-persona-switcher/LICENSE

涉及文件：`runtime/engine.py` 改编自上游 `lib/index.js` 中的角色 id 校验、角色路径、ROLE.md 序列化与 frontmatter 解析、角色库扫描和人设变更提示逻辑（文件头已注明修改）。

修改摘要：由 JavaScript/Cordis 插件改写为 WorkSwarm 原生 Python 工具；状态由每会话改为每工作目录；提示与说明改为简体中文；新增示例角色、init 操作及大小与符号链接边界；未包含上游网页客户端、设置页、吉祥物立绘与 role_probe 工具。示例角色、提示段、技能说明与工具封装为本适配新写。

未声明上游作者或其商标持有人认可本适配。
