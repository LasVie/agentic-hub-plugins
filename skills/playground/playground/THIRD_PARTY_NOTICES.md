# Third-party notices

## Anthropic official Playground skill

- Upstream: https://github.com/anthropics/claude-plugins-official/tree/d4226d062928f8d9505dbdeadd10217d23361052/plugins/playground
- Pinned commit: `d4226d062928f8d9505dbdeadd10217d23361052`.
- Upstream author identification: `.claude-plugin/plugin.json` identifies **Anthropic** as the author. The copied Markdown files have no separate copyright header. The license appendix contains an unfilled example copyright notice; this port does not present that example as an actual rightsholder declaration.
- Applicable files: `SKILL.md` and all six files under `templates/`, originally under `plugins/playground/skills/playground/`.
- License: Apache License 2.0, copied in full and unchanged to `licenses/claude-plugins-official/LICENSE`. The pinned repository root and plugin-level licenses are identical.
- Upstream NOTICE: none found at the pinned repository root, plugin root, or beneath the copied skill subtree. No upstream NOTICE has been fabricated.
- Modifications: `SKILL.md` adds the local release version, provider-neutral wording, template paths relative to the skill directory, Windows/macOS/Linux browser handoff, headless delivery, clipboard fallback, input handling, and validation boundaries. A prominent modification notice appears in that file. The six Markdown templates are copied without changes.
- Other copied materials: none. No logos, images, fonts, external datasets, runtime libraries, or upstream installation scripts are bundled.

The local installation guide and repository metadata are additions to this port. This notice does not replace the license, change its terms, determine a license for the rest of the repository, or imply upstream endorsement.


## 中文版本修改说明（2026-10-22）

版本 `1.0.1` 将展示信息与使用说明中文化；保留技术标识、原始许可和署名。 `playground` 的 SKILL.md 说明也已翻译，六份固定来源模板保持原样。 本说明不替代或改变上方原始许可条款。


## 六份模板完整中文化（2026-10-22）

本次翻译 `SKILL.md` 和 `templates/code-map.md`、`templates/concept-map.md`、`templates/data-explorer.md`、`templates/design-playground.md`、`templates/diff-review.md`、`templates/document-critique.md`。模板中的说明、界面标签、提示词、帮助、状态提示和注释默认使用简体中文，技术标识与代码语法保留。数据、差异和文档示例采用安全文本 DOM 操作，明确复制失败回退、键盘操作及拒绝建议的边界。上述各文件均带醒目的日期与修改声明。上文“模板原样复制”仅描述历史版本，当前七份指令/模板均为修改后的派生文件；原始来源哈希在 UPSTREAM_FILES.json 保留，另记当前载荷哈希。原始完整 Apache-2.0 许可与作者署名不变，不改变许可条款。


## 中文运行版本 1.0.2（2026-10-22）

按最新中文交付要求翻译实际 Skill、工具说明、帮助及可读提示；模板与资料按实际复用范围记录。技术标识和原始法律声明保持原值。最终包及宿主验证范围见资产测试记录。
