# Functional test report — 预印本目录助手 1.0.0

Owner Nguyen Trung Dung; Task AH-20261102-biorxiv-catalog; Candidate CAND-CLD-274.
Test date 2026-11-02 Asia/Singapore. Local branch port/biorxiv-catalog-20261102 from fetched main c4bf10e1e0cbc58f1c0ad12288f2501b926c1807.

## Exact package identity

- Stable ID repo:agent-plugin:biorxiv-catalog; upstream bioRxiv -> 预印本目录助手 -> biorxiv-catalog.
- Native import: test-packages/biorxiv-catalog-1.0.0-native.zip; 48082 bytes; SHA-256 9996c01204cf1f7b31eb5d194ac5bfa72ce19638c67295cc9a2367972b96ebeb.
- Canonical marketplace archive: releases/agent-plugin/biorxiv-catalog/1.0.0/biorxiv-catalog-1.0.0.zip; 49163 bytes; SHA-256 609fdd83f6480ab765c7f09627f965c691b7a0691386a569da23ca6846c935bd.
- All nine runtime files are shared unchanged by source, native and canonical formats. Native CRC, extraction, original 11358-byte license/Git-blob digest, UTF-8 decoding and Python syntax checks pass. Final archive-verification.json records both archive/extraction comparisons.
- Apache license SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30; applicable upstream source pinned at 2574e29377c7173d0cecffef29a6ecbd7f8ccb5d/bio-research. Connection change notice and complete license/notices verified. No paper/abstract dataset, credentials, logo, binary or dependency package is redistributed.

## Environment and executed checks

Windows, existing D:/Python 3/python.exe, Python 3.12. SDK source D:/jiuwen_repos/agent-core-latest at 0ab5913b250d565b35bff3828dae438939cb1acd. Runtime imports use MCP1.26.0, jsonschema4.26.0, httpx0.28.1 and pydantic2.12.5. Existing host SDK source/dependencies were used; no runtime dependency install or host configuration change. PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1, -B, explicit PYTHONPATH. Logs, isolated test agents and raw network records live under D:/jiuwen_repos/outputs/biorxiv-build, outside payload. Zero model calls.

1. `python tools/asset_release.py check plugins/biorxiv-catalog`: passes metadata, declaration, path and provenance checks.
2. `python -B plugins/biorxiv-catalog/tests/test_adapter.py`: 12/12 meaningful offline checks pass against source and separately exact extracted native payload. Covers date/selector/DOI/ROR validation before network, Chinese aliases without input mutation, response/count provenance, empty vs failed results, missing statistics/periods, 401/403/429 and Retry-After, bounded output, timeout/cancellation without retry, changed remote schema/readonly/tool availability, actual ToolCards and stream result.
3. `tests/live_checks.py --payload <source> --report <source-final-live.json>`: 7/7 real native Tool.invoke operations pass against biorxiv service3.2.0. Chinese category/platform/interval inputs are exercised.
4. Same seven real operations from extracted native ZIP: 7/7 pass. Search returns two date/category-matched papers; DOI10.1101/2023.12.30.573742 matches the next actual metadata lookup and has license/version. Published-preprint query returns actual DOI pairs and dates; documented funder ROR query returns a dated preprint. Monthly content/usage statistics return 156/154 records with nonnegative requested metrics; these variable source counts are observations, not fixed promises or independent source-count validation.
5. `tests/host_checks.py` loads the plugin using real DeepAgent, SkillUseRail, ability manager and Runner. All seven names are visible with DIRECT exposure. Registered invalid input rejects correctly; exact extracted package's registered category tool and medRxiv search return real data. All tools and Skill unload, and payload hashes stay unchanged. This is actual SDK execution, not a stub agent, frontend conversation, or model-planned tool-choice test.
6. `tests/test_biorxiv_catalog.py` is the repository discovery entrypoint: native/canonical/source digest contract plus the actual 12-test business suite in a fresh process when SDK dependencies exist. In packaging-only environments the SDK-dependent case explicitly skips; no mocked SDK success is claimed.
7. Final packaging runs deterministic native/canonical byte checks and `asset_release.py check-repo`. Raw command completion/exit results are recorded in the local build handoff; no GitHub CI run exists before an allowed PR.

## Real observed limitations and adaptations

