# Business Interruption Rehearsal and Recovery Review Team 1.0.0 test report

Executed 2026-11-20 for Cai Zhenze, task `AH-20261120-business-interruption-rehearsal-team`. Chinese display name 业务中断演练与复工核验专家团. Candidate Not Applicable. User manual testing passed on 2026-11-20.

| Exact archive | SHA-256 |
| --- | --- |
| Native WorkSwarm ZIP | `62d93cb9658846ccc90363cf8a5bc8a0783328b1fad8679bbaa7ffe7ab3fe56e` |
| Wrapped agent-group ZIP | `edaeadf4a6ca35b21b9bea9a39685e09581758fb1208a3a73796d848e8b6b1b6` |

## Format and deterministic behavior

The pinned official agentichub CLI 0.0.1 ran `init --type agent-group`, `validate` and `pack` successfully in clean staging. The native root and wrapped payload each match all 28 reviewed source files. Paths, wrapper identity and version, archive limits and all per-file and ZIP SHA-256 hashes were checked. The dynamic JavaScript preflight passed for the source and both ZIPs. [Verification record](tests/records/verification.json)

All 14 tests passed both on [source](tests/records/source-tests.txt) and on [the exact native extraction](tests/records/extracted-tests.txt) under Python 3.10.11. The suite checks the Chinese end-to-end CLI output, input bounds and types, unknown owners, dependency cycles, shared manual limits, read-only handling, duplicate or missing evidence, late and conflicting dispositions, forged review, stale case/plans and preservation of existing delivery. The simulator and independent computation agreed on 40 seeded valid variations.

WorkSwarm 0.2.8 source distribution and its existing frontend build were used read-only. The actual group creator accepted the exact ZIP extraction, and SDK 0.1.20 loaded the Leader entry and five member templates. Each got its own Skill and the shared Skill. Wrong member type, missing Leader entry and missing verifier were rejected. [Loader record](tests/records/host-loader.json)

## Installed WorkSwarm execution

An isolated loopback test instance ran the exact native installation. The real Leader created tasks, all five members claimed and completed them, and each used the actual Skill and shell tools. Task messages and seven successful installed-script receipts record handoffs. The verifier built its baseline from the original input before the facilitator ran the simulation, then independently checked all nine work items. The Leader verified all six upstream digests before delivering the Chinese playbook, JSONL trace, CSV action register and JSON audit. The run recorded 402 host events and 43 local scripted provider requests. [Execution evidence](tests/records/host-execution.json)

In the routine scenario, the three workflows reopened at minutes 30, 35 and 40, with six items accounted for. Two overflow items were held and later backfilled once each. The item already present at the same revision needed no duplicate entry. In the read-only scenario, no workflows reopened and all three items remained held. The independent verdict matched both traces, including the negative outcome.

These results verify the actual host mechanisms and deterministic work. The local model was scripted. The separate user run is recorded below. The shared workspace uses staged task handoffs for baseline independence.

## Manual instance

[Isolated WorkSwarm](http://127.0.0.1:6707/) has the exact native ZIP installed. The browser reached **专家 → 我的专家 → 专家团 → 创建 → 上传文件创建**, but the picker returned no selection. The supported local Expert Team import installed all 28 files byte for byte. The UI then displayed 1.0.0 and all six Chinese roles. The desktop picker remains a manual check. [Manual host installation record](tests/records/manual-host-import.json) · [Manual testing instructions](MANUAL_TESTING.md)

## User manual testing and exact-package recheck

Cai Zhenze confirmed that manual testing of the exact native 1.0.0 ZIP was complete and passed in the current Codex conversation on 2026-11-20 (Asia/Singapore). See [the five original screenshots and confirmation record](evidence/1.0.0/index.json).

The five specialists ran their assigned stages with actual host tools. The verifier confirmed the bundled sample from the native package directory, sealed the original-input baseline, and compared its nine items to the later trace. One compare attempt correctly refused a pre-created output directory. The verifier retried in a fresh directory and preserved the earlier evidence. The Leader assigned the final delivery command to the analyst. The ordinary scenario reopened at 30, 35 and 40 minutes, and the read-only scenario held all three of its items.

The delivery script from the exact native ZIP reproduced all four manual artifacts byte for byte from the saved handoffs. Six upstream digests matched the audit and the trace contained one accounting event per work item. Both archives and all 28 payload paths and hashes remained identical. All 14 source and 14 exact-native functional tests and all three dynamic JavaScript preflights passed again. [Phase 3 verification](tests/records/phase3-verification.json)
