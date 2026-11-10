# Engineering test report — 2026-11-10

CAND-EXT-013; AH-20261110-offline-pipe-network-workbench; owner Cai Zhenze. EPANET JavaScript Toolkit → **离线管网水力工作台** → `offline-pipe-network-workbench`, version **1.0.0**. Phase 2 engineering record retained; see the dated Phase 3 confirmation below for subsequent user testing.

## Exact packages

| Form | Path | SHA-256 |
| --- | --- | --- |
| Native WorkSwarm installation | `test-packages/offline-pipe-network-workbench-1.0.0-workswarm.zip` | `1414048b02e90649ed7708035fd2be68715b1fa5189b58686d33f11b397be6df` |
| Canonical Chinese wrapper | `../../releases/agent-plugin/offline-pipe-network-workbench/1.0.0/offline-pipe-network-workbench-1.0.0.zip` | `dd16d4fe65be52c55a3f379a2014e69cdc11e3f1a6eb8e730e9091668bc1d3f6` |

The 33-file source, native ZIP, extracted canonical inner payload and actual installed payload have identical path/SHA-256 maps. Both ZIPs are uncompressed, CRC-valid, and contain the original license texts. Legal evidence hashes match provenance.json. `package-verification.json` is the exact inventory. Neither SDK/browser tooling, host snapshots, model credentials, generated outputs nor runtime records are in the payload.

## Executed checks

- `python tools/asset_release.py check plugins/offline-pipe-network-workbench`: passed.
- `python tools/asset_release.py pack plugins/offline-pipe-network-workbench`: passed. Native/canonical extracted identity and Chinese README, Skill, display name, interface, errors and UTF-8 examples inspected.
- `python tools/asset_release.py preflight <native ZIP>` and `<canonical ZIP>`: **7 JavaScript modules scanned, 0 known dynamic-JavaScript signatures**, including all vendor JS. Original vendor hashes are unchanged. This is the maintained local gate, not official Hub acceptance.
- `node --test plugins/offline-pipe-network-workbench/tests/test_engine.mjs`: **7 passed**, Node 24.11.1 as development-only tooling; actual bundled OWA-EPANET 2.3.5 WebAssembly engine.
- `python -B -m unittest discover -s plugins/offline-pipe-network-workbench/tests -p test_runtime.py -v`: **11 passed**, real temporary loopback servers on macOS. Covers status without state creation, confirmation refusal, start/reuse/stop/restart, concurrent launch, idle exit, foreign/corrupt/hardlinked/symlink records, foreign listener preservation, instance identity, traversal/MIME restrictions and genuine user-click cross-origin entry navigation.
- `tests/browser.cjs <installed SDK-returned URL> <task scratch>`: passed in isolated headless desktop Chrome. Real solving, diagram selection, diameter edits, flow sensitivity, four actual downloads, model JSON reimport, duplicate-key rejection, restore/error recovery, negative pressure, actual non-convergence rejection, delayed-example freshness, and edit-during-run worker termination. Browser emitted **0 outside-origin requests and 0 page errors**. Chinese full-page screenshot visually inspected; it is engineering evidence, not a user-test screenshot. See `browser-verification.json`.

### Independent numerical expectations and observed values

The single-pipe fixture is 100 m long, 100 mm diameter, H-W C=100, reservoir head100 m, junction elevation0 m and demand1 L/s. Independent metric H-W using coefficient10.67 predicts **0.0435676785 m** loss; actual EPANET gives **0.0435542957 m**, within the declared0.1% coefficient tolerance, flow **1.0000000000000782 L/s** and junction head/pressure **99.9564457043 m**. Doubling diameter predicts loss reduced by `2^4.871`; the independent result is about0.00148884 m and engine about0.00148838 m. Full-precision JSON/CSV are checked; the UI rounds for readability.

Branch withdrawal sums, equal parallel paths, two-loop symmetry and signed headloss around the loop agree within declared tests; loop demand16 L/s and continuity residual below1e-6 L/s. Increasing P1 diameter from110 to200 mm increases its computed flow. Raising the single junction elevation to101 m produces actual negative-pressure warning6, preserved in exports. An intentionally ill-conditioned bounded loop with demand1000 L/s per junction, alternating10/3000mm diameters and100000/0.1m lengths yields actual **epanet_110**; no valid result/export is offered and the next valid model recovers. Unknown fields, duplicate keys (including escaped-equivalent keys), invalid ranges, disconnected nodes and unsupported structures reject rather than being silently dropped.

