# Source and redistribution review

Reviewed 2026-11-12 for Cai Zhenze; task `AH-20261112-offline-allocation-workbench`. Candidate ID: **Not Applicable** (approved external implementation; no fabricated candidate). Naming: **HiGHS → 离线资源配置优化台 → offline-allocation-workbench**. Integration mode: `ported`, with a new allocation-specific Chinese wrapper/model/UI and adaptations of maintained internal lifecycle, transport, packaging and verification components described below. The entire wrapper is not claimed as newly or independently written.

## Reviewed source and reuse decision

The chosen engine is official **HiGHS 1.16.0**, commit `f3f113d230429a8c0014b12ab0dd1a3847e58c55`:

- [Official release](https://github.com/ERGO-Code/HiGHS/releases/tag/v1.16.0).
- Binary artifact `highs-1.16.0-arm-apple-static-mit.tar.gz`, 11,095,570 bytes, SHA-256 `a3a1504a173aa1a6dffefd3243bcc4bb2d095e04683095fa43cf311edb36321c`.
- Official `source-archive.tar.gz`, 7,289,356 bytes, SHA-256 `05ba0a408e31fe933e4ee4ec9d0e244a0e3c5bd2613e7b138701f62708eceed9`. Its embedded Git HEAD independently resolves to the exact commit above. No source code or binary was executed during Phase 1.
- The binary archive's `include/highs/HConfig.h` identifies `1.16.0`, Git hash `f3f113d`, `CUPDLP_CPU` and `ZLIB_FOUND`; HIPO/GPU/shared-extras are undefined. The copied archive member is solely `bin/highs`; binary SHA-256 `c2f3c6d27708eac52d9c16b9306996c2511780e49c87b292d8617572593eb109`, 10,980,040 bytes. It is unmodified.

**Reuse is permitted for the recorded scope with the supplied conditions.** This is not a blanket MIT conclusion. Review found CSparse-derived LGPL code that the upstream root MIT label and summary notices do not enumerate. Full licensing, corresponding source and relink rights were resolved before the binary entered the plugin payload or was executed. `provenance.json` and `source-audit.json` record hashes and evidence; packaging verification remains a separate gate.

## Item-by-item coverage

| Material | Findings and distribution conditions |
| --- | --- |
| HiGHS core/CLI, including its QP and HiPDLP CPU implementation | Root MIT text, original authors and headers retained. No upstream icon, font, logo, benchmark dataset or unrelated examples copied into the distributable source. No official endorsement claimed. |
| CLI11 2.5.0 | Exact standalone header has the University of Cincinnati/Henry Schreiner copyright and BSD three-clause-style text. The entire original notice is bundled in `licenses/highs/cli11/LICENSE`. |
| pdqsort, upstream marker `git:b1ef26a` | Zlib grant; Copyright (c) 2021 Orson Peters. Full text and original header retained. |
| zstr 1.0.6 | MIT; Matei David/Ontario Institute for Cancer Research. Full grant retained. The linked zlib is an existing macOS system library, not redistributed. |
| IPX | ERGO-Code copyright retained. Explicit MIT option selected under its actual dual-license grant, preserved at `licenses/highs/ipx/LICENSE`; notice includes the required application statement. Evidence pin `e6cbac171d42bbb9b3c01b382a1c3392d84d0ce3` is license evidence, not the numerical implementation copied. The numerical implementation remains the HiGHS snapshot. Its CSparse-derived `sparse_utils.cc/.h` is separately covered below. |
| BasicLU | ERGO-Code copyright retained. Explicit MIT option selected; required application statement and complete grant retained. License-evidence pin `a2828782151288efa5e2cb2e0c1ac21925ed9db9`; numerical code remains HiGHS's pinned integration. `lu_dfs.c` explicitly acknowledges adaptation from CSPARSE and is separately covered below. |
| cuPDLP-C CPU | HiGHS's integration README pins `7b94c41efca42fa176a129a935b59718e1455fad`; its actual MIT grant is Copyright (c) 2023 COPT-Public. Original grant, authors and integration notes retained. Official later component provenance at `f81f459235c948b4a53fc96f359847eaedd4f0a9` identifies `cupdlp_cs.c/.h` as CSparse adaptations under LGPL-2.1-or-later; it supplies evidence, not new numerical code. |
| CSparse adaptations | Pinned HiGHS files explicitly identify CSparse origin; the binary exports the corresponding `cupdlp_dcs_*` functions. Also include IPX sparse utilities and BasicLU DFS adaptations. CSparse copyright is (c) 2006 Timothy A. Davis. [SuiteSparse v7.11.0 license evidence](https://github.com/DrTimothyAldenDavis/SuiteSparse/blob/v7.11.0/CSparse/Doc/License.txt) establishes LGPL-2.1-or-later; it does not establish the exact historical adaptation revision, which upstream does not specify. Full LGPL 2.1, CSparse notice and complete combined CLI source accompany the executable. |
| Required AMD/RCM/BLAS interface headers | Even with HIPO disabled, actual compiler dependencies include AMD `amd.h`/`SuiteSparse_config.h`, RCM `rcm.h` and `mycblas.h`. Retain required original headers plus AMD BSD-3 and RCM MIT grants. No AMD/METIS/RCM/BLAS provider implementations are selected. |
| macOS runtime/build tools | Only `/usr/lib/libz.1.dylib`, `/usr/lib/libc++.1.dylib`, `/usr/lib/libSystem.B.dylib` are dynamic dependencies. They are not redistributed. CMake, compiler and SDK are build tools/system components; none enters the plugin package. No proprietary GPU or service runtime is required. |

## LGPL corresponding source and modification conditions

`vendor/highs/source/HiGHS-1.16.0-corresponding-source.tar.gz` supplies the complete machine-readable combined CLI source required by **LGPL 2.1 section 6(a)**, including library adaptations, other linked HiGHS/CLI source, all required headers, version/configuration inputs and CMake utility files. Required `examples/CMakeLists.txt` is retained even when examples are disabled. Uncompiled provider implementations, tests, benchmark data, media, Python wrappers and Git metadata are omitted. Original and distributed source hashes are recorded inside `SOURCE_MANIFEST.json`.

Five source files receive only prominent dated license/origin comments on 2026-11-12: `cupdlp_cs.c/.h`, IPX `sparse_utils.cc/.h`, and BasicLU `lu_dfs.c`. Numerical code remains byte-for-byte unchanged after removing those added comments. Original attribution is retained. The binary itself is unchanged. The adapted source and notices identify upstream adaptation separately from our license-comment additions.

The Chinese notice and rebuild guide explicitly permit user modification, relinking and reverse engineering for debugging such modifications. Complete source accompanies the same package; no written offer, paid service or future download is needed. Users can update their own plugin copy's binary hash metadata after replacing their self-relinked program. The wrapper's checksum is not a restriction on these rights. Runtime attribution is shown by the plugin's Chinese output/UI; raw solver output is captured internally.

The mixed component licenses remain applicable. No repository-wide license or new trademark permission is asserted. The repository-owned integration communicates with the standalone process and is not silently relicensed. The shared `AGENTS.md` source/review rules remain unchanged.

## Maintained internal implementation reused

The lifecycle/transport/packager foundation is adapted from Cai Zhenze's existing `plugins/queue-capacity-workbench/` at commit `a858017d8f3fa928647e05027f99165c38a1e071`. Ownership is confirmed by the current task context and corroborated by that asset's explicit `publisher: Cai Zhenze`; it is not inferred from a GitHub account. The user's approved independent plugin build authorizes this task's changes within its own plugin, while preserving the earlier plugin and its environment.

| Pinned source | Current task destination | Adapted responsibility |
| --- | --- | --- |
| `queue-capacity-workbench/runtime/runtime.py` | `offline-allocation-workbench/runtime/runtime.py` | Ownership-checked state directories/file locks; start/status/stop; bounded child output, cancellation and liveness checks. |
| `queue-capacity-workbench/runtime/server.py` | `offline-allocation-workbench/runtime/server.py` | Authenticated ephemeral loopback HTTP transport, fixed asset allowlist, host/origin checks and service lifecycle. |
| `build_packages.py` | `build_packages.py` | Deterministic native ZIP and companion-artifact packaging derived from the canonical reviewed payload. |
| `verify_sdk.py`, `verify_workswarm.py` | Same task-local helper names | Public SDK and host import/install verification scaffolding, adapted for allocation-specific capabilities and isolated runtime. |

The paths above are relative to their respective asset roots. `provenance.json / repository_reuse` records exact source/destination paths and SHA-256 values. The allocation model and validation, HiGHS adapter/sandbox executor, allocation-specific Tool/Skill wrapper, interactive UI and scenarios are new work for this capability. No SimPy engine or queue simulation implementation is included. Reusing lifecycle/transport infrastructure does not repackage the queue capability as a new optimizer. No earlier plugin file, dependency, runtime, claim or testing environment is changed. This is maintained internal repository-code reuse, not a new external license grant or repository-wide licensing assertion.

## Rebuild and compatibility evidence

To demonstrate usable corresponding source, a task-private CMake **3.31.10** wheel was selected from official PyPI metadata, SHA-256 `ad697643a00d9ba85179590a383c4f7401169b55ebf4b8b2938daf28c6bdeb6d`. The Python distribution's Apache-2.0 and Kitware CMake BSD-3 grants were read. It was unpacked only in this task's private temporary directory, never installed into shared dependencies and never redistributed.

Actual configure and universal CLI build used AppleClang **16.0.0.16000026**, system SDK **15.2**, `Release`, `FAST_BUILD=ON`, static executable, system zlib, `HIPO/GPU/Python/tests/examples/Fortran/CSharp/vcpkg=OFF`, architectures `x86_64;arm64`, deployment target `26.0`, and `--parallel 2`. This machine's default C++ header lookup needed a task-local `-isystem <SDK>/usr/include/c++/v1` flag; no host or SDK files were patched. The bundled Chinese guide documents this optional local flag and normal toolchain requirements.

Read-only Mach-O inspection confirms the official binary's two architectures, **minimum macOS 26.0**, and SDK **26.5**. Its archive filename does not mean ARM-only. These requirements must be exposed to users; Linux, Windows and older macOS are outside this package's compatibility claim. Rebuilding with a different SDK/compiler does not promise byte-identical output. Rebuilt version reports `1.16.0`, hash `n/a` because the corresponding source omits Git metadata; official binary reports `1.16.0`, `f3f113d`.

Actual command/results, final minimized-source build verification and log hashes are in `source-audit.json`. Source/relink evidence is separate from plugin functional tests and actual WorkSwarm loading, recorded by the parent in `TEST_REPORT.md`. No source/host API changes, external model calls, shared dependency installation, paid service, push, PR or Hub action is part of this review.

## Frozen package audit

Both exact Chinese **1.0.0** ZIPs were extracted into this task's private audit directory and inspected on 2026-11-12:

| Form | Repository path | ZIP SHA-256 |
| --- | --- | --- |
| Native WorkSwarm | `plugins/offline-allocation-workbench/test-packages/offline-allocation-workbench-1.0.0-workswarm.zip` | `5bf081fdd1216bb801d855fedb9642499091cb3901255c8c1f8c3f7d9607d147` |
| Canonical wrapped | `releases/agent-plugin/offline-allocation-workbench/1.0.0/offline-allocation-workbench-1.0.0.zip` | `35eae9aa6c620da7b901ccb6c73dbcb477bce557ea83f84b8b1cda1930fcf089` |

All **45 payload files** match each other, current reviewed source and both artifact payload manifests. ZIP CRC, path safety, absence of symlinks/duplicate paths/caches, native root manifest and canonical wrapper layout pass. All **26 recorded legal-evidence hashes** match both extracted payloads. The unchanged engine hash remains `c2f3c6d27708eac52d9c16b9306996c2511780e49c87b292d8617572593eb109`.

Both contain corresponding-source SHA-256 `4a08127fd603af48a8449bf1c98eb876355f41ddbd8a4d4ce3e82704fc380c85`, **606 entries**, including **598 original source files**. Every distributed source hash and each original-source hash matches its recorded manifest; the five modifications remove cleanly to the exact originals and add license comments only. Full LGPL/CSparse/IPX/BasicLU/cuPDLP grants, source and CLI build inputs are present. This is the same numerical/build source used in the successful private universal rebuild; unaffected rebuild evidence is reused. Runtime UI/Tool files contain the CSparse attribution and license reference.

One optional evidence excerpt, `licenses/highs/original-headers/highs/pdlp/cupdlp/cupdlp_cs.c.txt`, is empty because the original begins with an include before its attribution comment. It is **not relied on** as attribution evidence. The complete exact source file with the original CSparse attribution, added license notice and all applicable full texts is in the corresponding-source archive. Payload and ZIP bytes were left unchanged during this audit.

`provenance.json` and `source-audit.json / final_zip_audit` record the exact results. This audit establishes package/source/legal consistency; it does not replace host functional tests or explicit user manual-testing confirmation. Compatibility remains macOS 26.0+ universal only. No user testing, GitHub delivery or Hub acceptance is claimed. Updating these outside-payload review records changes their metadata hashes only; refresh the artifact records' source-review hash without rebuilding the frozen ZIPs.
