# Source review — 离线分子结构工作台

- Reviewed: 2026-10-28, Asia/Singapore; rules blob `e6e315918b1d948ba37bd2a3312c55c05a254d97`.
- Candidate: `CAND-EXT-002`; task: `AH-20261028-molecule-structure-lab`; owner: Cai Zhenze.
- Mapping: RDKit.js / `@rdkit/rdkit` → **离线分子结构工作台** → `molecule-structure-lab`.
- Internal asset: `repo:agent-plugin:molecule-structure-lab`; package version: `1.0.1`.
- Mode: `ported`. Permission is verified for the scoped reuse described here, subject to retaining the bundled notices and Eigen source materials. This is not a unified relicensing of the plugin or repository.

## Exact material reused

The runtime is the official npm `@rdkit/rdkit@2026.9.1` distribution, generated from RDKit tag `Release_2026_09_1`, commit `fece8caa860bdf6c9c82bdb9253f22a0cf87150c`. The two runtime files are copied byte-for-byte; no upstream implementation, font or embedded data is edited.

| Original npm path | Payload path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `package/dist/RDKit_minimal.js` | `vendor/rdkit/RDKit_minimal.js` | 106667 | `ea427db9cc39be245065603de0df10c3053cb49af3b63fdf6bc2bf73d6fc17da` |
| `package/dist/RDKit_minimal.wasm` | `vendor/rdkit/RDKit_minimal.wasm` | 7379879 | `594ceaed387adc70ea13bfbb2e8eace916f6c782254ed5a6f0f0a0a7a4fe4061` |

Archive: <https://registry.npmjs.org/@rdkit/rdkit/-/rdkit-2026.9.1.tgz>, 2449562 bytes, SHA-256 `ae6b0e42b85114a2f38ef890fcb229a90b54b0b42d4636c50ae1c7f77d85ffe0`. Its computed SHA-512 matches registry integrity `sha512-nbdi5yEw+mG2kIxFvgVMGulS5fjNMzzocx9nKs01NAjNpFAEQVb6RDl3pd9AWEa7m5D8DR4QAS6CDzu+5xjzEA==`. The npm archive has five files and no complete LICENSE/NOTICE; the BSD label alone is insufficient. The required materials are supplied separately below.

