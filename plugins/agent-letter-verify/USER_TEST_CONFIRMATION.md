# User testing confirmation — 代理信件完整性校验 1.0.1

Candidate CAND-DSH-305; original task AH-20261023-agent-letter-verify; explicitly supplied owner and confirming user Cai Zhenze. Mapping: dsh-whale-post#verify → 代理信件完整性校验 → agent-letter-verify. Internal ID repo:agent-plugin:agent-letter-verify.

## Explicit confirmation

The user stated in this current independent Codex conversation, with two original PNG attachments:

> I confirm manual testing of 代理信件完整性校验 1.0.1 is complete and passed. Use my attached screenshots and proceed to Phase 3 under the latest AGENTS.md.

The message contains two spaces before “screenshots”; the rendering above normalizes only that spacing. Receipt/verification began 2026-10-23 15:40:40 Asia/Singapore. The exact message timestamp is unavailable; this is the observed processing time, not an invented sent time. Screenshot filenames show 15:40:01/15:40:11; visible test conversation timestamps are 15:37/15:38. Source: current conversation, with no invented message permalink. Confirmation Report ID: RPT-20261023-agent-letter-verify-confirmed-101.

## Exact tested and delivery packages

- Chinese native test ZIP: [test-packages/agent-letter-verify-1.0.1-workswarm.zip](test-packages/agent-letter-verify-1.0.1-workswarm.zip); SHA-256 `a6260d897de78677d64500e11e41e720b940dcc0661a65d3c0576be2e60494a6`. This is an exact-byte retained copy of the handoff dist ZIP, necessary to deliver the tested native host package.
- Chinese canonical ZIP: `releases/agent-plugin/agent-letter-verify/1.0.1/agent-letter-verify-1.0.1.zip`; SHA-256 `c195834594177edaef1516a3be7e725b75c20467454de6b80bb9d0842b64c9e6`.
- Source, canonical inner payload, native ZIP and installed plugin have the identical eight runtime files. Both ZIPs, wrapper, manifests, names/localization and runtime source are unchanged from the manual testing handoff. Screenshots/confirmation/native copy are outside the runtime payload. The two distinct wrapper formats were disclosed in the handoff; user confirmation is a direct reply to that exact current package/version handoff.
- TEST_REPORT.md and SOURCE_REVIEW.md retain the original build-time results and artifact hashes. This later confirmation supersedes their pending-user-testing statements and the initial fixture state. No package rebuild/change is needed for external evidence.

## Evidence assessment and corroboration

The two readable originals show the complete Chinese test request and result summary for version1.0.1: initial disabled/not_checked; revision0 enabling sender_demo to revision1; valid-letter acceptance; body digest and MAC tampering rejection; unknown sender/field and duplicate JSON rejection; stale-revision refusal preserving enabled state; normal disable to revision2 and repeated not_checked. The response separates request ok from verified and discloses HMAC/identity/replay/interception limitations. It reports no execution of envelope body, no key display and no letter modification.

All six screenshot envelope hashes match read-only hashing of the corresponding local public fictional fixtures. The local policy is now enabled=false, allow=[sender_demo], revision=2, consistent with the screenshots. The installed eight runtime files remain byte-identical to the confirmed ZIPs. This corroborates inputs/state; screenshot summaries are not independent raw backend-event proof. No other conversation history or model credential configuration was searched. Existing model-free installed SDK evidence remains a separate prior check.

No known blocking payload issue is identified. The screenshots do not prove every optional hardening/platform case was manually exercised. Restricted basic-v1 support, no replay/freshness defense or unique-author/content-truth guarantee, no automatic interception, and unverified Windows support remain documented limits. The previous AI-only model-disabled setup statement does not claim the later user test was model-free; no paid model request was made by this agent.

No key, credential or private letter content is visible. Only ordinary local paths, public fictional fixture identifiers and digests are present. Repository visibility was verified public and the user expressly authorized these screenshots for GitHub Phase3 delivery. Original files are copied byte for byte: no cropping, resizing, recompression or alteration.

## Original full-resolution evidence

The GitHub connector has no binary attachment-upload tool. As in prior repository handoffs, a dedicated PR evidence comment embeds the retained original PNGs from immutable commit URLs. Verify each remote original hash, full dimensions and rendered image plus the actual permanent PR comment before merging. Only that verified comment permalink goes in Test Screenshot; no local path or bare PR URL. The machine-readable original filename/hash index is [evidence/originals.json](evidence/originals.json).

| Original filename | Retained file | Pixels | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| Screenshot 2026-10-23 at 3.40.01 PM.png | [evidence/user-test-1.0.1-01.png](evidence/user-test-1.0.1-01.png) | 836×1714 | 296499 | `807bfb46a54dc8b1b46cdf08d88c813452abf27c162b85874059050755680605` |
| Screenshot 2026-10-23 at 3.40.11 PM.png | [evidence/user-test-1.0.1-02.png](evidence/user-test-1.0.1-02.png) | 842×1270 | 368279 | `8ed43a932b220db5a3ede36ad306520ade4a21b23c4bbffa2e828a0103559529` |

## Review and delivery scope

Latest main AGENTS.md blob e6e315918b1d948ba37bd2a3312c55c05a254d97 matches the fully read local rules. This worktree fast-forwarded from d462c34 to current origin/main69c0adf without changing any runtime payload or Main's checkout. Source/license review is complete and MIT/full original header/notices remain bundled. User testing and original screenshots now satisfy the materials gate for GitHub delivery; no Project Lead acceptance or Hub evidence is inferred.

Deliver only justified plugin source, functional tests, required source/license reviews, instructions, exact tested archives and original screenshot evidence. Keep upstream research, fixture keys/input workspace, environments, generated logs, AI UI inspection and temporary preflight archives outside the commit. After the unchanged-package fast-forward, the full local repository suite passed:218 tests in9.311s with one documented historical-package skip. Packaging check-repo passed29 source assets/37 ZIPs. Log /private/tmp/agent-letter-phase3-suite.log. Required PR CI must still pass before merge. After verified merge clean only feat/agent-letter-verify if still eligible, then keep task Awaiting Acceptance, candidate Planned, acceptance Pending Acceptance and completion date blank. Song Haoran handles Hub submission/publication; no GitHub Release or Hub operation and no Asset Ledger update.
