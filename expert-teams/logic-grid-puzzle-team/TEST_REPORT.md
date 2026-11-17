# Test report — 逻辑网格谜题编制与验解专家团 1.0.0

Task `AH-20261117-logic-grid-puzzle-team`; owner Cai Zhenze. Executed 2026-11-17, Asia/Singapore. Branch `codex/main4-logic-grid-puzzle-team-20261117`, base `3b5427812f027c85303ca5bd114bc0eedd00c451`. Changes remain local and asset-scoped.

## Exact packages

| Kind | File | SHA-256 | Bytes |
| --- | --- | --- | --- |
| Native | test-packages/logic-grid-puzzle-team-1.0.0-native.zip | e008b203078e53852de51675dc7fc9669b57663a64c33593f8231fc822cdd1a9 | 57893 |
| Wrapped | release/1.0.0/logic-grid-puzzle-team-1.0.0-agent-group.zip | 7d81dc589061607be905361e9c71e60058b6b40c0ce947622118ca498f99765e | 30517 |

All 21 payload files match source, native, wrapper and final installed files. Wrapper has exactly `<slug>-1.0.0/plugin.yaml` plus the same-name native inner directory. CRC, duplicate/traversal/absolute paths, symlinks, per-file hashes, compression ratio <=50 and GitHub size <=95MiB checked. See release artifact and tests/records/package-verification.json. No third-party distributable material or dependency is bundled.

Official Hub CLI 0.0.1 at c8ee4ef44be0453470114aa5a19f4e1017462907: init --type agent-group, validate and pack passed. build_packages.py records the invocation route; CLI ZIP is compressed, native ZIP is stored. Source and both exact ZIP dynamic-JS preflights pass (zero JavaScript files/signatures). The first shell Python lacked PyYAML; rerunning the unchanged preflight with the actual host environment passed. No dependencies were installed or changed.

Initial unconfirmed archives are preserved under .local/draft-packages after correcting two sample-name mentions from campus to the actual garden-tea-party example. No user testing had occurred; final hashes above supersede those drafts. A packaging assertion originally assumed a slug-only outer directory; inspection confirmed the CLI uses slug-version, and the assertion was corrected without changing archive bytes. No historical evidence was deleted.

## Business tests

`python3 -B -m unittest discover -s expert-teams/logic-grid-puzzle-team/tests -p test_puzzle.py -v`: **22 passed**, zero skips. Same 22 tests passed against exact extracted final ZIP; raw output at tests/records/extracted-tests.txt. Includes all 31 nonempty subsets of the five-clue fixture, complete permutation-vs-DFS solution-set agreement, 3/4-item unique cases, ambiguity with two real counterexamples, contradictory/no-vacuous-proof cases, changed Chinese negation, unknown fields, invalid bounds/references, duplicate keys, invalid UTF-8, nonfinite/deep/oversized JSON, Chinese CLI errors, escaped HTML without answer leakage, stale/forged review and explanation tampering, FIFO no-block, traversal/symlink rejection, no overwrite, partial writes without a success audit, and bundled example equality.

Mathematical explanation uses all numbered clues as premises and checks every answer relation across the nonempty complete solution set. It is explicitly not a minimal human deduction chain, calibrated difficulty measurement or proof that arbitrary natural-language clues were understood.

## Actual host/loader and assembly

WorkSwarm source 0.2.8 @fa91394e42a7af731424222db82b02351e694de9; installed SDK0.1.20; actual host Python3.13.5. Official creator --validate-only and load_agent_group_package_bundle pass for four complete members. Positive and three negative creator cases are in tests/records/loader-validation.json: missing member manifest, missing Leader AGENT.md and invalid member Skill frontmatter are rejected. Initial helper environment missed host PYTHONPATH; corrected. Creator emits its result on stderr, so helper captures combined output. Neither issue required host changes.

Final native ZIP was imported/installed using supported agent_groups.import_local/install/show/list operations. Installed 21-file map equals the final ZIP. Actual member assembly verifies only shared puzzle-collaboration plus that member's private workflow Skill; existing native bash/file/task/delegation tools are available. Scripts are member-owned resources, not invented SDK Tool registrations. See host-import.json, host-loader.json and role_execution in each host record.