- Search may report total=0 while returning two rows. Original total/count/data stay intact; received_count and a Chinese warning prevent reporting false absence/completeness.
- An earlier preparatory yearly-statistics call returned 14 records without period labels, and annual usage omitted abstract-view fields. The final adapter adds explicit Chinese missing-period/metric warnings and does not infer years, zero-fill or label them a verified time series. A regression covers this condition. Final real-network source/extracted matrix uses monthly statistics, with actual period labels. No upstream dataset is repaired or fabricated.
- Publication records can have null journal/author fields; ROR filtering does not provide complete funding-award evidence. Preserve unknowns. Funder data begins2025-04-10, category enum coverage is limited, especially for medRxiv.
- No live 401/403/429 was forced; those are controlled HTTP-boundary tests, not fresh service-failure observations. No retry loops, paid calls, bulk traversal, article downloads, browser actions or running WorkSwarm changes.
- Current seven-tool discovery differs from the official directory's older eight-tool listing; runtime checks the live tool, readonly annotation and input schema before one call.
- Initial licensing-file write introduced one trailing newline; corrected before packaging and verified against original Git blob. A multi-file warning patch failed atomically on README context and was reapplied correctly. These were build-only steps; no tested/user package version was overwritten.

## Reproducible evidence and handoff

Safe summaries in tests/evidence/ contain identifiers, checks, source response hashes and real SDK registrations. Raw source/extracted JSON remains in the local output folder; it is not bundled or included in the repository because article licenses vary. Snapshot/config/source review and schema/catalog preserve traceability; no private session or model transcript is copied.

Use MANUAL_TESTING.md for eight Chinese UI prompts covering all seven tools, medRxiv and the expected invalid-date rejection. The native package is ready for user testing after final local checks; explicit current-package WorkSwarm completion and original screenshots are still pending. Candidate remains Planned, acceptance Pending Acceptance, PR/Hub/completed date blank. No push, delivery PR, merge, Release, Hub action or Asset Ledger entry. No existing Pitwall confirmation, screenshot or task is reused.

## Final local verification

Completed 2026-11-02: the new repository regression entrypoint passes 2/2 checks (including a fresh process running all12 SDK business tests). `asset_release.py check-repo` passes with54source assets and64release ZIPs. These local results do not claim a full repository Windows unit-suite run or GitHub CI execution. Python version verified as3.12.6.

The first whole-repository contract check stopped at a pre-existing license digest because system Git autocrlf converted old tracked files toCRLF in the newly created worktree. Diagnosed40affected existing asset license checks. Restored1042checkout-only text conversions from exactHEAD blobs, only when replacingCRLF withLF was the sole difference. Both Git/index/object hashes and `git -c core.autocrlf=false diff --name-only` confirm no unrelated source changes; the only tracked implementation-adjacent edit is the intended four-line .gitattributes addition. No Git global/user configuration changed. Native/canonical bioRxiv hashes and its9runtime files stayed unchanged. Raw repair audit is outside the repo at outputs/biorxiv-build/checkout-crlf-repairs.json.

## Current-package user testing — 2026-11-02

User test confirmation: **“Testing results are as expected, shown in these screenshots”**; confirmed by **Nguyen Trung Dung** in the current conversation on **2026-11-02, Asia/Singapore**, immediately after the eight Chinese manual test prompts for the current 1.0.0 package. Exact message timestamp/permalink is unavailable; no capture timestamp is substituted for it. Confirmation Report RPT-20261102-biorxiv-catalog-confirmed-100.

Native ZIP SHA-256 `9996c01204cf1f7b31eb5d194ac5bfa72ce19638c67295cc9a2367972b96ebeb`.
Canonical ZIP SHA-256 `609fdd83f6480ab765c7f09627f965c691b7a0691386a569da23ca6846c935bd`.
Known blocking issues: none reported; earlier local functional and packaging checks passed. All nine runtime files and both ZIPs remain unchanged after confirmation. Only outer delivery documentation/evidence and their artifact report digests are updated.

Nine original full-resolution PNGs supplied in this message are preserved byte-for-byte without editing/recompression under evidence/1.0.0/. Their original filenames, dimensions, SHA-256 and individual evidence limits are in evidence.json. All images were visually inspected in the conversation: no credentials or personal medical records observed. They show the enabled Chinese plugin and calls spanning all seven tools, medRxiv and the intended invalid-date rejection. Some bodies are cropped; DONE or a generated success statement alone is not treated as independent proof of complete response correctness. User completion is explicit and separate from these screenshot limits; source/extracted live tests supply additional functional evidence.

Screenshots include bibliographic metadata and short visible excerpts of returned source abstracts. They are test evidence outside the runtime ZIP, not a redistributed paper/abstract dataset; source article licenses stay as returned and are not covered by the configuration's Apache license.

Ready for the Phase 3 GitHub delivery workflow once this record and saved tracker confirmation are verified. Project Lead acceptance remains pending; Song Haoran handles Hub operations. No Asset Ledger entry follows from GitHub delivery alone.
