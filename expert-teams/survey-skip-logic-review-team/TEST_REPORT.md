# Survey Skip-Logic Review Team — test record

Task: `AH-20261120-survey-skip-logic-review-team`. Candidate: Not Applicable. This report does not constitute user acceptance.

## v1.0.0 automated checks — 2026-11-20

- Official Agentic Hub CLI `0.0.1` at `c8ee4ef44be0453470114aa5a19f4e1017462907`: `validate` and `pack` passed. Both ZIPs were checked for exact entries, member bytes against the reviewed payload, CRC, and size limits. Paths and SHA-256 are in `release/1.0.0/artifact.json`.
- `tools/asset_release.py preflight` passed for the source payload, native ZIP and wrapped ZIP; no JavaScript files were present. The repository preflight does not validate AgentGroups as runnable in WorkSwarm.
- Eight functional tests passed on Windows against an extraction of the exact native ZIP. Covered a clean exit, Chinese fixture with all three defect categories, an unreachable internal cycle, duplicate keys, missing verification, false witness paths, changed source bytes and existing report protection. The Chinese fixture reported Q3 unreachable and reproduced the Q2 → Q99 break and cycles involving Q1 and Q2.

## v1.0.0 WorkSwarm 0.2.8 evidence — 2026-11-20

Installed payload matched all 12 members of the original native ZIP. The two chat screenshots and Task Planning screenshot were received for v1.0.0 only. The panel shows three completed tasks but not the assignee names or timing; the matching WorkSwarm session events establish these details:

- Case 1: `verifier` claimed `task-baseline` at 17:23:09.743; `analyst` claimed `task-analyze` at 17:23:10.085, **before** baseline task completion (17:24:25.983). The baseline script finished writing before the analysis script ran, but this was not gated. `verifier` claimed `task-verify` at 17:24:31.647 after both and completed it at 17:25:41.175 (UTC+08:00). The Chinese report and all three handoffs matched the fixture and verification digest.
- Case 2: the runtime returned the duplicate-key error, no baseline or final report was written to the designated output folder, and verification was cancelled. However, analysis was dispatched before validation succeeded and staff performed unnecessary retries/scratch diagnostics, contrary to the fail-fast procedure.

Do not submit v1.0.0: these runs demonstrated a dispatch-order defect, even though the requested output checks held. The new screenshot needs no replacement for the historical run; it is not evidence for the revised package.

## v1.0.1 retest

The Leader creates only the baseline task initially and stops on a failed baseline. The analysis command now rejects missing or mismatched baseline handoffs without using baseline findings in its search. A fresh WorkSwarm run of both cases is required to verify actual task sequencing and fail-fast behavior for this package. Nothing is approved for submission.

- Both regression tests failed on v1.0.0 code (analysis exited 0 with a missing or mismatched baseline). All ten tests passed after the fix, in source and from the exact extracted v1.0.1 native ZIP.
- Official CLI validation and pack passed. Native and wrapped payload bytes were checked against source; repository preflight passed on source and both ZIPs. Native SHA-256: `288495599a9ebbf124bfa4505a276d39cc183bd43a4479186bf69b64ec0102bd`. Hub wrapper SHA-256: `c81918bd7c52ed9b7ea6619a87761ce11db1ac3ce3da25a056c5ac57eac47f89`.

### WorkSwarm retest evidence — 2026-11-27

Reviewed the two original Share exports (`jiuwenswarm-share-20261127-110117.png` and `jiuwenswarm-share-20261127-110122.png`) and the task events from the sessions matching the v1.0.1 fixture paths. Times below are UTC+08:00.

- Case 1: the baseline completed at 10:15:58.359 before analysis was created at 10:16:05.178. Analysis completed at 10:17:08.678 before verification was created at 10:17:15.880. The three handoffs match the fixture hash, the verification seal matches the canonical analysis, and the Chinese report identifies unreachable Q3, the Q2 → Q99 break, and the Q1/Q2 loop. The Leader delegated report generation to the verifier after verification, rather than running the report step itself as instructed.
- Case 2: the baseline rejected the duplicate key; the output directory was empty and no analysis or verification task was created. However, the baseline stayed `in_progress` from its claim at 10:22:49.721 through the last task event at 11:01:11.718. The chat shows repeated waiting/status messages rather than closing the failed task. The downstream dispatch gate worked, but the fail-fast stop did not.

Keep v1.0.1 in integration testing; the screenshots are evidence of these runs, not user test-completion confirmation or a submission approval.

