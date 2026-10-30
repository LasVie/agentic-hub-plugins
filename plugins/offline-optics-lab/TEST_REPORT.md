# 离线光学实验室 1.0.0 — Verification and manual acceptance

Date: 2026-10-30. Owner: Cai Zhenze. Candidate: CAND-EXT-003.
Task: AH-20261030-offline-optics-lab. Branch: `feat/offline-optics-lab`.
Identity: Ray Optics Simulation → 离线光学实验室 → `offline-optics-lab`.

## Scope and environment

Plugin-only selected Apache-2.0 numerical port at upstream commit
`811f508d2b070898c241a568b0c167dcb8645251` (5.4.0), Chinese UI/native tools.
No host/core/SDK/dependency/other-plugin edits or model calls. Existing isolated
WorkSwarm frontend 6393/backend 29310 is reused through supported package APIs.
Python 3.12.14/openjiuwen 0.1.19; Node 22.23.3 (host) and 24.19.0 (existing fallback).
Node must already exist; no runtime library or npm install.

## Completed verification

- `python3 -m unittest discover -s tests -p test_offline_optics_engine.py -v`:
  **18 passed**. Snell/Fresnel, TIR, mirror, converging/diverging/rotated lenses,
  slab reflections/winding, composed geometry edit affecting detector bins,
  power-normalized beam sampling, endpoints/one-sided detector, occluded nearest
  boundary ordering, ambiguous boundaries, source-boundary rejection, strict
  schema/CLI/finite input limits and bounded mirror cavity termination.
- `PATH=<existing Node 22 bin>:/usr/bin:/bin:/usr/sbin:/sbin <host-python> -B
  tests/test_offline_optics_runtime.py -v`: **12 passed**. Also passed on existing
  Node 24 fallback. Real subprocess/server lifecycle, numerical HTTP execution,
  save/restart, confirmation, missing runtime, Host/Origin/token isolation,
  corrupt/symlink preservation and foreign installation refusal. Initial test
  listener failure was a sandbox restriction; approved loopback run passed.
- `verify_sdk.py <payload> --workspace <new test directory> --output <report>`:
  source-payload verification **14 real Tool.invoke calls passed** after
  DeepAgent.load_plugin registered two tools and one skill. All five examples,
  rejected unsupported input, start/status/reuse/stop/restart and HTTP 200 tested.
  External network denied by audit hook; no model invoked. Repeated against the
  exact installed payload using host Node 22.23.3: 14/14 passed; payload hashes match
  archives and source. See sdk-verification.json.
- `python tools/asset_release.py check plugins/offline-optics-lab`: passed under
  existing host Python (with PyYAML). Shell Python lacks PyYAML; nothing installed.

Additional independent real CLI comparisons passed: Brewster-angle unpolarized
reflection 0.07396449704142019 versus analytic 0.07396449704142012; front-focal-plane
output slope −0.2, inside-focal slope 0.5, diverging-lens slope 1; reversed detector
power +1/−1 with one hit and consistent bin sums. These are numerical checks,
not browser/manual evidence.

## Build defects corrected before package handoff

The local child-process argument count was corrected before service verification.
Nearest-boundary ambiguity now considers only final nearest intersections, so an
occluded shared vertex cannot spuriously reject an earlier hit. The regression is
order invariant. UI JSON import is bounded to the same 128 KiB as the service.
PlaneGlass shading was also aligned to the current fitted viewport after independent review. All these changes preceded user testing; no prior 1.0.0 artifact was handed off.

## Package and supported host verification

- Canonical ZIP SHA-256: `a45ab514eb845631a3cc6855532888368ab134b81af60fee4e66bdecc8fb1a6f`.
- Native WorkSwarm ZIP SHA-256: `5634e3e37c9a53920e59567cd81bce9df42677e18944ba0b2f539b9602785511`.
- `asset_release.py pack`, `build_test_package.py`, `verify_package.py`: passed.
  Exact 26-file payload equality, archive CRC/path/version, UTF-8, declared files,
  license hashes, extracted five examples and changed-lens distribution verified.
- `verify_workswarm.py --install`: supported live import/install succeeded.
  Frontend HTTP 200, direct backend and frontend-proxied WS ping/pong verified.
  Installed card is 离线光学实验室 1.0.0. All 26 installed hashes match the ZIP.