## Real integration with a scripted loopback model

| Fixture | Complete count | Delivery | Evidence |
| --- | --- | --- | --- |
| Three items | 1 | produced | tests/records/host-execution-three.json |
| Four items | 1 | produced | tests/records/host-execution-four.json |
| Ambiguous | 24 | refused, Exit2 | tests/records/host-ambiguous.json |
| Inconsistent | 0 | refused, Exit2 | tests/records/host-inconsistent.json |

All four cases used final native hash, actual build_team/create_task, all three member claims/completions, own/shared Skill reads, real member bash calls and 224 WebSocket events per case. Author copies original synthetic fixture; Modeler runs installed model.py; Reviewer receives learner.json as its command input and runs its separate installed review.py; Leader runs actual deliver.py. Output file hashes and refusal/no-delivery checks are recorded. Fixed responses do not establish natural-language reasoning, absolute blind context isolation, educational quality, same-model advantage or user acceptance. No paid model/API calls were made.

## Isolation and browser QA

Final URL http://127.0.0.1:6535/; state .local/host-manual-final/. Separate loopback model6536, backend28535, web29535. prepare_workspace(migrate_config=False), no credentials/config copied, no inherited provider keys. Only owned earlier fixture processes were stopped between cases; Main/other services and checkouts were unchanged. Source host/SDK/shared dependencies were not edited.

Browser verified Experts -> My Experts -> Expert Teams, installed Chinese team, version1.0.0, all four members, five listed Skills and Chinese README rendering. Upload dialog correctly requires native package_type agent_group. Automated file selection timed out; extension upload permission prevented completion, so **GUI file-upload completion is unverified**. Supported management import passed. Screenshots in evidence/1.0.0/ are engineering QA, not original user test evidence.

Four-item learner HTML from actual host output was served temporarily read-only on6537 for browser inspection: Chinese text, numbered clues and blank grid render correctly, no answer section. That preview server was stopped. Actual answer.md and audit.json exist separately. Screenshot engineering-puzzle-preview.png records layout; engineering-installed-team.png records installation.

## Build handoff and limits (historical state before user confirmation)

At the initial Build handoff, status was Ready for Testing. User needed to configure an authorized real model in this isolated instance; the default loopback provider is visibly scripted and cannot establish semantic acceptance. Follow MANUAL_TESTING.md, verify genuine original authoring/review on changed vocabulary and key failure cases, then explicitly confirm exact version/hash and provide original current-version screenshots. At that Build handoff no user pass or screenshot was claimed. Full GUI upload and real-model reasoning remain manual checks. No push, PR, merge, Release, Hub action or Asset Ledger change.


## User manual testing confirmed — 2026-11-17

Cai Zhenze explicitly confirmed manual testing of this unchanged Chinese 1.0.0 package complete and passed in the current Main4.0 conversation, and authorized Phase3. See USER_TEST_CONFIRMATION.md for the actual statement, exact native/wrapped hashes, date/time limits and screenshot association. Six original PNGs are preserved byte-for-byte with original filenames and full resolutions under evidence/user-testing-1.0.0/. All21 files in the actual manual installed package equal reviewed source/native/wrapper.

Actual user-run campus model v3 produced1 solution by both shipped algorithms. The independent learner-only review, learner source, rendered HTML and teacher answer match recomputation. The user screenshots show native tasks, Skill reads, actual modeler/reviewer calls, invalid-ID repairs and artifact delivery. Repair inputs changed; package bytes did not. An additional host-spawned puzzle-packager helper and separately labeled host_provenance audit annotation are disclosed; neither changes the4-role package or mathematical certificate. Read-only independent evidence verification is recorded in tests/records/manual-package-verification.json.

No known package blocker remains. Original images were reviewed for readability/current-task association/privacy before upload. Full GUI upload is not separately shown, and educational difficulty/minimal-clue guarantees remain out of scope. User confirmation now supersedes the earlier pending-acceptance state. GitHub delivery may proceed; Project Lead acceptance remains pending. No paid calls, Hub action or Release.