## Supported installation and integration

Fresh task-owned WorkSwarm **0.2.5.beta1**, source commit `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`, Python3.12.14 / openJiuwen0.1.19. Frontend `http://127.0.0.1:6431/`, backend29431, agent28431, auxiliary gateway30431. Separate code copy, data, home, logs, ports, cache and installed-plugin directory; no Main environment is reused or modified. Source inventory unchanged during verification. Dependency distribution files were physically copied, unmodified, from an already installed same-revision test dependency set;3013 SDK files were hash-compared. No dependency patch or shared runtime-state reuse. Fresh locked fetch initially failed; retained only in task scratch as setup evidence.

`verify_workswarm.py` exercised real running-backend `plugin_packages.import_local`, `install`, `list` and `show` through public WebSocket RPC, both frontend proxy and direct backend. Frontend HTTP200, ping/pong and installed version/name passed. Native ZIP and installed33-file map agree. Other plugin catalogue/files and model configuration unchanged during final verification. The visible Extensions panel is also inspected separately.

The exact installed manifest resolves through public `load_plugin_package` / `resolve_plugin_parts`; one real Tool and one Chinese Skill, no MCP/rails/subagents. Actual `Tool.invoke` status, confirmation rejection, start/reuse/status/stream and owned stop pass. A separate installed-tool-started QA service returned one actual URL, reused unchanged, and passed the full browser suite. This is **installed public SDK execution in a separate process**, not model-driven running-chat dispatch. An Extensions `connected` label alone is not native-tool execution proof. See `host-verification.json` and MANUAL_TEST.md.

Initial isolated launch accidentally retained template model settings and an auxiliary default port; its gateway exited on an occupied port without touching the existing listener. Automatic placeholder image probes reached example.com and failed405, with no valid provider credential or paid call. Corrected **only this task's runtime settings** to loopback:9 and explicit `react.enable_read_image_multimodal=false`; restarted only verified task-created processes. Failed logs retained. No host source, shared dependency or other plugin was changed, and no model request is used by the final installation/SDK/browser checks.

## Engineering review and remaining limits

Reviewed owner/callers, native registration, version/root/instance identities, lock and file ownership, browser input freshness, solver disposal, warnings and serializer boundaries. Reused the maintained lifecycle mechanism; the plugin's static server admits the unmodified `_engine.mjs` filename without allowing traversal or links. A delayed example/file read cannot overwrite newer input. Two redundant example copies were consolidated into canonical `web/*.json`. No obsolete standalone solver, generic command endpoint, generated JS evaluator, host hook or automatic install patch is included.

At the engineering-test checkpoint, actual running-chat tool dispatch and user browser acceptance remained pending. A same-model baseline A/B session was not run; no paid model calls are authorized. Compatibility is verified only for the stated unmodified host/SDK snapshot, macOS/POSIX and current Chrome; newer WorkSwarm0.2.8, Windows and other browsers are unverified. Launch requires Python3.11+ and `fcntl`/POSIX checks. The resource server expires after1800 seconds without resource requests; purely local browser calculations do not refresh that timer.

Bounded fixed-demand H-W steady state, one reservoir,50 nodes/80 pipes maximum,64KiB input,12-second worker budget. Negative-pressure demand-driven results do not prove real supply. No pumps, valves, tanks, water quality, controls, extended period, arbitrary INP or real-infrastructure certification. Browser cancellation and stale-result protection are tested; the12-second timeout has a fixed termination path but was not separately forced in a slow-machine browser test. No Hub submission/acceptance or GitHub delivery was claimed at the engineering-test checkpoint.

## User manual confirmation and Phase 3 gate — 2026-11-10

Cai Zhenze explicitly confirmed manual testing of 离线管网水力工作台1.0.0 complete and passed in this conversation, with six original PNGs. See USER_TEST_CONFIRMATION.md for the faithful statement, exact ZIP identities, original dimensions/hashes and observed scenarios. The first image shows actual WorkSwarm tool status/start/reuse/status returning version1.0.0 and one consistent URL; further images show the single-pipe fixture, double loop and changed diameter/demand scenarios. This resolves the pending user manual-testing gate within the approved scope. No new payload or wrapper change was made; both ZIP hashes remain unchanged. Previously passing unaffected engineering checks are reused. No blocker reported; documented compatibility/scientific limits remain. Delivery status and permanent screenshot evidence will be recorded in the original live task/PR.
