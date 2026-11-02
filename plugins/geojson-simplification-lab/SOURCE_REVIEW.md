# Source and distribution review

Review date: 2026-10-30. Contributor: Cai Zhenze. Candidate: `CAND-EXT-004`.
Original development task: `AH-20261030-geojson-simplification-lab`.
Stable internal asset ID: `repo:agent-plugin:geojson-simplification-lab`.

Naming: **Mapshaper → 离线地图简化工作台 → `geojson-simplification-lab`**.
Package version: `1.0.1`. Mode: **ported**. Reuse permission: **verified for the materials listed below**, subject to retaining the supplied texts and corresponding source. This is a source/distribution assessment, not a legal warranty, host-test result, user-test confirmation or final-package approval.

## Scope and ownership

The selected operation accepts bounded, local GeoJSON Polygon/MultiPolygon features, simplifies shared-boundary geometry, compares the result with the original, displays attributes as inert text, and exports GeoJSON/SVG. The separately implemented Chinese adapter owns validation, worker limits, user interaction, host tools and safe exports. No host/core/SDK or another plugin is modified. The upstream general-purpose command console, remote imports, reprojection, shapefiles, raster processing, full GUI, basemap integrations, original fonts/icons and sample data are not product features or copied assets.

The complete unchanged browser core contains other algorithms even though the adapter does not expose them. Their licenses remain relevant. Excluding a feature in the interface does not remove its embedded-code obligations.

Repository-local reuse is separate from Mapshaper reuse: `tools/runtime.py` derives its isolated loopback-service and identity-checked lifecycle mechanism from the maintained `plugins/molecule-structure-lab/molecule-structure-lab/tools/runtime.py` at asset version `1.0.1`, with this plugin's identity, stricter runtime-record checks and scoped worker response policy. The outer `verify_workswarm.py` and `build_test_package.py` adapt the maintained `plugins/offline-optics-lab/` verification and packaging helpers at asset version `1.0.0`. These are repository-owned integration mechanisms, not additional upstream Mapshaper files. They remain task-specific copies with their own verification; no source file or running instance of either existing plugin is changed. The native-package helper additionally checks the canonical artifact and current payload, verifies byte equality, and refuses differing existing outputs.

This is a distinct capability from Baidu Maps `5653980c74944e6e873b300f3749656b@1.0.0`, Amap `776d6b354659407ba7ec54091e70a126@1.0.0` and `e7c9971f0cdf47a7a0cf1f840765acf2@1.0.0` (hosted place/route/geocoding services), Scientific Visualization `1adb66983cdf4c858df2b76c4d885083@356ea33` (figure generation), Archify `21cbd7759f7440e1a5c043161368be30@1.0.0` (structural graph schemas) and Playground 1.0.2 (configurable previews). The distinction is transforming local polygon coordinates with a real geometry engine, not simply showing a map or generating HTML.

## Fixed upstream and exact reused bytes

- Repository: <https://github.com/mbloch/mapshaper>.
- Source commit: `b44c0fa95effac3d91526c8b62dc0de0ab88b464`; published npm version `0.7.101`.
- Official npm archive: <https://registry.npmjs.org/mapshaper/-/mapshaper-0.7.101.tgz>.
- npm archive SHA-256: `65af2bcc4fd563845bed9228abfaccecd7cc14c494c6d1e62fc0359bbc936f2c`.
- Pinned source research archive SHA-256: `200336d2fc15fc09984187a363ef29c7ec9b58d736f9372651c95e721f5b1932`.

| Inner payload path | Origin | SHA-256 | Change |
| --- | --- | --- | --- |
| `web/vendor/mapshaper.js` | npm `www/mapshaper.js`, 3,592,274 bytes | `20bd08942346edd6a2518f23ad40829ab80829cdb116a8b8d8cddb102d5cddc9` | None; exact published bytes |
| `web/vendor/modules.js` | npm `www/modules.js`, 1,098,484 bytes | `535f573e5d49ff743690d5955a9b6299864b8e591e12195f809017222833b544` | None; exact published bytes |
| `licenses/mapshaper/sources/mapshaper-0.7.101-source.zip` | Curated preferred source from the pinned commit | `f14d8fde00e66460c5b122c396e1b52be11aa2582463de7eceac040d7a06b512` | Container selection only; original source bytes unchanged; two clearly identified build-support files added |

