# Source and distribution review — 词汇练习室

Reviewed 2026-10-23 after user-authorized autonomous selection/claim; owner Song Haoran.

## Identity and deduplication

CAND-DSH-154 / AH-20261023-word-vault-local. Confirmed New Capability. Compared primary-school tutoring team d3cb3265e9894701b0b15b67228d4d2d@1.0.0 (subject tutoring), learning-output-style repo:agent-plugin:learning-output-style@1.0.4, existing Wiki/memory assets and all active tasks. None declares an executable per-learner word bank, repeat-occurrence counts, randomized answer evaluation or persistent consecutive-correct mastery. Exclude upstream third-party card methodology with unresolved coverage.

Original wangzhanchao883/dsh-word-vault -> 词汇练习室 -> word-vault-local@1.0.0. This is a bounded portable subset, not the complete upstream host/plugin.

## Pinned source and actual reuse

Source: wangzhanchao883/dsh-word-vault; exact revision `f90b94e3a1cbb9dbb8a033fd2d2cad78206c223a`; license MIT. Full root/subpackage license and actual reused files reviewed.

- words.mjs copied unchanged; lemmaOf is called by add_words.
- Occurrence/mastery behavior adapted to the native revisioned SQLite store; db/cards/cardgen/examgen/photos/TTS and third-party mnemonic/layout assets excluded.

## File and license evidence

- Full original license bytes: `licenses/upstream/LICENSE`, SHA-256 `aae1d49ba58af902bbc71ce1b5a60ede3487e09d570b87bf07891b776b4dc406`.
- `vendor/words.mjs`: SHA-256 `8243f11daf53f9b1ba161a9454d7d80cf481e8e45e6ef41c80f7c07ff306bce8`.
- `runtime/engine.mjs`: SHA-256 `dabee5b2d3e76575984346d2975a22be33688f27d808ab44a1b05a9e6ec0e288`.

Original copyright/attribution and headers remain intact; full notices are inside the runtime payload. For Apache-derived modified files, prominent change notices are in runtime/engine.mjs and vendor/readonly-argv.mjs; unmodified vendor/types.ts is byte-preserved. For MIT sources, original licenses including disclaimers are retained. No root/package NOTICE exists for the selected git graph source; unrelated third-party notices are not represented as applying to excluded components.

No external runtime packages, fonts, media, vocabulary datasets or upstream host runtimes are redistributed. Node and Python/OpenJiuwen are pre-existing host prerequisites, not bundled distributions. Browser layout and adapters are local additions; no additional repository-wide or new-code relicensing decision is made.

Permission status is verified only for the actual paths/subset above. Packaging and automated checks do not grant legal rights or prove full upstream feature parity. Functional/UI/host results are recorded separately in TEST_REPORT.md.
