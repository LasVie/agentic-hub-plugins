# Source and reuse review — Offline Optics Lab

- Reviewed: 2026-10-30.
- Candidate: CAND-EXT-003. Task: AH-20261030-offline-optics-lab. Owner: Cai Zhenze.
- Identity mapping: Ray Optics Simulation → 离线光学实验室 → `offline-optics-lab`.
- Approved scope: bounded offline, editable 2D geometric optics; plugin-only integration.
- Mode: `ported`; permission status: `verified` for the explicitly listed material.
- Upstream: https://github.com/ricktu288/ray-optics
- Fixed revision: `811f508d2b070898c241a568b0c167dcb8645251`; upstream package.json identifies version `5.4.0`.
- Retrieval: immutable GitHub codeload archive for that commit, inspected in designated scratch `/private/tmp/optics-upstream-20261030/`.

## Permission and distribution

The pinned root LICENSE is the complete Apache License 2.0. Each selected original source file has the Apache-2.0 header and `Copyright 2024 The Ray Optics Simulation authors and contributors`. Root/subtree license and NOTICE search found the root LICENSE and no separate NOTICE file. The exact selected originals and license are bundled under `offline-optics-lab/licenses/ray-optics/`; SHA-256 values are recorded in provenance.json. Upstream website branding or package metadata alone was not used as evidence. No additional restricted media or third-party implementation is copied.

Apache-2.0 permits modification and distribution subject to its terms. The modified numerical module preserves the applicable attribution/license header, carries a prominent dated modification notice, and ships the full license and original selected files. THIRD_PARTY_NOTICES.md explains the source mapping and scope. This review does not select a unified repository license, claim upstream endorsement, or certify patents/trademarks.

## Exact reuse and meaningful adaptations

| Upstream path | Delivered use |
| --- | --- |
| `src/core/geometry.js` | Copied byte-for-byte as `engine/geometry.mjs` (extension only); original also preserved |
| `src/core/sceneObjs/LineObjMixin.js` | Selected finite-segment/forward-ray intersection checks adapted in `engine/core.mjs` |
| `src/core/sceneObjs/lightSource/SingleRay.js` | Selected emission direction and equal initial s/p components |
| `src/core/sceneObjs/lightSource/Beam.js` | Selected midpoint sampling/perpendicular direction; explicit count replaces viewport-dependent density and random-angle behavior |
| `src/core/sceneObjs/mirror/Mirror.js` | `onRayIncident` reflection formula adapted |
| `src/core/sceneObjs/glass/IdealLens.js` | `onRayIncident` two-focal-plane geometry adapted; arbitrary orientation and signed focal length retained |
| `src/core/sceneObjs/glass/PlaneGlass.js` | Incident-side and normal construction adapted |
| `src/core/sceneObjs/glass/Glass.js` | Straight-edge intersection/incident-side behavior reviewed; deterministic winding replaces random probing, no arcs |
| `src/core/sceneObjs/BaseGlass.js` | Vector Snell/Fresnel and total internal reflection adapted; no merging/GRIN or stochastic low-power display amplification |
| `src/core/sceneObjs/other/Detector.js` | Signed power/normal/shear/bin accumulation adapted with endpoint clamp |
| `src/core/Simulator.js` | Closest-intersection composition reviewed; a new bounded queue records real segments and disclosed lost power, not a bundled full Simulator class |

All originals listed above remain unmodified as source/attribution evidence. The new orchestration is deliberately not described as an independent clean-room engine: it is a selected Apache-licensed port. It handles arbitrary supported geometry composed by the user rather than a set of preset-angle formulas. Examples are original synthetic scenes, not copied upstream gallery content.

## Dependency and host boundary

The complete upstream app lists i18next, i18next-http-backend, seedrandom, mathjs, bezier-js, canvas2svg, Vue, Bootstrap, Ace and build packages. Those package implementations are neither installed nor bundled. Retained evidence files contain their original imports but are not executed. Executed imports are exactly `engine/cli.mjs` → `engine/core.mjs` → `engine/geometry.mjs`; they use no npm package, network, filesystem or model operation. Browser rendering uses the plugin's own UI and the same engine through the plugin's native-tool/loopback service interface.

Runtime requirement: an existing Node.js >=18 executable, in addition to the plugin's documented Python runtime. No system installation, package patch, monkey-patch, host frontend/backend/SDK edit, other-plugin edit or installation script rewriting host files is part of this implementation. Node absence is reported explicitly; it is not repaired through host modification. Source modules are the executable deliverable, so no generated/minified bundle or npm build is required for reproducibility.

## Bounded behavior and acceptance evidence

Supported whitelist: SingleRay, Beam, Mirror, IdealLens, PlaneGlass, straight-edge Glass and Detector. Unknown fields/types, remote/background/module/formula/GRIN inputs, non-finite numbers, touching/nested glass, ambiguous vertices and emission from an optical boundary are rejected. Bounds: 32 objects, 16 polygon vertices, 256 initial rays, 5000 segments, 80 interactions per branch, ~3-second engine budget, 128-KiB CLI request. Low-power/limit truncation sets a flag and reports lost relative power. No result is substituted after an error.

Targeted repository tests in `tests/test_offline_optics_engine.py` exercise Snell's law and Fresnel energy conservation, total internal reflection, planar mirror reflection, converging/diverging and rotated lenses, repeated glass slab interactions, winding invariance, detector distributions changing after a composed-scene edit, power-normalized beam sampling, endpoint/one-sided detection, occluded/shared-boundary ordering, invalid scene/CLI inputs, and mirror-cavity termination. Engine self-tests are distinct from running WorkSwarm backend registration, browser interaction and the user's pending manual acceptance; those results belong in TEST_REPORT.md.

This is an ideal, monochromatic, two-dimensional geometric optics model using relative units. It omits diffraction, interference, absorption, dispersion, curved surfaces, GRIN, equations, full upstream JSON compatibility and hardware/laser safety certification. Detector sign and repeated-crossing semantics are explicit in engine/README.md and the Chinese package. The full upstream web application and its richer feature set are not claimed.

## Final archive review (2026-10-30)

Extracted both 1.0.0 archives with `verify_package.py`: 26 identical UTF-8 payload files, declared tools/skill present, 12 license/source-evidence hashes match provenance, Apache attribution and modified-module notices retained. No media, npm libraries, tests, caches or credentials are in either runtime payload. Actual extracted examples and edited-lens behavior passed. Canonical path: `releases/agent-plugin/offline-optics-lab/1.0.0/offline-optics-lab-1.0.0.zip`; SHA-256 `a45ab514eb845631a3cc6855532888368ab134b81af60fee4e66bdecc8fb1a6f`. Native companion: `plugins/offline-optics-lab/test-packages/offline-optics-lab-1.0.0-workswarm.zip`; SHA-256 `5634e3e37c9a53920e59567cd81bce9df42677e18944ba0b2f539b9602785511`. Both contain the same reviewed implementation; only wrapper differs. Source directory, archives, installed host files and SDK-test payload hashes agree.
