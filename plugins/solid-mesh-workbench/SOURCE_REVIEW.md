# Source review: 立体网格布尔工坊 1.0.0

Reviewed 2026-10-31 for Cai Zhenze, Task `AH-20261031-solid-mesh-workbench`; Candidate ID: Not Applicable. Naming: **Manifold / manifold-3d → 立体网格布尔工坊 → solid-mesh-workbench**. Mode: `ported`; permission status: `verified` for the precisely identified distribution below. This is a source-permission review, not a claim of legal advice, user test completion, or Project Lead acceptance.

## Decision and actual reuse

The approved capability is offline Boolean editing of existing closed, oriented triangular solid meshes, through our own supported WorkSwarm native plugin and local tool/service. The package does not change WorkSwarm or another plugin. This extends beyond the ledger's parametric model generation scope; fixtures are only bounded boxes/cylinders. The review and live ownership checks preceding registration were handled in the original task. There is no fabricated external candidate record.

Reuse is limited to the **unchanged** official `manifold-3d@3.5.4` package files `manifold.js` and `manifold.wasm`, stored under the inner payload's `vendor/`. The project independently implements OBJ validation, topology checks, indexed project JSON, the engine adapter, process control, native tool, Chinese UI and tests. `vendor/package.json` is our two-field ESM declaration, not an npm installation. No upstream editor, examples, media, font, icon, service credential or full dependency tree is included. No upstream file was modified by this project; therefore no project change notice is missing from a modified upstream file. Original embedded modification statements are retained with the license evidence.

## Immutable sources and artifact integrity

