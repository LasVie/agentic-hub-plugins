# Source and distribution review — Git 分支全景

Reviewed 2026-10-23 after user-authorized autonomous selection/claim; owner Song Haoran.

## Identity and deduplication

CAND-DSH-033 / AH-20261023-git-branch-atlas. Partial Overlap - Extend Existing Capability. Compared Git History Trace 825e6a41c9094622b131d0575d06cb97@0.1.0, official detail explicitly limits tools to file history, blame and show_commit; GitCode Repo a19afa7386394f92bc5a14116d898e1e@1.0.0 handles repository/PR collaboration. Add read-only branch topology, ahead/behind and worktree comparison as a companion, without reimplementing file history/blame or Git mutation. No active task reserves this increment.

Original zhu1090093659/dsh-web -> Git 分支全景 -> git-branch-atlas@1.0.0. This is a bounded portable subset, not the complete upstream host/plugin.

## Pinned source and actual reuse

Source: zhu1090093659/dsh-web; exact revision `56b81a665b4a33a2a6b6a25282ffb1252fadf15e`; license Apache-2.0. Full root/subpackage license and actual reused files reviewed.

- Unmodified Apache core parseGraph, parseBranches, parseWorktrees and computeLanes invoked directly; read-only argv builders ported with prominent change notices.
- Native bounded read-only runner, canonical workspace restriction and ahead/behind added; excluded mutation/UI/telemetry/auto-isolation/service modules. No root/package NOTICE file exists in the reviewed trees.

## File and license evidence

- Full original license bytes: `licenses/upstream/LICENSE`, SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
- `vendor/types.ts`: SHA-256 `a7876578f2e9dcb3d1a7c3a47221c8d779e7b54b72d47e339767f094d5f515c5`.
- `vendor/readonly-argv.mjs`: SHA-256 `a8bb50e18f17ec9bc3f679cbb0f4ef5f3c9ece839c7688725d94d64e6d13a337`.
- `runtime/engine.mjs`: SHA-256 `7c1ac5688173fb79cdb27c184d58e6cb6c76b51334b6088f108d28950f143b31`.

Original copyright/attribution and headers remain intact; full notices are inside the runtime payload. For Apache-derived modified files, prominent change notices are in runtime/engine.mjs and vendor/readonly-argv.mjs; unmodified vendor/types.ts is byte-preserved. For MIT sources, original licenses including disclaimers are retained. No root/package NOTICE exists for the selected git graph source; unrelated third-party notices are not represented as applying to excluded components.

No external runtime packages, fonts, media, vocabulary datasets or upstream host runtimes are redistributed. Node and Python/OpenJiuwen are pre-existing host prerequisites, not bundled distributions. Browser layout and adapters are local additions; no additional repository-wide or new-code relicensing decision is made.

Permission status is verified only for the actual paths/subset above. Packaging and automated checks do not grant legal rights or prove full upstream feature parity. Functional/UI/host results are recorded separately in TEST_REPORT.md.
