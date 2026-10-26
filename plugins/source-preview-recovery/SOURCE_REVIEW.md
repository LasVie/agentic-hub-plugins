# Source and reuse review

Reviewed 2026-10-23 for Cai Zhenze; CAND-DSH-121; AH-20261023-source-preview-recovery.
Mapping: vibe-any/dsh-plugin-save-token → 原文快照与精简预览 → source-preview-recovery.
Internal identity: repo:agent-plugin:source-preview-recovery.

## Pinned source and permission

Retrieved upstream Git commit e241dbc23288d7d1b6865cf726c8e777c4ce7e08, DSH package2.4.1 / standalone adapter1.0.0, into a separate sparse checkout in /private/tmp. Root full MIT LICENSE states Copyright(c)2026 PlayWithAI. Inspected root/source/subtree file listing, package metadata, README, src/compress.js, standalone tools.js/store.js. No selected subtree has a conflicting license or NOTICE. GitHub public access alone was not the permission basis: the complete MIT grant, conditions and disclaimer were read. No media, fonts, service code, benchmark datasets, third-party fixtures, research papers or performance claims are reused. Root devDependencies esbuild/React are not needed or bundled; no runtime external dependencies are declared by the selected upstream modules.

Mode ported: runtime/recovery.py adapts the licensed compact-view workflow and head/tail, error-context and table-sampling ideas from src/compress.js plus spill-before-preview/recovery behavior from standalone tools/store. It replaces the host/storage/orchestration and scalar rendering rather than claiming an independent implementation. README adapts the workflow explanation; new wrapper, snapshot integrity/path handling and tests are repository implementation. Full original MIT license and original compress.js/tools.js/store.js headers are retained in the inner payload under licenses/save-token/. Original claims in that historical header are not adopted as product guarantees. No applicable upstream NOTICE found; none fabricated. No unified license is assigned to repository-owned additions.

## Required corrections and scope

All condensed output is explicitly a preview. Raw bytes are persisted before preview transformation; durable SHA-256 content IDs, verified full snapshots, correct source-line coordinates and exclusive export replace memory-only references, truncating expansion, lexical-only path checks and automatic pruning. JSON scalar types are displayed explicitly; large numbers do not pass through binary float. Duplicate JSON keys fall back to a source-line preview. Snapshot creation does not modify the source. No shell/host hook/deduplication/billing/model action is included. Token/cost/intelligence savings are not promised.

Closest assets: Context Insight72c01bbdeaee47c4ad9eeaa9d7ae630e@1.0.3 and d0facc36f10c4f82b9592633a2dc0b11@1.0.3 inspect usage; encoding guard repo:agent-plugin:dsh-fs-encoding@1.0.4 preserves edit encoding. This plugin supplies compact views with exact snapshot recovery. Kickoff checked deliveries through PR44; WindowsToolkitPR42 and Main InvadersPR44 are distinct and preserved.

## Final package audit

Preflight1.0.0 source/extracted43 tests, installed13 Tool calls and fresh-process recovery passed; full292 tests/1skip and check-repo32assets/41ZIPs passed. Final header review added original standalone tools/store headers, so unhanded1.0.0 artifacts were moved outside deliverables to /private/tmp/source-preview-recovery-preflight-100. Final1.0.1 was subsequently rechecked as recorded below. This preflight history does not claim user confirmation for1.0.0.


Final1.0.1 audit2026-10-23: canonical SHA-256183bc30c69074c0748d07e399a0664478200152699fd91e97bd86b5a521a2d14; native SHA-25699d19c3d678c8c6a64fa269375362a71345bb8bf9335a39553f320af2da168b5. All8 source/canonical/native/installed payload files identical; UTF-8 checked. Full licenses/save-token/LICENSE exactly matches upstream SHA-256d9f4d0687b6934f18e9bab4e75f26c04b83a5f5d7898f464a921abd1ee8ef85e. licenses/save-token/UPSTREAM_HEADER.txt retains verbatim opening headers for compress.js, standalone tools.js and store.js; THIRD_PARTY_NOTICES.md maps actual scope and modifications; runtime/recovery.py has prominent port/change notice. No applicable upstream NOTICE or selected media. Source43/extracted43 tests,13 installed Tools plus new-process recovery and full292tests/1skip passed. No known unresolved reuse condition for these actual8 files. Current package ready for manual testing; user confirmation/original screenshots remain future gates.

## Phase3 re-verification2026-10-26

User explicitly confirmed current1.0.1 manual testing complete/passed and authorized Phase3. Five original full-resolution PNGs were received before delivery push/PR; USER_TEST_CONFIRMATION.md records the actual message, exact package association, hashes and stated limits. All8 source/canonical/native/installed files and bothZIP hashes remain identical to the tested handoff. Read-only manual-state comparison independently verified all5snapshots, the1000000-byte export and61-byte CRLF range without modifying user files. User restart testing remains unperformed; prior automated new-process recovery evidence is separately attributed. No real token/billing/answer-quality claim.

Latest origin/main e6769f6 incorporated into this isolated feature branch; latest AGENTS.md remains blob e6e315918b1d948ba37bd2a3312c55c05a254d97. Scope/license/headers rechecked against actual unchanged payload; no additional distribution obligation or blocking issue found. Private Python3.12.14/PyYAML6.0.3 environment passed313repository tests with64optional SDK/Pillow skips, including all43source-preview tests and localhost music integration from currentmain. check-repo34assets/43ZIPs passed. CI and actual PR evidence-link verification are still required before merge. Main's checkout/branch/runtime and Asset Ledger are preserved; no Hub operation or Release.
