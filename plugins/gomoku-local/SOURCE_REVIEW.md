# Source and distribution review

Reviewed 2026-10-23 by Song Haoran task agent.

dsh-gomoku → 本地五子棋 → `gomoku-local`.

Candidate: CAND-DSH-336; task: AH-20261023-gomoku-local.

Pinned source: https://github.com/omdsh-dev/dsh-gomoku@26fdf6e99c95447f250ab51478fbc694b6024e8d. Selected license: MIT; full texts and SHA-256 evidence are in payload and provenance.json.

Pure winsAt/isLegalMove/hasEmpty port and original TypeScript subset bundled; DSH HTTP/provider/UI hooks excluded. Wrapper enforces board, turn, coordinates and revisions. HTML is a read-only snapshot; current conversation model chooses moves through native tool. No independent account or background daemon.

Permission conclusion: reuse permitted for the declared bundled paths subject to retained full notices; this is an operational source review, not a representation that a label grants trademark/service rights. Team-owned adapter code has no new unified licensing decision.

Build/test evidence: TEST_REPORT.md (created after actual execution). Native install ZIP and Hub-wrapper ZIP must have identical inner payload hashes. Keep local pending explicit current-package user completion; no Hub publication or PR implied.

Final archive review2026-10-23: verified every declared license-evidence SHA-256 against extracted runtime bytes, preserved full upstream texts and applicable authorship/notices, and confirmed source/native/Hub/installed payload identity. Selected reuse paths and modification/exclusion scope are enumerated in provenance.json and THIRD_PARTY_NOTICES.md. Local functional and delegated desktop/visual evidence are linked from TEST_REPORT.md. User authorized exact1.0.0 GitHub submission/merge by `pr合入`; no Hub action was requested.