The runtime files are obtained directly from the official archive, not independently rebuilt. `web/vendor/UPSTREAM.json` records exact package URLs, registry integrity values, dependency archive hashes, additional notice sources and every bundled evidence-file hash. `provenance.json` records 48 source entries with 55 hashed license-evidence references. It does not represent absent optional runtime packages as installed dependencies.

## Permission and distribution conditions

### Mapshaper and corresponding source

The pinned root `LICENSE` states Copyright (c) 2026, Matthew Bloch, and MPL-2.0. The original notice is retained in `licenses/mapshaper/UPSTREAM-LICENSE`; full MPL-2.0 is retained in `licenses/mapshaper/LICENSE`. Under MPL sections 3.1–3.4, covered source and any covered modifications remain available under MPL, the recipient is told how to obtain corresponding source, and existing notices are preserved. No new restriction is imposed on those rights. The independent adapter is not presented as an upstream work or a blanket relicensing of repository-owned code.

`licenses/mapshaper/SOURCE_AVAILABILITY.md` tells recipients how to obtain the included source without an account or request. The curated ZIP includes the original non-GUI `src` files, core/modules entry points, package metadata/lockfile, upstream Rollup configuration, original license and full MPL. It excludes GUI-only source, separate optional GeoPackage/GeoParquet/GeoTIFF entry points, tests, fixtures, fonts, images and documentation. The two new build-support files are `BUILD.zh-CN.md` and `build-runtime.config.mjs`; they do not modify upstream modules. The archive contains 455 byte-identical original source/build-metadata files, full MPL and those two additions. `SOURCE_FILES.json` distinguishes additions and hashes all 458 entries. Build dependency installation is a developer operation; the browser runtime needs no npm install or network access. No bit-for-bit reproducible build claim is made.

### Third-party npm material

Actual published license files were inspected for the retained bundle/source dependencies, rather than relying on SPDX fields alone. Their full original texts are supplied under `licenses/<upstream>/LICENSE`. The itemized source/version/coverage table is `THIRD_PARTY_NOTICES.md`; machine-readable copies and hashes are in `provenance.json` and `web/vendor/UPSTREAM.json`.

The relevant families are D3 color/interpolation/chromatic schemes (ISC plus ColorBrewer Apache-2.0), Delaunator/robust-predicates (ISC/Unlicense), Flatbush/Flatqueue/TinyQueue (ISC), fflate/msgpackr/big.js (MIT), FlatGeobuf/FlatBuffers/Repeater/slice-source (BSD/Apache/MIT), Buffer/base64/ieee754 (MIT/BSD), iconv-lite/safer-buffer (MIT), idb-keyval/Safari compatibility (Apache), KML converters (MIT/BSD), mproj/PROJ/GeographicLib (MIT plus embedded original grants), kdbush (ISC), rw (BSD) and the browser polyfill build source (MIT with separate embedded notices).

Two npm omissions were resolved with actual upstream evidence before copying:

1. `@placemarkio/tokml@0.3.3` does not ship a license file. Its npm gitHead is `53a4791c4114651bc4212fd0631b60ae6bbbb519`. The complete `lib/` tree (`a9aa38705fe3e6cd22572f428a98e8d9d91eda25`) is byte-identical at the later author commit `4cd5c52ae4e482693812565311b790a5fd54e0fa`, which adds the complete MIT text, Copyright (c) 2022 Placemark. That original text is bundled. Evidence: <https://github.com/placemark/tokml/blob/4cd5c52ae4e482693812565311b790a5fd54e0fa/LICENSE>.
2. `@repeaterjs/repeater@3.0.6` omits its license in npm. The repository redirects to `bikeshaving/repeater`; publish commit `638a53f2729f5197875ec12a9d578c274c5f6709` confirms version 3.0.6 and contains the complete MIT text, Copyright 2019 Brian Kim. Evidence: <https://github.com/bikeshaving/repeater/blob/638a53f2729f5197875ec12a9d578c274c5f6709/LICENSE>.

