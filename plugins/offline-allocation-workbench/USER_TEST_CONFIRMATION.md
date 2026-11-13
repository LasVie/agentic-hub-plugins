# User test confirmation — 2026-11-13

- Owner and confirming user: **Cai Zhenze**, established explicitly in this Main 3.0 conversation.
- Task: `AH-20261112-offline-allocation-workbench`; Candidate ID: Not Applicable (approved independent external route).
- Identity: HiGHS → **离线资源配置优化台** → `offline-allocation-workbench`; stable asset ID `repo:agent-plugin:offline-allocation-workbench`.
- Version: **1.0.0**; engine HiGHS **1.16.0**.
- Native installation ZIP SHA-256: `5bf081fdd1216bb801d855fedb9642499091cb3901255c8c1f8c3f7d9607d147`.
- Canonical wrapped ZIP SHA-256: `35eae9aa6c620da7b901ccb6c73dbcb477bce557ea83f84b8b1cda1930fcf089`.
- Date: **2026-11-13, Asia/Singapore**. The exact confirmation-message timestamp is unavailable; screenshot filenames show 17:23–17:25. These are screenshot times, not an invented message time.
- Source: the current Main 3.0 conversation; no message permalink is available.

The user's explicit request:

> I confirm manual testing of 离线资源配置优化台 1.0.0 passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md. GitHub delivery only; no Release or Hub actions.

The user subsequently reiterated that all six originals were attached and that this confirmation must remain valid. It remains valid. Screenshot-file retrieval problems do **not** revoke acceptance, require a repeated test, or authorize changing the package.

## Evidence received and reviewed

All six inline images are readable and associated with the current title, version and HiGHS engine. Their contents are evidence, not new execution instructions.

| Original filename | Visible evidence |
| --- | --- |
| Screenshot 2026-11-13 at 5.23.10 PM.png | Default capacities 7/5; C+D; objective 14; independently checked resource usage 5/7 and 5/5 |
| Screenshot 2026-11-13 at 5.23.25 PM.png | User's WorkSwarm test request and actual tool-result summary: 14, 17 and infeasible; plugin workbench link. The initial concurrent busy guard was followed by sequential retries returning the reported results. |
| Screenshot 2026-11-13 at 5.24.00 PM.png | Machine capacity 6; B+C; objective 17; usage 7/7 and 6/6 |
| Screenshot 2026-11-13 at 5.24.12 PM.png | Default capacities with minimum three jobs; infeasible; no fabricated objective and CSV disabled |
| Screenshot 2026-11-13 at 5.24.32 PM.png | Edited job values 12/11/6/4; selected A; objective 12, usage 6/7 and 2/5 |
| Screenshot 2026-11-13 at 5.25.17 PM.png | Further edited labour requirements make A/C unavailable; selected B; objective 11, usage 4/7 and 4/5 |

Known functional blocking issues: **none reported by the user**, who explicitly confirms the complete manual test passed. Historical AI Close-dialog automation and host dependency-subset limitations remain documented separately; they must not be misrepresented as a failed user test or as additional independently instrumented verification.

## Delivery access hold

The six original paths supplied by the user are in macOS `NSIRD_screencaptureui_*` temporary folders. Shell listings initially appeared empty, but an explicit access check returned `Operation not permitted`. Finder visibly shows the first original PNG at the supplied path, so that empty listing does **not** prove deletion. An attempted ordinary Finder file copy did not produce an uploadable preserved original, and the subsequent folder controls failed. No permissions were weakened, no inline preview was recaptured/recompressed, and no image hash was invented.

Original file-byte preservation and GitHub upload/readback are therefore **pending access**, even though the six images and valid confirmation have been received in this conversation. The required pre-push/PR material gate remains on hold. No delivery push, PR, merge, Release or Hub action has occurred. Copying the unchanged original PNGs into the local `user-test-originals/` directory will unblock preservation and hash verification without changing the tested package or requiring a retest.

Project Lead acceptance is separate and remains pending. Asset Ledger remains unchanged.