- Canonical repository: [elalish/manifold](https://github.com/elalish/manifold/tree/ce50d78021d64507f89e8c9fc2c2e51018117857), version `3.5.4`, commit `ce50d78021d64507f89e8c9fc2c2e51018117857` (also the npm registry's `gitHead`). `manifoldcad/manifold` is not the source repository.
- Official archive: [manifold-3d-3.5.4.tgz](https://registry.npmjs.org/manifold-3d/-/manifold-3d-3.5.4.tgz), 721465 bytes, SHA-256 `cf57c91fcd33b6315bff28e424ac8c5f04acb5410e9dd8e9886838303910c568`. SHA-512 matched the registry integrity `sha512-WWsme5HabwLHVcWPHT9m+s7mdmDVSEvCny+uXH1E7jEc8FbFUgM75C3Dh6NVw57Eeh3Ow7+xHCuXfxDMOemi9A==`. Registry signatures were not separately verified. No installation/build scripts ran.
- `vendor/manifold.js`: 82371 bytes, SHA-256 `ca3c8a88df63bb3083013d1eb7f700bf23216594f6e98a2566e34f55d7341ce8`.
- `vendor/manifold.wasm`: 541470 bytes, SHA-256 `73e3b419ad31294f6b1cc478173944e50efc4a34bfdeeff0107bdfc12975f11c`.
- The complete pinned Manifold source archive was inspected read-only in task-owned scratch: SHA-256 `c7b3626593380866b599f7b5927de857d4780e94fdb97bf2f015a879d7084537`. It is not part of the deliverable. Relevant `src/`, `include/manifold/`, binding headers, build options and dependencies were inspected; no upstream NOTICE exists in this fixed tree or npm archive.
- The source workflow uses Emscripten `5.0.2` / commit `dc80f645ee70178c11666de0c3860d9e064d50e4`, serial WASM publication (`MANIFOLD_PAR=OFF`) and Node 24 for upstream CI. Emscripten source archive SHA-256 `59f3b1a8e25b514f0d6f6993b3860e53a2d4f5057b6a8bc8f508f209ee145548` was read only for license inventory, not built or installed.

## License findings by covered material

The npm `Apache-2.0` label alone is insufficient: all of the following evidence is bundled inside the runtime payload. `provenance.json` records each actual license file and SHA-256. Required original English legal text remains unchanged in substance. The Chinese `THIRD_PARTY_NOTICES.md` maps rights holders, compiled coverage and modifications.

| Covered material | Finding and distribution action |
| --- | --- |
| Manifold core and JS bindings | Root and binding LICENSE contain Apache-2.0; preserve full `licenses/manifold/LICENSE` and AUTHORS. The two generated files remain byte-identical. No upstream NOTICE to copy; no trademark endorsement asserted. |
| Embedded `src/disjoint_sets.h` | Wenzel Jakob 2015; complete zlib-style grant and restrictions appear in the file header. The header explicitly describes Manifold's connected-component modification. Retain complete header in `licenses/dset/LICENSE`. |
| Embedded `src/svd.h` | MIT, wi-re 2019 and Manifold Authors 2023; complete grant/disclaimer and Manifold's CUDA/inverse-square-root modification statement preserved in `licenses/tbtsvd/LICENSE`. |
| Embedded `include/manifold/math.h` | Apache Manifold adaptation plus Sun Microsystems 1993 permission conditioned on notice preservation. Complete original header retained in `licenses/sun-math/LICENSE`. |
| Embedded linalg adaptation | Fixed Manifold header identifies public-domain linalg 2.2, Sterling Orsten, Stan Melax and Dimitri Diakopoulos. Preserve header and full upstream Unlicense. License evidence was read at upstream tree `4460f1f5b85ccc81ffcf49aa450d454db58ca90e`; no code from that newer tree was copied. Manifold does not specify the original linalg commit. |
| Embedded QuickHull adaptation | Fixed Manifold header identifies public-domain work by Antti Kuukka, alongside Manifold Apache terms. Upstream README at tree `4ef66c68950cb4db11d3b75bfe4034d807485ad0` explicitly dedicates the implementation to the public domain. Preserve both declarations; no separate QuickHull implementation was copied. Original adapted commit is not specified by Manifold. |
| Embedded PhysX snippets in `src/tri_dist.h` | Manifold names BSD 3-Clause and source URLs, noting minor modifications. Preserve those statements and full NVIDIA 2008–2025 BSD-3-Clause license from immutable upstream tree `b97365c6ddb32fda8469bc788ec18024862b0368`, license blob `2388f6f9a26a42277e0dd0bf4b7b55af5aee29e5`. Original snippet commit is unspecified; no code from the inspected latest tree was copied. |
| Clipper2 default CrossSection backend | Build/workflow pin `46f639177fe418f9689e8ddb74f08a870c71f5b4`; full Boost Software License 1.0 and Angus Johnson 2010–2025 file attribution preserved. Upstream build carries its documented no-iostream guard patch; this project performs no new Clipper modification. |
| Emscripten-generated glue | Full MIT/NCSA text includes Emscripten authors and Node/Joyent notice. Choose MIT for Emscripten dual licensing; retain full original text plus AUTHORS. |
| Embedded libc/C++ runtime | Preserve Emscripten 5.0.2's musl COPYRIGHT, all identified per-file copyright/permission blocks from musl source (including Sun, Arm, BSD and MIT terms), and libc++/libc++abi/compiler-rt full Apache-2.0 WITH LLVM-exception and legacy license texts with CREDITS. This is a conservative notice superset, not a link-map claim that every listed function survives compilation. |
| dlmalloc serial allocator | Emscripten's default serial allocator retains Doug Lea 2.8.6 public-domain declaration referencing CC0 1.0. Preserve original statement and full referenced Creative Commons legal text. Parallel-only mimalloc and TBB are excluded by the inspected serial build configuration. |

Binary inclusion is derived from the official archive, pinned source/build workflow and generated imports; no independent binary-reproducibility or exact symbol link-map claim is made. The reviewed notices cover the relevant permissive source and runtime families conservatively. This package does not relicense repository-owned adaptation work. No API/service terms or paid calls are required for runtime operation.

## Compatibility and scope limits

The adapter uses documented `Mesh`/`Manifold` construction, `add`, `subtract`, `intersect`, `rotate`, `translate`, `getMesh`, metrics and `delete`. The generated JS imports only Node built-ins (`node:module`, `node:fs`, `node:path`, `node:url`); it contains no `eval` or `new Function`. The adapter supplies local WASM bytes. Browser-only fetch paths in upstream glue are never used by the Node adapter. Upstream issue [1902](https://github.com/elalish/manifold/issues/1902) concerns the full package dependency tree; none is installed or bundled here.

Require an existing Node.js 22+ runtime, Python as documented in the plugin, and a modern desktop browser for the local UI. Actual core execution is verified on Node 24.19.0 on this worktree machine; Node 22 host validation is recorded separately by integration testing. No Node 18 compatibility claim or runtime installation is made. Host UI changes and arbitrary browser DOM/CSS injection are out of scope.

Inputs require explicit `units: "mm"`, schema `solid-mesh-workbench/v1`, and union/difference/intersection. Supported OBJ is only finite `v x y z`, three positive one-based integer `f` indices, whitespace and comments. No slash/relative indices, n-gons, normal/material/texture records, external reference, script or arbitrary HTML/CSS is accepted. An imported closed oriented mesh must have valid directed edge pairing, a connected manifold neighborhood at each topological vertex, nonzero triangle area, valid indices and positive total volume. This is not exhaustive geometric self-intersection detection or mesh repair, and does not certify print readiness.

Coordinates become IEEE Float32 positions in Manifold; project roundtrip preserves those accepted positions, triangle indices and explicit merge maps, not arbitrary original decimal precision or unsupported attributes. Equal coordinates are never implicitly welded. OBJ export resolves only explicit topology merge identities. Project JSON stores canonical local mesh operands plus transforms; transforms rotate in degrees about the origin before translation. Cylinder is a regular polygon prism approximation. Empty Boolean results succeed with zero metrics and null bounds; their comment-only OBJ is not a valid solid input.

Limits: input/project JSON 2 MiB; each input and exported OBJ 1 MiB; each operand/result 10000 property vertices and 20000 triangles; coordinates and translation within ±100000 mm; primitive dimensions/radius 0.01–10000 mm; rotations ±360°; cylinder 8–128 integer segments. Results beyond limits fail in Chinese. The caller imposes 20 seconds, 256 MiB JS heap and 4096 WASM pages (256 MiB), with only its own child process terminated on cancellation. These separate heap ceilings are not a 256 MiB total-RSS promise.

## Actual functional evidence and remaining gates

`node --max-old-space-size=256 --wasm-max-mem-pages=4096 --disallow-code-generation-from-strings --test tests/test_solid_mesh_engine.mjs` passed **15 tests** on Node 24.19.0. The executable was the existing runtime at `/Users/IDLE_And_R/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`; no installation occurred. Verified:

- Analytical overlapping 20 mm cubes: union volume 12000 mm³ / area 3200 mm²; difference and intersection 4000 mm³ / 1600 mm², with expected bounds. An independent test consumes exported OBJ and computes signed volume, area and oriented edge closure.
- Canonical project JSON serialization/reload; exported OBJ reimport; explicit property-vertex merge identity preservation; rotations and polygon-cylinder metrics; successful empty intersection/subtraction.
- Regression: decimal primitives must first be accepted at the Float32 precision written into the project. Without that step, the first reload changed their reported metrics. The adapter now canonicalizes primitive meshes before calculation; exact metric and result-mesh equality across reload is tested for decimal boxes and rotated cylinders.
- Unsafe/malformed OBJ, open/nonmanifold/degenerate/reversed meshes, nonfinite/out-of-bounds values, unknown fields, size and primitive bounds; 30 mixed repeated operations without poisoning later calculations.
- Real CLI JSON framing, invalid UTF-8, invalid JSON, excessive input, clean stderr and execution with dynamic JS compilation disabled under the runtime memory limits.

These are automated checks, not Cai Zhenze's manual testing. Native SDK loading, loopback/UI flows and Chinese package verification are recorded in `TEST_REPORT.md` and the task's machine-readable evidence. User completion confirmation and original current-package screenshots remain required before any delivery push or PR. Source/notice changes that alter a packaged payload require a rebuilt and retested package.

## Final archive review, 2026-10-31

The maintained packer produced `releases/agent-plugin/solid-mesh-workbench/1.0.0/solid-mesh-workbench-1.0.0.zip`, SHA-256 `5c3c4315bab1107752220c13e4061d931dfd23a3a3e970519130f51b16904de6`. The derived native companion is `plugins/solid-mesh-workbench/test-packages/solid-mesh-workbench-1.0.0-workswarm.zip`, SHA-256 `6d5bd3e547633f0ba05f1298c8da69fdc180538871d4d937ae891e7a1fe469cb`.

Actual archive extraction verified all 45 payload files identical to maintained source and between both ZIPs; unchanged JS/WASM sizes and hashes; every provenance license reference matching the 25 bundled license/attribution files; original notices; strict UTF-8 for every non-WASM file; Chinese manifest/README/Skill/UI content; declared paths; and absence of caches, symlinks or extra development files. The wrapper contains only `plugin.yaml` and the native inner directory. Extracted code executed all three analytical Boolean fixtures, accepted the Chinese-named closed OBJ, rejected the Chinese-named hole fixture with a Chinese error, and roundtripped the project and exported OBJ. See `package-verification.json` for the exact file inventory and measurements. No required distribution condition remains unresolved for this payload.
