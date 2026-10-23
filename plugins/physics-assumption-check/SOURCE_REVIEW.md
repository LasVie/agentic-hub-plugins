# Source review — 物理解题审校 1.0.1

Candidate: `CAND-CLD-250`; Task: `AH-20261023-physics-assumption-check`; owner: **Cai Zhenze**. Reviewed 2026-10-23, Asia/Singapore. User explicitly approved Phase 2 in the current independent second Codex conversation. This is a ported Plugin, not an independent rewrite claim.

Naming: **Fisica → 物理解题审校 → physics-assumption-check**. Stable internal identity: `repo:agent-plugin:physics-assumption-check`. No Hub identity or submission is inferred.

## Pinned source and actual coverage

Source: <https://github.com/Carlotess/fisica/tree/f53864e09df2a7d91f5c2a86ac60b4ac7e987bbf>; manifest version `1.0.0`. The complete tree, README, root LICENSE, manifest, Skill, reference and image script were inspected. Exact fetched bytes were checked against the pinned Git blob identities; the review did not execute upstream scripts. `audit-upstream` is supporting detection only; its automatic `unknown` output does not replace this content review.

Root MIT text contains **Copyright (c) 2026 Carlotess**, the permission grant for software and associated documentation, notice-retention condition and full disclaimer. No nested LICENSE or NOTICE appears in the complete inspected tree. The README identifies MIT without conflicting additional reuse terms. No third-party copied material is identified in the selected text/script paths. The optional icon has no separately established provenance and is excluded.

| Upstream path | Pinned Git blob SHA-1 | Adapted runtime path |
| --- | --- | --- |
| `skills/fisica/SKILL.md` | `af981cd27265671a9ff89c3039c4c5947980d5d9` | `skills/physics-review/SKILL.md` |
| `skills/fisica/references/errores-comunes.md` | `e4df4c2afc692c5934dcf5132e44b2c15dc920da` | `skills/physics-review/references/common-errors.md` |
| `skills/fisica/scripts/ampliar.py` | `4851e1f8b688806598f61ff966ea042892a8368e` | `scripts/prepare_figure.py` |
| `README.md` | `d5c030001c1c432dabc2ba46dd9a2f9322b908d1` | `README.md` (adapted installation/use documentation) |
| `LICENSE` | `91a1890c91bde3c25fabf7c12b9975cf0c9474c5` | `licenses/fisica/LICENSE` (unchanged bytes) |

The selected scope is covered by MIT; `mode: ported`, `permission_status: verified`. Bundle the complete original license at `licenses/fisica/LICENSE`, SHA-256 **`b273a3590e2290ab4e55acdd824bb37f19940cea6c01cfef271c32f2628005d2`**, and retain original attribution in each adapted file. Bundled `THIRD_PARTY_NOTICES.md` lists source, revision, covered paths and modifications. MIT does not require an Apache-style change notice, but prominent modification records are included under repository convention. Upstream NOTICE: absent; Apache-specific obligations: not applicable to these MIT materials. No repository-wide licensing decision is made.

## Changes and dependencies

Chinese localization covers name, description, Skill, reference, installation/use instructions, defaults, tool description, JSON messages and CLI help/errors. The end user's explicit output-language request overrides the Chinese default. Technical schema/parameter names and original legal text are retained.

The script retains crop/LANCZOS/enhancement ideas, with a new bounded dictionary/JSON interface, EXIF orientation normalization, transparent-pixel preservation, metadata removal, optional enhancement off by default, format/frame/byte/pixel checks and exclusive PNG creation. It never overwrites an existing path or changes the source file. The native openJiuwen adapter and Plugin manifest are new host integration. This helper prepares evidence for viewing; it does not infer diagram topology, perform OCR or solve equations. The Skill supplies a model-guided reasoning protocol. Simplified upstream statements about momentum and rolling friction are qualified in the Chinese reference.

External Python dependency: Pillow `12.2.0`, already available in the isolated testing interpreter. Its installed complete license (MIT-CMU plus bundled codec/dependency notices) was inspected. Pillow binaries/source/codecs are not copied into the Plugin; a pinned requirement and attribution/reference are supplied. No upstream font, image, data, icon, service credential or model weights are distributed. openJiuwen `0.1.19` and WorkSwarm are host-provided dependencies, not vendored. Test fixtures are independently drawn synthetic diagrams, kept outside the runtime payload.

## Functional comparison

Compared the Phase 1 review with current live development records and open/merged PR activity at kickoff. Existing primary-school tutoring `d3cb3265e9894701b0b15b67228d4d2d@1.0.0` / `582da98925144fae85d9496d0ea97e92@1.0.0` excludes secondary/higher tutoring. Simulation review `da13d597743247348214550bd2aa3f78@1.0.0` assesses numerical-model credibility; CFD team `d8bcb2d409884f5da841d3846ecf48fa@0.0.1` explicitly excludes analytical fluid dynamics without simulation. Peer Review `1f53f98b3e4348d69a42b25b6c6ce459@356ea33` annotates submitted academic work. Fisica instead produces text/diagram interpretation, a physical model, equations linked to assumptions, checked results and a risk-ordered assumption audit. Main's `CAND-CLD-219 — fet`, Deckaura Tarot and DSH 韵律分析 cover different inputs/actions/outputs and remain excluded from this task.

## Distribution review procedure

Canonical output: `releases/agent-plugin/physics-assumption-check/1.0.1/physics-assumption-check-1.0.1.zip`. Native WorkSwarm companion: `dist/physics-assumption-check/1.0.1/physics-assumption-check-1.0.1-workswarm.zip`, derived from the canonical inner payload without changing runtime bytes. Exact ZIP identity and real extracted-package/host verification results are recorded in `TEST_REPORT.md` and `artifact.json`; the companion equality record is local test evidence. Extracted review must confirm all declared paths, Chinese files, the unchanged full license and notices; source/ref/license mappings above are the checklist. No screenshots, logs, caches, environments or upstream research copies belong in the runtime ZIP.

Extracted-distribution review completed on 2026-10-23 for delivery 1.0.1. The 9-file payload, four adapted text/script paths, their attribution/modification records, full MIT bytes and license-evidence hash all matched the current source, native companion and installed payload. All declarations and relative license links resolve. Original notice text is intact, no applicable upstream NOTICE is missing, and excluded media/binaries/development files are absent. Canonical SHA-256 is `e363550695bda9524f5f1c3e3d6764f35ab36a2111fe5f4d5e7275dd7be5b06f`; native SHA-256 is `9eb25694e42a1c9b952cb32f6c511bd4921a867a2e5f12c31430880077794707`. The independently reviewed failure-handling fixes are included in 1.0.1; unpublished preflight 1.0.0 is archived outside the release tree.

User manual testing, explicit completion for the exact version/hash and original screenshots remain separate future gates. This source review does not establish testing completion, legal clearance beyond the reviewed permission scope, or Hub acceptance.