- Other four plugins/catalog entries and 93 file hashes remained unchanged.
  Configuration SHA-256 before/after:
  `7c5d0dcb0b1e408f3f89102677c5fdb1923b5d73f5f6b4dcde061fc5820939fb`. No host process restart.
- Browser inspection of actual Extensions → My Extensions showed the installed
  Chinese plugin, two tool declarations and its skill. Create → Upload File entry
  was visible. Installation itself used the supported backend import API; the
  native OS ZIP-selection dialog was not exercised. No chat/model request sent.

## Chinese language and UI

Packaged descriptions, README, Skill, editor controls, examples, errors and boundary
messages use Simplified Chinese. Compatibility keys and required original
Apache texts/source notices remain intact. Chinese scene/object names passed
extracted and SDK tests. Browser UI confirms readable Chinese controls/results.
Actual browser checks passed for refraction 1.5→2 (signed detector power
−0.958477→−0.887046), lens 9-rays/27-segments/power 1, stale-result clearing,
Chinese invalid-geometry error, expanded glass shading, save/reload and
CSV/JSON download. Actual exported lens JSON validated/retraced to power 1 and 9
hits; CSV contains 20 Chinese-header data rows. Browser file-picker reimport
remains unverified: automation hung and was stopped, so no UI roundtrip pass is
claimed. Direct pointer dragging, every preset in the UI and responsive layouts
also remain manual checks. The numerical/service tests cover their underlying
supported geometry, schema and persistence separately. See browser-verification.json.
AI proof image: dist/offline-optics-lab/1.0.0/browser-proof.jpg (not user evidence).
Dedicated SDK/QA workers were stopped; WorkSwarm is left running.

## Build handoff status (historical, before user testing)

No current-package manual testing or user/model conversation has occurred in this
Build. Native-only WorkSwarm `connected` status mirrors installation and is not
proof that the chat worker has invoked these tools. The live WS schema exposes
package management but no generic native Tool.invoke RPC; no test endpoint,
fake model or monkey-patch is introduced to claim such a test.

Manual acceptance must demonstrate the current ZIP/version's real WorkSwarm
calls, optical edits/results, persistence and exports. Original screenshots should
hide the localhost URL token. Packaging checks are not functional/manual testing.

Limits: ideal monochromatic 2D ray optics and relative power only; no full-wave,
3D, curved glass, overlapping glass, upstream arbitrary scene format or hardware
certification. Limits/truncation are reported. See the packaged Chinese README.

## User confirmation and original evidence — 2026-10-30

User test confirmation: “I confirm manual testing of CAND-EXT-003 — 离线光学实验室
v1.0.0 passed.” Confirmed by Cai Zhenze in the current conversation on
2026-10-30; recorded 16:01:39 Asia/Singapore (message time is not exposed).
Task: AH-20261030-offline-optics-lab. Confirmation report:
`RPT-20261030-offline-optics-lab-confirmation`.

The canonical ZIP remains `a45ab514eb845631a3cc6855532888368ab134b81af60fee4e66bdecc8fb1a6f`;
the tested native ZIP remains `5634e3e37c9a53920e59567cd81bce9df42677e18944ba0b2f539b9602785511`.
The identical 26-file source, canonical/native and installed payload association
was rechecked. No packaged source, wrapper, localization or version changed.
Known blocking issues: none reported or demonstrated. User confirmation resolves
the manual-testing gate; it does not rewrite the narrower historical AI results.

Six original PNGs were received. Five credential-free originals at 15:51:28,
15:51:42, 15:52:16, 15:52:49 and 15:53:14 show the v1.0.0 optical workbench:
glass/lens composition with explicit truncation, total internal reflection,
modified source geometry, moved lens/changed detector distribution and edited
refraction brightness. They corroborate visible interactive results, not every
acceptance operation or backend tool invocation independently. The 15:51:15 chat
original contains a localhost session credential and is preserved privately,
excluded from public delivery. Original bytes/hashes are retained locally; the
five safe originals are attached directly to the delivery PR evidence comment.

GitHub-only delivery is authorized. No Release, Hub operation or paid model call
is authorized or performed. Project Lead acceptance remains pending.