The published npm provenance identifies the same source commit and [official publishing run](https://github.com/rdkit/rdkit/actions/runs/37104484827). Its [build job](https://github.com/rdkit/rdkit/actions/runs/37104484827/job/111150237761) was read to resolve actual dependency versions. This review checked content hashes and inspected the published provenance; it does not claim independent Sigstore or PGP signature verification or a reproducible rebuild.

## Code, fonts and dependency coverage

The primary runtime is BSD-3-Clause, but the compiled binary is a mixed-license work. The following original texts, copyright statements and conditions are preserved under the inner payload's `licenses/`. `THIRD_PARTY_NOTICES.md` is a new Chinese inventory, not an invented upstream NOTICE. `SOURCE_NOTICES.txt` files preserve original source comments verbatim with their paths and a Chinese collection preface. Their deliberately conservative module coverage is not a claim that every compiled function survived static linking.

| Component and fixed source | Actual coverage and license decision | Bundled evidence |
| --- | --- | --- |
| [RDKit](https://github.com/rdkit/rdkit/tree/fece8caa860bdf6c9c82bdb9253f22a0cf87150c) | BSD-3-Clause root plus original module/file copyrights, including Greg Landrum, Rational Discovery, Julie Penzotti, Novartis, Schrödinger, David Cosgrove, Gareth Jones/Glysade and other named contributors. ChemReactions has an additional full BSD notice. | `licenses/rdkit/` |
| [Linchemin](https://github.com/syngenta/linchemin/blob/f44fda38e856eaa876483c94284ee6788d2c27f4/LICENSE) | RDKit's compiled Descriptors/OxidationNumbers source explicitly derives from this code; preserve its MIT ©2022 Syngenta Group Co. Ltd. in addition to RDKit BSD. No independent Linchemin application is bundled. | `licenses/linchemin/LICENSE` |
| [FreeType 2.13.3](https://github.com/freetype/freetype/tree/VER-2-13-3) | Select **FTL**, not the alternate GPL. Preserve FreeType credit, full FTL, original dual-license explanation and the separate BDF/PCF/hash/Adobe and other source notices. Official build disables external HarfBuzz, BZip2, PNG, Brotli and FreeType external-zlib options. The font engine's own permissive components remain covered. | `licenses/freetype/` |
| [InChI 1.07.3](https://github.com/IUPAC-InChI/InChI/releases/tag/v1.07.3) | Actual source archive headers: MIT ©2024 IUPAC and InChI Trust. Preserve those plus the root InChI Project MIT text. `sha2.c/h` credits Paul Bakker and Christophe Devine and permits MIT use only in combination with InChI; it remains inside the unmodified combined RDKit/InChI binary, never a standalone hash utility. | `licenses/inchi/` |
| [CoordGen 3.0.2](https://github.com/schrodinger/coordgenlibs/tree/v3.0.2) | BSD-3-Clause ©2017 Schrödinger, Inc.; additional original source copyrights retained. | `licenses/coordgen/` |
| [Maeparser 1.3.3](https://github.com/schrodinger/maeparser/tree/v1.3.3) | MIT ©2017 Schrödinger, LLC. It is built through the CoordGen dependency even with direct MAE parsing disabled. Conservatively preserve its license. | `licenses/maeparser/LICENSE` |
| [RingDecomposerLib 1.1.3_rdkit](https://github.com/rareylab/RingDecomposerLib/tree/v1.1.3_rdkit) | BSD-3-Clause ©2016 University of Hamburg/ZBH, Niek Andresen, Florian Flachsenberg, Matthias Rarey. RDKit's build applies documented qsort/header compatibility changes; plugin does not modify that result. | `licenses/ringdecomposer/` |
| [Boost 1.87.0](https://github.com/boostorg/boost/tree/boost-1.87.0) | BSL-1.0, including its machine-executable-object exception. Full license retained anyway. No Boost installer or native application is bundled. | `licenses/boost/LICENSE` |
| [zlib 1.3.2](https://github.com/madler/zlib/tree/v1.3.2) | zlib license ©1995–2026 Jean-loup Gailly and Mark Adler; original notice retained. | `licenses/zlib/LICENSE` |
| [Eigen Debian 3.4.0-4](https://deb.debian.org/debian/pool/main/e/eigen3/) | Select MPL-2.0 for MPL/dual-licensed covered files; preserve separate BSD terms. Actual Debian patches alter headers, so provide the exact original source archive, Debian changes archive and source descriptor. Unused tests/modules inside those unchanged source archives retain their original licenses; they are not asserted to be linked into WASM. | `licenses/eigen/`, including `sources/` and `SOURCE_AVAILABILITY.md` |
| Telex Regular 1.100, embedded in WASM | OFL-1.1 ©2011 The Telex Project Authors; reserved name Telex. No font bytes or font names modified; not sold separately. Retain full copyright/OFL. | `licenses/telex/LICENSE` |
| Roboto Regular 2.137 (2017), embedded in WASM | Apache-2.0; font name-table copyright ©2011 Google Inc.; Christian Robertson credited. Exact binary name-table identity and RDKit's font-license pointer inspected. Preserve full Apache text and original attribution. No separate upstream font NOTICE supplied in this source. | `licenses/roboto/` |
| Bison 3.8.2 generated SMILES/SMARTS parsers | GPL-3.0-or-later **with Bison-exception-2.2** permits this larger chemistry runtime under other terms. No parser-generator product is created and the exception is not removed. Keep full GPL and exact generated exception/header. | `licenses/bison/` |
| Flex 2.6.4 generated scanners | Original COPYING explicitly exempts generated scanners from its copyright conditions; retain the original explanation and BSD notice as evidence. | `licenses/flex/LICENSE` |
| [Emscripten 6.0.11](https://github.com/emscripten-core/emscripten/tree/a0014542110d6078c3a1a7941fa1ddb3a2281f16) | Actual build log resolves SDK release `f6264d4a4dd9ba24a9f0a5702835a44d1463de13`; source tag commit `a0014542110d6078c3a1a7941fa1ddb3a2281f16`. Select MIT from MIT/NCSA for Emscripten-owned code; preserve Node-derived notice and AUTHORS. Runtime components retain their distinct terms. | `licenses/emscripten/` |
| Emscripten's musl, LLVM compiler-rt, libc++, libc++abi and libunwind; dlmalloc | Full musl COPYRIGHT and per-source permissive notices; full LLVM Apache-2.0-with-LLVM-exception texts, including their historical license material; dlmalloc public-domain/CC0 dedication and full CC0 fallback. No claim that all Emscripten code is covered by one MIT text. | `licenses/musl/`, `licenses/llvm-*/`, `licenses/dlmalloc/`; collected runtime notices in `licenses/emscripten/SOURCE_NOTICES.txt` |

The actual InChI release archive MD5 `b761f37a7d3a3ff8574daf6906993759`, CoordGen `bc9dabbbb2b99ae426f3a1bf16c4d3cc`, Maeparser `c43dfb89c495512f695ce018b32ac749`, and RingDecomposer `e9a0bcdda8b921a35e812b9888a9a874` match RDKit's pinned download checks. SHA-256 values for all inspected archives are preserved in `vendor/rdkit/UPSTREAM.json`. MD5 is used here to match the upstream recipe, not as a modern security guarantee.

## Source availability and modifications

The exact Eigen source files delivered with the package are:

| File under `licenses/eigen/sources/` | SHA-256 |
| --- | --- |
| `eigen3_3.4.0.orig.tar.bz2` | `b4c198460eba6f28d34894e3a5710998818515104d6e74e5cc331ce31e46e626` |
| `eigen3_3.4.0-4.debian.tar.xz` | `10746fe711162ac7882a838b0af1e9826b5a0ea5b8d9963220ec78f71586250c` |
| `eigen3_3.4.0-4.dsc` | `fc8497759df4b6d3803b90fb03853d69feee68a76c992355c187ca59ae60afe1` |

The two archive hashes also match the `.dsc` SHA-256 entries. These original archives provide the source and changes locally, without relying on a future download or installing anything. Their existing licenses and source headers remain intact. MPL rights are not restricted by this plugin. The detailed Chinese source-availability note explains extraction and version identity.

Our additions are the plugin adapter, bounded execution and input policy, Chinese interface/instructions and outputs, tests, this review, inventory and packaging metadata. Those are separate from the unmodified upstream loader/WASM and source archives. New Chinese explanations surround, but do not translate away or replace, original license texts. No upstream icon, logo, screenshot, external chemical dataset, paid service, model endpoint or fetched molecule database is used. Embedded fonts, chemical constants and descriptor implementation remain inside the reviewed upstream binary. Do not imply RDKit, Google, FreeType or other rightsholder endorsement.

## Validation and remaining gates

Permission and source identity were reviewed before copying the runtime into the authorized plugin paths. A read-only Phase 1 engine probe used the exact package with local `wasmBinary` on Node `v24.19.0`; engine version `2026.09.1` parsed aspirin, ethanol and benzene, returned descriptors and SMARTS matches, rejected malformed `C1CC`, and generated a highlighted SVG. Fetch was disabled and invoked zero times. This establishes limited offline engine behavior only, not plugin integration or user testing.

### Frozen-package license audit — 2026-10-28 22:28 Asia/Singapore

Both frozen ZIPs were independently inspected and extracted into separate new temporary directories. The audit passed: each extracted payload has exactly the same 60 files and bytes as the reviewed source, including all 44 license/source files. All 47 license-evidence entries (41 unique files), all five reused-file hashes and all 21 source records are covered. The runtime matches the official npm archive byte-for-byte; the bundled Eigen archives match the source descriptor. Original full license texts and collected source notices were checked, and every component directory is represented in the Chinese third-party inventory. No distribution-condition blocker remains for these exact bytes.

| Distribution | Repository path | Bytes / entries | SHA-256 |
| --- | --- | --- | --- |
| Agentic Hub wrapper | `releases/agent-plugin/molecule-structure-lab/1.0.0/molecule-structure-lab-1.0.0.zip` | 11207708 / 61 | `07904c3c058641ca68c23fda0e400623e4d36092a7fa2cdce58d4473186e86f4` |
| Native WorkSwarm test package | `plugins/molecule-structure-lab/test-packages/molecule-structure-lab-1.0.0-workswarm.zip` | 11201681 / 60 | `55e943a1fe105ff0ce3dc210cb83ed85fd1e30b4300af0a5018271df59da637b` |

`license-verification.json` records the actual audit and a reusable procedure: validate source provenance; check frozen ZIP identity, safety and inventory; extract and compare all payload hashes; compare runtime with the pinned npm archive and Eigen sources with their descriptor; then review notices, license choices, attributions, source availability and modifications. This is a source/license distribution audit, not an independent reproducible build, legal warranty, functional test or user test confirmation. Functional and host results belong in `TEST_REPORT.md`; explicit testing confirmation and original user screenshots remain separate Phase 2 gates.

Any change to the upstream bytes, dependency version or distributed license/source materials requires a new audit and rebuilt test package. Any packaged change requires the applicable testing and confirmation again. Do not submit while any required condition is unresolved.

### 1.0.1 navigation repair — 2026-10-30

Only repository-authored server routing, version labels and installation guidance change. The entry page accepts user-activated top-level GET navigation from the WorkSwarm chat origin; Host, capability path, Origin, asset/control-route and installation ownership checks remain enforced. No host, SDK, dependency or other plugin is modified. The pinned RDKit runtime and all bundled license/source files were compared byte-for-byte against 1.0.0 and are unchanged. All 60 source, native ZIP, canonical ZIP and installed payload files match; both archives were extracted and inspected. The prior license audit therefore remains applicable to the unchanged upstream materials. Evidence: `dist/molecule-structure-lab/1.0.1/package-verification.json`. Version 1.0.0 packages and failure evidence remain preserved. The 1.0.1 package requires renewed user testing.
