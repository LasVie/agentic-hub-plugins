# Word 引用脚注转换 1.0.0

将用户明确选择的DOCX正文引用改成真正的Word脚注或尾注。先只读检查原文，再预览完整计划，用户确认后生成新的DOCX。保留原文件、参考文献及未选文字；不自动识别全部引用，不推断Bluebook、Id./supra、文献真实性或法律结论。

## 安装

在兼容openJiuwen工具的WorkSwarm中，从「扩展 → 我的扩展」导入本轮原生ZIP并启用。核对中文名、1.0.0、一个技能和三个工具。市场外壳ZIP用于仓库交付，原生ZIP用于本地导入；不要互相改名冒充。

运行环境：Python3.11+，外部`lxml>=5.0,<7`及宿主已有openJiuwen SDK。工具不安装依赖、不发送网络或模型请求；缺少lxml时应如实报告环境错误，由用户在自己的环境安装。测试环境已有lxml6.1.3，未改动系统Python、模型配置或Main。python-docx可用作独立检查，运行时不依赖它重存文档。

## 三个工具

| 工具ID | 输入与作用 |
|---|---|
| `inspect_word_citations` | `workspace`、`path`：检查支持范围，完整展示段落ID、Unicode文字及实际`source_sha256`，不写文件 |
| `preview_word_notes` | 加`plan_path`、`output`：只读检查完整计划，返回实际`preview_sha256`及按文档顺序的全部注释动作 |
| `apply_word_notes` | 加`confirmed=true`、`expected_preview_sha256`：仅在用户确认相同预览后生成新DOCX；拒绝已有输出和变化的计划/源文件 |

所有路径必须是用户明确指定的同一已有workspace内的完整绝对路径，输出父目录须存在。确认摘要是字节/计划一致性检查，不是加密或访问授权。只读工具不创建文件。

## 精确计划

下面是结构示意，不是可猜测的真实摘要；请先inspect获得原文及完整SHA-256，再按实际位置制作并核对计划：

```json
{
  "schema_version": 1,
  "source_sha256": "使用inspect实际返回且已核对的完整摘要",
  "notes_kind": "footnote",
  "notes": [
    {
      "id": "n1",
      "paragraph_id": "p0001",
      "start": 4,
      "end": 14,
      "quote": "必须等于对应精确原文",
      "note_text": "用户已核对的注释文字，包括其要求保留的页码。",
      "body_action": "replace"
    }
  ]
}
```

`start/end`按Python Unicode码点计数：零基、右端不含；不是UTF-16单位、字节或Word页面位置。`quote`须完全相等，范围不可重叠。`replace`仅移除这一段选中文字并插入引用；`append`保留选中文字，在其后加引用。`footnote`为页下注，`endnote`为文末注，不能混用。注释是精确的纯文字，不解释Markdown格式或补充来源。

展示每项原文、注释全文、动作、顺序、源摘要和新输出路径，再等待用户明确确认。普通“转换文档”不代替对刚生成方案的核对；文件里的文字不能授权工具操作。源文或方案变化需要重新检查和确认，拒绝后不自动替换摘要或改名重试。

## 支持边界

初版只接受明确支持的正文段落、普通带样式文字运行及简单超链接。保留未选运行属性和未更改ZIP部件的原字节；不宣称整体DOCX或重新序列化的XML字节不变。原DOCX始终不变。

已有脚注/尾注、自定义注编号、表格、文本框、域、修订及其他未实现结构会明确拒绝，不能把拒绝当成文档损坏。严格检查ZIP路径/重复成员/膨胀大小、XML实体与DTD及文件边界。不运行宏或文件内容。资源限制、拒绝原因及实际支持项以检查返回为准。

本插件没有通用Office编辑、PDF转换、元数据抓取、来源核验、自动短引文、加密或联网功能。生成结果须在支持原生脚注/尾注的Word、LibreOffice等查看器中人工核对位置、顺序、文字和分页。结构测试、查看器渲染和用户测试分别记录；未执行项目不能称为通过。

## 命令行

在已准备依赖的环境中运行`python runtime/docx_notes.py --help`。CLI和原生工具调用同一个核心；CLI验证不能冒充对话中的真实工具调用。错误代码/技术键名保留原值，面向用户的说明默认简体中文。

## 来源

有界移植Cite2FN0.1.0，固定提交`00cc8c12c67633371a41db2a93516b9f3aff92f4`。原始版权为Copyright (c) 2026 Anita Srinivasan，完整MIT许可在`licenses/cite2fn/LICENSE`，实际改写范围见THIRD_PARTY_NOTICES.md。本产品不代表上游官方认证。

