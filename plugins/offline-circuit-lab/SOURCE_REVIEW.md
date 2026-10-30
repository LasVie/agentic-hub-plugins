# Source review — 离线电路实验室 1.0.0

Reviewed 2026-10-28 for Cai Zhenze, Candidate `CAND-EXT-001`, Task `AH-20261028-offline-circuit-lab`. The user approved a bounded offline, editable RLC circuit simulator. This is Phase 2 local Build; no user manual-test completion, GitHub delivery, Project Lead acceptance, Release or Hub operation is claimed.

Naming: **CircuitJS1** → **离线电路实验室** → `offline-circuit-lab`. Internal asset identity: `repo:agent-plugin:offline-circuit-lab`.

## Fixed source and actual reuse permission

- Official upstream: <https://github.com/pfalstad/circuitjs1>, fixed revision `e952e788a4135a693bfd4cee7883f9b3314e3e76`. The inspected `ts/CirSim.ts` identifies `5.0.3ts`; the commit, rather than the mutable default branch or package metadata version, pins this review.
- Downloaded archive: <https://codeload.github.com/pfalstad/circuitjs1/tar.gz/e952e788a4135a693bfd4cee7883f9b3314e3e76>; SHA-256 `e9e6d8dba599172290c734bd5c38e52b70c2db732ddbe67709260d6b9dd261a5`.
- The four selected TypeScript source files each begin with the original `Copyright (C) Paul Falstad and Iain Sharp` notice and an explicit GNU GPL **version 2 or, at the recipient's option, any later version** grant. Root `README.md` independently gives the same grant. This is the basis for the `GPL-2.0-or-later` conclusion for the actual reused code.
- Root `COPYING.txt` is the complete GPL version 2 text. Its original bytes are bundled as `licenses/circuitjs/LICENSE`, SHA-256 `8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643`. Full original selected files, including unmodified attribution and permission headers, are also included under `licenses/circuitjs/upstream/`.
- `ts/package.json` contains a generic `ISC` field. It does not override the explicit GPL notices in the selected source files and is not used as permission evidence. A public repository alone is not the reuse conclusion.
- Mode is **ported**, permission status **verified** for the specifically mapped numerical routines below. The Python port retains the original copyright notice, a prominent dated modification notice, GPL terms, warranty disclaimer and license path. No invented copyright ownership or repository-wide relicensing is asserted. Distribution of this derived numerical code remains subject to GPL terms, including corresponding-source availability and preserved notices; the package contains its readable source.

## Exact source mapping

Line ranges refer to the pinned upstream revision. Complete originals are bundled for attribution and inspection, not as runtime imports or a claim to ship the complete upstream application.

| Original path | SHA-256 of complete original | Adapted logic in `runtime/solver.py` |
| --- | --- | --- |
| `ts/ResistorElm.ts` | `f8e4c560a87788b8552e570d386ecf003f027ebda0c2643e7707cbec3bb150e4` | Lines 119–126: resistor current from terminal voltage difference and resistance; conductance stamping. |
| `ts/CapacitorElm.ts` | `84d78ee77eed8c0318894f98ef358285d4d20b3104ea0dff317fdac13feabc5d` | Lines 182–228: backward-Euler/trapezoidal Norton conductance, previous-voltage/current history source, current reconstruction and current-source stamping. |
| `ts/Inductor.ts` | `2256ebc668b53444995ad4680301f1530befd2922d2dc63c1413ad9d102e5794` | Lines 64–118, linear branches only: backward-Euler/trapezoidal Norton conductance, history current and reconstructed current. Saturation and nonlinear branches are excluded. |
| `ts/SimulationManager.ts` | `7754d920a638ed735948608dea391616eb357c84387c80f882e0a6ff4c907949` | Lines 1257–1315: voltage-source, conductance and current-source MNA stamps; lines 1692–1770 and 1785–1820: dense Crout LU factorization with pivoting and forward/back substitution. |

The sole adapted runtime implementation is `runtime/solver.py`; `provenance.json` additionally lists the four verbatim bundled originals. GPL is not bypassed by translating these routines into Python.

## Changes and exclusions

The port solves arbitrary supported connected networks from explicit node/component data, rather than selecting preset formula outputs. For each transient step it assembles the modified nodal-analysis equations, stamps Norton companions, solves the coupled linear system and reconstructs branch currents. The linear matrix is reused between equal-step iterations.

Actual adaptations:

