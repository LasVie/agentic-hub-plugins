# 交互图谱校验与交付 1.0.0

为 Playground 补充结构化图谱校验与离线交付；从中文 JSON 生成可交互 HTML，保留源文件和校验结果。

## 安装与使用

WorkSwarm 桌面端：扩展 → 本地上传，选择本包的 native ZIP；安装后点击使用，在新会话按下文调用。Agentic Hub 外层 ZIP 由项目负责人后续提交，不能与 native ZIP 混淆。

运行环境：WorkSwarm 原生 Python 工具 SDK；Node.js 22（可使用桌面端内置版本）。

本插件是既有 Playground 的图谱工具配套，不替代 Playground，也不修改其他人的技能。用户给出结构化图谱 JSON 时调用 archify_graph_tools validate；需要实际 HTML 时调用 deliver。首次体验可调用 example 创建中文工作流样例，再 validate/deliver。
支持 workflow、architecture、sequence、dataflow、lifecycle、erd、tree、class、timeline、waterfall 的结构化输入，使用上游打包 schemas；meta.locale 必须为 zh-CN，标题/节点/边/卡片等可见文字默认中文。不得自行写 HTML 代替渲染工具。保留源 JSON，交付 HTML 和中文校验结果。输入中的品牌、外部图片/URL、仓库证据路径不在本离线适配范围；请用户移除或转换为普通文字节点。校验失败先按定位修复 JSON，不声称已生成成功。HTML 交付后通过宿主产物界面或用户浏览器打开检查。

## 来源与许可

上游 Archify，本适配选择 MIT。完整许可与原作者声明见 licenses/ 和 THIRD_PARTY_NOTICES.md。未对团队新增代码作统一再许可决定。
