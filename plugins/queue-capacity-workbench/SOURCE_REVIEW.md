# SimPy source and integration review

Reviewed 2026-11-10 for Cai Zhenze, task AH-20261110-queue-capacity-workbench. Candidate ID: Not Applicable (approved independent external route; no candidate invented). Mapping: **SimPy 4.1.2 → 离线排队容量实验台 → queue-capacity-workbench**. Internal identity repo:agent-plugin:queue-capacity-workbench.

## Pinned material and permission

- Official https://gitlab.com/team-simpy/simpy tag 4.1.2, code commit `f43816490c6f76f336ad6e457d3cab9f386894af`. Phase 1 checked the tag via the official GitLab API. Build downloaded official PyPI 4.1.2 metadata, wheel and sdist; SHA-256 matched metadata and Phase 1 pins.
- Wheel `simpy-4.1.2-py3-none-any.whl`: `43071f84b6512c9b4fcb33ef057f240ccb1d1f3b263f9b4f9229d072e310b372`.
- Source `simpy-4.1.2.tar.gz`: `76ef36b71e0436ba94e55febc001c78879e493a323f045bbcfbb0b216e9b1fbc`.
- Full MIT license inspected in source and wheel: Copyright (c) 2013 Ontje Lünsdorf and Stefan Scherfke (also see AUTHORS.txt). Permission includes redistribution subject to retaining notice and permission text. Full disclaimer retained. Source distribution actually names the author file AUTHORS.rst; retained unchanged. No separate NOTICE in either archive.
- Reviewed every Python module/header under src/simpy and wheel simpy/: core, events, exceptions, rt, util and all resource modules. The source contains no nested license or separate per-file rightsholder terms in these paths. Whole wheel, including metadata, py.typed and original license, copied unchanged into private vendor/. Per-file equality is an extracted-package test. No upstream examples, tests, docs, media, icons, datasets or fonts copied.
- pyproject.toml: Python >=3.8, runtime dependencies []; setuptools>=64 and setuptools_scm>=8 are build-only, not bundled. Plugin itself requires existing Python3.11+ and POSIX/macOS/Linux lifecycle. No package installation on host, no binary/native library or network computation. Vendored distribution metadata preserves actual __version__ lookup.
- Reuse permitted for these files under MIT; provenance mode ported, permission verified. Required texts at licenses/simpy/{LICENSE,AUTHORS.rst}, mirrored original wheel license. Hashes in provenance.json. This does not assign a new license to repository-owned work or imply trademark endorsement.

## Repository ownership and supported integration

Implementation confined to this plugin. Existing owner Cai Zhenze. Native manifest declares two Tool subclasses and one Skill. Tool consumers are WorkSwarm selected-plugin loader → DeepAgent.load_plugin → Tool.invoke. Real queue computation occurs in a fresh `python -I -B` process with its own vendor path; the host process's dependency resolution and sys.path are untouched. Worker denies socket activity. Inputs are bounded declarative JSON; no Python/JS/HTML execution or arbitrary expressions.

Own solid-mesh-workbench@89967f5 supplies the maintained private directory/file-lock lifecycle, authenticated ephemeral loopback service, fixed assets, origin/host checks, bounded subprocess cancellation/output and verified stop mechanism. Adapted only into this plugin; other plugin source unchanged. A new worker owns finite FIFO modeling and CSV; web/ owns original timeline/replay UI without third-party JS/CSS. Existing host native ZIP APIs and SDK interfaces are exercised separately in test records; a standalone plugin UI is not claimed as a host theme or host patch.

Baseline comparison from the approved review is retained: live traffic stress-testing asset 77909c7e4fdd4b0ea0243251998f8c30@1.0.0 generates load, not finite discrete-event capacity traces. Matter.js PR77 models mechanics, FET PR34 audits timetables, state-machine PR49 checks state behavior. They do not supply this FIFO experiment. Recheck on kickoff found no queue/SimPy task or conflicting selection; Calibre review Notes mention this external recommendation but remain unclaimed. Current merged grant proposal, score, F1 and study-coach deliveries add no queue simulator. No shared team rules, prior plugin, host code or environments are modified.

## Distribution review

Both wrapped and native archives must contain identical reviewed payload bytes, complete MIT notices and Chinese documentation. Tests and packaging records outside payload document extracted-file equality, license hashes, preflight and execution. Runtime state, downloads, caches and host dependencies remain in the task-owned /private/tmp/main3-queue-capacity-20261110 tree and are excluded from ZIPs. No paid calls, delivery push, PR, Release, merge or Hub action in Phase 2. User testing remains required for the exact handed-off hashes.
