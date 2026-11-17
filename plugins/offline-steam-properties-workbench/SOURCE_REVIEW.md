# Source and distribution review

Reviewed 2026-11-16 for **Cai Zhenze**, task `AH-20261116-offline-steam-properties-workbench`. Candidate ID: **Not Applicable**: the selected source is an approved external implementation, not a fabricated tracker candidate. Naming: **CoolProp 8.0.0 → 离线水与蒸汽物性工作台 → offline-steam-properties-workbench**. Mode: `ported`, combining unmodified official numerical-engine wheels with this plugin's Chinese interface and maintained internal integration components.

## Scope and permission decision

The selected upstream is [CoolProp 8.0.0](https://github.com/CoolProp/CoolProp/tree/ae81610e7d23efc57f9d051c8e70a4d66e87537f), commit `ae81610e7d23efc57f9d051c8e70a4d66e87537f`. The official [PyPI release](https://pypi.org/project/CoolProp/8.0.0/) supplies the exact four wheels below. Root MIT alone was not treated as complete binary permission. Source headers, the pinned dependency/build recipes, each native module, package contents and applicable additional grants were reviewed before copying the wheels into the payload or running them.

**Reuse is permitted for the recorded scope with the bundled conditions.** Full notices and the MPL-covered corresponding Eigen headers accompany the engine. No upstream numerical code or wheel is modified. This conclusion applies to the recorded artifacts and supplied legal material; it is not a repository-wide license decision. Final ZIP consistency and actual host/numerical tests are separate gates.

| Original upstream filename | Bytes | SHA-256 |
| --- | ---: | --- |
| `coolprop-8.0.0-cp311-cp311-macosx_11_0_arm64.whl` | 10552223 | `ad8bca80518c9777e81dd861fc274e4a56115712b54af7413504249e8fe83078` |
| `coolprop-8.0.0-cp311-cp311-macosx_11_0_x86_64.whl` | 10683032 | `7b8e17dd611b6e1a0b91bec887c84056c4492dcb033fda4b3e93a6b77dc9e074` |
| `coolprop-8.0.0-cp312-abi3-macosx_11_0_arm64.whl` | 10571251 | `46de36f51330ce8c7f8384a7360e1058739d20604736158aac6bd2abf6ae26bd` |
| `coolprop-8.0.0-cp312-abi3-macosx_11_0_x86_64.whl` | 10672568 | `939803aa9d849961e76512d4c3d60b15c25802c75cbecc801892edb3b023f200` |

All downloaded bytes match official registry SHA-256 values. Each wheel passes ZIP CRC, duplicate/path/symlink checks and all 146 nonempty RECORD hashes. Each contains three native modules. All twelve Mach-O modules have the expected architecture and minimum macOS **11.0**; their only linked dynamic libraries are existing `/usr/lib/libc++.1.dylib` and `/usr/lib/libSystem.B.dylib`, which are not redistributed. All four numerical core modules contain the pinned Git revision. `source-audit.json` records individual module hashes and static evidence.

The `cp311-cp311` wheels require CPython 3.11. The other wheels explicitly declare `cp312-abi3` in their WHEEL metadata; upstream's pinned Python CMake and publish configuration use stable ABI for Python 3.12 and later. This is a supported artifact selection, not an assumption that a CPython 3.11 extension works on 3.13. Actual host testing remains recorded by the integration owner in `TEST_REPORT.md`. Intel and ARM compatibility are distinguished from the architecture actually exercised.

## Item-by-item legal coverage

Paths below are inside the native payload. `provenance.json` records source URLs, exact revisions and hashes of the actual bundled evidence.

| Material and original statement | Actual reuse and conditions |
| --- | --- |
| CoolProp core, Python package, equations/data; Copyright (c) 2012–2018 Ian H. Bell and other CoolProp developers | Four complete unmodified wheels under `vendor/coolprop/`. Full MIT in `licenses/coolprop/LICENSE`; original wheel copyright and headers remain intact. No new license is imposed on upstream data or code. |
| Devin Lane cubic-spline code in `include/CoolProp/numerics/numerics.h` | Its complete Beer-Ware notice, origin and upstream change attribution are retained in `licenses/coolprop/BEER-WARE.txt`, in addition to the original header inside the wheels. The optional beer sentence is not a required purchase. |
| NIST superancillary implementation | Its full US and foreign permission/warranty notice, including subsequent edits by Ian Bell, is retained in `licenses/coolprop/NIST.txt`. This is not treated as a blanket worldwide public-domain assumption. |
| Cubic-EOS implementation, Bell and Jäger | Original explicit public-domain statement and paper attribution retained in `licenses/coolprop/PUBLIC-DOMAIN-CUBIC.txt`. The plugin exposes only HEOS Water, but other compiled backend notices are still retained. |
| Eigen 5.0.1 | Primarily MPL-2.0, with specific BSD, Apache and MINPACK material. Full grants are in `licenses/eigen/`. The exact unchanged covered header source accompanies the binary as described below. |
| fmt 12.0.0; Victor Zverovich and contributors | Full MIT plus original optional object-code exception retained in `licenses/fmt/LICENSE`. Installed fmt headers inside the original wheels retain their original notices. We do not rely on the exception to omit attribution. |
| msgpack-c `919908742b4fdbc575e77fe1a8657e70c9573c44`; MessagePack for C++, FURUHASHI Sadayuki | Boost Software License 1.0 and original header attribution retained in `licenses/msgpack/`. |
| nlohmann/json 3.12.0; Niels Lohmann and additional header authors | MIT plus the embedded Google Abseil-derived Apache-2.0 portion are both respected. Full MIT and Apache texts and the complete original single-header attribution/source are in `licenses/nlohmann-json/`. That exact original header is 953436 UTF-8 bytes, SHA-256 `aaf127c04cb31c406e5b04a63f1ae89369fccde6d8fa7cdda1ed4f32dfc5de63`. The upstream root has no separate NOTICE; none is fabricated. GPL text elsewhere in upstream concerns other materials and is not used to relicense this header. |
| Valijson 1.0.6; Tristan Penman and Akamai Technologies | BSD two-clause grant retained in `licenses/valijson/LICENSE`. Its nlohmann adapter is the relevant JSON dependency; other adapters/providers are not separately redistributed. |
| IF97 `7aaced024a702f0985474bf293cdaae9c8d06521`; Ian H. Bell | Full MIT retained in `licenses/if97/LICENSE` for the compiled backend, although the plugin's fixed public backend is HEOS. |
| REFPROP-headers `b4faab1b73911c32c4b69c526c7e92f74edb67de` | These interface headers are MIT; full grant in `licenses/refprop-headers/LICENSE`. No proprietary REFPROP library, fluid files, installation or service is supplied or invoked. Interface-header permission is not described as permission to distribute REFPROP itself. |
| Boost headers `c68104660ca4bd80d0d5cb34c4eba0cf5bab3f73`; including TOMS748 by John Maddock and Matt Borland | Boost Software License 1.0 and exact relevant original copyright retained in `licenses/boost/`. |
| miniz 3.1.1 integrated source | MIT notice by RAD Game Tools, Valve, Rich Geldreich and Tenacious Software, and its embedded public-domain/Unlicense statement, retained in `licenses/miniz/`. No system zlib is bundled. |
| incbin | Full Unlicense retained in `licenses/incbin/LICENSE`. |
| nanobind 2.12.0; Wenzel Jakob and named contributors | BSD three-clause grant plus source-header copyright inventory retained in `licenses/nanobind/`. Source package SHA-256 `0ae77c1a88f27153fa57045ee00f7b0a7b06b1cd3df942e95a34b38c5d0a5bee` was inspected without execution. |
| nanobind's robin-map `4ec1bf19c6a96125ea22062f38c2cf5b958e448e`; Thibaut Goetghebuer-Planchon | Full MIT retained in `licenses/robin-map/LICENSE`. |
| Cython-generated State/constants sidecars | Native State modules identify Cython 3.2.6. The official 3.2.6 COPYING text explicitly states that embedded compilation snippets do not encumber the output; this evidence is retained in `licenses/cython/COPYING.txt`. Cython itself is not redistributed or installed. |

The pinned dependency list is `cmake/dependencies.cmake`; the Python build starts at `wrappers/Python/CMakeLists.txt`, selected by `pyproject.toml`. Build-tool and header dependency facts are not invented from a package's top-level SPDX field.

## MPL source availability

`licenses/eigen/eigen-5.0.1-corresponding-headers.tar.gz` supplies the preferred, machine-readable source form of all distributed Eigen core headers and the actually included unsupported Polynomials module. Its **420 original files** are unchanged from the official Eigen 5.0.1 archive, whose pinned SHA-256 is `e9c326dc8c05cd1e044c71f30f1b2e34a6161a3b6ecf445d56b53ff1669e3dec`. The selected source archive has SHA-256 `0a44ffcab8abdb2515f3b418d298da9a78ed7c309bdbfce3ed54e756d47dfca0`; its `SOURCE_MANIFEST.json` lists every original file hash.

All `Eigen/` headers, `unsupported/Eigen/Polynomials`, its four implementation headers, original README and complete root COPYING/LICENSE files are included. Source include inspection establishes that these cover the Eigen modules used by CoolProp's pinned source. Unrelated Eigen benchmarks, test programs, documentation/media and unsupported modules are omitted. Header-only source needs no object-code relink kit; we do not confuse MPL conditions with LGPL conditions or assert that the entire plugin must adopt MPL. The Chinese source guide tells recipients where the source is and preserves their MPL rights. No corresponding-source fee or future network download is required.

## Test-only and excluded material

The source audit found multicomplex references only in `include/CoolProp/fluids/Helmholtz.h` and `src/Helmholtz.cpp`: all **32 references** are under `ENABLE_CATCH` guards. The main CMake adds its include directory only to CatchTestRunner; the Python runtime include list omits it and the published Python wheel builder does not define ENABLE_CATCH. The numerical binaries expose no MultiComplex/one_mcx/diff_mcx symbols or string markers. This combined evidence establishes test-only scope for the inspected build; absence of a symbol alone was not treated as proof. No multicomplex implementation, Catch tests or unknown-license source is copied into this payload. An explicit `ENABLE_CATCH=OFF` line was not found and is not claimed.

The source-only research sdist `coolprop-8.0.0.tar.gz`, SHA-256 `fb77fff0acf1623a25eb84963020b4f9d0b36d9431a8d8ae4221271effc30457`, remains private research scratch and is not bundled wholesale. Upstream instructions, GUI, examples, JavaScript, media and unrelated toolchains are not copied. Native wheel metadata may contain source/citation URLs; the plugin does not fetch those URLs. No upstream logo, font, screenshot, paper/PDF or ChemSpider image is supplied.

The built-in fluid/correlation database is distributed as part of the upstream MIT package, not scraped from an external service. Its source JSON files contain no separate restrictive license marker in the inspected release. Water's EOS and transport citations remain in the engine/BibTeX database; this wrapper adds no copied paper text or independently licensed fluid dataset. The public interface fixes `HEOS::Water` and does not expose user fluid definitions or arbitrary configuration/backend loading.

## Runtime integration boundaries

Runtime requirements are existing CPython 3.11 or a compatible CPython 3.12+ interpreter, existing interpreter-compatible NumPy >=1.20, and the matching macOS architecture. NumPy is neither bundled nor installed; its package/assets/license are not claimed as distributed here. The reviewed original wheel is extracted only into this plugin's private temporary worker directory. No pip installation, shared dependency modification, host source/API changes, system monkey-patching or paid/network property service is part of this integration.

## Maintained internal reuse

The lifecycle, authenticated loopback server, deterministic native packager and SDK/WorkSwarm verification scaffolding are adapted from Cai Zhenze's existing `plugins/offline-allocation-workbench/` at commit `426f7230bc0a11a0d410cda5aa4866141f491649`. The user approved this new plugin build; routine adaptation of that member's maintained integration mechanisms is within the build scope. This is not a claim that the user explicitly named each helper in a separate reuse instruction. Ownership is confirmed in the task context and existing asset metadata, not inferred from the GitHub account.

The adapted responsibilities are `runtime/runtime.py`, `runtime/server.py`, `build_packages.py`, `verify_sdk.py` and `verify_workswarm.py`. The verification helpers have unchanged source hashes `893a805e49ef97bcee864d9fe5c6223a4cccc612fa7c6a25f2d02ea890a9bbe5` and `2f9fc0d16419fe493c24bf42c79780ed86151df1fca6e09da1be3e148efd5cbb` at that source snapshot. `provenance.json / repository_reuse` records full source/destination paths, original hashes and actual adapted hashes for all five files. No earlier plugin, tracker assignment, dependency or runtime is modified. This internal maintenance reuse makes no external or repository-wide licensing assertion, and does not imply that the whole wrapper was independently rewritten.

## Verification boundaries and package gate

Completed here: official-byte hashes, ZIP/RECORD/path checks, static architecture/minimum-OS/dynamic-library inspection, dependency/header/grant review and corresponding Eigen source hashes. No binary or downloaded source was executed during this source audit. Native model calculations, recovery, Chinese UI/Tool behavior and host discovery are verified separately in `TEST_REPORT.md`; Intel execution is not inferred from ARM results.

The four exact wheel archives and corresponding Eigen source archive were also inspected for nested `.js`, `.mjs`, `.cjs` and `.ts` files: **none are present**. This does not bypass the required normal raw-text preflight of the plugin's own JavaScript and both final ZIPs; that verification is recorded by the packaging owner. The read-only engineering review of `runtime/engine.py`, `runtime/worker.py` and `runtime/model.py` found no P1/P2 blocker after the raw-name-length and free-threaded-CPython checks. Its exact file hashes and scope are recorded in `source-audit.json`.

## Frozen package audit

Both final Chinese **1.0.0** archives were extracted and audited on 2026-11-16:

| Form | Repository path | ZIP SHA-256 |
| --- | --- | --- |
| Native WorkSwarm | `plugins/offline-steam-properties-workbench/test-packages/offline-steam-properties-workbench-1.0.0-workswarm.zip` | `41764bfdaa0799b9944adadafc922bbc857d3e0e926170f5a25692f12fac156e` |
| Canonical wrapped | `releases/agent-plugin/offline-steam-properties-workbench/1.0.0/offline-steam-properties-workbench-1.0.0.zip` | `39e40862077801745b45da9140b203e4ec36671d43f646d11255ded05866b2e7` |

The native archive is **44877944 bytes / 53 entries**; the wrapped archive is **44885893 bytes / 54 entries**. Both are stored ZIPs below 95 MiB. All **53 payload files** match each other, current reviewed source, both artifact payload manifests and the extracted contents. CRC, paths, duplicate entries, symlinks, hidden/cache files, native manifest and canonical wrapper layout checks pass. No review files, runtime state or unrelated evidence are packaged.

All **30 license/source evidence hashes** match both archives. All four original engine wheel hashes are unchanged, allowing reuse of the matching RECORD, ABI, architecture, native-library and licensing review. The Eigen source archive's **420 original files** match both its source manifest and the pinned original Eigen archive byte for byte. Both ZIPs contain the complete exact original nlohmann header at the hash recorded above. Full source/legal terms remain available inside the package.

The only payload difference from the preceding audited build is `runtime/worker.py`: its temporary wheel-extraction directory now sits under the parent-owned calculation directory, so the parent can reap that complete tree after worker termination. Independent read-only review confirms the parent waits for the child before outer-directory cleanup. The other **52 payload files** are unchanged, including every wheel and legal/source file. Unaffected corresponding-source checks were reused only after verifying their exact hashes.

`source-audit.json` and `provenance.json / final_zip_audit` contain the compact audit record. Payload and ZIP bytes were left unchanged during this final audit. Changes to outside-payload review records require refreshing their artifact metadata hashes; they do not require rebuilding these ZIPs. This establishes archive/source/legal consistency, distinct from functional testing and explicit user manual-testing confirmation. Intel execution and a byte-identical full engine rebuild are not claimed. User manual testing and original screenshots remain later gates; no GitHub or Hub delivery is claimed here.