FlatGeobuf's package metadata says BSD-3-Clause, but its actual license has two conditions. The original text is retained intact and classified BSD-2-Clause in the reviewed source record. No conflicting extra restriction was found. D3 chromatic's ColorBrewer section is preserved alongside ISC, not collapsed into a single label. The d3-scale-chromatic and idb-keyval directories retain their exact original notice files as `UPSTREAM-LICENSE` and supply complete Apache text in `LICENSE`; D3's full ISC text remains included there too. Full Apache-2.0 is additionally supplied at `licenses/apache-2.0/LICENSE`.

### Embedded adaptations outside the npm dependency list

The whole bundles also contain the following original implementation notices, all retained separately:

- D3-geo-polygon polyhedral/Lee/Cahill–Keyes/butterfly adaptations: ISC plus Philippe Rivière's Gray–Fuller public-domain declaration. D3-geo rotation: ISC plus the original GeographicLib MIT section. D3-dsv parsing: ISC. Original credits, including Mary Jo Graça and Enrico Spinielli, remain in unchanged source/runtime.
- Imago transformations credited to Justin Kunimune: complete root MIT (2023) and full source-file MIT headers (2017) from fixed review source `028222e91a533ef14f4ba96431117d4c28914a7f`; `licenses/imago/SOURCE_NOTICES.txt` preserves both original file headers.
- Mapbox Polylabel 2.1.0 adaptation and geokdbush: complete embedded ISC notices. Fabio Crameri Scientific colour maps 8.0.1: complete embedded MIT plus the upstream sampling/modification explanation.
- Equal Earth: Bernie Jenny's 2018 Apache-2.0 header and Matthew Bloch's August 2018 JavaScript port notice; this is distinct from Natural Earth. Full Apache text and original header are separate bundled files. Existing upstream change notices remain intact; this plugin changes no Apache-covered runtime file.
- Browser process: Roman Shtylman MIT. Browser hrtime: kumavis BSD-2-Clause. Node string decoder: full Joyent/Node-contributor MIT. Microsoft generated helpers: the original permissive, 0BSD-style text is preserved without inaccurately relabeling it standard MIT.
- Mustache HTML escaping, Underscore object test and historical php.js `addslashes`: complete original MIT texts and applicable contributor credits.
- Wirth quickselect: the original author's source at <http://ndevilla.free.fr/median/median/src/wirth.c> was retrieved successfully and explicitly states public domain. The full original file and declaration are bundled under `licenses/devillard/`. The original endpoint uses HTTP and rejects HTTPS; its fixed hash is an observed-content identity, not a claim of authenticated transport or an author signature.

The additional fixed commits identify inspected license evidence, not invented historical copy commits. Mathematical-paper citations alone are not treated as copied code or newly invented license obligations. Full notice details and primary URLs are kept in the itemized inventories.

No standalone upstream `NOTICE` file was found in the actual inspected package contents. Original notice blocks are preserved; no purported upstream NOTICE was fabricated. No original logos, fonts, basemap data, example geographic data or API-service credentials are distributed. Any synthetic test/example data is owned by the separate implementation work.

## Integration and correctness constraints

The pinned browser entry exposes `window.mapshaper`; `src/mapshaper-api.mjs` exposes `applyCommands`. `src/cli/mapshaper-run-commands.mjs` returns output content through its callback/Promise rather than file I/O. `modules.js` must load first because the core resolves browser dependencies through `window.modules` and initializes Buffer. The existence of that path is established by static source review; successful runtime/host behavior is established only by recorded functional tests.

The wrapper must not expose arbitrary user command strings or expressions. It must bound input/work, isolate synchronous computation in a cancellable worker, keep original input immutable, and handle failures without presenting stale output as current. `keep_shapes` does not promise to preserve every island or hole; upstream repair cannot fix intersections already in the original input. Source review found that arbitrary feature properties can affect upstream SVG styling, and that default `FID` handling can collide with attributes. Safe geometry-only SVG export and independent property/id preservation therefore belong to the adapter's tested contract. These are not unsupported promises that the upstream engine fixes every invalid geometry.

## Verification performed and remaining gates

The focused local hash audit on 2026-10-30 verified:

