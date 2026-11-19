# Verification — household-chore-rota-team 1.0.0

Task `AH-20261117-household-chore-rota-team`, owner Cai Zhenze, Candidate Not Applicable. The automated verification below was recorded on 2026-11-17. Cai confirmed the exact 1.0.0 package passed manual testing on 2026-11-19, before GitHub delivery.

## User confirmation and delivery review, 2026-11-19

Cai explicitly confirmed manual testing was complete and passed, and supplied five original PNGs. See `tests/records/user-confirmation-20261119.json`, linked Progress Report `RPT-20261119-household-chore-rota-team-user-confirmation`, and `evidence/user-testing-1.0.0/index.json` for filenames, dimensions and hashes. The screenshots show native member tasks, the source-only verifier baseline, completed handoffs, Chinese calendar and CSV. They do not show file-picker installation or failure exercises. The supported management import and failure cases are documented in the earlier host verification below.

The user-run `shared-home` case preserved all seven chores and 180 agreed minutes. Weekly totals were 55, 45 and 80 minutes. The only preference miss was `c04`, assigned to the eligible, available participant. Analyst intake and planning preceded independent arithmetic and content review. The planner ran the packaged delivery script after both reviews passed, and the Leader presented the verified deliverables. The saved baseline, intake, plan, independent review and review notes match the delivered audit's input and report digests. The calendar and CSV agree on all seven rows. Every declared file in the installed user-host group matched the frozen native ZIP.

The pre-submit check replayed delivery using the exact extracted script and saved handoffs in a fresh directory. It reproduced all three existing user-run output files byte for byte without invoking a model. The 23 tests passed again against both source and the unchanged native extraction. Preflight and exact native/wrapped identity checks also passed. See `tests/records/delivery-review-20261119.json`. The original manual artifacts and full engineering logs were retained locally. Path references in the published CLI, creator and preflight records are normalized to avoid carrying machine-specific paths.

## Program behavior

`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s expert-teams/household-chore-rota-team/tests -p test_rota.py -v` passed **23 source tests and 23 exact-extracted tests** on Python 3.10. Actual CLI subprocesses exercised intake → planning → independently implemented verification → Leader delivery. The seven-duty case totals 180 agreed minutes; the six-person/21-occurrence case totals 315 minutes. Availability overrides a conflicting soft preference; all outputs remain Chinese UTF-8. Tests include missing/duplicate duties, wrong totals, eligibility/unavailable/daily/weekly constraints, stale input/report hashes, content-review blocking, a forged passing review defeated by Leader recomputation, impossible versus search-limited cases, malformed/duplicate-key input, symlinks, existing-output refusal, strict numeric representation, false optimality claims and HTML/CSV escaping. Records: `tests/records/source-tests.json`, `source-tests.txt`, `extracted-tests.txt`.

These are deterministic program/fixture tests. Content-review notes in these tests are explicitly fixture-supplied, not real expert judgment. No model, network or household-data access is used by this suite.

## Exact packages and completed packaging checks

| Archive | Bytes | SHA-256 |
|---|---:|---|
| `test-packages/household-chore-rota-team-1.0.0-native.zip` | 75625 | `d9545a66730afc6748407af543b5e2265990d61f0cfb06985339afa41bd363c9` |
| `release/1.0.0/household-chore-rota-team-1.0.0-agent-group.zip` | 39588 | `7942f574b44e545b984b3674b4e781bdbb97b7567ff912b9f0ef6d37c05a26af` |

The 25 runtime files match source, native ZIP, wrapped ZIP, extracted test payload and installed manual-host payload byte for byte. Per-file digests are in `release/1.0.0/artifact.json`; independent final comparisons are in `tests/records/final-verification.json`. Native manifest is at archive root. The wrapper has one top-level slug, the full inner native directory, `plugin.yaml` with `type: agent-group`, and original geometric calendar/tick icon. Neither ZIP includes tests, host state, credentials or frameworks.

Actual official Agentic Hub CLI 0.0.1 at `c8ee4ef44be0453470114aa5a19f4e1017462907`: init → validate → pack passed. `build_packages.py` compares native/wrapped paths and bytes, CRC, symlinks and archive bounds. Source/native/wrapper repository preflight passed; no JavaScript files or known dynamic-JavaScript signatures were found (`tests/records/preflight.json`). That limited scan is not general security certification. Wrapper success is separate from team validation.

