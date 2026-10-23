# FET timetable audit: source and distribution review

Reviewed 2026-10-23. Candidate `CAND-CLD-219`; task `AH-20261023-fet-timetable-audit`; owner Cai Zhenze. Naming: upstream `fet` → **课表校验与导出** → `fet-timetable-audit`. Local version 1.0.0 is independent of upstream 1.2.1. The user approved the offline audit/export scope in the current conversation; claim/task were written and verified before implementation.

## Functionality and source

Compared `child-after-school-planning-team` 4388eb53fbc4495ebefe271d0ee466fb@0.0.1, `time-management-optimization-team` 748c5ba007174fd3aed776cb31f96fec@0.0.1, `editorial-calendar` e7d544bde62d408dbce9f4428bcf34cc@1.0.0 and `research-codebook-conformance` 43e55c7831c4428e935444ae44a48ab6@1.0.0. Advisory planning, content calendars and research CSV/codebook checks do not parse `.fet` relationships or verify school activity assignments. Live development records/current main 49eaab9 also covered Tarot 1.0.4, DSH 韵律分析 1.0.1 and vault/piano/simulated-life; none supplies timetable checking.

Scope: references, workload against available grid slots, supplied teacher/student overlap, unplaced/overflow activities, supported 100% unavailable-time constraints and filtered CSV/JSON export. Unsupported constraints are disclosed. No solving, repair, full feasibility proof, room-conflict validation, FET executable or OR-Tools.

Fixed source: https://github.com/nispa/fet-claude-skill/tree/beb2e1193665deb68b8f29d7617e7bb972573d95 . Checkout matches this commit; `.claude-plugin/plugin.json` declares 1.2.1. Inspected the tree, full root LICENSE, README, reference, three scripts and test source. No additional license/NOTICE, bundled FET binary, media or vendored dependency was found. `audit-upstream` identified the root MIT-like text; the actual full-text/scope review supplies the permission conclusion.

## Reuse and distribution

Full MIT license: **Copyright (c) 2026 nispa**. It grants modification/distribution of this software and associated documentation subject to retention of the original copyright/permission notice. The complete disclaimer is also retained under repository policy. No conflicting restriction was found for the selected scripts. Upstream identifies FET as a separate AGPLv3 program; no part of that executable, setup/run script or OR-Tools module is included here.

| Original path | Fixed-source SHA-256 | Delivered use |
| --- | --- | --- |
| skills/fet/scripts/fet_common.py | 0ba754369e54845378795770400711e91e71aef3f182bf40a394ab1f38417734 | lib/fet_audit.py: parser and student expansion |
| skills/fet/scripts/fet_inspect.py | 7cd5f1a84fd692d65edf2e6e60a8eea282bf3bb6286bf375c2ab18f4743ebefb | lib/fet_audit.py: references and workload |
| skills/fet/scripts/fet_timetable.py | 4e1b6f80f5009480049383bc0c871d88996822c7717c393823840ecabda4e770 | lib/fet_audit.py: occupancy, filtering and export |

The merged port identifies the three original scripts, preserves applicable original encoding/header information and records modifications. Changes add bounded local UTF-8 XML parsing, duplicate/invalid-ID and malformed day/hour handling, consistent inherited availability, structured Chinese results, explicit coverage, and CSV formula-text protection. This is a port, not an independent-implementation claim.

The native adapter, metadata, Chinese Skill/README, CLI and Chinese fictional fixtures are newly authored for this port. Upstream tests/examples were inspected but no real school data or upstream dataset is bundled. Scaffold and companion-builder structure reuse this repository's template/prior utility; no new repository-wide license is assigned.

Runtime code requires Python's standard library; the adapter uses the host's existing openJiuwen SDK, which is not vendored. No npm packages, external service, credentials, images, icons, fonts, upstream prompt text or branding artwork are copied. Original legal text remains English; human-facing instructions/results are Chinese. No official affiliation or endorsement is claimed.

## Bundled evidence and release audit

- Complete MIT text: `licenses/fet-claude-skill/LICENSE`, SHA-256 `e3ed89d5dfdbd375ad42d40bce582e5d35f4749e5e2a9112e975965f6cec9cfb`, byte-identical to pinned upstream.
- `THIRD_PARTY_NOTICES.md` lists the source/version, rightsholder, paths and modifications. Upstream NOTICE is absent; none fabricated. Apache-specific obligations are not applicable.
- `provenance.json`: `mode: ported`, `permission_status: verified`, actual reused destination and license hash.
- Canonical ZIP prefixes these paths with `fet-timetable-audit/fet-timetable-audit/`. Extracted file/license equality, declarations and exact archive checks are recorded in TEST_REPORT.md after packaging. The WorkSwarm companion removes only the market wrapper.

Final archive audit on 2026-10-23: canonical 1.0.0 SHA-256 `20ce4ca8188428a8d8abd957be6158f83d76337322cf70ba78c9b3ba1b80c911` contains the wrapper and eight runtime files. Every inner file matches source and the native WorkSwarm companion byte-for-byte. Extracted `fet-timetable-audit/fet-timetable-audit/licenses/fet-claude-skill/LICENSE` matches the full original MIT text and the provenance hash above; the corresponding `THIRD_PARTY_NOTICES.md` and `lib/fet_audit.py` attribution/modification header are present. Declared paths resolve, matching versions are 1.0.0, and no development fixtures, tests, caches or screenshots are bundled. All 43 tests also passed against the extracted payload with the real SDK, without skips. No unresolved license/distribution condition was found for this archive.

Permission is **verified for these selected MIT software paths and distribution scope**. No unresolved reuse condition identified. This does not grant trademark rights or decide a new license for team-owned materials. Content review, functional testing and actual host testing are separate checks.
