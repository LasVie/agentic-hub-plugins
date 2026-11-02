# 离线观星规划台 v1.0.0 — Build verification

Task AH-20261030-offline-observing-planner; CAND-EXT-005; Cai Zhenze. 2026-10-30. Branch feat/offline-observing-planner from b3dad00f. This report distinguishes the original Build verification from the user manual-testing confirmation recorded below on 2026-11-02.

## Functional verification

`python3 -B -m unittest discover -s plugins/offline-observing-planner/tests -p 'test_*.py' -v` covers three groups. Tests were executed in their focused groups; no unrelated repository suite was required.

- 12 engine tests passed: all7bodies/289maximum samples, UTC/fixed-offset invariance, shifted-interval consistency, exact partial endpoint,1second duration, polar no-event intervals, twilight root residuals, rise-set vs airless convention,2000/2100limits and malformed/out-of-range inputs. These are behavioral tests, not independent accuracy evidence.
- 5 independent reference tests passed:38JPL Horizons airless topocentric observations,6USNO solar/lunar/civil events, and a future time-scale diagnostic. Fixed numerical facts/query/hash provenance are in tests/fixtures; no runtime network.37position comparisons are within0.313305arcmin. Moon2100-12-30 differs1.395233arcmin; explicit fixture budget2arcmin. Matched JPL time scale reduces it to0.015534arcmin. No uniform1arcmin guarantee. Reported issue383 Mercury/Mars case independently matches within0.03424/0.01436arcmin; this does not prove all possible cases fixed. USNO minute-rounded events max28.365seconds against60second budget.
- 10 real runtime tests passed: loopback HTTP/direct calculation consistency; start/reuse/status/stop; explicit overwrite and save/readback; corruption preservation; Host/Origin/token/traversal rejection; invalidUTF8/oversizedJSON; symlink/foreign installation protections; a real10second child timeout followed by OS-confirmed child termination. Loopback tests require sandbox permission; an initial sandbox-denied bind was an environment failure, then unchanged tests passed with localhost allowed. Latest UTF8/32KiB check rerun passed.

Environment: macOS arm64, systemPython3.10 for pure engine/runtime tests; actual WorkSwarmPython3.12.14/openjiuwen0.1.19 for supported native SDK verification. Declared packagePython3.11+; no added package dependency.

## Chinese browser and files

Actual local UI testing in the in-app Chromium browser: Chinese rendering, Singapore2026-10-30T12:00Z calculation49samples×7bodies, six-hour slider move, changing latitude cleared old charts/table and disabledCSV, saving/loading restored parameters, reload preserved disk plan, JSON export/import roundtrip invalidated old results. CSV exported343rows; every UTC/name/numeric coordinate matched a fresh engine calculation within1e-12. After the small revision-aware save-message adjustment, JavaScript syntax and browser reload/save/read/recalculation passed. Browser proof remains in ignored dist, not runtime ZIP or user acceptance evidence.

## SDK, running WorkSwarm and packaging

Source-payload real public DeepAgent.load_plugin registered2native tools+1Skill, then12registered Tool.invoke calls passed (calculation,changedUTC,rejection,start/status/restart/stop). External socket connections denied in verifier; no model/chat calls. SDK verification is a separate process, not execution inside the running WorkSwarm chat worker.

The final installed payload was separately checked with the same public SDK: 2 native tools + 1 Skill registered and 12 real invocations passed; its file hashes match the final package. No model request was made. See sdk-verification.json.

The running isolated WorkSwarm frontend http://127.0.0.1:6393/ returned HTTP 200; backend port 29310 and frontend-proxied WebSockets passed ping/pong. Supported import_local/install/catalog succeeded and all 13 installed payload files match the native ZIP. Existing five plugins' files/catalog and model configuration hashes remained unchanged. No host code edits or service restart. Actual Extensions UI showed the installed Chinese card, and its Create / Upload form opened with ZIP/TAR support. Installation used the same supported backend API; a second browser upload was unnecessary. No generic native Tool.invoke request exists in the inspected WS interface; actual chat-worker execution remains a user manual check. See host-verification.json and local extensions-proof.png.

Format check and pack passed using the existing WorkSwarm venv Python (system Python lacks PyYAML; no package was installed). verify_package.py passed: exact canonical/native/source payload equality, archive integrity, 13 declared UTF-8 files, full pinned MIT license/module hashes, manifest/tool/Skill paths, artifact SHA, extracted all-seven-body calculation, shifted-time results and Chinese input rejections. No screenshots, SDK logs, caches or test state are inside either ZIP.

- Canonical ZIP SHA-256: 64903378e0b7906a0a9b178ff2046cf66d273c9f54a7e551497a48813a099ef9.
- Native companion SHA-256: 6e9d379e35ce0b5a7d8e2d373c5eab3668cbbd091f47895ae340997749fb9b68.

