# math-olympiad source and package review

Date: 2026-10-27 (Asia/Singapore). Member: Vannes Wijaya.
Task: `AH-20261027-math-olympiad`; candidate: `CAND-ANT-038`.

## Scope, authority and naming

Vannes Wijaya explicitly selected CAND-ANT-038 and asked to start development in the
current Claude Code conversation on 2026-10-27, requesting a Plugin (not a bare Skill).
Candidate `Planned` / owner / linked task and the new Development Tasks row were written
by the user in the tracker and read back by export before implementation. The retired
Task ID `AH-20261022-math-olympiad` (cancelled 2026-10-22) is not reused.

Naming: upstream `math-olympiad` → Chinese display name **奥数竞赛证明与对抗验证** →
internal slug `math-olympiad` (stable internal ID `repo:agent-plugin:math-olympiad`).

Duplicate finding (Phase 1, unchanged): `Confirmed New Capability`; no Asset Ledger entry
covers competition-proof solving with adversarial verification and calibrated abstention.
Kickoff recheck 2026-10-27: no live Development Task other than this one references the
candidate; no newer ledger/task capability found by name/purpose search in the export.

## Pinned source and coverage

Upstream: https://github.com/anthropics/claude-plugins-official
Revision: `d4226d062928f8d9505dbdeadd10217d23361052`; path `plugins/math-olympiad`.
Upstream declares no plugin version; skill frontmatter `version: 0.1.0`.
Author: Anthropic, `support@anthropic.com`, from the pinned `.claude-plugin/plugin.json`.

Inspected the complete plugin tree (README, LICENSE, plugin.json, SKILL.md, 7 references,
2 scripts, 1 eval file) plus the repository root. Root `LICENSE` and plugin `LICENSE` are
byte-identical Apache-2.0 texts (SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`).
No NOTICE exists at the root, `plugins/` or in the plugin. No file carries a copyright
header; ownership is not invented.

| Package path | Upstream source | Treatment |
| --- | --- | --- |
| `skills/math-olympiad/SKILL.md` | `skills/math-olympiad/SKILL.md` | Translated to Chinese; single-agent staged workflow; model-tier table replaced by budget presets; verdict mapping added; change notice at top |
| `skills/math-olympiad/references/*.md` (6 files) | same names | Faithful Chinese translation; subagent wording rewritten as stages; change notice at top of each. Heading/code-block/pattern-number/math-marker counts match upstream exactly |
| `skills/math-olympiad/scripts/check_latex.sh` | same | Checks `xelatex` + `ctexart.cls`; change notice |
| `skills/math-olympiad/scripts/compile_pdf.sh` | same | `ctexart`, xelatex only, Chinese theorem names, usage check, mkdir; change notice |
| `README.md` | partly from upstream README | New Chinese README; benchmark claims removed; adaptation notice |
| `LICENSE`, `licenses/claude-plugins-official/LICENSE` | upstream LICENSE | Unchanged copies |
| `manifest.json`, `THIRD_PARTY_NOTICES.md` | — | New repository files |
| Not shipped | `references/model_tier_defaults.md`, `evals/trigger_eval.json`, `.claude-plugin/plugin.json` | Claude-specific / not runtime |

Brand: the name “Anthropic” appears only in attribution; no logos, icons or endorsement
claims. No fonts, data, services or third-party dependencies bundled. Optional runtime
dependency `xelatex` + `ctex` is user-installed and not distributed.

Permission status: `verified`; mode: `ported`. Apache-2.0 §4 obligations: (a) license copy
bundled twice; (b) prominent change notices at the top of every modified file;
(c) no upstream attribution notices to retain beyond author credit, which is kept in
THIRD_PARTY_NOTICES.md and README; (d) no NOTICE to carry. §6: no trademark use.

## Functional differences from upstream

- Upstream launches 8–12 parallel solver subagents and up to 5 fresh-context verifier
  subagents. The host runs one agent and the repository manifest forbids `subagents`, so
  these become sequential stages of the same agent with procedural isolation. This is a
  real weakening of upstream's main lever and is disclosed in SKILL.md, README and every
  final answer.
- Chinese output by default; Chinese LaTeX/PDF via ctexart.

## Final ZIP review

Repository ZIP `releases/agent-plugin/math-olympiad/1.0.0/math-olympiad-1.0.0.zip`,
SHA-256 `f401d739852e5549445d0929154a9aaca53958e46ae752a66521c15afcff52f0`. Extracted and checked by
`tests/math_olympiad_package_test.py`: outer dir holds only `plugin.yaml` + `math-olympiad/`; exact
14-file payload; both license copies hash-match `license_evidence`; Apache change notice at the top of
all 9 adapted files; THIRD_PARTY_NOTICES.md lists every covered path. No tests, task records or
caches in the wrapper.

Fulfilled: license copy, change notices, author attribution, no fabricated NOTICE, no trademark use.
Unresolved: none for licensing. AI conclusion: `verified` / `ported`.
