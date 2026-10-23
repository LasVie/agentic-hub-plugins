# Source and distribution review — 小说创作台

Reviewed 2026-10-23 after user-authorized autonomous selection/claim; owner Song Haoran.

## Identity and deduplication

CAND-DSH-229 / AH-20261023-story-workbench. Partial Overlap - Extend Existing Capability. Compared webnovel-writing e5830b8ba502461c9ed165263d524f70@c3f17a0 (writing/outline/coherence guidance) and long nonfiction chapter editing 04bd85fd593c408abdb08826c5621eab@1.0.0 (explicitly excludes novels). Add persisted editable fiction project records, revision-checked character/chapter editing and text-anchored annotation, while reusing the existing writing entry point conceptually; do not duplicate its writing instructions or corpora.

Original LiPu-jpg/Openwrite -> 小说创作台 -> story-workbench@1.0.0. This is a bounded portable subset, not the complete upstream host/plugin.

## Pinned source and actual reuse

Source: LiPu-jpg/Openwrite; exact revision `34b038f7c0c037f4f6ee238f6476db34f584e6b0`; license MIT. Full root/subpackage license and actual reused files reviewed.

- Unmodified MIT Studio core functions locateQuote/readableWritingUnits/parseMarkers are invoked directly.
- Native project/character/chapter persistence and annotation API added. Root Apache host, Python backend, DoG, presets, Vditor, fonts, runtime archives and model integrations are not distributed.

## File and license evidence

- Full original license bytes: `licenses/upstream/LICENSE`, SHA-256 `e38aeb00e87dccbb024038215ef856d4211dbc7ce1a279646302872ebc1415f1`.
- `vendor/manuscript-selection.ts`: SHA-256 `c058c8efc474091fec06d275858aa3a40e4106898c9c33f54ca6af410ae807b5`.
- `vendor/manuscript-markers.ts`: SHA-256 `1df2d184b379c28ff212ce1a1000a649a9765423952b5b0426f6c68694c79090`.
- `runtime/engine.mjs`: SHA-256 `ae066f4bccc40a67f3af3643a81a5237343e064053a63ae4fdf5893b5bcd54aa`.

Original copyright/attribution and headers remain intact; full notices are inside the runtime payload. For Apache-derived modified files, prominent change notices are in runtime/engine.mjs and vendor/readonly-argv.mjs; unmodified vendor/types.ts is byte-preserved. For MIT sources, original licenses including disclaimers are retained. No root/package NOTICE exists for the selected git graph source; unrelated third-party notices are not represented as applying to excluded components.

No external runtime packages, fonts, media, vocabulary datasets or upstream host runtimes are redistributed. Node and Python/OpenJiuwen are pre-existing host prerequisites, not bundled distributions. Browser layout and adapters are local additions; no additional repository-wide or new-code relicensing decision is made.

Permission status is verified only for the actual paths/subset above. Packaging and automated checks do not grant legal rights or prove full upstream feature parity. Functional/UI/host results are recorded separately in TEST_REPORT.md.
