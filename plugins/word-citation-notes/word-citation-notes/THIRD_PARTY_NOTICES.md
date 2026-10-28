# 第三方来源与修改声明

- 原始项目：Cite2FN，https://github.com/anitasrinivasan/cite2fn 。
- 固定版本0.1.0，提交`00cc8c12c67633371a41db2a93516b9f3aff92f4`。
- 原始版权：**Copyright (c) 2026 Anita Srinivasan**。完整MIT及免责声明原样保存在`licenses/cite2fn/LICENSE`（SHA-256 d611e5491dca3e4e98428beebd7d70b7cc20bd6796e66eb5a98a51446e2d446b）。所查树无子目录许可、NOTICE或所选源文件独立版权头。
- 本包`runtime/docx_notes.py`适配原`cite2fn/footnotes.py`的OOXML脚注/尾注部件、关系、分隔符与正文引用构造；README与技能指令改写原交互核对/转换工作流。本次模式是ported，不将改写伪称独立原创。
- 修改日期2026-10-27：使用ZIP部件保留及lxml处理，加入中文工具与说明、严格支持范围、精确Unicode跨度、源/计划/输出摘要绑定、明确确认和排他新输出；移除模糊年份/作者定位、自动删除参考文献、联网元数据获取及自动Id./supra逻辑。详细支持边界见README。
- 外部依赖lxml6.1.3为BSD-3-Clause，其已安装二进制使用libxml2 2.14.6；这些库不随ZIP分发，也不把Cite2FN的MIT用于覆盖它们。宿主SDK独立提供。python-docx1.2.0（MIT）只用于独立测试读取/构造，未打包。
- 没有复制Office Toolkit/学术引用比较资产的代码，没有第三方图片、字体、示例论文、Bluebook手册或真实用户数据。示例均为本次公开虚构材料。

本说明不改变原始MIT条款，不为整个仓库统一选择许可，也不提供Bluebook准确性或法律结论保证。
