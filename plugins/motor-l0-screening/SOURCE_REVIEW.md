# Source and distribution review

Reviewed 2026-10-23 by Song Haoran task agent.

dsh-motor-ai-l0 → 电机方案粗筛 → `motor-l0-screening`.

Candidate: CAND-DSH-135; task: AH-20261023-motor-l0-screening.

Pinned source: https://github.com/wangxuewangxue98/dsh-motor-ai-l0@45769d11b4b996e51429ccaeffcfeb06d0bf3229. Selected license: MIT; full texts and SHA-256 evidence are in payload and provenance.json.

Actual core1.4.1 registry integrity verified. Only four pure core modules copied; stale lib/formula-engine.mjs from L0 repository excluded. Pure buildParamMatrix port omits DSH registration and local quota/usage calls under MIT; bounded to120 candidates. No hosted paid service, telemetry, experience upload, surrogate model or solver. Formula validity limitations retained.

Permission conclusion: reuse permitted for the declared bundled paths subject to retained full notices; this is an operational source review, not a representation that a label grants trademark/service rights. Team-owned adapter code has no new unified licensing decision.

Build/test evidence: TEST_REPORT.md (created after actual execution). Native install ZIP and Hub-wrapper ZIP must have identical inner payload hashes. Keep local pending explicit current-package user completion; no Hub publication or PR implied.

Final archive review2026-10-23: verified every declared license-evidence SHA-256 against extracted runtime bytes, preserved full upstream texts and applicable authorship/notices, and confirmed source/native/Hub/installed payload identity. Selected reuse paths and modification/exclusion scope are enumerated in provenance.json and THIRD_PARTY_NOTICES.md. Local functional and delegated desktop/visual evidence are linked from TEST_REPORT.md. User authorized exact1.0.0 GitHub submission/merge by `pr合入`; no Hub action was requested.
