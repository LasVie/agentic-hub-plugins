# Offline Circuit Lab — local Build verification

- Candidate: CAND-EXT-001; Task: AH-20261028-offline-circuit-lab; Owner: Cai Zhenze.
- Mapping: CircuitJS1 → 离线电路实验室 → `offline-circuit-lab`, version 1.0.0.
- Branch: `feat/offline-circuit-lab`, based on updated main `0c1a735`.
- Date: 2026-10-28 (Asia/Singapore). Phase 2 only. User manual testing has **not** been completed or claimed.

## Scope and source

A bounded, editable offline RLC numerical simulator: true node/component topology, MNA transient/DC calculations, Chinese interactive browser editor/waveforms, explicit workspace save/reload, JSON circuit import/export and CSV numerical export. The numerical routines are a GPL-2.0-or-later port of the precisely mapped CircuitJS1 sources at `e952e788a4135a693bfd4cee7883f9b3314e3e76`. The four selected original source files, full license and attribution are bundled. See SOURCE_REVIEW.md and provenance.json.

All implementation is inside this plugin. No host/core/frontend/backend/SDK/installed dependency/other-plugin patch or host-rewriting installation script is required. Runtime uses Python standard library plus the host's existing Tool/ToolCard interface. Test helpers use the already installed host environment; no package installation or paid/model call was made.

## Numerical and local-service functional checks

