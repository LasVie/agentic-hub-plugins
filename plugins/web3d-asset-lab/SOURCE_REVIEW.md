# Source and distribution review: web3d-asset-lab

Reviewed 2026-11-02. glTF Transform -> 网页 3D 模型瘦身台 -> web3d-asset-lab. Task AH-20261102-web3d-asset-lab; Candidate CAND-EXT-010; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/donmccurdy/glTF-Transform . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
- three@0.187.0 — MIT；licenses/three--0.187.0/LICENSE

仅采用glTF Transform的有界模型操作；原生Sharp/libvips及其LGPL二进制不打包。未提供的原生图像I/O入口替换为显式报错模块。彩色贴图缩放由独立浏览器Canvas与SDK实现，属于用户主动选择的有损分辨率调整。演示模型由本插件自行构造，不搬运第三方模型。

This asset does not bundle the MPL component used by the mock workbench. No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.

## Concrete tracker comparisons

Compared parametric modeling 0e1febdb63934c92b64fe4f64d8c2a01@e7bda4f and active solid-mesh Boolean task AH-20261031-solid-mesh-workbench. Targets existing glTF scenes/materials and web delivery costs; excludes CAD construction, STEP/STL conversion and Boolean operations.

Main was refreshed through de13a4b (PRs 69/70: offline observing and GeoJSON simplification); those scopes do not overlap these developer engines. Final source/native/canonical/installed file equality and current ZIP hashes are in package-verification.json.


## 1.0.5 source-level compatibility rebuild (2026-11-04)

Owner Song Haoran, Task AH-20261102-web3d-asset-lab and Candidate CAND-EXT-010 remain unchanged. The frozen 1.0.4 Hub upload was rejected for Function string compilation in vendor/engine.mjs; no Web3D Hub asset was created. That result is a platform packaging gate, not a finding of malicious intent. Canonical 1.0.4 SHA b8ede1eaae52659cdd030f6f13a07576703c904081c5cc741059d998a19eca67 remains in its versioned release; native 1.0.4 SHA d26594e8c0217ea5d029b80322a18cc3765ded770ef3b655bf6c13792376bb88 is preserved byte-identically under test-packages/history/. Historical package-verification and build inventories are in build-evidence/history/.

The changed source input is official @gltf-transform/functions 4.5.1 dist/index.js, pinned npm gitHead 41156dfa2324ac6c44ddf0a40ec0da194c4731d6. Its package and full MIT license remain under their original terms. build/rebuild_engine.mjs uses a TypeScript AST to narrow its public exports to dedup/weld/prune and actually remove the unused ndarray and ndarray-lanczos import declarations; esbuild then removes the unreachable image-transform bodies. It does not rename/encode Function, supply a fake ndarray, move prohibited code to a hidden archive, or fetch missing code at runtime. The emitted vendor/engine.mjs contains no ndarray/lanczos identifier or string-compilation call in the recorded AST check. The original algorithms and the existing explicit unsupported-native-image-codec error remain. No claim of full image-codec support or upstream-certified safe build is made.

The functions derivative is documented in build-evidence/geometry-subset-build.json with original/derived input SHA values and emitted module graph. vendor/model-view.mjs, vendor/texture-resize.mjs, runtime/handler.cjs and web/app.js retain exact 1.0.4 bytes. All original copyright/license files remain unchanged. Four unused code dependencies (ndarray, ndarray-lanczos, iota-array, is-buffer) retain full MIT texts as historical notices and are expressly marked code_in_current_runtime=false in licenses/COMPONENTS.json; they are not advertised as runtime capabilities. Other retained components keep their original MIT texts. Build-only esbuild/TypeScript/glTF validator and platform binaries are not distributed in the runtime payload.

Isolated dependencies came only from the existing build-evidence/npm-build.lock.json fixed official registry URLs and integrity fields; 13 archives totaling 10,343,146 compressed bytes were independently integrity-verified, extracted outside the repository/runtime, and no lifecycle script/global environment was run. No Sharp/libvips or new platform toolchain was added. Build reproduction: set WEB3D_BUILD_DEPS to this isolated directory and run Node 22+ build/rebuild_engine.mjs. The source transformations and intermediate parser guards are explicit in that script.

Actual source regression: 42/42 checks passed, including frozen-engine byte equality for fixture and optimized demo/animated GLBs, zero-error original/optimized GLB validator reports, identical rejection of 13 invalid cases through inspect and optimize, and real optimization under Node --disallow-code-generation-from-strings. Existing 1.0.4 GUI images and user-delegated testing stay historical; the 1.0.5 WorkSwarm GUI import/prompt, browser rendering/Canvas recheck and new originals remain REQUIRED before PR/Hub delivery. No current Hub success is inferred from these local tests.


## Final current-package GUI evidence — 1.0.5 (2026-11-04)

The earlier pre-GUI gate in this record is now satisfied for the exact frozen 1.0.5 package under explicit user Agent delegation. Root Agent performed actual native import/install and prompt operations in **WorkSwarm desktop0.2.8 / Python3.12.13 / Node22.12.0**, using the host internal BrowserWindow, not Safari. All 27 installed files match source/native/canonical/artifact. Geometry and explicit lossy Canvas operations, real GLB/report export, native EngineTool load, restore/own-service restart persistence and final stop are recorded in GUI_TEST_REPORT.md and evidence/1.0.5/. Three actual GUI GLBs validate with zero errors/warnings/infos and downloaded files match saved bytes. Sixteen original images remain unmodified, including the native WorkSwarm long PNG.

No code, license text, runtime payload or ZIP changed after freezing/import. Both full original 1.0.4 ZIPs/history and original rights/owner/IDs remain preserved. Outer test/provenance/artifact references are updated to the actual final evidence; this is not a new runtime release or repack. Current evidence is Agent-operated, not personal human acceptance. Project Lead acceptance, remote head CI, PR merge and future Hub acceptance are separate states; none is invented by this source review. See build-evidence/history/ for full original historical records.
