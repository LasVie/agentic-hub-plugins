# Source and integration review

- Candidate: CAND-EXT-013. Task: AH-20261110-offline-pipe-network-workbench. Owner: Cai Zhenze.
- Approved mapping: EPANET JavaScript Toolkit → 离线管网水力工作台 → `offline-pipe-network-workbench`, version 1.0.0.
- Mode: ported. No reuse of the separately FSL-licensed EPANET-JS application, its implementation, visuals, datasets or assets. That application's public functional description/license was seen during review.
- Starting repository: origin/main `933fc0f232c677fbf7f38c12482deb22cef8fded`; own branch `feat/offline-pipe-network-workbench`. Historical untracked evidence and parallel work preserved.

## Pinned materials and actual use

Official npm `epanet-js@0.9.0` archive SHA-256 `8ee2b2bc8a0f31f254dba3d664865ccefeb21b04262d2686eda298740e76d035`, toolkit tag `v0.9.0`, commit `84fcb48880a640119ad968161d08a97815931584`. The only compiled files copied, byte for byte, are `dist/engines/v2.3.5/index.mjs`, `_engine.mjs` and `EpanetEngine.wasm`. Payload hashes are recorded in `web/vendor/epanet/UPSTREAM.json`. No dependency is patched.

The proposed slim Workspace entry contains only Workspace; the main Project entry also embeds the default MSX engine. Neither is needed. Plugin-owned `hydraulics.js` instead calls the explicit non-MSX engine's exported, documented EPANET C API through `ccall`. Numeric warning codes are retained directly, avoiding the high-level wrapper's console-only warning handling. This is a bounded adapter, not a host/dependency patch.

OWA-EPANET 2.3.5 source commit `444725fbf16ab28b0470ef0ed281dc4849d49583`, source archive SHA-256 `9bd03df20d53b0fe26be755be40b9219a95843f4a92c8d878dcc42d020e857e2`. Toolkit source archive SHA-256 `bc3fe501a07c0f4341d74fb706e4b00e78c77eea3816eeb0c02cdbd0e46e8909`. Pinned engine Dockerfile specifies Emscripten 4.0.6. The published binary is used unmodified; no reproducible-binary-build claim is made. Source and archives were retrieved to task-owned temporary research storage, not packaged as redundant runtime copies.

## License coverage

Full toolkit MIT text (Luke Butler, 2019) and full engine MIT text plus required AUTHORS were read and bundled. The engine MIT explicitly requires the author list. `mempool.c` references Steve Hill / Graphics Gems III; its original attribution and the permissive Graphics Gems grant are retained. `genmmd.c` attributes Joseph W. H. Liu; that attribution is retained under the engine's distributed MIT grant. These credits are not replaced by new team attribution.

Generated browser glue and linked runtime notices: Emscripten 4.0.6 complete LICENSE and AUTHORS (MIT option selected, original dual text retained); musl complete COPYRIGHT plus original copyright/permission headers collected from its math/complex/stdlib/stdio/string sources; compiler-rt complete Apache-2.0 WITH LLVM-exception / historical license text; dlmalloc 2.8.6 original public-domain/CC0 statement and full CC0 grant. The compiled engine is C, not C++; no libc++ font or GUI code is used. Original legal texts are unchanged. No upstream NOTICE file was found for the selected toolkit or OWA source; component notices were retained separately without inventing an upstream NOTICE.

The three vendor files are unmodified; no Apache source-file modification notice is applicable. Plugin-owned adapter/UI/schema/tests/examples are newly written. The standard-library POSIX lifecycle and native Tool loader are adapted from the repository's maintained offline-score-workbench 1.0.0 mechanism, retaining foreign-installation rejection, random ports and user-click navigation. No shared host, SDK, other plugin or dependency file is changed. No blanket repository relicensing is asserted.

## Scope and correctness boundaries

One fixed-head reservoir, 2–50 nodes, 1–80 open pipes, steady demand-driven flow; LPS, metres, mm, H-W, zero minor loss. No pumps/valves/tanks/controls, quality or extended period. Strict model reader rejects duplicate JSON keys, unknown fields, disconnected models and invalid ranges. Node insertion respects EPANET's junction-before-reservoir index ordering. Worker owns the complete solver and is terminated on edits, cancellation or 12-second timeout. Exports require a current completed result and include warnings/version/units.

Baseline inventory review found no ready hydraulic tool. Baseline can calculate formulas or write code; no paid same-model A/B session is run. Numerical tests use independent H-W, conservation and symmetry expectations, not model prose. Actual installed-host dispatch and manual acceptance must be recorded separately from standalone SDK/browser engineering tests.

## Packaging verification

Native/canonical hashes, extracted payload equality, dynamic-JavaScript preflight, legal evidence hashes, actual host/browser checks and remaining limitations are recorded in TEST_REPORT.md and the final artifact records after testing. No Hub acceptance is claimed from local checks.

Post-build review (2026-11-10): all33 inner paths match the native ZIP, extracted canonical payload and actual installed package. Seven real engine tests, eleven POSIX lifecycle tests and installed-browser QA passed; report details and hashes are in TEST_REPORT.md. WorkSwarm integration used a fresh unmodified0.2.5.beta1 source snapshot and an independent physical copy of its existing unmodified dependency distribution files. Only task-local supported runtime configuration was adjusted; no host source/dependency patches. Runtime freshness/ownership checks and current-result export gating retained. Public SDK invocation is distinguished from pending model-driven chat dispatch. Local dynamic-script preflight passes both exact ZIPs; no Hub success is asserted.

Phase3 distribution check2026-11-10: retained exact native `plugins/offline-pipe-network-workbench/test-packages/offline-pipe-network-workbench-1.0.0-workswarm.zip` SHA-256 `1414048b02e90649ed7708035fd2be68715b1fa5189b58686d33f11b397be6df` and canonical `releases/agent-plugin/offline-pipe-network-workbench/1.0.0/offline-pipe-network-workbench-1.0.0.zip` SHA-256 `dd16d4fe65be52c55a3f379a2014e69cdc11e3f1a6eb8e730e9091668bc1d3f6`. Rechecked all selected license-evidence hashes and33-file equivalence; original compiled files and legal texts unchanged. Required conditions fulfilled for this identified distribution; no unresolved reuse condition identified. User confirmation/original screenshot inventory is separate in USER_TEST_CONFIRMATION.md; no unsupported-host or Hub acceptance is inferred.
