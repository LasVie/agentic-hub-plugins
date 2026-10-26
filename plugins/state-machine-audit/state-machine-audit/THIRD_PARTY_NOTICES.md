# 第三方来源与修改说明

上游：AmethystLuna/logicprobe，版本1.4.2，固定提交 `e1b5ac4a426c43878863092bc79387700a8189cb`。
来源：https://github.com/AmethystLuna/logicprobe/tree/e1b5ac4a426c43878863092bc79387700a8189cb

Copyright (c) 2026 Amethyst Luna

适用许可为MIT；完整原文（含版权、许可及免责声明）保留于 `licenses/logicprobe/LICENSE`。上游 `tools/python/logicprobe-engine.py` 的完整原文件头保留于 `licenses/logicprobe/UPSTREAM_HEADER.txt`，该文件头描述上游完整引擎，并不表示本包提供那些全部功能。未发现适用的上游NOTICE。

实际移植范围：`runtime/audit.py` 的结构化守卫求值、守卫优先/无守卫回退语义、变量更新和BFS反例搜索参考并改写自该Python文件；JSON模型键及语义参考对应 `skills/logicprobe/references/dsh-model-schema.md`。其余严格校验、路径/哈希确认封装、中文交互文档、SDK工具、资源上限与示例由本次适配提供。

2026-10-26修改：只支持显式有限布尔/小整数模型、禁止状态/先决事件属性；删除广泛声称/源码提取、UML/数据模型/并发/概率/外部求解器与DSH钩子套件。新增闭合schema与严格类型/引用/有限域校验；按启用守卫检测死端；预算耗尽明确未决；结果绑定已确认的完整源文件哈希；错误和说明使用简体中文。纯Python3.11标准库，宿主SDK由用户环境提供，不随包复制。

未使用上游图标、截图、字体、Web界面、benchmark数据、开发依赖或Superpowers方法学提示词。不得将本包描述为上游官方版本、完整形式化证明或实际代码正确性保证。团队新增代码的统一许可仍由项目负责人决定，此说明不对整个仓库重新许可。
