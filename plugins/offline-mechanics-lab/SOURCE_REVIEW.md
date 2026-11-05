# Matter.js → 离线力学实验室 → offline-mechanics-lab

Reviewed 2026-11-02 for CAND-EXT-011, AH-20261102-offline-mechanics-lab; owner Cai Zhenze.

## Reuse decision

Mode: ported; permission_status: verified. Upstream https://github.com/liabru/matter-js, version 0.20.0, commit `8a67787735585f02c4b46eabf7b9fcc1c7c321da` (annotated tag `64e44bead8f3c92baa1573b906488511a75ef30a`). Read the pinned root LICENSE, build/matter.js header, package.json and repository file tree. The root MIT grant and the complete embedded MIT header cover the copied engine. Copyright (c) Liam Brummitt and contributors. No separate NOTICE or additional license in the selected core path. This review is about the exact copied paths, not every upstream example or media asset.

Only `build/matter.js` is copied, unmodified, to `assets/vendor/matter.js`; SHA-256 `016f108075a42e8bb8f75c43cf5b6d9f07b1d88857975ed9d96b0ede921416ce`. Full root license is bundled as `licenses/matter-js/LICENSE`; SHA-256 `ed182087be5b26734aa6d4789743de3a97417950e8c1e3ff2e3d19c6462720d3`. The engine's original header is retained. No upstream images, fonts, demo UI, MatterTools, resurrect-js, SVG parser, concave decomposition, or remote scripts are included. Pinned package.json has no runtime dependencies. Build/dev dependencies are not needed or bundled.

The lab, validation, scene format, UI, worker and tests are repository-owned additions; this document makes no repository-wide relicensing decision. The private loopback lifecycle is adapted locally from maintained offline-observing-planner/runtime/lab.py at main `856284cb52e1e10f916a1bb98aa43a56254b9e9d`, with its protections retained and astronomical computation removed. Other plugins are unchanged.

## Supported integration and scope

Native manifest-declared Tool/ToolCard and Skill; ordinary WorkSwarm local-package import/install. Python standard library serves only this plugin's assets and explicitly saved scene on 127.0.0.1. Matter.js runs in a browser worker with no model call, external request, host patch, dependency installation, or SDK patch. Node is a development-test tool only. macOS/Linux with Python 3.10+ and desktop Chrome are the test targets; Windows is not supported by the POSIX lifecycle implementation.

Rectangles, polygon-approximated circles, static bodies and distance/pin constraints; bounded body count, duration and fixed timestep. Screen-world units are not calibrated SI units. The iterative solver has finite error, can tunnel at high speeds, and is not an engineering/safety validator. Restitution is a relative normal velocity coefficient, not an energy-retention fraction. No arbitrary JavaScript, scripts in imported JSON, SVG/concave geometry, motors, fluids, 3D, online collaboration or host modification.

The closest existing assets are physics-review reasoning/image-crop and Invaders' fixed game physics; neither supplies this editable collision/constraint experiment and numerical sampling flow. Circuit, optics and observing labs calculate different systems. Packaging and functional evidence are recorded in TEST_REPORT.md after validation; user testing is pending.

## Final distribution inspection (2026-11-02)

Canonical v1.0.0 ZIP SHA-256 `b69f0177931df25d7103aede52ac8e2177cc5e8e5ff252d36ac48edd724f758b`; native companion SHA-256 `e850a5458ea3fb7ef22b31bdfd79f68482f6144ed17508e1d86e4fa4bdf69319`. Extracted contents and installed payload have the same 13 runtime files. The unchanged engine hash, full original MIT text, embedded header and Chinese attribution were verified in both ZIPs. No additional media or runtime dependency was introduced. Current WorkSwarm local installation and standalone SDK registration passed without host changes; actual chat-worker and manual browser acceptance remain pending. See TEST_REPORT.md and package-verification.json.
