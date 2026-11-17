# Native design — 逻辑网格谜题编制与验解专家团

Approved by Cai Zhenze in Main 4.0 on 2026-11-17. The user explicitly corrected the destination to `expert-teams/logic-grid-puzzle-team/`. Task: `AH-20261117-logic-grid-puzzle-team`; Candidate: Not Applicable. This independent design predates implementation. No upstream puzzle implementation, puzzle dataset, copied prompt or media is an input.

## Functional boundary

Create original Chinese matching puzzles for teachers, activity organizers and puzzle authors. Exactly three categories of three or four distinct items; the first category anchors rows. Only explicit match/non-match clues and one-to-one matching are supported. All factual clues use controlled Chinese sentence templates. The complete search space is 36 or 576 assignments. No service, solver dependency, network request, arbitrary expression or host modification is needed.

Four native AgentTemplates: Leader clarifies/freezes the brief and delegates; Author chooses original vocabulary/clues and submits a model; Modeler enumerates the model and produces learner-visible source; Reviewer independently reconstructs the learner source and solves using a different algorithm, checks language/content and reports blocking disagreements. Leader routes specific clue IDs back for at most two repairs. A mathematical certificate is distinct from evidence that a separate member participated.

Scripts are member-owned resources invoked with the existing host command tool, not fictional registered Tool classes. Private Skills describe each role's script and task; only the collaboration protocol is shared. No model/MCP/subagent overrides, external leader runtime or root DAG extension.

## Authority and outputs

Inputs are data, never instructions to execute. Strict bounded JSON, controlled clue strings, existing-reference and unknown-field checks. Modeler and Reviewer use separate enumeration implementations. Final exporter recomputes source/model/review agreement and answer, rejects stale/tampered reports, escapes HTML, and writes exclusively into a new directory. User originals are never overwritten. Output: learner-only `puzzle.html`, separate `answer.md`, structured audit and source/review evidence. Explanations state checked entailments, not a promise of minimal clues, calibrated difficulty or deduction-only human solvability.

Ready-for-manual-testing requires source and extracted-ZIP functional failure checks, official CLI validation, actual target loader, actual installation and native delegation/tool/artifact integration. Scripted loopback-model fixtures are labeled and cannot establish semantic model reasoning. Paid calls are not authorized. Final user confirmation and original screenshots remain required before delivery.

## Research grounding and exclusions

- Bogaerts/Gamba/Guns, arXiv:2006.06343: logic-grid CSP explanation principles; no algorithm or text copied.
- Lin et al., ICML 2025, PMLR267/lin25i: CSP framing and complexity limitations; no ZebraLogic puzzle/data/code copied.
- Wu et al., arXiv:2308.08155 and official AutoGen termination tutorial: complementary conversation and author/critic precedents; no runtime/code/prompts copied. AutoGen is archived and not a dependency.
- Official pinned JiuwenSwarm AgentGroup package specification and agent-core loader: interface contract only.

Phase 1 compared live cross-type ledger, tasks, claims and merged PRs. General game design produces mechanics/economy/GDDs; game playtest produces player-feedback records; math-olympiad reviews proofs without a dedicated solution-counting tool; state-machine audit explores transitions. None of the inspected records provides this bounded original puzzle pack workflow. Main's procurement team is excluded in full and remains untouched. Recheck claims at future selection boundaries.

## User-authorized repeatable cycle

Preserve these Main 4.0 instructions for later cycles without changing shared team rules: research one genuinely native complementary team; check live cross-type records and subsequent claims, including unmerged work; wait for user selection; register under Cai Zhenze before implementation; use this separate worktree and a fresh unique branch based on current remote main. All code/tests/docs/packages stay in the selected expert-teams/<slug>/, apart from required non-code tracking. Never change the host, SDK, APIs, shared dependencies or other assets. Preserve Main and all parallel services. Use an isolated state/port allocation, actual host loader and supported Expert Team import; distinguish scripted checks from real model reasoning. No paid calls without separate authorization. Stop for exact-package manual testing and original screenshots. Only after that gate may GitHub delivery/CI/merge occur; no Releases or Agentic Hub actions. Refresh current AGENTS and PACKAGING at the relevant phase. This records this user's scope, not a new repository-wide rule.
