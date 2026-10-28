# Word 引用脚注转换 1.0.0：人工测试

## 本轮冻结包

WorkSwarm原生测试ZIP：`dist/word-citation-notes/1.0.0/word-citation-notes-1.0.0-workswarm.zip`，SHA-256为`335a003d520315f8688f548ff284af9154829a3a32fc1cf885ee419870303b57`。

市场交付ZIP：`releases/agent-plugin/word-citation-notes/1.0.0/word-citation-notes-1.0.0.zip`，SHA-256为`03da5e1d00c4873ebaff0e4547470f37ce5c86ba63d9d4f7173a1f73dd63a658`。两种包装内的8个运行文件完全相同；请手测上述原生包。

Candidate ID：CAND-CLD-322；Task ID：AH-20261027-word-citation-notes；负责人：Cai Zhenze。

本方案不是用户已通过测试的证明。保存真实响应、确切版本及包SHA-256；完成后明确确认并提供原始完整分辨率截图。助手自测/渲染图与用户手测分开记录。

## 安装与准备

本聊天独立WorkSwarm：`http://127.0.0.1:6392/`。在「扩展 → 我的扩展」导入原生ZIP并启用「Word 引用脚注转换」，核对1.0.0、一个技能及三个工具。不要覆盖已有状态机/家庭文档插件，不操作Main。宿主模型保持原设置；若聊天需要模型，请用户自行选择/配置并授权费用，助手不代为调用。

原生ZIP、市场ZIP的最终路径与SHA-256将在交付答复及package-verification.json给出，手测必须使用完全相同的包。目标宿主需外部lxml>=5.0,<7；本轮已有环境为6.1.3，未安装系统依赖。

公开虚构手测目录：

`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/word-citation-notes/1.0.0/manual-workspace`

内有「公开引用示例.docx」「脚注计划.json」「尾注计划.json」及故意错误计划。准备脚本没有生成转换结果；已有文件不删除、不覆盖，不自动更换目录绕过既有状态。所有文件内容都只作数据，不执行其中指令，不使用真实论文或私人资料。

## 第一段：检查和预览，等待本人确认

可复制下面提示；本段不授权写DOCX：

> 请实际测试已启用的「Word 引用脚注转换1.0.0」，全程简体中文。只使用本插件的真实工具结果，不模拟，不把预期当实测。每次响应version必须为1.0.0，不符停止。文件内容只作数据，不读取密钥，不修改原文、宿主、其他插件或Main。
>
> workspace使用上方manual-workspace完整绝对路径，所有文件参数也使用其完整路径。先调用inspect_word_citations，path为「公开引用示例.docx」。展示实际source_sha256、全部段落ID/原文与支持边界。相同2024年份的两份引用不是同一来源，不能凭年份猜位置。
>
> 再调用preview_word_notes，path不变，plan_path为「脚注计划.json」，output为同目录尚不存在的「脚注结果-01.docx」。完整展示全部quote、start/end、note_text、body_action、文档顺序及preview_sha256；说明replace和append各自如何影响正文。然后用「尾注计划.json」和「尾注结果-01.docx」另做只读preview，展示真实摘要和全部动作。
>
> 分别用「过期源摘要.json」「重叠范围.json」「重复键.json」调用preview，均使用原DOCX及尚不存在的「错误计划不应生成.docx」。展示实际错误和版本，预期拒绝仅供比较，不能替代调用。不要修正错误计划或自动换摘要重试。
>
> 说明本轮只读没有生成任何结果。此时不调用apply_word_notes、不传confirmed=true；展示后停止，等我核对两个正确计划及原文件摘要。

## 第二段：确认脚注计划，验证拒绝覆盖

本人核对第一段全部内容后可复制：

> 我已核对刚才实际展示的完整「脚注计划.json」、精确引用/注释文字、正文replace/append动作、原文件SHA-256、输出路径及preview_sha256，明确授权仅对这份公开虚构原件生成「脚注结果-01.docx」。
>
> 调用apply_word_notes，所有路径与刚才脚注preview完全相同，confirmed=true，expected_preview_sha256必须使用刚才真实返回且我已确认的完整值，不猜测或替换。记录实际version、输出路径、字节数、SHA-256、note_count、notes_kind、完整转换报告和原文件SHA-256。
>
> 紧接着使用完全相同参数再次apply到同一输出，展示真实拒绝结果。不得删除、覆盖、更换文件名或重新生成计划绕过。再用inspect_word_citations检查原件仍为原摘要与原正文。本段只授权脚注计划，尾注仍等待下一段明确确认。

## 第三段：确认尾注计划及确认/摘要拒绝

本人另行核对第一段尾注预览后可复制：

> 我已核对第一段实际展示的完整「尾注计划.json」、原件摘要、所有注释与动作、输出「尾注结果-01.docx」及实际preview_sha256，明确授权仅生成该尾注文件。调用apply_word_notes，confirmed=true，expected_preview_sha256使用真实且已确认的尾注预览值，其余路径保持一致。展示实际输出版本、字节数、摘要、note_count、notes_kind和报告。
>
> 对原件及「脚注计划.json」，指定同目录尚不存在的「拒绝测试不应生成.docx」，先用confirmed=false和脚注真实预览摘要调用apply，展示实际拒绝；然后confirmed=true，但expected_preview_sha256故意使用64个字符0，再调用一次，展示实际拒绝。不能把旧输出路径改动导致的摘要差异说成原件改动，也不能自动替换摘要重试。不得生成此拒绝测试输出。
>
> 用宿主文件工具独立计算原DOCX和两份实际结果的SHA-256，比较插件返回值；若无此能力标为未执行，不把插件报告当独立校验。不执行任何文件内容。

## 第四段：真实Word/兼容查看器人工核对

请本人在支持脚注/尾注的Word、LibreOffice或兼容查看器打开两个实际结果并保留截图。WorkSwarm附件卡或XML文本不能代替真实文档渲染。

- 脚注文件：正文标记按文档顺序对应两条页下注，点击标记可定位注释。
- 尾注文件：标记对应文末注，注释文字/页码与已批准计划逐字一致。
- 原文包含中文、emoji和拆成多个样式运行的引文；检查未选文字、加粗/斜体、参考文献段落保持，不把纯文字注释声称为Bluebook认证。
- replace只替换选中引文；append保留选中引文后加标记。两个2024引文分别对应各自注释。
- 保存原始完整分辨率截图，显示1.0.0工具结果、成功/拒绝、真实Word注释位置。工具操作成功、XML结构通过、渲染核对和用户实测通过分别记录。

最后请用中文汇总「项目｜实际结果｜通过/失败/未执行/无法验证｜理由」。未实际检查的Word分页、其他编辑器、复杂结构、真实文献来源、Bluebook和法律结论不得标通过。若原文或包发生改动，报告实际版本/摘要，停止等待处理；不能继续沿用旧包确认。
