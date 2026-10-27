# Third-party notices

## Anthropic math-olympiad

Source: https://github.com/anthropics/claude-plugins-official

Pinned revision: `d4226d062928f8d9505dbdeadd10217d23361052`.
Plugin: `plugins/math-olympiad` (no version declared upstream; skill frontmatter `version: 0.1.0`).
Original author: **Anthropic**, `support@anthropic.com`, as credited in the pinned
`.claude-plugin/plugin.json`. Upstream files carry no separate copyright headers;
no replacement ownership claim is added here.

License: **Apache-2.0**. Complete, unchanged texts are bundled in `LICENSE` and
`licenses/claude-plugins-official/LICENSE` (identical to the upstream root and plugin LICENSE).

No separate upstream NOTICE file exists at the repository root, `plugins/`, or within
this plugin at the pinned revision. This file is an attribution inventory, not a
fabricated upstream NOTICE, and does not change license terms.

## Covered files (adapted from upstream)

| Package path | Upstream path |
| --- | --- |
| `skills/math-olympiad/SKILL.md` | `plugins/math-olympiad/skills/math-olympiad/SKILL.md` |
| `skills/math-olympiad/references/verifier_patterns.md` | same name under upstream `references/` |
| `skills/math-olympiad/references/adversarial_prompts.md` | same |
| `skills/math-olympiad/references/solver_heuristics.md` | same |
| `skills/math-olympiad/references/presentation_prompts.md` | same |
| `skills/math-olympiad/references/known_constructions.md` | same |
| `skills/math-olympiad/references/attempt_agent.md` | same |
| `skills/math-olympiad/scripts/check_latex.sh` | `plugins/math-olympiad/skills/math-olympiad/scripts/check_latex.sh` |
| `skills/math-olympiad/scripts/compile_pdf.sh` | `plugins/math-olympiad/skills/math-olympiad/scripts/compile_pdf.sh` |
| `README.md` | partially based on `plugins/math-olympiad/README.md` |

Each modified file carries a prominent Chinese change notice at its top.

Not included: upstream `references/model_tier_defaults.md` (Claude model-tier specific),
`evals/trigger_eval.json`, and the upstream `.claude-plugin/plugin.json` manifest.
No icons, fonts, data, services or dependencies are bundled.

## Modifications (2026-10-27, Vannes Wijaya)

- Translated instructions, references, README and output templates into Simplified Chinese; Chinese output by default.
- Rewrote multi-subagent parallel solving and voting verification as a single-agent staged workflow (procedural context isolation), because the target host runs one agent.
- Replaced Claude model-tier defaults with task-based budget presets.
- Switched PDF typesetting to `ctexart` + `xelatex`; localized theorem names and messages.
- Removed upstream benchmark claims that depend on a non-public evaluation harness.
- Added native `manifest.json`, this inventory and the conventional full-license path.

No Anthropic endorsement or general trademark rights are claimed.