- Standard-library Python replaces the TypeScript runtime and its application-wide classes. Source/terminal orientation is explicit: `Va − Vb = value`, with positive branch current from `a` to `b`.
- All capacitors start at zero voltage and inductors at zero current. The returned `t=0` sample is the **pre-step** zero state. All ideal voltage sources step simultaneously immediately after that sample. First-step backward Euler initializes history; subsequent steps use trapezoidal companions. The upstream's default capacitor 1 mV seed is not used.
- Direct or chained ideal-source/capacitor constraints that require an instantaneous capacitor-voltage jump are rejected. Singular or inconsistent ideal-source systems, floating networks and non-finite inputs fail explicitly; the solver does not invent a leakage path or perturb a singular diagonal.
- Optional tool/API DC analysis treats capacitors as open circuits and inductors as ideal zero-volt constraints. It does not copy upstream's 100 MΩ capacitor leakage approximation. The current Chinese browser editor is intentionally a transient editor; the documented numerical API also supports DC.
- Row normalization, a near-zero-pivot rejection, a reconstructed matrix residual check and physical KCL checks were added. KCL allows absolute `1e-12 A` plus relative `1e-7` tolerance; this prevents silently losing small branch currents next to large companion conductances while tolerating floating-point cancellation near steady state. These checks do not establish a general engineering accuracy guarantee.
- Input limits: 24 components; 16 nodes including ground `0`; at most 5000 equal timesteps; duration an integer multiple of the timestep; explicit finite SI parameter ranges. Results beyond ±10⁶ V/A or failed numerical checks are rejected. Chinese validation and limitations are returned to the caller.
- The plugin-specific Chinese interface, host-tool wrapper, local loopback service, state handling, export actions and tests are new task-specific code. They do not import or translate CircuitJS's full editor, graphing UI, browser assets or third-party helpers.

Excluded from reused implementation and runtime dependencies: sparse EJML/Apache code, `lz-string`, `canvas2svg`, fonts/icons/images, upstream circuit/example datasets, optional LDRElm/Thermistor code, nonlinear and semiconductor models, saturation, AC frequency sweep, full CircuitJS application classes, Node/npm/Vite build, Java/GWT, Electron and hosted web services. The four original evidence files naturally retain references/import names from their original context; those files are not executed, and their referenced implementation trees are not copied. No permission assertion is made about materials outside this selected scope.

## Plugin-only integration and distribution

Runtime requirements are macOS/Linux with Python 3.11+, the target host's already installed supported `openjiuwen` Tool/ToolCard extension interface, and a desktop browser. Numerical solving uses the Python standard library only. The host SDK is neither patched nor bundled/relicensed. No pip/npm runtime installation or model/account/network service is needed for the plugin's circuit computation.

All implementation belongs to this plugin; additional repository changes are limited to its tests, review/test documentation, provenance and release packaging. No host/core/frontend/backend, installed dependency or another plugin is rewritten. Supported extension installation and configuration are separate from modifying the host. Host/SDK and website verification results must be reported in `TEST_REPORT.md`; source review alone is not proof of running-host compatibility.

The readable adapted Python source, local web source, tool/manifest definitions, original license text and upstream attribution evidence are included in the package. No minified/compiled-only numerical deliverable is substituted for corresponding source. The original selected GPL notices and full license must remain in distribution. This adapter is not an official CircuitJS release or endorsement and does not grant trademark or unrelated-content permissions.

## Verification evidence and remaining gate

`python3 -m unittest discover -s tests -p test_offline_circuit_solver.py -v` passed 20 numerical functional tests on 2026-10-28. Tests cover a divider and DC power balance, arbitrary multisource bridge/KCL, RC parameter and topology edits, parallel capacitors, RL and underdamped RLC analytic responses, halved-step convergence, DC capacitor/inductor treatment, 5000-step steady state, floating/singular/inconsistent/ill-conditioned rejection and input bounds.

For a 5 V step, 1 kΩ/1 µF series RC, 10 µs step, the result at 1 ms was `3.160526606529667 V`; changing resistance to 2 kΩ gave `1.9673120463966265 V`. These are actual solver results, not proof of browser/host/manual testing. Neither packaging nor numerical self-tests satisfy the user's manual-testing gate. Current package hashes, extracted-payload checks, browser/host evidence and later user confirmation belong in the task's test report and tracker; do not invent them here before they exist.

## Final extracted-package distribution check — 2026-10-28

Canonical archive `releases/agent-plugin/offline-circuit-lab/1.0.0/offline-circuit-lab-1.0.0.zip`, SHA-256 `f588be67bf47de305e5622c671e017fc53e2f54c1aa4acc634ddc27b7b23fab7`, and native companion SHA-256 `66075b03aacacd969c37d1f70c6ed64fc331b76de20788860daf242b5d9f2f05` were extracted/inspected. Their 15 payload files are identical to source. All five license/source-evidence hashes match provenance; the GPL source header and dated change notice are present. Full preferred-source Python/JavaScript, original selected source evidence, complete GPL text and Chinese THIRD_PARTY_NOTICES are included. The Chinese interactive footer names Paul Falstad/Iain Sharp, the GPL-2.0-or-later terms and lack of warranty, and links to the exact bundled license through a fixed read-only endpoint. No unresolved reuse condition was identified within this narrow selected scope; this does not assert permission for excluded upstream material or license the entire repository. See package-verification.json and TEST_REPORT.md for separate functional/host checks and remaining manual-testing gate.
