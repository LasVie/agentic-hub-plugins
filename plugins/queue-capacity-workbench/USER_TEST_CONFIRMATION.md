# User test confirmation and original evidence

Task: AH-20261110-queue-capacity-workbench. Owner: Cai Zhenze. Candidate ID: Not Applicable.

## Explicit confirmation

> I confirm manual testing of 离线排队容量实验台 1.0.1 passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md. GitHub delivery only; no Releases or Hub actions.

Confirmed by Cai Zhenze in the current Main 3.0 conversation, received 2026-11-10 Asia/Singapore. The exact message timestamp is not exposed; the attached screenshots are named 16:25:57 through 16:26:29. Evidence intake verified at 2026-11-10 08:28:03 UTC. No message permalink is available; none is invented.

- Version: 1.0.1; SimPy 4.1.2 -> 离线排队容量实验台 -> queue-capacity-workbench.
- Native ZIP SHA-256: `378588d14ab74941b102542cff782973096a9fe4a944d9c91788bc8043d38413`.
- Canonical ZIP SHA-256: `2335d36aa1e5c2276084ba76441d2e455a1353988d810eb61894928743f89438`.
- Both hashes match the exact prior testing handoff and current bytes. No payload or wrapper changes after confirmation.
- Known blocking issues: none reported. Prior limits remain: POSIX lifecycle, single-stage deterministic FIFO; assistant tested WorkSwarm0.2.5.beta1, while a fresh0.2.8 dependency build failed upstream Swift compilation. User screenshots do not identify a host version.
- Scope authorized: GitHub delivery under AGENTS.md, including merge/checks/evidence and safe branch cleanup. No Release or Hub action. Project Lead acceptance remains separate.

## Original screenshots received before any delivery push or PR

Full-resolution PNG bytes copied unchanged from the four user-supplied temporary files into this task’s local evidence handoff. Originals contain no visible credentials, keys, private correspondence or other sharing blocker; the WorkSwarm conversation includes an ordinary local work-directory path supplied for this test. No cropping, recompression or generated replacement. Original filenames are preserved.

| Original filename | Pixels | SHA-256 | Scope |
| --- | --- | --- | --- |
| Screenshot 2026-11-10 at 4.25.57 PM.png | 3224 × 1670 | `1ad4082d0ee052790031f52720417f9e23a8b7e5efbe2f4ae6d44f5952641a1b` | Burst-arrival capacity comparison |
| Screenshot 2026-11-10 at 4.26.07 PM.png | 3212 × 1678 | `52da7ecea42ea333b64e9000c14ce4a32098aae9413e3687134c8d24de1c9ad0` | Four-job exact fixture |
| Screenshot 2026-11-10 at 4.26.18 PM.png | 3218 × 1606 | `06021155a39be4310974c202dbdf9ab63873a158122d3b0beb50e70f4efa36a4` | Idle-capacity scenario |
| Screenshot 2026-11-10 at 4.26.29 PM.png | 574 × 1352 | `084bcd840f37124b4ea66430e8296408452a5fe1cfbade197f0421510b38e896` | Actual WorkSwarm tool invocation and returned metrics |

The three workbench images visibly identify version1.0.1/SimPy4.1.2 and show burst, exact and idle fixtures. The fourth is the supplied WorkSwarm conversation reporting tool invocation and exact capacity metrics. The explicit user statement establishes manual completion; screenshots alone are not substituted for it.

Original images will be attached to the delivery PR conversation and their permanent comment link verified before merge. Test Screenshot remains link-only. Local intake paths and images are not written to tracker screenshot fields. The complete package/license/test/instruction/confirmation/original-image materials gate passed before delivery.