Final command (Python 3.12 host environment, with localhost binding permission):

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/state-machine-audit-workswarm-20261026/venv/bin/python -m unittest discover -s tests -p 'test_offline_circuit*.py' -v
```

**27 passed**: 20 numerical cases plus 7 runtime/input cases. Numerical tests include analytical divider/power balance, RC/RL/underdamped RLC response, timestep convergence, arbitrary multisource bridge/KCL, actual topology changes, parallel capacitors, 5000-step boundary, DC capacitor/inductor behavior and explicit invalid/floating/singular/inconsistent/ill-conditioned failures. Actual RC at1ms (5V,1kΩ,1µF,10µs step) was3.16052660653V; changing to2kΩ produced1.96731204640V.

The real plugin-owned HTTP workers verified Chinese UI, actual numerical response, saved-circuit readback, invalid-save preservation, private permissions, symlink refusal, wrong-token/path rejection, Host/Origin rejection, request bounds, session reuse, verified stop and the exact bundled license endpoint. The initial sandbox-only run could not bind loopback; the same tests passed after authorized loopback execution. A development-only bytecode cache was removed before packaging. A child-reaping thread was added before final tests; final run has no subprocess ResourceWarning. Focused peer review also found a stop/restart race: stop now verifies shutdown before returning success under the launch lock. A real immediate-restart regression confirms a distinct live new session; the final 27-test run passed.

## SDK execution

The initial standalone SDK check registered two native tools and one Skill, executed seven actual registered Tool.invoke calls, confirmed divider2.5V/2.5mA, unconfirmed-start refusal, start/status session identity, Chinese UIHTTP200 and stop/unload. A verification-helper assumption about SDK-suffixed tool IDs was corrected before calls; it was not a plugin defect. Raw development results remain in ignored dist.

Final extracted-package SDK, browser, running-backend installation and archive evidence are recorded below. These are distinct layers: SDK success is not proof of the running WorkSwarm chat worker invoking the tools; installed/connected metadata is not proof of execution. The user's actual chat and browser tests remain pending.

## Limits and manual gate

macOS/Linux, Python3.11+, supported native-tool host and desktop Chrome. At most24 components,16 nodes including ground and5000 fixed timesteps. Ideal linear R/L/C and simultaneous ideal voltage steps with zero initial energy only; no semiconductor/SPICE file import, nonlinear/AC sweep, parasitic/device-rating or hardware-safety certification. Numerical accuracy depends on timestep and conditioning. Browser editor exposes transient simulation; the tool also exposes DC. Model-facing traces are explicitly truncated to12sample previews; full samples are available in the browser/CSV.

The loopback session URL contains a private local token. It is excluded from committed evidence; users should conceal the address bar in screenshots. State belongs only to the chosen dedicated workspace; saving explicitly replaces its one plugin circuit record. There are no screenshots or runtime state in the release ZIP.

Manual instructions: MANUAL_TESTING.md. Stop at manual-testing handoff. No commit, push, PR, merge, Release or Hub action is authorized in this phase.

## Browser interaction evidence

Actual Chrome UI actions against the plugin-owned service verified RC response (4.9663 V at 5 ms with 1 kΩ; 4.5896 V after editing to 2 kΩ), stale-result clearing and disabled CSV after editing, divider 2.5 V → 3.75 V after editing R2 to 3 kΩ, then 3 V after adding a parallel 3 kΩ branch. Save and refresh restored all four components and parameters while requiring fresh simulation. A disconnected branch produced the Chinese floating-network error and no waveform. RLC preset produced 2501 samples, displayed peak 5.815 V and final 5 V; Chinese UI and schematic were visually inspected.

CSV and JSON exports created real browser downloads. CSV contained 101 data rows, the expected Chinese headers, and the actual final voltage 3.0000000000000004 V; JSON preserved the four-component edited topology. The browser automation download-event waiter timed out even though the file had downloaded; filesystem readback supplied the evidence. Native confirm-dialog automation also stalled; the plugin now uses an accessible in-page confirmation dialog, verified through preset switching and saving. No host/browser security setting was changed. JSON file-chooser re-import remains a manual-test item; no successful automated import is claimed. See browser-verification.json.

## Final ZIP and installed-host verification

Canonical: `releases/agent-plugin/offline-circuit-lab/1.0.0/offline-circuit-lab-1.0.0.zip`

SHA-256: `f588be67bf47de305e5622c671e017fc53e2f54c1aa4acc634ddc27b7b23fab7`

Native WorkSwarm: `plugins/offline-circuit-lab/test-packages/offline-circuit-lab-1.0.0-workswarm.zip`, also copied into `dist/offline-circuit-lab/1.0.0/` for the user.

SHA-256: `66075b03aacacd969c37d1f70c6ed64fc331b76de20788860daf242b5d9f2f05`

`asset_release.py check` and `pack` passed. `build_test_package.py` derived the native ZIP from the canonical inner payload. `verify_package.py` checked all 15 runtime files against source and both ZIPs, declared paths/version, UTF-8 decoding, full license/source evidence hashes, absence of runtime state/caches/screenshots, and actual extracted-source Chinese RC calculation/error paths. Canonical and native ZIP payloads are byte-identical. Packaging is not a claim of Hub acceptance.

Final SDK check used the native ZIP's extracted manifest root, registered two tools and one Skill and executed **9 actual Tool.invoke calls**. It verified the exact divider result, explicit-start denial, start/status identity, Chinese page, confirmed shutdown, immediate restart into a new live session, final stop and unload. See sdk-verification.json. A first command used an incorrect nested extraction path; this harness-only command error was corrected without changing the package.

Existing isolated WorkSwarm at **http://127.0.0.1:6393/**, backend port29310: frontend HTTP200, direct/proxied WebSocket ping/pong, supported `plugin_packages.import_local/install/show` all passed. All 15 installed payload files match the exact native ZIP and final SDK extraction. Chrome Extensions shows the Chinese plugin, its Skill and both tool cards; the Create/Upload dialog opens. Installation used the supported backend API; OS file-chooser upload was not exercised.

Host source: 6098 tracked files match `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`; installed openjiuwen0.1.19 has 2726 checked code/config files matching distribution records. Model configuration SHA-256 stayed `7c5d0dcb0b1e408f3f89102677c5fdb1923b5d73f5f6b4dcde061fc5820939fb`. Existing ebook and word-citation plugin payloads/catalog were unchanged. No host service restart or host/dependency/other-plugin modification. See host-verification.json for supported integration points and exact evidence.

The host exposes no supported generic native-tool-invocation RPC, so no test endpoint or fake-model conversation was introduced. Actual running-chat-worker tool invocation, JSON browser re-import and user-operated acceptance remain pending in MANUAL_TESTING.md. No model calls were made. Current state: **Ready for Testing**, candidate Planned, owner Cai Zhenze. No manual completion, delivery or acceptance is asserted.


## User confirmation and Phase 3 gate — 2026-10-30

User test confirmation: "I confirm manual testing of 离线电路实验室 v1.0.0 passed." Confirmed by Cai Zhenze in the current conversation on 2026-10-30, Asia/Singapore (exact message timestamp is not exposed). Task `AH-20261028-offline-circuit-lab`; Candidate `CAND-EXT-001`; canonical ZIP SHA-256 `f588be67bf47de305e5622c671e017fc53e2f54c1aa4acc634ddc27b7b23fab7`; native tested ZIP SHA-256 `66075b03aacacd969c37d1f70c6ed64fc331b76de20788860daf242b5d9f2f05`. Known blocking issues: none reported. The user explicitly authorized Phase 3 GitHub delivery only, with no Release or Hub operation. This dated confirmation supersedes the historical manual-testing-pending statements above without rewriting their original test scope. Tracker confirmation Report ID: `RPT-20261030-offline-circuit-lab-confirmation-102`.

Five original screenshots were received and preserved locally without recompression. The 10.29.34 chat screenshot displays v1.0.0, the reported 2.5 V / 0.0025 A tool result and matching start/status session identity. It also contains a local access credential, so it is retained privately and excluded from the public PR. The four credential-free simulator originals below are the public Test Screenshot evidence. They visibly show the Chinese v1.0.0 UI, edited component values, numerical results, waveforms and probe selection. Screenshots do not independently prove backend tool invocation; explicit user confirmation, prior SDK/host checks and screenshot observations remain separate evidence.

| Original filename | Dimensions | SHA-256 | Visible result |
| --- | --- | --- | --- |
| Screenshot 2026-10-30 at 10.29.48 AM.png | 2120 × 1960 | `78a81200258b1411cf5c874164fa3618a09a2aa9864b7026fb069d87375867a1` | Edited RLC network; 2501 samples; node 3 about 48.681 V at 5 ms. |
| Screenshot 2026-10-30 at 10.30.03 AM.png | 2112 × 1982 | `4b6901a0df4d0fc2dcfb34f3437b66745ca0fb70ff2fea19949534a326552265` | 5 V divider with 1 MΩ / 1 kΩ; about 0.004995 V. |
| Screenshot 2026-10-30 at 10.30.22 AM.png | 2094 × 1970 | `0ce6cf92bfb3009a757e1b27365ac1ba44d43b6792d9ec65c9f528a620e83796` | 500 V ideal RC simulation; 1001 samples; node 2 about 496.63 V at 5 ms. |
| Screenshot 2026-10-30 at 10.31.05 AM.png | 2118 × 1924 | `05cd8993d3574f1ec110f741de8fd775637e3c61f3db7f9568279353d0001884` | Same ideal RC circuit with node 1 selected; 500 V source trace. |

Filenames above retain the original wording; the actual macOS filename uses a narrow no-break space before AM. The screenshots show simulated values, not physical hardware testing or safety validation. No screenshot is placed in either plugin ZIP or the source tree. The PR evidence comment and tracker will hold the verified attachment permalink.

Pre-delivery review rechecked all current source, ZIP, manifest, license and provenance hashes, and reused unchanged functional/browser/SDK evidence. The feature branch was fast-forwarded to current main `400e1e72bd26f2cc703cecff43915ddf864fd28a`; incoming changes do not alter this plugin or its packaging mechanism. Source and both ZIPs are unchanged. Only this report, its artifact hash and plugin-specific byte-preservation attributes are updated for delivery. Runtime state, downloaded exports, raw logs and private screenshots stay outside the Git tree. CI remains a separate pre-merge requirement. Project Lead acceptance is pending; no Completed/Delivered status or official catalog entry is asserted.

### Phase 3 CI import-cache regression — 2026-10-30

PR #62 initial CI ran 549 tests successfully (90 dependency-gated skips), then
`check-repo` rejected development files. Reproduction in a clean temporary HEAD
extraction showed that the circuit test imports generated `runtime/__pycache__`
inside the payload. Only the two repository test modules changed: their direct
imports now temporarily suppress bytecode and restore the previous setting.
All 27 circuit tests then passed with normal interpreter settings and local
loopback access; the following asset check passed with zero payload caches.
The packaged runtime, Chinese UI, canonical ZIP and WorkSwarm ZIP are unchanged.
This test-isolation correction does not alter the user-tested behavior.
