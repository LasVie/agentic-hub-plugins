This template applies to plugin development or changes. For pure repository maintenance, describe the change and verification; mark plugin-only fields Not Applicable. Do not create plugin tasks, reports, or asset/candidate records for maintenance.

## Scope and identity

- Change type: Plugin development/change / Repository maintenance
- Task ID (required for plugin work):
- Candidate ID (if applicable):
- Confirmed primary owner (Unassigned if unspecified):
- Asset type / stable Asset ID:
- Difference from existing Asset Ledger capabilities:

## Submission gate — before pushing/opening this delivery PR

- [ ] The user explicitly confirmed testing is complete for the current package, and known blocking issues are resolved
- Confirmation Progress Report ID / actual conversation reference:
- Confirming user and date/time:
- Tested version and final ZIP SHA-256:
- [ ] The ZIP and payload submitted here match the confirmed test package; any changed package has been retested and explicitly confirmed

AI self-tests, CI, downloading a package, starting tests, or a screenshot alone do not establish user test completion. Keep package development local until the gate is met. Pure repository maintenance is exempt; do not invent user testing or confirmation records.

## Validation and distribution

- Source review and pinned upstream version:
- Permission review / independent implementation basis:
- Actual functional-test environment, commands and results:
- ZIP path, version and SHA-256:
- [ ] Repository format checks pass and every declared file exists
- [ ] Actual asset functionality was tested, beyond packaging-tool tests
- [ ] License coverage was checked for code, prompts, documents, media and dependencies
- [ ] The final ZIP preserves applicable copyright statements, full licenses, THIRD_PARTY_NOTICES.md and any applicable upstream NOTICE
- [ ] Apache-2.0 modified files carry prominent change notices; original applicable statements remain intact
- [ ] Extracted final ZIP license paths and hashes were checked; materials with unknown permission are excluded

Evidence within the final ZIP (explain Not Applicable items):

- Sources, licenses and covered files:
- Copyright / attribution / THIRD_PARTY_NOTICES.md:
- LICENSE / upstream NOTICE (state if absent):
- Modified-file notices:

This checklist does not relicense repository-owned code or upstream materials. Required functional tests, CI and distribution review must pass before merge.

## After merge — plugin work only

- [ ] Actual merge and merge commit verified
- [ ] Missing original test screenshots proactively requested; actual full-resolution images attached to this PR
- [ ] Verified test-evidence permalinks recorded in Development Tasks / Test Screenshot
- [ ] Asset Ledger, original Development Task, Progress Reports and linked candidate synchronized as applicable
- [ ] Candidate/task IDs, owners and any handoff or conflict verified
- [ ] Merged release path, version/hash, installation notes and test evidence handed off to Song Haoran
- [ ] Final Project Lead acceptance recorded only from Song Haoran's explicit conclusion
- [ ] Completed / Delivered used only after contributor delivery gates and explicit Project Lead acceptance pass; test completion alone is insufficient

Song Haoran personally handles Agentic Hub submission/publication and associated Hub evidence. Contributors and their agents do not perform those operations. Preserve the Agentic Hub Submission Screenshot column for real evidence supplied by him; it may remain blank and is not a contributor completion gate. Both screenshot columns accept only verified PR evidence permalinks.

## Temporary branch cleanup — all PRs

- [ ] Actual merge and merge commit verified
- [ ] Source-branch head has no post-merge commits and no open PR depends on the branch
- [ ] Eligible temporary source branch confirmed deleted automatically or manually; exceptions and missing permissions recorded in this PR

Preserve main/default, protected and explicitly long-lived branches. Do not delete other contributors' fork branches or force-delete unmerged local work. Cleanup does not wait for plugin screenshots or final acceptance. Start subsequent changes from current main.