- Both shipped browser files exactly match the official npm bytes and the hashes above.
- All 55 provenance evidence references, all 59 bundled license/source-evidence files, and the three reused runtime/source-archive records match their declared SHA-256 values.
- The curated source archive passes ZIP CRC checks; all 458 entries match their manifest; all 455 retained original entries match the pinned source checkout byte-for-byte. Paths remain relative, with no symlinks/traversal, GUI directories, test fixtures or media included.
- Complete license texts and preserved adaptation notices were read manually. A format/hash tool does not replace the scope assessment.
- `check_provenance()` from the maintained `tools/asset_release.py` passed for all 48 sources and three reused paths. `audit-upstream` was also run on the fixed source tree: its automatic output deliberately remains `unknown` and reports root/test-data license candidates. The test fixtures, including separately licensed shapefile test material, are excluded from this payload; that scanner output does not override the item-by-item manual review.

The pre-package checks above do not establish successful functional/WorkSwarm tests or user testing. The actual final package extraction and distribution checks are recorded below; user confirmation and original screenshots remain separate gates.

### Internal 1.0.0 packaged distribution check — 2026-10-30

The exact version `1.0.0` archives were independently read, extracted to disposable audit storage, and verified without executing upstream code or changing either archive:

| Archive | Size | SHA-256 |
| --- | ---: | --- |
| `releases/agent-plugin/geojson-simplification-lab/1.0.0/geojson-simplification-lab-1.0.0.zip` | 6,288,463 bytes | `c5b9921149aac1db61d2ff8edf96f2295f2817a870b3337fe48aa4b83c7efffc` |
| `dist/geojson-simplification-lab/1.0.0/geojson-simplification-lab-1.0.0-workswarm.zip` | 6,279,880 bytes | `eb895ff49b87ad8fe7f7542bd31a665a953c4cce463f2fd5635a45bd9462ff9a` |

- The marketplace ZIP has 76 entries: one wrapper and 75 inner payload files. All 75 native entries equal the corresponding canonical inner file bytes and current payload files. The retained native ZIP under `plugins/geojson-simplification-lab/test-packages/` also equals the distribution copy byte-for-byte. `artifact.json` and `companion-artifact.json` payload and ZIP hashes match those actual bytes.
- Both archives pass CRC, safe-path, duplicate/case-collision and symlink checks. All 59 bundled license/source-evidence files match the complete `web/vendor/UPSTREAM.json` inventory, with no missing or extra `licenses/` files. All 55 unique provenance evidence references across 48 sources, and all three reused-file hashes/sizes, match the extracted bytes. The maintained `check_provenance()` passes against that extracted payload.
- Every source name and license-evidence path is represented in the packaged `THIRD_PARTY_NOTICES.md`. The complete MPL, applicable original copyright/permission/disclaimer texts, supplemental source notices, and offline source-availability instructions are retained. The previously reviewed browser file hashes remain unchanged, so the original headers and embedded upstream change notices remain intact. No missing distribution notice was identified in this exact payload.
- The nested source ZIP matches `f14d8fde00e66460c5b122c396e1b52be11aa2582463de7eceac040d7a06b512`; its CRC, all 458 entry hashes/sizes and exact manifest entry set pass. Independent inspection found no unsafe/duplicate/case-colliding paths, symlinks or special files. All 455 retained upstream files match the pinned Mapshaper source checkout byte-for-byte. The two separately authored build-support files are present; excluded GUI, tests, fixtures, documentation and media assets are absent. `src/fonts/` contains three implementation modules, not distributed font media.
- The audit identified one inaccurate classification: the remaining entry, `MPL-2.0.txt`, was marked `plugin_added: false`, but is a supplemental complete license text, **not** a file from the pinned Mapshaper checkout. It exactly equals bundled `licenses/mapshaper/LICENSE` (SHA-256 `fab3dd6bdab226f1c08630b1dd917e11fcb4ec5e1e020e2c16f83a0a13863e85`). The verified source accounting is 455 upstream files + one supplemental original license text + two authored build helpers; the license text and permission coverage themselves are correct.
- The extracted Chinese README, Skill instructions, third-party notices and source-availability guide decode as UTF-8 without replacement characters. This content inspection is not a substitute for the separately recorded actual browser/host tests or the user's current-package confirmation and original screenshots.

