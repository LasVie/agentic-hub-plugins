# DSH Ears Prosody 1.0.1 test report

Candidate `CAND-DSH-189`; task `AH-20261022-dsh-ears-prosody`; owner Cai Zhenze; branch `feat/dsh-ears-prosody`. Tested 2026-10-22 on macOS arm64, Python 3.12.14, Node.js 22.23.3, openJiuwen 0.1.19 and PyYAML 6.0.3.

## Why this version exists

The user explicitly confirmed the unchanged English 1.0.0 complete/passed and supplied an original screenshot. Submission preflight fetched main `e0f6b866649e82cbf37fbd082db9891ca977ae8e`, adding mandatory Chinese final deliverables and renewed testing for a localized ZIP. Version 1.0.1 changes human-facing language and version only. The user subsequently explicitly confirmed Chinese 1.0.1 complete/passed and supplied its original screenshot on 2026-10-22. `USER_TEST_CONFIRMATION.md` preserves both actual statements, hashes and screenshot attribution; no historical acceptance is erased or silently extended to another package.

## Functional and localization checks

- Format check passed for 1.0.1.
- All 31 source functional tests passed in 4.729 seconds, using actual Node and the openJiuwen SDK. Chinese error/usage/output tests, Chinese filenames and documentation/metadata checks are included.
- Independent before/after comparison of five signals produced identical numbers, schema keys and machine enum values against the SHA-verified 1.0.0 archive; only version and human-readable explanations differ.
- JavaScript inverse-substitution audit and manual diff review show only message literals/version changed; the Python adapter likewise changes only descriptions/messages/version. Original license, notice and source headers remain intact.

The original 27-case coverage remains: known pitch/contours, activity and pauses, 18 dB energy changes with/without silence, energy-peak pacing proxy, silence/noise, anti-alias filtering, integer/float/extensible WAV formats, stereo/sample rates, malformed headers/chunks/samples, size/duration limits, 60-second voiced input, literal metacharacter paths, symlinks/FIFOs, and deterministic read-only operation. Real host-tool invocation is exercised. Only missing-runtime and timeout errors are mocked.

The full repository suite passed **81 tests in 5.370 seconds with no skips**, with the historical comparison explicitly enabled. The extracted canonical ZIP passed **31 tests in 4.395 seconds with no skips**. `check-repo` passed for eight source assets and nine release ZIPs. The previously tested unchanged assets' evidence was reused; no unrelated runtime was modified.

## Exact package and archive review

- Canonical: `releases/agent-plugin/dsh-ears-prosody/1.0.1/dsh-ears-prosody-1.0.1.zip`, 42,739 bytes; SHA-256 `be6bddccd8fc5c42a5259d66cd9c2b8f474d0a174b0ac2a29c20ac97c6fcf9e8`.
- Native WorkSwarm: `dist/dsh-ears-prosody/1.0.1/dsh-ears-prosody-1.0.1-workswarm.zip`, 41,671 bytes; SHA-256 `a68c0ba7687a98a274dfeb0102e641895084ccf516c3e703b19c0ba6a6e9afb2`.
- `asset_release.py pack` passed. The canonical archive contains one marketplace wrapper plus nine regular runtime files; the native archive contains the same nine files. Source/canonical/native equality, CRCs, safe unique paths, UTF-8 decoding, declared paths and matching 1.0.1 identity/version passed.
- Original MIT text and THIRD_PARTY_NOTICES.md remain byte-identical to 1.0.0; license bytes also match fixed upstream evidence. No caches, tests, screenshots, audio fixtures or development records are bundled.
- Raw local extraction audit: `/private/tmp/prosody-101-package-audit.json`; final ZIP test log: `/private/tmp/prosody-101-final-zip-tests.log`; full-suite log: `/private/tmp/prosody-1.0.1-all-tests.log`.

## Installed host and interface

The existing isolated WorkSwarm instance at `http://127.0.0.1:6283/` (backend/WebSocket port 29110) passed frontend and WebSocket checks. Version 1.0.1 was imported and installed through its actual backend import/install RPCs after preserving the previous installed version. All nine installed runtime files match source, canonical ZIP and native ZIP byte-for-byte.

The actual host loader resolved one Skill and one tool. Tool invocation and streaming passed with Chinese filenames and human-readable outputs/errors. The five-second demo returned three activity segments, two 365 ms pauses and mean pitch 220.1 Hz; the one-second silence returned zero activity and unavailable pitch/pacing. Invalid URLs, relative paths, missing files and unexpected arguments returned appropriate errors. Numeric measurements match 1.0.0. Inputs were unchanged, and instrumented Python/Node execution recorded zero network attempts.

Browser inspection verified the Chinese package name `DSH 韵律分析`, description, tags, Skill description and `WAV 韵律分析` tool label. The plugin is enabled in a fresh unsent Agent session at `/chat/new`. Deckaura's 13 installed files remain unchanged. Native operating-system file-chooser completion was not verified; installation used the same host import/install RPCs. No agent/model conversation was submitted during these checks.

Local evidence is preserved under `/private/tmp/prosody-workswarm-zh-20261022/`, including `installed-plugin-test-result.json`, `extensions-details.png` and `extensions-selected.png`. These automated checks and screenshots are distinct from the user's original 1.0.0 screenshot and do not establish manual acceptance of 1.0.1.

## Reproduce

Use a compatible Python environment with the actual openJiuwen SDK and PyYAML, with Node >=20 on PATH:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B tools/asset_release.py check plugins/dsh-ears-prosody
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p test_dsh_ears_prosody.py -v
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v
```

Set `PROSODY_PAYLOAD` to an extracted inner payload for release testing. The optional five-signal historical comparison requires `PROSODY_BASELINE_ZIP` pointing to the preserved 1.0.0 ZIP, SHA-256 `819341f0c0000225beb197ef04dd0c96982187bbfec670c7658b45716f302008`. Without it, that one historical comparison is explicitly skipped; all independent synthetic functional cases still run. Generic CI without Node or the SDK also skips affected tests. Such skips do not establish the complete local evidence reported here.

The superseded English canonical ZIP/artifact remain unchanged in ignored `dist/dsh-ears-prosody/history/1.0.0/`, with source and historical report in local commit `1f6f30c`. The native 1.0.0 ZIP and original user screenshot remain preserved outside the delivery tree. Only the current Chinese release belongs in the delivery PR.

## Remaining gates and limits

User testing of the exact Chinese 1.0.1 package is explicitly confirmed complete/passed. The original 566 × 1256 screenshot (SHA-256 `6252eda92c0d96cbfdbb871cd929da14db72f593d629c9284935a3e4fd251751`) shows the correct version and Chinese demo/silence results. It corroborates the separate host test but does not alone prove backend invocation. No blocking issue is known. GitHub delivery and Project Lead acceptance are tracked separately in the original task.

Submission preflight against updated main `ab6ad4dd3fa2da955fdeac56a843d1cd8d41f2c2` passed the updated format checker, 18 packaging regression tests and repository structure checks (13 source assets, 21 release ZIPs). Two independent read-only audits reverified all nine runtime hashes, original license/attribution and unchanged confirmed ZIP hashes. Valid functional and manual evidence was reused because no runtime payload changed. The delivery commit excludes the superseded English archive, local companion/audio files, screenshots and temporary host/debug evidence; local history and originals remain preserved.

WAV-only, at most 60 seconds/12 MiB, mono/stereo 8–48 kHz; pitch 70–400 Hz; no transcription, recording, identity/emotion/intent inference or remote service. Activity and pacing are acoustic proxies. No paid model call was made by the delivery agent. Song Haoran handles Hub operations and separate final acceptance.
