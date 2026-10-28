# Word 引用脚注转换 1.0.0：用户测试完成确认

- Task ID：`AH-20261027-word-citation-notes`；Candidate ID：`CAND-CLD-322`；负责人及确认人：Cai Zhenze。
- 确认日期：2026-10-28，Asia/Singapore。来源为当前 Codex 对话；没有可用的消息永久链接或精确收信时间，不虚构。截图显示操作时间为14:38–14:41，原图文件名时间为14:53–14:54。
- 用户原话： “I confirm manual testing of Word 引用脚注转换 1.0.0 is complete and passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md, keeping it isolated from Main.”
- 确认报告 ID：`RPT-20261028-word-citation-notes-confirmed-100`。
- 市场包装 ZIP：`03da5e1d00c4873ebaff0e4547470f37ce5c86ba63d9d4f7173a1f73dd63a658`，55944字节。
- WorkSwarm 原生 ZIP：`335a003d520315f8688f548ff284af9154829a3a32fc1cf885ee419870303b57`，54780字节。

## 原始证据与实际范围

六张用户原始PNG保存在`evidence/1.0.0/`，按收到的完整像素和字节复制，没有缩放、重编码或替换；原始文件名、尺寸、字节数和SHA-256见`originals.json`。原图1–4是操作/结果长图，原图5–6分别为实际脚注/尾注结果的宿主文档预览。内容是公开虚构文献与测试路径，未发现账号密钥或私人文档正文。原图不是完整原始工具日志，也不证明Microsoft Word特定版本或点击导航效果。

证据显示1.0.0的真实流程：只读原件检查及完整精确范围预览；过期源摘要、重叠范围和重复键拒绝；用户明确确认后生成脚注并拒绝覆盖；再次明确确认后生成尾注；未确认与错误预览摘要拒绝；宿主独立文件SHA-256及字节数核对；两份结果在实际文档预览中显示正文引用与注释内容，原件和参考文献保留。截图4的“Word渲染未执行”为当时模型报告，后续截图5–6补充用户实际打开的文档预览，不将其泛化为所有Word版本兼容性。

助手于2026-10-28只读复核手测文件，未重新执行或修改人工流程：

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| 公开引用示例.docx | 1844 | `380dcd1233e8eade020a8e6b2ef06d2ab34ba076860ac11637dbc07fb70758e3` |
| 脚注结果-01.docx | 3055 | `1fd9f56e127aa0607169feb09c45aebfa69f3d9175265bc98e8329fcac54d786` |
| 尾注结果-01.docx | 3039 | `3dcc6b0bbd0ff7acd690f1fecebc4d61c9c3a72ea00da63f1c20dd9d16428ef8` |

上述值与截图中的实际输出一致，也与开发阶段实际生成并经LibreOffice渲染验证的两份结果逐字节一致。冻结包和载荷未改变。当前main `2e5aedd6d6d257be8fc635e239d85c4557224f04`仅在本独立工作树快进；最新AGENTS全文重新阅读，blob `e6e315918b1d948ba37bd2a3312c55c05a254d97`。本插件24项功能测试重新通过，包括真实SDK invoke/stream；无模型请求。源许可、安装说明及原始MIT全文完整。

## 交付门槛与限制

当前包测试完成、原图齐全，未发现阻塞问题。历史SOURCE_REVIEW.md、TEST_REPORT.md的“待用户测试”是2026-10-27当时状态，由本确认记录更新当前门槛，不改载荷或ZIP。仍仅支持明确声明的正文结构和用户核准引用范围；不证明文献真实性、Bluebook规范或法律结论，不承诺所有Word版本的分页及导航一致。

用户已授权GitHub交付。PR必须展示六张原图、核验永久证据链接和CI后才可合并。Song Haoran的Project Lead接受仍待完成；不进行Agentic Hub提交、GitHub Release或Asset Ledger更新。