The source/hash coverage and archive byte-identity checks above passed, but the provenance classification finding required correction before manual handoff. The corrected payload marks the supplemental license `plugin_added: true`, records its Mozilla source URL and `supplemental_original_license` role, explicitly states `authored_by_plugin: false`, and corrects the three-addition accounting in `THIRD_PARTY_NOTICES.md`. The source-archive and vendored engine bytes remain unchanged. Its inventory hash is refreshed in `web/vendor/UPSTREAM.json`. The internal 1.0.0 ZIPs above are preserved; the first user handoff was bumped to 1.0.1 and audited below.

### Final 1.0.1 packaged distribution check — 2026-10-30

The following exact final archives were independently read and the payload extracted to disposable audit storage. This audit changed only outer documentation; no packaged file, ZIP, runtime record or host setting was modified.

| Archive | Size | SHA-256 |
| --- | ---: | --- |
| `releases/agent-plugin/geojson-simplification-lab/1.0.1/geojson-simplification-lab-1.0.1.zip` | 6,288,928 bytes | `5bc7e39e5db5fd92cfc07ad9638fd225f6a4c7cb5b0eaf26c3eaff1d1fa79141` |
| `dist/geojson-simplification-lab/1.0.1/geojson-simplification-lab-1.0.1-workswarm.zip` | 6,280,345 bytes | `32b0bb79a8881d184ea5ad5f01a19357c3c6dfb313fe63dc769795d6f9753e1a` |

- Canonical/native CRC, safe-path, duplicate/case-collision and regular-file checks pass. The canonical ZIP contains 76 entries; all 75 inner payload files match the native ZIP, retained native copy and current payload byte-for-byte. Manifest/wrapper version is 1.0.1; artifact and companion ZIP/payload hashes agree with the actual files.
- All 59 license/source files exactly match the recorded inventory. All 55 evidence references across 48 sources and all three reused-file hashes/sizes pass; `check_provenance()` passes against the extracted payload. Every source and license-evidence path remains covered by the notices. Previously reviewed license texts, vendored code and original headers are unchanged.
- The corrected `SOURCE_FILES.json` hash is `9af95e6b824cc7d11ae1a534753827fa01deae45f72f36153dbcd5b6af509f8e` (103,115 bytes). All 458 nested source entries match their hashes/sizes and exact manifest set. The three additions are correctly distinguished: two authored build helpers and Mozilla's original supplemental MPL text, with its precise source URL and `authored_by_plugin: false`. The notice now describes those three additions. The 1.0.0 classification finding is resolved.
- The nested source archive remains byte-identical at SHA-256 `f14d8fde00e66460c5b122c396e1b52be11aa2582463de7eceac040d7a06b512`. Its CRC and paths pass; the prior independent verification of 455 original source files and excluded GUI/test/media material remains applicable. The supplemental MPL text still exactly matches the complete bundled license.
- Extracted README, Skill instructions, notices and source-availability instructions decode as valid UTF-8 without replacement characters. The manual guide links to the exact 1.0.1 packages and requires user import through Extensions at WorkSwarm port 6394, normal Settings configuration of the currently disabled chat model, and the user's own real tool/chat test.
- `dist/geojson-simplification-lab/1.0.1/manual-workspace-user-20261030` was verified to be an existing, non-symlink, empty directory. No SDK invocation, runtime creation or service start was performed there by this audit.

No unresolved source/license distribution or package-identity blocker was found for these 1.0.1 hashes. Actual functional/host test results remain in their separate evidence records. This is not user test-completion confirmation, screenshot evidence, Project Lead acceptance or Hub submission; those boundaries remain unchanged. No reproducible upstream build or publisher-signature claim is made.

Local research records, not packaged deliverables: `/private/tmp/geojson-license-audit-20261030/packages.json`, `extra.json`, the original downloaded dependency archives/notices under `packages/`, and the pinned samples under `/private/tmp/main2-phase1-20261030/`. Temporary fetch/assembly helpers are not included in the plugin or committed.
