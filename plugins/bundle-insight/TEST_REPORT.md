# Test report: 前端包体积透视台 1.0.4

Task AH-20261102-bundle-insight; candidate CAND-EXT-009; owner Song Haoran. Tested 2026-11-02–2026-11-03 (Asia/Singapore).

## Authority and package identity

Song Haoran explicitly delegated development, local WorkSwarm tests, original screenshots and PR submission without further confirmation. This is agent-run testing, not fabricated human testing or Project Lead acceptance. See USER_TEST_CONFIRMATION.md.

Final Chinese version: 1.0.4. Canonical ZIP: releases/agent-plugin/bundle-insight/1.0.4/bundle-insight-1.0.4.zip. Native companion: test-packages/bundle-insight-1.0.4-workswarm.zip. Exact ZIP SHA-256 and every runtime file hash are in package-verification.json. Source, canonical inner payload, native inner payload and actual WorkSwarm installation were compared byte for byte.

## Actual functional results

The installed UI loaded actual Rollup/Visualizer statistics, rendered the treemap, selected /catalog.js and displayed its importer /app.js. Snapshot comparison measured 1,508 -> 14,669 rendered module bytes; /catalog.js increased by 13,161 bytes. The engine suite performs real small/large builds and rejects invalid input. The exported interactive HTML is the actual generated file.

The shared real-engine integration suite passes 14 cases from source and again from extracted final canonical ZIPs: lifecycle/confirmation, real HTTP scenarios, OpenAPI examples/external-reference rejection, page persistence/export, actual PostgreSQL JSONB/write/restart/isolation/error recovery/snapshot, actual Rollup builds/comparison, real GLB optimization/persistence, invalid inputs, cross-origin/owner/symlink checks and bounded host-tool output. Commands and preserved logs are in ../../docs/deliveries/dev-five-20261102/.

The final version was installed with the running WorkSwarm 0.2.9b1 standard plugin_packages APIs, enabled in a real conversation, and invoked through its actual native SDK tool loader. This host evidence is separate from direct engine tests. Global host configuration and other catalog entries were compared without recording configuration secrets.

An additional regression imports identical snapshots with the same module ID in multiple parts and verifies every delta is zero. Both comparison sides sum all module parts.

## Original screenshots and exports

- ../../docs/deliveries/dev-five-20261102/images/bundle-insight.jpg

Original browser JPEG bytes are preserved without resizing, retouching or reconstruction. The evidence index records image hashes, task and version. Actual HTTP exports were compared to saved files; the PostgreSQL snapshot additionally used the browser download flow. Other endpoint checks are not claimed as browser download tests. See export-verification.json; GLBs also passed independent gltf-validator (zero errors/warnings).

## Environment and limits

macOS arm64, Python 3.11.17 test runner, Node.js 22.12.0 from the existing WorkSwarm application, local WorkSwarm's existing SDK/runtime and configured model. Host/model configuration was not changed. Desktop in-app browser and real local services were used; other platforms were not verified.

Rollup/Vite Visualizer raw-data input only, 10 MiB / 5,000 modules; does not execute a user's project configuration. Fixture builds are labeled as fixtures. Per-module gzip/Brotli sums are not whole-response transfer size.

## Resolved development failures

Unpublished trials exposed oversized Base64 model results, a GrapesJS class/build issue, browser language overriding Chinese and missing icon fonts. Binary tool results now return byte/hash summaries bounded to 16 KiB; actual host calls pass. GrapesJS follows upstream ES5 class semantics with explicit Chinese locale and local text controls. Model loading disables operations until rendering completes. Only final ZIPs enter the PR; earlier local trials remain in ignored research storage.

No Hub operations, Asset Ledger registration, automatic merge or Project Lead acceptance are claimed.
