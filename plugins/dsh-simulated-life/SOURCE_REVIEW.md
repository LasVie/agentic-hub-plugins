# Source review

Owner: Song Haoran. Candidate: CAND-DSH-047.

Source: https://github.com/john-walks-slow/dsh-simulated-life at `93cbc648fa4efb6da11513aff9eaf7888db94105`. The complete root MIT license covers the selected implementation modules; no conflicting nested license or header was present in those copied modules. The original license text/copyright is bundled unchanged at `licenses/dsh-simulated-life/LICENSE` and its SHA-256 is recorded in provenance.json. This review concerns these pinned files and this port, not the entire marketplace or future upstream revisions.

Actually reused files: vendor/deduplication.ts, vendor/formatter.ts, vendor/loader.ts, vendor/types.ts, runtime/engine.mjs. Full TypeScript source accompanies compiled derivatives. The runtime does not bundle npm SDKs, service clients, third-party UI assets or recorded audio packs. Node.js is a host prerequisite. esbuild 0.25.12 is a development-only compiler; its executable is not included in either ZIP. WorkSwarm's own Python Tool/Rail interfaces are referenced as host APIs. This does not assert a unified license for repository-owned work.

Scope/modifications: Chinese WorkSwarm edition; DeepSeek registration/UI removed; native Tool adapter, local file boundaries, atomic updates and Chinese help/errors added. See bundled THIRD_PARTY_NOTICES.md. All original MIT conditions remain attached. No external accounts or paid service calls are required.

Verification: source paths and license hashes checked against the pinned checkout. Extracted final-package checks, actual functional tests and WorkSwarm evidence are recorded in TEST_REPORT.md before handoff. Source-review status does not claim Hub approval, user completion or legal certification.

Additional changes: loader constrains day directory names and skips malformed event records; deduplication prunes expired records even when no active events remain.

Naming map: upstream/candidate `dsh-simulated-life` -> Chinese display name `本地模拟生活` -> internal slug `dsh-simulated-life`. Native extracted payload matched all installed source files byte-for-byte; complete MIT license hash was verified in the extracted archive. Native test ZIP: `dist/dsh-simulated-life/1.0.0/dsh-simulated-life-1.0.0-workswarm.zip`, SHA-256 `d4f8679550432e7a72f9f5f08d13d92f50a5822ad7bb4339048730e00b64d774`. Canonical wrapper is built separately from the exact same tested payload; final wrapper path/hash are recorded in artifact.json and the handoff manifest.
