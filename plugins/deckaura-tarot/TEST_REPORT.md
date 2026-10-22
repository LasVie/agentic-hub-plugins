# Deckaura Tarot 1.0.2 test report

Candidate `CAND-CLD-140`; task `AH-20261022-deckaura-tarot`; owner Cai Zhenze. Tests and source review were performed on 2026-10-22. The user subsequently confirmed manual testing complete for this unchanged package and explicitly authorized Phase 3 in the current conversation on the same date; the exact confirmation time is unavailable. The task is `Submitting` and the candidate remains `Planned`. PR merge, Hub submission/publication and Song Haoran's final acceptance are not established by this report.

## Environment

macOS arm64; Python 3.12.14; PyYAML 6.0.3; openJiuwen 0.1.19; Node.js 22.23.3. WorkSwarm snapshot commit `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`. Dependencies were already installed; no npm installation or paid model call occurred. Packaging used the existing WorkSwarm Python environment, which included PyYAML.

## Results

| Layer | Actual verification | Outcome |
| --- | --- | --- |
| Package format | `python tools/asset_release.py check plugins/deckaura-tarot` and `pack` | Passed native manifest/paths/version/provenance and deterministic market wrapper |
| Plugin functional tests | `tests/test_deckaura_tarot.py` with actual SDK/Node and `DECKAURA_PAYLOAD` pointing to the extracted final Hub ZIP | 26 passed, zero skipped; raw record retained in `FUNCTIONAL_TEST.log` |
| Repository regression | `python -m unittest discover -s tests -v` with actual SDK/Node | 49 passed, zero skipped; generated local log archived outside the delivery tree |
| Final archive | Extracted ZIP, full license/source/hash audit and runtime-file comparison | Passed; findings recorded below and in `SOURCE_REVIEW.md` |
| Actual installed host | WorkSwarm resolver -> `load_plugin_package` -> `resolve_plugin_parts` -> native tool provider | One Skill and one Tool materialized; all functional assertions passed |
| Services | HTTP 200, direct/proxied WebSocket ping/pong, `config.get` and plugin catalog | Passed on the isolated local instance |
| Extensions | Actual backend import/install and installed card/detail visual check | Passed; title, description, tags, Skill and Tool visible |
| Native file chooser | Browser request reached macOS chooser; automation could not operate chooser | Final selection not verified by automation; import used the actual backend API |
| User testing | Explicit completion confirmation and original user screenshot | Confirmed for unchanged 1.0.2; screenshot association and limits documented below |
| Model execution | Disabled local model endpoint; no agent/model call in automated tests | Model-generated conversational behavior was not tested |

The 26-test suite covers 78-card validation/hash, aliases and reversed meanings, unique/replayable draws, all six spread positions, full-deck draws, malformed action-specific inputs, missing-Node/timeout errors, native async invoke/stream, CLI parity, and relocation outside the repository. Only unavailable-runtime and timeout failure paths are mocked; normal operations use real Node and the host Tool API.

The installed host test independently invoked the provider-loaded class with network connections blocked. It verified the dataset, reversed lookup, 78 unique cards, repeatability, daily/three-card/decision/relationship/celtic-cross/yes-no spreads, invalid input failures and streaming. The test recorded zero network attempts and no agent/model invocation. Generated host-response records, the AI-driven UI smoke screenshot, archive-comparison records and the earlier tracker snapshot are preserved in the local development archive, outside the delivery tree; they are summarized here rather than treated as portable test dependencies or user acceptance images.

An independent source reviewer ran six selected upstream tests successfully on Node.js 24.19.0 plus boundary/meaning/replay assertions. The complete upstream seven-test run has one expected asset-existence failure because the research copy omits branding SVGs. The complete upstream suite is not claimed green. Our native manifest and packaged files were verified separately.

## Exact package identity and archive inspection

- Canonical Hub ZIP: `releases/agent-plugin/deckaura-tarot/1.0.2/deckaura-tarot-1.0.2.zip`.
- Canonical SHA-256: `b98f0bf8a1284f8671445339c61137719662b3a4df1686c5e0fbcc5778f2aeb4`.
- Generated WorkSwarm companion: `deckaura-tarot-1.0.2-workswarm.zip`.
- Companion SHA-256: `8c8fd7ccc0316e341071b9f88ef8b36a8af7cad12ae67b4714bd88e1b21f8ee7`.
- Dataset SHA-256: `4b47fc22b3220a23a5d9ac06065698315de338a2265fe5491f6fdaa0f0c447c9`.
- Bundled full MIT SHA-256: `2a870b98a936750e931a5833bc362778ae474aa3042532609a97cbe1b09cb654`.

