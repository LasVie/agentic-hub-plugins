# Build verification · 家庭日用品补货核验专家团 1.0.0

Cai Zhenze · AH-20261126-household-essentials-restock-review-team · 2026-11-26 Asia/Singapore.

- WorkSwarm native ZIP SHA-256 `d84845ebdd42aae9a1950058622425d2f4b99f172eca671327ebf8fcdbdd3d4d`.
- Hub-compatible wrapped ZIP SHA-256 `6c035111a5bee2f750facde8a25436a4d750f7fb5fb36640ed4ece73cfd70e7c`.

The pinned official Agentic Hub CLI 0.0.1 validated and packaged the wrapper. The 17-file payload matches the native source across both archived forms and the exact extracted native ZIP. Repository preflight passed on the source and both archives. The package uses Python 3.10 or later and the existing WorkSwarm task, file, and command tools. See [source review](SOURCE_REVIEW.md), [artifact record](release/1.0.0/artifact.json), and [preflight results](tests/records/package-preflight.txt).

All eight functional tests passed on [source](tests/records/source-tests.txt) and the [exact native extraction](tests/records/extracted-tests.txt). Tests covered same-day confirmed arrivals, past and next-shop date boundaries, pending orders, exact fractional rates, missing quantities, compatibility, limited shelf space, same-quantity pack choices, Chinese help and errors, changed receipts, and existing output directories.

An isolated WorkSwarm 0.2.8 instance validated the roster, imported and installed the exact native ZIP, and matched every installed file to the archive. In a session driven by fixed loopback model responses, all three roles loaded their own Skills and the shared Skill. Two native specialist tasks completed, the verifier sealed the original-input baseline before the leader issued the proposal, and five stage commands succeeded across 24 requests and 215 events. The four decisions were one 10-count pack of bin liners, one 2-roll pack of toilet paper to bridge the gap, model confirmation for vacuum bags, and waiting on dishwasher tablets with seven already usable. The run generated all three Chinese outputs and verified their digests. See [creator validation](tests/records/host-creator.json), [native installation](tests/records/host-import.json), and [role execution](tests/records/host-execution.json).

The integration used fixed responses and the bundled fictional JSON. The desktop ZIP picker, pasted-note transcription and orchestration by the user's configured model remain for [manual testing](MANUAL_TESTING.md). The loopback test processes were stopped and their local records preserved.

## Manual test and delivery recheck

Cai Zhenze confirmed in the current Codex conversation that manual testing of the exact native 1.0.0 ZIP was complete and passed. Confirmation was recorded at 2026-11-26T16:40:08+08:00 in RPT-20261126-household-essentials-restock-review-team-user-confirmation. The five [original screenshots](evidence/1.0.0/index.json) show the version, participant activity, final results and rendered Markdown and CSV.

The manual run used the bundled fictional case and the repository script. Phase 3 checked all 17 runtime files and reproduced all four manual stage receipts plus all three delivered files byte for byte from the exact native ZIP. The verifier’s source-only baseline precedes the proposal, verification and delivery. The verification receipt reports `matched` for four items and `issues=[]`. The eight functional tests passed again on source and the native extraction. Both ZIPs retain their build hashes. [Delivery recheck](tests/records/phase3-verification.json)

The WorkSwarm leader delegated planning and delivery to a temporary session operator, in addition to the two packaged specialists. The operator reported reading the sealed baseline before planning. The actual planning command took the intake receipt alone, the operator’s proposed cross-comparison was refused, and the original verifier completed the independent comparison. A truncated delivery command was declined and a complete command targeting a fresh directory succeeded. The final response supplied details about confirmed toilet-paper delivery, six-roll capacity and pending dishwasher-tablet delivery that appear only in abbreviated form in the Markdown and CSV. The three delivered files retained their verified digests. This manual evidence covers the bundled JSON run. Pasted notes and the desktop picker are outside the supplied screenshots.
