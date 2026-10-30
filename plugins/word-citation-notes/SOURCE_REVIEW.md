# Word 引用脚注转换：来源与复用审查

Task ID：AH-20261027-word-citation-notes；Candidate ID：CAND-CLD-322；负责人：Cai Zhenze；审查日期2026-10-27。

名称：Cite2FN → Word 引用脚注转换 → word-citation-notes；内部身份repo:agent-plugin:word-citation-notes。

## 固定材料和许可

实际检出 https://github.com/anitasrinivasan/cite2fn/tree/00cc8c12c67633371a41db2a93516b9f3aff92f4 ，版本0.1.0；目录/private/tmp/cite2fn-upstream-20261027，只作静态审查，没有执行上游代码。已阅读完整LICENSE、manifest、pyproject、递归树及footnotes.py、assemble.py、detect.py、supra.py、docx_io.py、Skill/README。根完整MIT为Copyright (c) 2026 Anita Srinivasan；许可SHA-256 d611e5491dca3e4e98428beebd7d70b7cc20bd6796e66eb5a98a51446e2d446b。没有子目录许可、NOTICE、媒体、字体、数据集或额外文件版权头。

MIT覆盖该项目所选代码/说明，允许适配及分发，但须保留完整版权、许可和免责声明。本次mode=ported、permission_status=verified，不宣称独立原创或为仓库重新选择许可证。

| 本包路径 | 实际来源及使用方式 | 条件 |
|---|---|---|
| runtime/docx_notes.py | 改写cite2fn/footnotes.py中的Word脚注/尾注部件、关系、引用及编号元素构造；重做严格文档检查、精确跨度、确认计划及排他输出 | 文件头保留来源/作者/MIT及显著修改记录；完整许可随包 |
| skills/word-citation-notes/SKILL.md、README.md | 改写原Skill的检查、展示、用户确认、生成与人工复核工作流，中文化并收紧范围 | 原始MIT及THIRD_PARTY_NOTICES随包 |
| tools/notes_tools.py、测试/公开虚构样例 | 本次适配的宿主包装、契约和示例；未搬入Office Toolkit或其他比较资产代码 | 不把比较材料改写为原创源 |

实际运行依赖使用已安装lxml；不随ZIP复制其库文件，完整版本/许可在测试记录核对。python-docx仅可作独立测试/视图读取，不要求其承担运行时保存；宿主openJiuwen SDK外部提供，不再分发。不上网抓取元数据，不使用httpx、BeautifulSoup、PyMuPDF、付费模型、品牌图或私有文档。外部依赖的许可不等于上游MIT；无服务调用。

## 业务范围与查重

已比较Office Toolkit440c3c6e0e654b1eb9ec32c17bcd2923@1.0.0及58423394089843bcb863654f02ab937a@1.0.3实际包：普通Word编辑/排版没有创建脚注或尾注接口。academic-citation-manager0b3aefa276af49bc863c42001a77e695@1.0.0生成引用文字/参考文献；Citation Management1f4e4a2df62a40879bbbd77580973b99@356ea33生成元数据/BibTeX；Word批注修订和LaTeX引用守卫也不提供本次DOCX原生注释引用转换。家庭文档台账、电子书阅读、备份/快照/状态机工作不同。具体来源哈希已在候选英文Notes保留。

本版只处理明确支持的Word正文段落与经确认的精确范围，生成新的DOCX及转换报告，原件/未选内容/参考文献保留。未知结构明确拒绝，不默默只处理部分。缺陷修正：去除年份/作者/子串猜测锚点；无自动删除参考文献；不自动推断Id./supra及来源身份，不丢页码；计划固定源摘要、跨度、文字与输出路径，拒绝过期/重叠计划和已有输出。中文通过用户批准的精确范围支持，不声称原上游Latin作者正则能识别中文。无Bluebook正确性、文献真实性或法律结论保证。

## 包检查

完整原MIT已原样放置于licenses/cite2fn/LICENSE，THIRD_PARTY_NOTICES.md记录移植和修改。2026-10-27已解开最终1.0.0市场包和原生包，核对全部8个载荷文件/许可摘要/声明路径、无缓存或比较资产代码；两包载荷与源码及实际宿主安装一致。三个复用路径都有上述许可与修改记录覆盖。市场ZIP为releases/agent-plugin/word-citation-notes/1.0.0/word-citation-notes-1.0.0.zip，SHA-256为03da5e1d00c4873ebaff0e4547470f37ce5c86ba63d9d4f7173a1f73dd63a658；原生ZIP为plugins/word-citation-notes/test-packages/word-citation-notes-1.0.0-workswarm.zip，SHA-256为335a003d520315f8688f548ff284af9154829a3a32fc1cf885ee419870303b57。

源码、两种解包载荷和实际安装载荷各24项中文/安全/真实SDK功能测试通过，真实LibreOffice渲染脚注与尾注核对通过，详见TEST_REPORT.md、package-verification.json和host-verification.json。本段为实现后的最终包复核，不改变实现前源许可结论。没有未完成的原始MIT分发条件；不宣称外部依赖归本MIT覆盖。用户手测是独立门槛，尚未完成；本轮不得push、开交付PR、Hub提交或Release。
