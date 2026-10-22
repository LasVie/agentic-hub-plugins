# Source review

Owner: Song Haoran. Candidate: CAND-DSH-036.

Source: https://github.com/Ox0400/dsh-vault at `deebe535663e17db5daf94683888e17928ec74e6`. The complete root MIT license covers the selected implementation modules; no conflicting nested license or header was present in those copied modules. The original license text/copyright is bundled unchanged at `licenses/dsh-vault/LICENSE` and its SHA-256 is recorded in provenance.json. This review concerns these pinned files and this port, not the entire marketplace or future upstream revisions.

Actually reused files: vendor/crypto.ts, vendor/totp.ts, runtime/engine.mjs. Full TypeScript source accompanies compiled derivatives. The runtime does not bundle npm SDKs, service clients, third-party UI assets or recorded audio packs. Node.js is a host prerequisite. esbuild 0.25.12 is a development-only compiler; its executable is not included in either ZIP. WorkSwarm's own Python Tool/Rail interfaces are referenced as host APIs. This does not assert a unified license for repository-owned work.

Scope/modifications: Chinese WorkSwarm edition; DeepSeek registration/UI removed; native Tool adapter, local file boundaries, atomic updates and Chinese help/errors added. See bundled THIRD_PARTY_NOTICES.md. All original MIT conditions remain attached. No external accounts or paid service calls are required.

Verification: source paths and license hashes checked against the pinned checkout. Extracted final-package checks, actual functional tests and WorkSwarm evidence are recorded in TEST_REPORT.md before handoff. Source-review status does not claim Hub approval, user completion or legal certification.

Naming map: upstream/candidate `dsh-vault` -> Chinese display name `本地凭据保险库` -> internal slug `dsh-vault`. Native extracted payload matched all installed source files byte-for-byte; complete MIT license hash was verified in the extracted archive. Native test ZIP: `dist/dsh-vault/1.0.0/dsh-vault-1.0.0-workswarm.zip`, SHA-256 `2911404a57c3a55fe8f46973ec80bfe9d719e8b0d9d94854c03453dc8b3026a6`. Canonical wrapper is built separately from the exact same tested payload; final wrapper path/hash are recorded in artifact.json and the handoff manifest.
