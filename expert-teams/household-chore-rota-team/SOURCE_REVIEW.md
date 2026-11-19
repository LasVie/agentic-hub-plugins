# Source and licensing review

Reviewed 2026-11-17 for Cai Zhenze, task `AH-20261117-household-chore-rota-team`; Candidate Not Applicable. Naming: independent Household Chore Rota and Review Team → 家务轮值与负担复核专家团 → `household-chore-rota-team`. Mode: **native**. No upstream implementation, prompts, data, figures, media or logos are copied into the runtime payload. This does not make a patent, trademark or service-terms exemption claim or assign a new repository-wide license.

## Material inspected and actual use

| Material | Pin / license evidence | Actual use |
|---|---|---|
| Google OR-Tools employee scheduling documentation | https://developers.google.com/optimization/scheduling/employee_scheduling, inspected 2026-11-17 | Functional concepts: coverage, availability, limits, preferences. No tutorial prose or code copied. |
| Google shift-scheduling sample | `google/or-tools` commit `c931f5f778c88050a3f71d72dfc30d3d020aa821`, `examples/python/shift_scheduling_sat.py`; header Copyright 2010–2025 Google LLC / Apache-2.0; root LICENSE inspected | Reference only. No CP-SAT code, OR-Tools, absl, binaries or examples bundled. Any future reuse needs exact-path notices/license review. |
| AutoGen original paper | https://arxiv.org/abs/2308.08155v2 | Historical multi-agent design research; no paper text/figures copied. No household-quality superiority inferred. |
| Microsoft AutoGen reflection documentation/repository | https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/reflection.html ; commit `8390985108cb1e3881f5f7297765758d8ad2540c`; code LICENSE-CODE MIT, documentation LICENSE CC-BY-4.0 | Bounded generation/reviewer workflow reference only. Project is archived; it is not a runtime dependency. No code/prompts/documentation copied. |
| Official WorkSwarm creator/package specification | `openJiuwen-ai/jiuwenswarm` `9843516a165bd9a6ad9c37f394fac90be128e551` | Package-interface reference; no host source bundled or changed. |
| AgentGroup loader | `openJiuwen-ai/agent-core` `5a35c39f0163a4e6190800df53ad7e24848756eb` | Existing supported loader contract; no SDK bundled. |
| Repository maintained Expert Team packaging/host-integration examples | current base `4e190253f00b2a1d65fdc657161a67fecde15a48` | Read for actual API conventions; business implementation is written for this approved scope. No dependency on another asset at runtime. |

All of these were seen before implementation. No non-reusable implementation was supplied for translation or laundering. Design is in NATIVE_DESIGN.md. Original Chinese prompts, documents, synthetic household cases and program code are authored for this package; no user private household records are bundled. Optional artwork, if present, is original programmatic geometry.

## Functional distinction and live claims

Phase 1 screened live candidate findings/claims (740 rows), 872 ledger records, development tasks, recent reports and PRs; reused existing valid findings. Current public details were rechecked for 家庭收纳改造团 `27b466e2b7824a1fa6e425b31df34436`@1.0.1 (space/storage planning), time-management-optimization-team `748c5ba007174fd3aed776cb31f96fec`@0.0.1 (productivity coaching), and 课表校验与导出 `45e9aed9a31a46e1a9d6c2eb92c039ef`@1.0.0 (audit existing school schedules, explicitly no generation). Existing offline-allocation-workbench selects binary jobs under budgets and explicitly excludes scheduling. The proposed core is user-constrained household-duty assignment across people/days plus independent workload checking, not renamed packaging for these assets.

Kickoff refreshed live tasks, candidate Notes/retired IDs, Progress Reports and recent PRs. The procurement team, logic-grid team and newly claimed robot-route-review-team are excluded. Their acceptance/ownership/evidence records remain untouched. No competing household-rota claim was found. No candidate row or public Hub identity is invented.

## Distribution audit

The native edition requires Python 3.10+ standard library and a compatible WorkSwarm AgentGroup host with delegated file/shell tools and an authorized model. On 2026-11-19, the exact native and wrapped ZIPs were inspected against the 25-file reviewed source and the installed user-host package. Scripts, prompts, documents, synthetic data and the original icon are independently authored. The archive contains no third-party files that require bundled licenses, notices or modified-file statements. The development harness reuse below is outside both ZIPs. Package digests, the prior loader and host tests, and the user's confirmation are recorded in TEST_REPORT.md and release/1.0.0/artifact.json. The Project Lead retains responsibility for repository-owned licensing and final acceptance.

## Development-only reuse

The maintained repository test harness `expert-teams/logic-grid-puzzle-team/tests/host_integration.py` at the current base is adapted under this task for process isolation, management RPC and a loopback scripted provider. Its exact original hash and adapted path are recorded in provenance.json. This is repository-owned test-tooling reuse, not third-party runtime code or a new license decision. All puzzle-specific business commands/expectations are replaced by this task’s real chore entry points and negative cases. The harness is outside both runtime ZIPs; the original asset and its evidence are unchanged.
