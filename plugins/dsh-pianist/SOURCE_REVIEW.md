# Source review

Owner: Song Haoran. Candidate: CAND-DSH-192.

Source: https://github.com/Laplace-bit/dsh-pianist at `6ab631567700efa80a954f33eb5534b265d91ddd`. The complete root MIT license covers the selected implementation modules; no conflicting nested license or header was present in those copied modules. The original license text/copyright is bundled unchanged at `licenses/dsh-pianist/LICENSE` and its SHA-256 is recorded in provenance.json. This review concerns these pinned files and this port, not the entire marketplace or future upstream revisions.

Actually reused files: vendor/audio/generated-piano.ts, vendor/core/errors.ts, vendor/core/normalizer.ts, vendor/core/performance-payload.ts, vendor/core/performance-state.ts, vendor/core/tempo-map.ts, vendor/core/timeline-index.ts, vendor/core/timeline.ts, vendor/core/transpose.ts, vendor/core/types.ts, vendor/core/validator.ts, runtime/engine.mjs, runtime/player.js. Full TypeScript source accompanies compiled derivatives. The runtime does not bundle npm SDKs, service clients, third-party UI assets or recorded audio packs. Node.js is a host prerequisite. esbuild 0.25.12 is a development-only compiler; its executable is not included in either ZIP. WorkSwarm's own Python Tool/Rail interfaces are referenced as host APIs. This does not assert a unified license for repository-owned work.

Scope/modifications: Chinese WorkSwarm edition; DeepSeek registration/UI removed; native Tool adapter, local file boundaries, atomic updates and Chinese help/errors added. See bundled THIRD_PARTY_NOTICES.md. All original MIT conditions remain attached. No external accounts or paid service calls are required.

Verification: source paths and license hashes checked against the pinned checkout. Extracted final-package checks, actual functional tests and WorkSwarm evidence are recorded in TEST_REPORT.md before handoff. Source-review status does not claim Hub approval, user completion or legal certification.

Naming map: upstream/candidate `dsh-pianist` -> Chinese display name `离线钢琴演奏` -> internal slug `dsh-pianist`. Native extracted payload matched all installed source files byte-for-byte; complete MIT license hash was verified in the extracted archive. Native test ZIP: `dist/dsh-pianist/1.0.0/dsh-pianist-1.0.0-workswarm.zip`, SHA-256 `ab958ffb941b5e94653f250e1cdb33535146ca9cb694178423d961ec95443a1e`. Canonical wrapper is built separately from the exact same tested payload; final wrapper path/hash are recorded in artifact.json and the handoff manifest.