The actual host creator accepted the final extracted four-member package. Actual `openjiuwen.agent_teams.experts.agent_group.load_agent_group_package_bundle` (SDK 0.1.20) assembled all four templates, Leader entry, each member's own private Skill and shared evidence Skill (`tests/records/host-loader.json`). Three unchanged negative assembly checks (wrong member type, missing Leader entry, missing member) are explicitly reused from the pre-freeze draft with original hash/reason recorded; the final positive load was rerun. Supported management import/install/show/list recognized `agent_group`, version 1.0.0 and all four members. Installed files matched the final ZIP (`host-import.json`, `manual-host-import.json`).

## Actual host execution with a scripted provider

The existing WorkSwarm host and compiled frontend were used read-only. Each scenario had fresh task-owned runtime/configuration, registry, task database, logs, temporary files and loopback ports. No credentials or shared configuration were copied. A deterministic loopback provider drives actual native members, delegation, tasks, Skills, messages, bash commands and files; it does not establish autonomous reasoning or user acceptance. No paid model/API calls were made.

| Record under `tests/records/` | Planner | Independent math | Delivery |
|---|---|---|---|
| `host-complete.json` — 7 duties | feasible | pass | verified |
| `host-full.json` — 21 duties | feasible | pass | verified |
| `host-impossible.json` — no eligible person | infeasible after exhaustion | block | draft |
| `host-limited.json` — bounded search exhausted | unknown | block | draft |
| `host-content-blocked.json` — fixture content objection | feasible | pass | draft |

Each record captures all four members and scoped Skill reads, 258 host events, command exits, input-first verifier baseline, report/output hashes and the fixture boundary. At each verification checkpoint the four roles had 28 captured scripted model requests in total; this is a harness observation, not a billing estimate or real-model promise. The verifier's original-input baseline precedes the planner. Content-review text is fixture-supplied. The actual host produced HTML, CSV and audit JSON.

## Phase 2 manual host and browser observations

Isolated instance: **http://127.0.0.1:6645/**; HTTP 6645, local provider 6646, agent 28645, web 29645, gateway 30645. State: `.local/host-manual-final/`. Exact package installed; default `household-rota-scripted-fixture` cannot perform autonomous manual tests. User must configure their own authorized real model or import the exact native ZIP into their already configured compatible host. Other instances' keys/settings were not borrowed.

The installed-team detail page showed Chinese name, version 1.0.0, four members, five Skills and Chinese instructions. The route **专家管理 → 我的专家 → 专家团 → 创建 → 上传文件创建** and Expert Team category were observed. GUI file upload completion remains unverified: Chrome chooser returned no handle; native fallback was unavailable while Mac locked. No extension/security or OS settings changed. Supported management import is separately verified and does not imply GUI-upload success. This exact route needs manual testing.

The scripted host's seven-day Chinese calendar rendered in Chrome. The 180-minute table, preference exception and fixture label were readable. The local engineering capture and synthetic preview documented layout before the user tested the package. The user originals are indexed separately above.

## Pre-freeze correction and evidence history

An initial 20-test checkpoint preceded packaging/host checks. Review found Python equality could accept `35.0` where a report requires integer `35`. Before any user test handoff, report comparisons became canonical/type-sensitive, intake counts were tightened, and false optimality/search metadata was rejected. Three regressions were added; all 23 tests and affected final package/host scenarios were rerun. Initial native ZIP is retained unchanged in `test-packages/history/pre-freeze-1.0.0/` with original hash and superseded label. Draft logs/wrapper remain in ignored `.local/pre-freeze-1.0.0/`. Neither draft was handed off as the final user-test package.

## Project Lead acceptance

`MANUAL_TESTING.md` describes the exact packages, setup and cases. The successful user run and its scope are documented above. GitHub delivery and Project Lead acceptance are tracked in the original Development Task and its Progress Reports.

## Evidence boundaries

The scripts validate the agreed data. Household effort, fairness and consensus require human judgment. The host records demonstrate member participation, and role-scoped Skills provide workflow guidance. The planner reports `unknown` on reaching its node limit. Infeasibility and content objections prevent a verified rota.
