# Test report: 网页 3D 模型瘦身台 1.0.5

**Current result: source/extracted-package engine regression and actual Agent-operated WorkSwarm GUI passed.** Owner Song Haoran; Task AH-20261102-web3d-asset-lab; Candidate CAND-EXT-010. This records delegated Agent execution, not personal human acceptance.

## Frozen delivered package

| Package | Bytes | SHA-256 |
| --- | ---: | --- |
| Canonical 1.0.5 | 1,861,915 | `bfa66c5faa59cf88127633e94137de808b16c521a15a196e41ee0fb539384c0a` |
| Native 1.0.5 | 373,986 | `1dafe82986d6cda8b328b463b70b2dcbb01b9fbd16c4b208b2e0c5a02d935cce` |

All 27 source, canonical, native and artifact payload hashes match; all 27 actual installed files also match with no extra/missing files. No runtime file or ZIP changed after the frozen package's GUI import. Current package-verification.json records those values; both outer artifact report references are refreshed after this final report.

## Source-level build and real engine regression

Node v22.12.0 with fixed original-lock esbuild 0.28.2/TypeScript 5.9.3 built the official glTF Transform 4.5.1 source derivative exporting only dedup/weld/prune and genuinely removing unused ndarray/lanczos imports. Original transform algorithms and the existing unsupported-native-codec boundary remain. The emitted dependency graph excludes ndarray/iota-array/is-buffer/lanczos; AST review found no retained direct Function/eval-family call or string timer. This is bounded inspection, not a formal security guarantee or Hub approval.

The source suite passed **42/42**, then actual canonical ZIP extraction passed **42/42**. It compared fixture, inspect and optimized bytes against frozen 1.0.4 for demo and animated data, checked preserved nodes/animations, repeated optimization, four validator reports, and thirteen malformed/unsupported cases through both inspect and optimize. Actual fixture→optimization also passed Node `--disallow-code-generation-from-strings`. Eight final source/extracted validator reports have zero errors/warnings. Unsupported names initially added only to a synthetic animation fixture were removed before the recorded final run; its initial warnings remain in local audit history. No plugin bytes changed for that fixture correction.

Commands:
- `WEB3D_BUILD_DEPS=<isolated pinned deps> node plugins/web3d-asset-lab/build/rebuild_engine.mjs`
- `node plugins/web3d-asset-lab/tests/geometry_subset_regression.mjs <payload> <frozen 1.0.4 engine> <output> <isolated pinned deps>`

Final results: [source](tests/results/1.0.5/engine-regression-results.json), [extracted canonical](tests/results/1.0.5-extracted/engine-regression-results.json), [build](build-evidence/geometry-subset-build.json). Isolated official downloads totaled 10,343,146 compressed bytes across thirteen integrity-verified fixed archives; no global installation/lifecycle script or Sharp/libvips distribution occurred.

## Actual current WorkSwarm GUI

2026-11-04 15:30–15:43 Asia/Singapore: **WorkSwarm desktop 0.2.8 / Python 3.12.13 / Node 22.12.0**, with the actual native internal BrowserWindow. This is distinct from older isolated SDK/1.0.4 environments. The root Agent completed current native import/install, status/start prompt, both rendered model views and rotation, real geometry optimization, explicit lossy 128×128 color-texture resize, native Save-panel GLB/report exports, second native EngineTool load, restore, own-service stop/start persistence and final stop.

Observed actual fixture sizes: 6,114,024 → 383,548 bytes (geometry), then 5,456 bytes after explicit lossy texture resize. Meshes 16→1, nodes 16→16. Downloaded final GLB/report equal saved files exactly; original GLB SHA stayed unchanged. Three actual GUI GLBs validate with zero errors/warnings/infos. Both test ports were confirmed closed after final stop.

See [GUI_TEST_REPORT.md](GUI_TEST_REPORT.md), [full session](evidence/1.0.5/gui-test-session.json), [16 unmodified originals](evidence/1.0.5/originals.json), [actual export hashes](evidence/1.0.5/gui-export-verification.json), [actual validators](evidence/1.0.5/actual-gui-validator/actual-gui-glb-validation-index.json), and [current Agent test authority](USER_TEST_CONFIRMATION.md). All old 1.0.4 full records remain in build-evidence/history/ and below.

Limits: GUI fixture has no animation, so playback was not verified. Automated animated-data tests do not establish playback. Other platforms, arbitrary models/extensions, guaranteed compression or total absence of vulnerability are not claimed. The GUI pass does not imply PR merge, Hub acceptance or Project Lead acceptance.

---

# Historical 1.0.4 report (original text preserved below)

Historical path map: its native archive is now test-packages/history/web3d-asset-lab-1.0.4-workswarm.zip; its exact original package-verification.json is build-evidence/history/package-verification-1.0.4.json. The full original historical report is also retained byte-for-byte as build-evidence/history/TEST_REPORT-1.0.4-original.md.

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
