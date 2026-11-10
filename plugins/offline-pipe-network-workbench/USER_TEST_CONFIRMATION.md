# Current-package user test confirmation

- Task: `AH-20261110-offline-pipe-network-workbench`; Candidate: `CAND-EXT-013`; owner/confirming user: **Cai Zhenze**.
- Mapping: EPANET JavaScript Toolkit → **离线管网水力工作台** → `offline-pipe-network-workbench`, version **1.0.0**.
- Received: **2026-11-10, Asia/Singapore**, in this conversation. Exact message time/permalink is unavailable; no fabricated message link.
- Actual user statement: “I confirm manual testing of 离线管网水力工作台 1.0.0 is complete and passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md, keeping it isolated from Main.”
- Native tested ZIP SHA-256: `1414048b02e90649ed7708035fd2be68715b1fa5189b58686d33f11b397be6df`.
- Canonical exact inner-payload equivalent ZIP SHA-256: `dd16d4fe65be52c55a3f379a2014e69cdc11e3f1a6eb8e730e9091668bc1d3f6`.
- Confirmation report: `RPT-20261110-pipe-network-confirmed`.
- Known blocking issues: none reported. POSIX/verified-host and bounded fixed-demand-model limitations in TEST_REPORT.md remain; acceptance does not certify real engineering safety, unsupported hosts or Hub submission.

## Original evidence collected before push/PR

All six original PNGs were received locally, inspected for association/readability, and preserved byte for byte at their original dimensions; no resize, conversion or recompression. They contain synthetic network examples and local workbench addresses, with no provider key or mailbox/private-infrastructure content observed. The user's instructions to upload them authorize the delivery evidence; the text displayed inside images is test data, not new execution instructions. The PR evidence comment must link the full-resolution originals with these exact hashes. Tracker screenshot fields remain blank until that comment and its images are verified.

| # | Original filename | Pixels | SHA-256 | Observed coverage |
| --- | --- | --- | --- | --- |
| 1 | `Screenshot 2026-11-10 at 5.44.47 PM.png` | 1360×1338 | `fcedd4a2f2a1b8eccd40eed9ab06b2b688546efdd7d9af43f80aa8c0ca7cc483` | Actual WorkSwarm pipe_network_workbench status/start/reuse/status;1.0.0 and one returned URL. |
| 2 | `Screenshot 2026-11-10 at 5.44.59 PM.png` | 1694×1626 | `895b65d072707ed20748a522b38fb998d260cc151cb9b040b362dd8e16ce7162` | Single-pipe analytical fixture:1 L/s,100mm,head99.95645m. |
| 3 | `Screenshot 2026-11-10 at 5.45.12 PM.png` | 1126×1422 | `08776f794da21a426103704713e7c99d1749b980550e2ca9b074ccf41c327171` | Default two-loop fixture:16 L/s,7nodes/8pipes,minimum pressure31.58701m. |
| 4 | `Screenshot 2026-11-10 at 5.47.22 PM.png` | 1238×1404 | `f0665c8a6c7579462dcbca96222a1260e5b66ce0bf697ca85b15353c5ab0c8ef` | Pipe P2 changed to170mm; flows redistributed and minimum pressure33.51409m. |
| 5 | `Screenshot 2026-11-10 at 5.47.37 PM.png` | 1136×1414 | `dc3a9bdcb4c7dd08bbe6b146d80de53851942d29ac40acbd9b6e33201f35d99e` | Junction A demand changed to3.5L/s; total17.5L/s,minimum pressure33.29653m. |
| 6 | `Screenshot 2026-11-10 at 5.48.04 PM.png` | 1688×1634 | `113c38da340b51044167e85242db769cd61d1373d804859e6ae89aed56d075ca` | Single-pipe scenario:160mm and5L/s,head99.91305m. |

The screenshots document the user's actual WorkSwarm/browser session separately from earlier model-free SDK engineering checks. They do not independently show every download/error case; those retain their previously passing automated engineering evidence together with the user's explicit overall completion confirmation. No additional hidden tests, unsupported-host compatibility or Hub acceptance is inferred.

Phase3 authority covers reviewed source, exact ZIPs, original evidence, GitHub PR/merge and eligible branch cleanup only. Project Lead acceptance is pending; Asset Ledger remains unchanged. No Release or Agentic Hub operation is authorized.
