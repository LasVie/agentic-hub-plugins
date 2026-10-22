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