## v1.0.2 local checks — 2026-11-27

- Added leader-only, read-only `validate` before task creation using the same JSON parser. The leader runs report generation directly. After a member reports failure, the leader is instructed to cancel only the still-open task using the `update_task` capability documented in the installed WorkSwarm bundle and verify the resulting task state. No successful task state is fabricated on failure.
- The three new CLI regressions failed on v1.0.1 because `validate` was unsupported, then passed after the change: duplicate-key rejection with an empty output directory, valid fixture acceptance without writes despite structural findings, and nonempty output rejection without modifying existing files. All 13 tests passed in source and against the extracted native ZIP; CLI help printed the new command in Chinese.
- Official Hub CLI 0.0.1 validate/pack passed, archive members matched the reviewed source bytes, and repository preflight passed on the payload and both ZIPs. Native SHA-256: `8a95dc972094d12c2c0d290f4e0e9090788114c7886d0f5987d65877f3d5e107`; wrapper SHA-256: `031de2214e497b88fc2d52f43b71644dc8fb26ef1af1ed52419be52ecd2efb25`.
- Replayed both handoff fixtures with the staged native ZIP in scratch directories. Case 1 preflight wrote nothing; the four subsequent files were byte-identical to the v1.0.1 WorkSwarm outputs. Case 2 returned the Chinese duplicate-key error and wrote nothing. The user test directories remained empty. The standalone SDK install timed out, so SDK package loading is not claimed.
- Live WorkSwarm behavior is not yet verified. Retest the two synthetic cases in new chats using v1.0.2: valid input must preserve the real handoffs; duplicate-key input must end after one error with no new tasks and no output files. The post-dispatch cancellation path is documented but not exercised by the CLI suite. Collect original screenshots and explicit test-completion confirmation before delivery.

### v1.0.2 WorkSwarm retest — 2026-11-27

Reviewed original Share exports `jiuwenswarm-share-20261127-114916.png` (Case 1) and `jiuwenswarm-share-20261127-114919.png` (Case 2), matched to the fixture paths and scoped WorkSwarm histories. The installed manifest reported 1.0.2, and all 12 native ZIP members matched the installed payload byte for byte. Times are UTC+08:00.

- Case 1 passed: the leader ran preflight before dispatch. The verifier completed baseline at 11:40:30.094 before analysis was created at 11:40:47.122; the analyst completed analysis at 11:41:58.955 before verification was created at 11:42:07.987. The verifier completed verification at 11:42:28.465. The leader generated the report directly, with no fourth task. The Chinese report and three handoff files matched the expected results; all input hashes and the analysis verification seal matched.
- Case 2 passed the fail-fast behavior check: the leader ran validation, the chat displayed the Chinese duplicate-key error, and the run ended after its final reply. The matching history had no team-task events, no group messages and no further tool calls after validation; the output directory stayed empty. The final user-facing explanation was in English despite the test explicitly requesting Simplified Chinese; only the quoted validation error was Chinese. This is a localization defect, not a recurrence of the task hang.

### Case 2 retest with Simplified Chinese preferred — 2026-11-27

- Verified the new original Share export `jiuwenswarm-share-20261127-125913.png` against the fresh Case 2 session and the unchanged installed v1.0.2 payload. The leader explained the duplicate option key and confirmed the run had ended, in Simplified Chinese. This supports a preference-dependent language difference rather than a package change being necessary; it does not prove the host's instruction precedence.
- Validation ran once and exited 2. The leader did one additional read-only inspection of the synthetic input to identify the repeated key. There was no validation retry, task creation, repeated waiting or output. The fail-fast and Chinese output checks passed. Case 1 evidence remains valid for the unchanged ZIP.
- No package or screenshot rerun is needed for the two agreed cases. The after-dispatch cancellation path was not invoked in these cases.

### User test confirmation — 2026-11-27

`RPT-20261127-survey-skip-logic-review-team-confirmation`: Nguyen Trung Dung replied “confirm” in the current conversation to the explicit request to confirm that WorkSwarm testing of v1.0.2 was complete and that no blockers remained. Recorded 2026-11-27 14:08 (Asia/Singapore), task `AH-20261120-survey-skip-logic-review-team`, native ZIP SHA-256 `8a95dc972094d12c2c0d290f4e0e9090788114c7886d0f5987d65877f3d5e107`. No known blocking issues for the agreed cases. This is user test completion, not Project Lead acceptance. The after-dispatch cancellation instruction was not exercised in these cases.
