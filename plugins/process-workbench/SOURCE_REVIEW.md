# Source and distribution review — 流程执行台

Reviewed 2026-10-23 after user-authorized autonomous selection/claim; owner Song Haoran.

## Identity and deduplication

CAND-DSH-227 / AH-20261023-process-workbench. Partial Overlap - Extend Existing Capability. Compared workflow-standardization-team f928db94a6c7499ba3d177c24d50e8e8@0.0.1, agent-team-orchestration b68e551f74ec46818b51492be6efb83c@e7bda4f and project delivery expert 907e16140e984e82898b7cee47f44f94@1.0.0. Their SOP/coordination guidance does not declare a persisted executable template validator with step/run revisions and locally recorded evidence gates. Add an explicit local execution-record companion, without duplicating agent orchestration or automatic work.

Original weibaohui/dsh-process -> 流程执行台 -> process-workbench@1.0.0. This is a bounded portable subset, not the complete upstream host/plugin.

## Pinned source and actual reuse

Source: weibaohui/dsh-process; exact revision `97c11790728f897278d044b17062c36d069e9a8b`; license MIT. Full root/subpackage license and actual reused files reviewed.

- flowTarget and extractMeta preserved; structural validation adapted from the reviewed validator.
- JSON templates replace YAML; manual explicit evidence-backed transitions replace host agent execution, scoring, scheduling and arbitrary commands. No bundled process library or external kit/yaml dependency is copied.

## File and license evidence

- Full original license bytes: `licenses/upstream/LICENSE`, SHA-256 `8f466caa0d7f2244d1ac0d4ec523692c9c8e5f509fcdd89b974b82988c736807`.
- `vendor/process-core.mjs`: SHA-256 `4aa8c681737e8835865a1d0e35b82f4379bc0a12ffc6267a0fab983ab2ac3087`.
- `runtime/engine.mjs`: SHA-256 `94e395b535c79fd95953a563a0b2b08fa095fb82c069909c7110c321ff1107eb`.

Original copyright/attribution and headers remain intact; full notices are inside the runtime payload. For Apache-derived modified files, prominent change notices are in runtime/engine.mjs and vendor/readonly-argv.mjs; unmodified vendor/types.ts is byte-preserved. For MIT sources, original licenses including disclaimers are retained. No root/package NOTICE exists for the selected git graph source; unrelated third-party notices are not represented as applying to excluded components.

No external runtime packages, fonts, media, vocabulary datasets or upstream host runtimes are redistributed. Node and Python/OpenJiuwen are pre-existing host prerequisites, not bundled distributions. Browser layout and adapters are local additions; no additional repository-wide or new-code relicensing decision is made.

Permission status is verified only for the actual paths/subset above. Packaging and automated checks do not grant legal rights or prove full upstream feature parity. Functional/UI/host results are recorded separately in TEST_REPORT.md.
