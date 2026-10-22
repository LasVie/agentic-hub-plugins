# Third-party notices

## Anthropic learning-output-style

- Author statement: the upstream Plugin's `.claude-plugin/plugin.json` identifies **Anthropic**, `support@anthropic.com`, as its author. No additional copyright holder or year is invented here.
- Source: https://github.com/anthropics/claude-plugins-official/tree/d1adba47161a271799de7b548225d929310046bd/plugins/learning-output-style
- Pinned commit: `d1adba47161a271799de7b548225d929310046bd`; upstream version: `1.0.0`.
- Applicable license: Apache License, Version 2.0, as supplied in that Plugin directory.
- Full license: `licenses/claude-plugins-official/LICENSE`.
- Covered materials: `prompt_sections/learning-output-style.md` (the SessionStart hook's extracted `additionalContext`); `skills/learning-contribution/SKILL.md` (an adapted invocation procedure).
- Modifications on 2026-10-22: load the teaching text through native prompt sections instead of executing Bash; prepend an attribution/change notice; add a Skill entry for explicit contribution coaching. Each derived text file carries a prominent modification notice. The original teaching text remains byte-identical after the notice in the prompt file.
- Applicable upstream NOTICE: none found in the repository root or Plugin subtree at the pinned commit. This file is an adaptation notice, not a fabricated upstream NOTICE.
- Original file headers: the upstream script's explanatory comments are described in the source review; the full original script and author metadata remain in the review evidence outside the runtime payload. No original copyright or attribution header is removed from a copied runtime file.

The runtime payload bundles no icons, fonts, datasets, third-party packages, or executable upstream hooks. JiuwenSwarm and its configured model are external host dependencies and are not redistributed. Brand names describe origin and compatibility; this package does not imply endorsement or general trademark permission.

## Chinese documentation update, version 1.0.2

Modified on 2026-10-22 at the Project Lead-side user request: localized market display metadata and README/user instructions in Chinese and updated package version/source records. The active prompt and contribution Skill retain their exact 1.0.1 bytes. Original full licenses, author statements and earlier change notices are retained. This documentation change does not add a new upstream source, runtime dependency, or endorsement.


## 中文运行指令修改（2026-10-22）

本次将 `prompt_sections/learning-output-style.md` 及 `skills/learning-contribution/SKILL.md` 翻译为简体中文，默认中文讲解、邀请和反馈，并保留用户明确指定其他语言的选择。教学流程和技术标识保留，实际译文字节与上方历史版本所述英文内容不同。英文原文来源哈希、中文正文哈希和中文完整文件哈希在 SOURCE.json 中分开记录。两个派生文件均有醒目的修改说明。原始完整 Apache 许可与署名文本未变，本说明不改变许可条款或表示官方背书。


## 中文运行版本 1.0.3（2026-10-22）

按最新中文交付要求翻译实际 Skill、工具说明、帮助及可读提示；模板与资料按实际复用范围记录。技术标识和原始法律声明保持原值。最终包及宿主验证范围见资产测试记录。


## 中文运行版本 1.0.4（2026-10-22）

按最新中文交付要求翻译实际 Skill、工具说明、帮助及可读提示；模板与资料按实际复用范围记录。技术标识和原始法律声明保持原值。最终包及宿主验证范围见资产测试记录。