The canonical archive contains 14 regular file entries: the market wrapper and 13 runtime files. The companion contains those same 13 runtime files without the market wrapper. Every payload file is byte-identical across source, both archives and the installed package. Source/canonical/installed equality and the confirmed canonical hash were reverified before Phase 3. Archive paths, uniqueness, CRCs, declared manifest paths, full license/notice coverage, and provenance hashes were checked; no traversal path, symlink, cache, test file or development record was found in either runtime payload. Seven reused code/data/reference files are unchanged; the eighth is the explicitly adapted Skill.

Companion construction remains reproducible with `python plugins/deckaura-tarot/build_local_test_package.py`. Its generated ZIP and metadata are local testing outputs, not committed delivery artifacts. Internal 1.0.0/1.0.1 artifacts were preserved outside the repository rather than overwritten; 1.0.2 fixes WorkSwarm's required localized display metadata and tags. The confirmed 1.0.2 payload and ZIP were not changed during documentation cleanup.

## User confirmation and screenshot

The user explicitly confirmed manual testing complete and authorized submission of unchanged Deckaura Tarot 1.0.2 in the current conversation on 2026-10-22. No exact time or conversation URL is available, so neither is invented. No known blocking issue remained in the confirmation and accompanying checks. This is the Phase 3 authorization; it is distinct from final Project Lead acceptance.

The original user-provided screenshot has SHA-256 `d2561650a539ad64f7825fd51b1a4487e214b9a14eee17fa9d3e6b5a17c0dc2d`. Its cards and orientations are reproduced by the bundled CLI with a three-card spread, seed `project-demo`, and reversals enabled: Justice upright, King of Wands upright, and Strength reversed. The screenshot has no visible version and does not independently establish that the backend tool was invoked. Its association with 1.0.2 is corroborated by the user's explicit declaration and the byte-identical installed-payload records.

The original image must be attached to the delivery PR with the task, candidate, version and canonical ZIP hash, then linked through a verified PR evidence permalink in the tracker. The earlier AI-driven UI smoke screenshot is separate evidence and does not replace this original. No attachment URL, PR merge or Hub result is claimed here before it exists.

## Repeat the tests

Activate a compatible openJiuwen/WorkSwarm Python environment with PyYAML installed and Node.js >=18 on `PATH`; the tested versions are recorded above. From the repository root:

```sh
python tools/asset_release.py check plugins/deckaura-tarot
tarot_extract_dir="$(mktemp -d)"
python -m zipfile -e releases/agent-plugin/deckaura-tarot/1.0.2/deckaura-tarot-1.0.2.zip "$tarot_extract_dir"
DECKAURA_PAYLOAD="$tarot_extract_dir/deckaura-tarot/deckaura-tarot" \
  python -B tests/test_deckaura_tarot.py
python -B -m unittest discover -s tests -v
```

These commands use actual installed host classes and Node; they require no model configuration or paid calls. Generic CI without SDK/Node skips the functional suite explicitly, and such skips are not functional evidence. The archived host-specific launcher and test helper were used for the recorded installed-host checks but are not required by the portable suite.

## Remaining delivery gates

The canonical Hub wrapper is structurally verified; Hub upload/review is not established by local validation. The tested WorkSwarm importer requires the generated native companion. Automated native file selection and model-generated conversational interpretation retain the limits described above even though the user has confirmed manual testing complete. Finish the authorized PR and Hub workflow against the unchanged confirmed ZIP, record actual screenshot evidence permalinks and results, and obtain Song Haoran's final acceptance before marking the task `Completed` or candidate `Delivered`.

## Current submission boundary

The user subsequently limited authorization to pushing the reviewed source and unchanged canonical ZIP and opening the delivery PR. Stop at that PR handoff. Merging, creating a Release, and uploading/submitting/publishing to Agentic Hub require a new explicit user authorization. Earlier Phase 3 authorization does not override this latest boundary.
