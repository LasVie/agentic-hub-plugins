# Test report: 网页 3D 模型瘦身台 1.0.4

Task AH-20261102-web3d-asset-lab; candidate CAND-EXT-010; owner Song Haoran. Tested 2026-11-02–2026-11-03 (Asia/Singapore).

## Authority and package identity

Song Haoran explicitly delegated development, local WorkSwarm tests, original screenshots and PR submission without further confirmation. This is agent-run testing, not fabricated human testing or Project Lead acceptance. See USER_TEST_CONFIRMATION.md.

Final Chinese version: 1.0.4. Canonical ZIP: releases/agent-plugin/web3d-asset-lab/1.0.4/web3d-asset-lab-1.0.4.zip. Native companion: test-packages/web3d-asset-lab-1.0.4-workswarm.zip. Exact ZIP SHA-256 and every runtime file hash are in package-verification.json. Source, canonical inner payload, native inner payload and actual WorkSwarm installation were compared byte for byte.

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
