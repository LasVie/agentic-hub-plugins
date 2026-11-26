# Build verification — 家校通知变更与待办核验专家团 1.0.0

Task AH-20261120-school-notice-action-review-team · Cai Zhenze · 2026-11-20 Asia/Singapore.

- Native SHA-256 `4f34070f46787c9c57fc421d3ad736d76d9c73c70e023bc3b5ec007c5a1964c0`.
- Hub-compatible SHA-256 `7acc7fe4213205def7cc06e0d199b9e8ce33e1387a6f6cb17b120d74771a907c`.

The pinned official CLI 0.0.1 validated and packed the wrapper. The 17-file UTF-8 payload matches source, both archive forms, exact native extraction and WorkSwarm installation. Repository preflight passed on all three forms. No upstream data, code or extra runtime distribution is bundled. See [artifact manifest](release/1.0.0/artifact.json), [preflight](tests/records/package-preflight.txt), and [source review](SOURCE_REVIEW.md).

All 16 functional tests passed on [source](tests/records/source-tests.txt) and the [exact native extraction](tests/records/extracted-tests.txt). The checks cover class-specific corrections, cancellation, duplicate reminders, undated forwards, missing links, ambiguous scope and same-day ordering. Negative controls reject altered quotes, missing notice coverage, malformed clock excerpts, prefilled baseline input, stale source, forged verification and overwrites. The final revision distinguishes “下午5点一起” from “下午5点半” and leaves ambiguous “晚上12点” open. Verified UTF-8 Chinese help, errors and output.

WorkSwarm 0.2.8 reported three valid agents from the exact extraction, and SDK 0.1.20 mounted the respective private and shared Skills plus the Leader instructions. A missing verifier was rejected. A fresh loopback WorkSwarm instance used the supported local import and install route, and the installed bytes matched the exact ZIP. The Leader created native tasks, both members claimed and completed tasks with actual handoff messages, and the reviewer sealed a baseline before the draft existed. Fixed local model responses drove four successful stage commands over 22 requests and 193 events. The delivery contained four verified actions, two changes, one unresolved date and all three files with recorded digests. See [loader](tests/records/host-loader.json), [installation](tests/records/host-import.json), and [actual role execution](tests/records/host-execution.json).

The fixed role readings were supplied as test fixtures. This establishes the installed team wiring and review behavior. The desktop ZIP picker, pasted-message transcription and orchestration with the user's chosen model were outside the scripted engineering test. The isolated host test used only this asset's local runtime directory and stopped afterward. See [manual testing instructions](MANUAL_TESTING.md).

## Manual confirmation and delivery recheck

Cai Zhenze confirmed in the current Codex conversation on 2026-11-26 that manual testing of the exact native 1.0.0 ZIP was complete and passed. The confirmation was recorded at 2026-11-26T15:28:04+08:00 under RPT-20261126-school-notice-action-review-team-confirmed. The four original full-resolution screenshots show the version, participating members, source-only baseline, completed verification and delivery tasks, and the rendered Chinese checklist. The [evidence index](evidence/1.0.0/index.json) records their original hashes and dimensions.

The run referenced the checked-in script and fictional notices, whose bytes match the exact native ZIP. The original reviewer baseline precedes the analyst draft, followed by verification and delivery. In the user's run, the Leader delegated the final delivery command to the notice analyst after verification. The analyst remained the same packaged role. The screenshots cover the supplied JSON workflow; the desktop ZIP picker and pasted-message transcription are outside the supplied screenshot evidence.

The exact extracted ZIP independently reproduced all three stage receipts and all three delivered files byte for byte. The manual results covered eight notices with zero disagreements, four actions, two changes, and one unresolved relative date. Class A pickup moved from 16:30 to 17:00 and Class B stayed at 16:30. The cancellation and duplicate reminder were handled as expected. Both ZIPs and all 17 payload files retain their tested hashes, and all 16 functional tests passed again on source and exact extraction. See [delivery verification](tests/records/phase3-verification.json).
