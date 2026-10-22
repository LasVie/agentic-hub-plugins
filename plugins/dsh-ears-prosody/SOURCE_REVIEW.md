# DSH Ears Prosody source review

Reviewed 2026-10-22. Candidate `CAND-DSH-189`; task `AH-20261022-dsh-ears-prosody`; owner Cai Zhenze. The user approved the previously reviewed offline scope in the current conversation. This is Build authorization, not user test completion or Project Lead acceptance.

Naming mapping: original candidate/upstream `chaoge762/dsh-ears-prosody` (DSH Ears Prosody) → final Chinese display name **DSH 韵律分析** → internal slug `dsh-ears-prosody`. Stable internal asset ID: `repo:agent-plugin:dsh-ears-prosody`. Current 1.0.1 user testing confirmation is recorded separately in `USER_TEST_CONFIRMATION.md`.

## Fixed source and permission

- Repository: https://github.com/chaoge762/dsh-ears-prosody
- Revision: `f28cd16bc5646fb17c3c76564598e2c37e997d77`.
- Git package version: **0.1.4**; Node >=20.
- Full root LICENSE: MIT, **Copyright (c) 2026 chaoge888**.
- License SHA-256: `125fba30b32d7fa4fb44458066f73682a725b9355561fa6c972e36f1695c72ef`.
- Full recursive tree, package metadata, README, core implementation and upstream selfcheck were inspected. No nested license, NOTICE, media, fonts, dataset, model weights or core third-party package dependency occurs in that revision.

The full MIT text permits copying, modification and distribution subject to preservation of the copyright and permission notice. The complete original license, including disclaimer, is bundled. Original core file headers are retained with explicit adaptation notes. `provenance.json` uses `mode: ported` and `permission_status: verified` for the actually reused paths. This assessment concerns those fixed materials, not a legal guarantee or repository-wide relicensing decision.

`asset_release.py audit-upstream` found MIT-like text with the expected hash; its automatic `unknown` result was followed by the manual text/scope review above. The audit copy includes only the inspected source files, license, README, package metadata and selfcheck; the complete tree was separately inspected through GitHub.

## Version discrepancy

The tracker retains its original npm **0.2.0** snapshot. Its registry tarball SHA-256 is `993b0f1345ef2d1d10dee6039a1c27b678ae0d7ddac8a070a5ca9f3500535f4d`, and its published SHA-512 integrity was verified. That archive omits LICENSE and adds recording UI/host and optional `sherpa-onnx-node`/SenseVoice transcription. It is not our distribution source. Its WAV/analyzer core is byte-identical to the licensed fixed Git source, verified independently by two readers. We reuse only the Git acoustic files and bundle that revision's full license; none of the npm-only material enters this package.

## Reuse inventory

| Upstream path | Original SHA-256 | Delivered path | Treatment |
| --- | --- | --- | --- |
| `lib/wav.js` | `ab4eb37b2cdacb7f83141ded46a4fa17bab77f0083f18dda562f00e7cd588bcd` | `lib/wav.mjs` | Adapted: strict header/chunk/format/finite-sample/size validation and Chinese errors |
| `lib/hearing.js` | `b607f79096e3c269a7561fc1297f0385ed5d44bdc7e3c3c0d30e1496cbbc0c00` | `lib/hearing.mjs` | Adapted: bounded analysis rate, revised pitch estimation, activity terminology, Chinese metric explanations, no emotion/arousal output |
| `LICENSE` | `125fba30b32d7fa4fb44458066f73682a725b9355561fa6c972e36f1695c72ef` | `licenses/dsh-ears-prosody/LICENSE` | Unchanged full text |

The Python host adapter, CLI orchestration, Skill, manifest, README and functional tests are repository additions. The tests use generated signals rather than third-party voice recordings. Upstream synthetic-test concepts inform measurement cases; the upstream selfcheck is not bundled. No existing author statement is replaced, and no blanket license is assigned to the repository additions.

Excluded: upstream `lib/index.js`, `lib/model.js`, DSH/Cordis registration, recording/transcription UI, API clients, emotion/intent interpretations, logos and model downloads. The native host supplies Python/openJiuwen; the operating environment supplies Node.js. These runtimes are not vendored. No network service or paid model is used by the plugin.

## Functional comparison

The Review read all 609 then-current ledger assets plus merged Deckaura Tarot 1.0.2. Build rechecked later records and current main, including LaTeX Guard, without finding a new prosody overlap.

- `audio-transcriber` `05df7e483d59492d90e21103d5393dac` @ `e7bda4f`: transcript/documentation output.
- `audio-post-delivery` `98529d5e450c44569d0df532723de4c9` @ `1.0.0`: WAV edits and peak/RMS/clipping checks.
- `audio-loudness-master` `d59d594136824a6d916d79126048ec52` @ `1.0.0`: loudness mastering/compliance.
- `audio-quality-team` `94e2a85b3e3948b082a24846dc7c00a3` @ `1.0.0`: mastering-quality review by a SwarmSkill.

This Plugin accepts local WAV bytes and returns pitch contours, activity/pause timing, energy dynamics and a pacing proxy without changing the file. Shared energy concepts do not cover the combined measurements. No transcription, recording, identity, emotion, intent or medical claim is included. Activity detection does not prove speech, and the pacing proxy is not a syllable/word counter.

## Final archive review

### Historical confirmed 1.0.0

Verified the final 1.0.0 canonical archive on 2026-10-22: runtime prefix `dsh-ears-prosody/dsh-ears-prosody/`; both reused `.mjs` files, `THIRD_PARTY_NOTICES.md` and `licenses/dsh-ears-prosody/LICENSE` are present. The outer directory contains only `plugin.yaml` and the same-name inner payload. All nine runtime files match the source and native WorkSwarm companion byte for byte. Full MIT text matches the fixed upstream file and the recorded `license_evidence` hash. Both reused files retain original headers followed by explicit modification/source notices. Declared Skill/tool paths, versions, regular file types, CRCs and unique safe archive paths passed inspection. No tests, evidence, fixtures, caches or development records occur in either runtime archive. Exact ZIP hashes and extracted-payload functional results are recorded in `TEST_REPORT.md`; package validation alone does not establish functionality or user acceptance.

### Chinese edition 1.0.1

Main `e0f6b866` (PR #20) introduced mandatory Chinese packaged deliverables after the English 1.0.0 test handoff. Version 1.0.1 translates display metadata, README, Skill instructions, tool descriptions and all human-readable runtime explanations/errors; it defaults to Chinese interpretation while honoring an explicit requested output language. Machine identifiers, schema keys, error codes, enum values, acoustic computations and resource limits are unchanged. Original headers, full MIT text and THIRD_PARTY_NOTICES.md are unchanged. Tests compare the numerical/protocol output with the original 1.0.0 ZIP and check Chinese paths, UTF-8, messages and actual host behavior. This changes the tested package and requires new user confirmation; the 1.0.0 screenshot/confirmation remains historical evidence.

The original source/records are preserved by local commit `1f6f30c`, with the old canonical ZIP/artifact archived unchanged under ignored `dist/dsh-ears-prosody/history/1.0.0/`. Only the current Chinese ZIP belongs in the eventual delivery PR. Final 1.0.1 extraction verified all nine source/native/canonical files, declared paths, safe unique regular entries, UTF-8, identity/version and CRCs. The full MIT/license-evidence hash and original notice bytes match both fixed upstream and 1.0.0. Chinese instructions and human-readable outputs/errors passed the extracted-payload tests, with exact hashes recorded in TEST_REPORT.md. No new source or dependency was introduced.
