# Test report: 可视化网页搭建台 1.0.4

Task AH-20261102-visual-web-studio; candidate CAND-EXT-007; owner Song Haoran. Tested 2026-11-02–2026-11-03 (Asia/Singapore).

## Authority and package identity

Song Haoran explicitly delegated development, local WorkSwarm tests, original screenshots and PR submission without further confirmation. This is agent-run testing, not fabricated human testing or Project Lead acceptance. See USER_TEST_CONFIRMATION.md.

Final Chinese version: 1.0.4. Canonical ZIP: releases/agent-plugin/visual-web-studio/1.0.4/visual-web-studio-1.0.4.zip. Native companion: test-packages/visual-web-studio-1.0.4-workswarm.zip. Exact ZIP SHA-256 and every runtime file hash are in package-verification.json. Source, canonical inner payload, native inner payload and actual WorkSwarm installation were compared byte for byte.

## Actual functional results

Installed GrapesJS editor loads with Chinese text controls, without fetching external icon fonts. A Chinese heading was changed to 让插件交付看得见、改得动, a component card was added, mobile and desktop devices were selected, and the project was saved and restored. The exported HTML contains that heading and 协作交付; exported project JSON contains one resumable page.

The shared real-engine integration suite passes 14 cases from source and again from extracted final canonical ZIPs: lifecycle/confirmation, real HTTP scenarios, OpenAPI examples/external-reference rejection, page persistence/export, actual PostgreSQL JSONB/write/restart/isolation/error recovery/snapshot, actual Rollup builds/comparison, real GLB optimization/persistence, invalid inputs, cross-origin/owner/symlink checks and bounded host-tool output. Commands and preserved logs are in ../../docs/deliveries/dev-five-20261102/.

The final version was installed with the running WorkSwarm 0.2.9b1 standard plugin_packages APIs, enabled in a real conversation, and invoked through its actual native SDK tool loader. This host evidence is separate from direct engine tests. Global host configuration and other catalog entries were compared without recording configuration secrets.

## Original screenshots and exports

- ../../docs/deliveries/dev-five-20261102/images/visual-web-studio.jpg
- ../../docs/deliveries/dev-five-20261102/images/visual-web-mobile.jpg

Original browser JPEG bytes are preserved without resizing, retouching or reconstruction. The evidence index records image hashes, task and version. Actual HTTP exports were compared to saved files; the PostgreSQL snapshot additionally used the browser download flow. Other endpoint checks are not claimed as browser download tests. See export-verification.json; GLBs also passed independent gltf-validator (zero errors/warnings).

## Environment and limits

macOS arm64, Python 3.11.17 test runner, Node.js 22.12.0 from the existing WorkSwarm application, local WorkSwarm's existing SDK/runtime and configured model. Host/model configuration was not changed. Desktop in-app browser and real local services were used; other platforms were not verified.

Static HTML/CSS component projects only; no arbitrary React round-trip or automatic website publication. The unreviewed old formatting addon is excluded. The upstream source is transpiled with its ES5 class semantics to preserve Backbone compatibility.

## Resolved development failures

Unpublished trials exposed oversized Base64 model results, a GrapesJS class/build issue, browser language overriding Chinese and missing icon fonts. Binary tool results now return byte/hash summaries bounded to 16 KiB; actual host calls pass. GrapesJS follows upstream ES5 class semantics with explicit Chinese locale and local text controls. Model loading disables operations until rendering completes. Only final ZIPs enter the PR; earlier local trials remain in ignored research storage.

No Hub operations, Asset Ledger registration, automatic merge or Project Lead acceptance are claimed.