Chinese package instructions and provenance are inspected independently from functional outcomes. MANUAL_TESTING.md gives exact paths, hashes and an actual-tool prompt. At the 2026-10-30 Build handoff, user/model conversation and final manual testing were pending and delivery was not yet authorized; the dated confirmation below supersedes that status. Dedicated SDK test services stopped; the UI QA service is stopped after recording evidence. The existing isolated WorkSwarm stays running.

## Known limitations

Only bounded2000–2100 solar-system observing planning; no star catalog/weather/terrain/guaranteed visibility/navigation/telescope control. Airless curves and refracted limb rise-set use distinct labeled conventions. Upstream reduced maintenance and futureUTC/ΔT assumptions are disclosed. DesktopmacOS/Linux only;Windows/mobile notverified. Supported host Extensions import and separate SDK invocation cannot be substituted for actual user chat use. The Build verification made no paid calls, host/dependency/other-plugin patches or delivery actions. GitHub delivery is authorized by the dated user confirmation below; no Release or Hub action is authorized.

## User confirmation and Phase 3 review — 2026-11-02

User test confirmation: “I confirm manual testing of 离线观星规划台 v1.0.0 passed.” Confirmed by Cai Zhenze in the current conversation on 2026-11-02 (Asia/Singapore; exact message time unavailable). Task AH-20261030-offline-observing-planner; candidate CAND-EXT-005. Canonical ZIP SHA-256 `64903378e0b7906a0a9b178ff2046cf66d273c9f54a7e551497a48813a099ef9`; tested native companion `6e9d379e35ce0b5a7d8e2d373c5eab3668cbbd091f47895ae340997749fb9b68`. No known blocking issue remains. GitHub delivery only is authorized; Project Lead acceptance is still pending. Confirmation record: RPT-20261102-offline-observing-planner-confirmed, linked to the original task.

Seven original PNGs were received and preserved byte-for-byte in ignored local evidence storage. The chat image at 11.43.43 contains private local session credentials and is retained locally, excluded from public upload. The six safe UI originals below show the Chinese name/version, empty initial state, actual displayed Singapore/Beijing calculations, and synchronized time-slider/chart/numeric changes. They corroborate the package association and visible results; screenshots alone do not prove backend tool invocation, all acceptance steps, numerical accuracy or every saved/exported result. Explicit user confirmation is separate from these visible facts.

| Original filename (2026-11-02) | SHA-256 | Dimensions |
| --- | --- | --- |
| Screenshot 2026-11-02 at 11.43.55 AM.png | d675f63efc0d84da677103740d6cb2bcd99a84d69b0b975f71382d918134b83b | 982×1630 |
| Screenshot 2026-11-02 at 11.44.14 AM.png | b7f0b9b64ac0220d52678e7c742c92c9c0b60fc3f6a192be133e79c3aa223f3b | 984×1882 |
| Screenshot 2026-11-02 at 11.44.28 AM.png | fdcbff0e956c487d1167e187dc681287a1a62a2a2f6ab640c68af32688fc0e96 | 996×1886 |
| Screenshot 2026-11-02 at 11.44.42 AM.png | b66b446a31d25464d4929fafa913a4a0fe923a359ac2fc15b2f681d6e0db1ef9 | 990×1898 |
| Screenshot 2026-11-02 at 11.46.26 AM.png | b02c9819119c3d850a9d4da17db5b9aaef632afcd3a5a2f387c4c05c1186d669 | 1004×1878 |
| Screenshot 2026-11-02 at 11.46.41 AM.png | 09be03a894cefb847822b4d86daff46c5d19bb5dc75523df2bf219fc7317772e | 980×1886 |

Latest main was fast-forwarded to 2794b5ac18b270aa871b15a1b6ad02dcf899b774 with unrelated worktrees preserved. Delivery review found no required payload change; the 27 functional tests, 12 registered SDK invocations, running-host and browser evidence above remain applicable. Only outside-payload confirmation/source-review documentation and artifact metadata are refreshed. Package reinspection verifies both unchanged archives, all 13 source/runtime files and license coverage. Six safe originals must be attached directly to the delivery PR and verified before merge. No screenshot is inside either plugin ZIP. Contributor handoff remains distinct from Song Haoran's acceptance.

Submission-time commands (2026-11-02): `python tools/asset_release.py check plugins/offline-observing-planner`, `pack` and `check-repo` passed using the existing Anaconda Python 3.13.5/PyYAML after the prior temporary venv was found absent; no dependency was installed. `python3 -B plugins/offline-observing-planner/verify_package.py` passed against the exact archives and extracted numerical runtime. Both ZIP hashes remained unchanged; artifact.json report hashes were refreshed. Repository-wide structural check covered 55 source assets / 65 release ZIPs. Existing unaffected functional/host/browser tests were reused; CI is recorded separately in the PR.
