# 第三方许可与修改说明

## fet-claude-skill

- 上游：https://github.com/nispa/fet-claude-skill
- 版本：1.2.1；固定提交：`beb2e1193665deb68b8f29d7617e7bb972573d95`。
- 原始声明：**Copyright (c) 2026 nispa**。
- 许可：MIT；完整版权、许可及免责声明位于 `licenses/fet-claude-skill/LICENSE`。
- 原始路径：`skills/fet/scripts/fet_common.py`、`fet_inspect.py`、`fet_timetable.py`。
- 本包适用路径：`lib/fet_audit.py`，合并并改编上述解析、工作量、占用校验和导出算法。
- 修改：结构化中文返回、有界的本地 XML 输入、重复标识与非法时段处理、继承学生不可用时段、显式检查边界、导出筛选和 CSV 公式文本中和。宿主适配器另行提供不覆盖文件的导出行为。
- 上游没有 NOTICE 文件。本包不含 FET 可执行程序、OR-Tools、上游模型提示词、图标、字体或真实学校数据。

MIT 原文保留英文，不以译文替代。本说明不改变原许可、不授予商标权，也不宣称上游作者背书。
