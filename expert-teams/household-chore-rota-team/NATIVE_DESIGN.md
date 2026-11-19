# Native design — household-chore-rota-team

Task `AH-20261117-household-chore-rota-team`, owner Cai Zhenze. Approved in the current Main 4.0 conversation on 2026-11-17. Candidate: Not Applicable. Base: `4e190253f00b2a1d65fdc657161a67fecde15a48`.

## Responsibility and scope

One native AgentGroup with Leader, chore analyst, rota planner and independent verifier. A complete case contains a seven-day start date, 2–6 named participants and 1–21 dated chore occurrences. Durations, eligible participants, daily/weekly caps, unavailable days and optional preferences come from the user. Missing facts require visible clarification; complete explicit instructions do not require another routine approval. Natural-language material is converted to a visible case snapshot, with assumptions separated from supplied facts. No automatic assignments to real people or calendar writes.

The analyst validates/normalizes the case and writes a bound intake record. The planner performs a bounded deterministic depth-first search, choosing constrained occurrences first and preferring lower budget utilization. This is a feasibility heuristic, not a globally optimal or socially fair allocation. Exhaustion differs from reaching a search limit. The independent verifier uses its own case validation and assignment calculations, rather than the planner's helpers. Its content review compares the case and plan against the user's actual instructions. Leader permits one correction round, then delivers a verified schedule or a clearly blocked draft.

## Ownership and interfaces

- Root shared `rota-evidence` Skill supplies only the data contract and low-level I/O/structural checks.
- Every role has its own workflow Skill and persona. Leader alone has AGENT.md.
- Analyst owns intake; planner owns search; verifier owns independent recomputation/content review; Leader owns final HTML/CSV/JSON delivery.
- Scripts are ordinary packaged Python programs executed through existing authorized host shell/file tools. They are not fictitious native Tool registrations. Member Skills have member-relative declarations. Root Skills are available to every member; this is not security isolation.
- Reports bind original input bytes, canonical case values and plan bytes. Leader re-reads original input, rechecks every assignment and compares independent totals before delivery. Input edits invalidate previous reports. Script results never certify that members participated; actual host traces and manual screenshots must establish that separately.

## Invariants and failures

Every occurrence is covered exactly once by an eligible, available participant. Per-day and weekly minutes cannot exceed agreed caps. Preference misses remain visible and do not override hard limits. IDs are stable ASCII identifiers, labels are Chinese UTF-8 text, dates are calendar-valid, and minutes are bounded integers. Reject duplicate keys/IDs, unknown fields, bool-as-integer, invalid references, missing data and malformed/stale reports. Read explicit regular files only, bounded in size; never overwrite existing output directories. Escape HTML/CSV data. Partial failures remain evidence, not completed deliveries.

Planner outcomes are feasible / infeasible after exhaustive bounded search / unknown at its node limit. No non-feasible report receives a verified-calendar verdict. A reviewer block or disagreement remains visible; a script success cannot override it. No proof of optimality, calibrated difficulty, personal ability, medical suitability or agreement by household members is inferred from arithmetic.

## Verification plan

Meaningful source and extracted-package tests cover complete cases, all 21 occurrences, availability/caps, preference misses, stale/tampered assignments and reports, negative input cases, bounded search status, conflicting review, Chinese/escaped outputs and existing-output refusal. Official Hub CLI validate/pack, security preflight and exact archive equality are separate from actual host creator/loader, import and four-member handoff tests. Scripted loopback-model host integration proves plumbing only; autonomous model quality and user manual acceptance remain pending.

All implementation, tests, records, packages and isolated runtime state stay inside this asset. No host, SDK, core API, shared dependency or other-asset modifications. No paid model/API calls, delivery push, PR, merge, Release or Hub operation in Phase 2.
