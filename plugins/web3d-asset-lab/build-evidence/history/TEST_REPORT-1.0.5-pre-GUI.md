# Current prototype: 网页 3D 模型瘦身台 1.0.5

2026-11-04, macOS arm64, WorkSwarm bundled Node v22.12.0. Owner Song Haoran; stable Task/Candidate IDs unchanged. This is actual Node engine/validator testing under the existing explicit Agent delegation; it is not a claim of new GUI or personal human acceptance.

The source-level minimal build removes unused ndarray code generation. 42/42 meaningful checks passed against source: frozen 1.0.4/new fixture equality, exact optimized bytes and resource reports for demo plus an animated fixture, preservation of nodes/animation counts, repeated optimization, four zero-error GLB validator reports, 13 malformed/unsupported inputs rejected identically by both inspect and optimize, and actual engine operation with string code generation disabled. See tests/results/1.0.5/engine-regression-results.json. Validator reports retain actual warnings/info counts; no arbitrary-model guarantee is inferred.

Commands (Node is an existing local runtime):
- WEB3D_BUILD_DEPS=<isolated pinned deps> node plugins/web3d-asset-lab/build/rebuild_engine.mjs
- node plugins/web3d-asset-lab/tests/geometry_subset_regression.mjs <new payload> <frozen 1.0.4 engine> <output> <isolated pinned deps>

New WorkSwarm GUI import/prompt, Three.js rendering, explicit Canvas texture resize, real browser exports/reimport and unmodified screenshots for the exact new package are still pending root-agent testing. The animation fixture checks stored model data, not animation playback. No Hub acceptance has occurred. Current source/native/canonical hashes are in package-verification.json once packed; old hashes are retained in build-evidence/history/package-verification-1.0.4.json.

---

Final canonical extraction was independently tested: another 42/42 checks passed from the actual 1.0.5 ZIP payload. Eight final source/extracted validator reports (original/optimized demo/animated fixtures) have zero errors and zero warnings. See tests/results/1.0.5-extracted/. Initial synthetic animation-name warnings remain in the local rebuild audit; no plugin payload change was made to resolve this fixture-only issue.

# Historical 1.0.4 report (preserved)

# Test report: 网页 3D 模型瘦身台 1.0.4

Task AH-20261102-web3d-asset-lab; candidate CAND-EXT-010; owner Song Haoran. Tested 2026-11-02–2026-11-03 (Asia/Singapore).

## Authority and package identity

Song Haoran explicitly delegated development, local WorkSwarm tests, original screenshots and PR submission without further confirmation. This is agent-run testing, not fabricated human testing or Project Lead acceptance. See USER_TEST_CONFIRMATION.md.

Final Chinese version: 1.0.4. Canonical ZIP: releases/agent-plugin/web3d-asset-lab/1.0.4/web3d-asset-lab-1.0.4.zip. Native companion: test-packages/history/web3d-asset-lab-1.0.4-workswarm.zip. Exact ZIP SHA-256 and every runtime file hash are in build-evidence/history/package-verification-1.0.4.json. Source, canonical inner payload, native inner payload and actual WorkSwarm installation were compared byte for byte.

## Actual functional results

The installed Three.js UI rendered both actual models. Geometry/resource deduplication reduced the self-generated GLB from 6,114,024 to 383,548 bytes (16 meshes -> 1, 16 scene nodes retained). An explicit lossy color-texture resize reduced 512x512 to 128x128, yielding 5,456 bytes; the original remains. Both original and final exported GLBs passed gltf-validator with zero errors and zero warnings. Initial loading now disables operations to prevent stale load/operation rendering.

The shared real-engine integration suite passes 14 cases from source and again from extracted final canonical ZIPs: lifecycle/confirmation, real HTTP scenarios, OpenAPI examples/external-reference rejection, page persistence/export, actual PostgreSQL JSONB/write/restart/isolation/error recovery/snapshot, actual Rollup builds/comparison, real GLB optimization/persistence, invalid inputs, cross-origin/owner/symlink checks and bounded host-tool output. Commands and preserved logs are in ../../docs/deliveries/dev-five-20261102/.

The final version was installed with the running WorkSwarm 0.2.9b1 standard plugin_packages APIs, enabled in a real conversation, and invoked through its actual native SDK tool loader. This host evidence is separate from direct engine tests. Global host configuration and other catalog entries were compared without recording configuration secrets.

## Original screenshots and exports

- ../../docs/deliveries/dev-five-20261102/images/web3d-geometry.jpg
- ../../docs/deliveries/dev-five-20261102/images/web3d-textures.jpg

Original browser JPEG bytes are preserved without resizing, retouching or reconstruction. The evidence index records image hashes, task and version. Actual HTTP exports were compared to saved files; the PostgreSQL snapshot additionally used the browser download flow. Other endpoint checks are not claimed as browser download tests. See export-verification.json; GLBs also passed independent gltf-validator (zero errors/warnings).

## Environment and limits

macOS arm64, Python 3.11.17 test runner, Node.js 22.12.0 from the existing WorkSwarm application, local WorkSwarm's existing SDK/runtime and configured model. Host/model configuration was not changed. Desktop in-app browser and real local services were used; other platforms were not verified.

Embedded standard GLB <=25 MiB; required decoder extensions/external resources are rejected. Geometry operations are dedup/weld/prune; no universal compression or arbitrary-extension/no-loss guarantee. Only base-color/emissive PNG/JPEG textures are resized; data/normal maps are skipped. The fixture contains no animation, so animation playback is not claimed.

## Resolved development failures

Unpublished trials exposed oversized Base64 model results, a GrapesJS class/build issue, browser language overriding Chinese and missing icon fonts. Binary tool results now return byte/hash summaries bounded to 16 KiB; actual host calls pass. GrapesJS follows upstream ES5 class semantics with explicit Chinese locale and local text controls. Model loading disables operations until rendering completes. Only final ZIPs enter the PR; earlier local trials remain in ignored research storage.

No Hub operations, Asset Ledger registration, automatic merge or Project Lead acceptance are claimed.
