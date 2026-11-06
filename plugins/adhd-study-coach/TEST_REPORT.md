# Functional test report — ADHD 学习教练 1.0.0

Owner Nguyen Trung Dung; Task AH-20261106-adhd-study-coach; Candidate CAND-CLD-288.
Test date 2026-11-06 Asia/Singapore. Local branch feat/adhd-study-coach from main e8258e9.

## Exact package identity

- Stable ID repo:agent-plugin:adhd-study-coach; upstream ADHD Study Coach -> ADHD 学习教练 -> adhd-study-coach.
- Native import: test-packages/adhd-study-coach-1.0.0-native.zip; 56098 bytes; SHA-256 67844108ca8f3b498d967be36056f37aad018e8011fe40138fcdc02fa7b47e2d.
- Canonical marketplace archive: releases/agent-plugin/adhd-study-coach/1.0.0/adhd-study-coach-1.0.0.zip; SHA-256 f670d3ad797d05ddd35685e3239244c2f4c1075102b6c75f4dc7bfb2404ed7f9; 57152 bytes.
- Six runtime files (README.md, THIRD_PARTY_NOTICES.md, licenses/adhd-study-coach/LICENSE, manifest.json, skills/adhd-study-coach/SKILL.md, tools/study_card.py) are shared unchanged by source, native and canonical formats. The bundled MIT license (SHA-256 d9487d7e75e16293408fe8556dc940f400c0d6e7fbeed42a7d149a5be43fd748, 1069 bytes, LF) is byte-identical to the raw Git blob of the pinned upstream LICENSE (blob b0ed61b8356ec0529ba1ca429dc38074ca34e688), compared with `git cat-file blob`. No data, image, icon, binary, dependency package, credential or cache is included.

## Scope actually delivered

One Skill plus three native read-only calculation tools (`adhd_card_inspect`, `adhd_card_review`, `adhd_card_log_session`). The Skill is a Chinese adaptation of the instruction text of upstream ADHD Study Coach 0.2.0 @eec04896c443b76d34546698905ec0911fa3f17f (MIT); the tools are original. No network, no file access, no stored state: the learner keeps a plain-text Progress Card. No diagnosis or treatment claims. See SOURCE_REVIEW.md and NATIVE_DESIGN.md.

## Environment and executed checks

Windows 11, CPython 3.11.9, openjiuwen 0.1.20.post1 from PyPI in an isolated venv outside the repository (D:/jiuwen_repos/outputs/pitwall-build/venv); the plugin itself uses only the Python standard library. PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1, -B. Extracted payload and raw evidence live under D:/jiuwen_repos/outputs/adhd-build, outside the payload. Zero model calls.

1. `python tools/asset_release.py check plugins/adhd-study-coach`: format_ok true.
2. `python -B plugins/adhd-study-coach/tests/test_adapter.py`: 37/37 offline checks pass against the source and, separately, the exact extracted native payload. Covers: three real ToolCards with closed schemas and Chinese descriptions; stream equals invoke; 25 invalid-argument cases rejected (non-object, unknown field, bad/impossible/out-of-range dates, empty or oversized card, empty/oversized/invalid grades, wrong types, booleans as integers, nulls inside objects); null treated as absent; internal errors do not leak details; new learner routes to onboarding; due-today counts as due and future does not; overdue days; nothing-due routing; recent open loops; solid reviews walk 1→3→7→16→35→90→90 with matching due dates; odd or oversized intervals never shrink; shaky keeps the interval and returns tomorrow; blank resets interval and streak, adds a lapse; worst grade wins; key point update; unknown and duplicate topics; review is all-or-nothing and never mutates the input card; log_session creates or updates cards without moving the schedule of existing topics; only the last 10 recent rows are kept; check-in every 5 sessions and its reset; subject/plan/preference merging without duplicates; render-parse round trip; the README sample card parses and round-trips; surrounding text and code fences tolerated; injected instruction lines inside a pasted card are rejected, not obeyed; injected text inside fields is neutralised (no new lines, no pipes, no early card end); structural prefixes (`---`, ```` ``` ````, `===`) in fields cannot make a saved card unreadable or drop rows; 11 kinds of malformed card get CARD_INVALID; limits (150 topics, 12 subjects) give CARD_TOO_LARGE instead of silent truncation; date defaults and 2000–2100 range; deterministic Chinese output that does not echo the card; the source has no network, file, environment, process or dynamic-execution access; manifest, Skill and tool names agree; every payload file is UTF-8 without BOM and Chinese where it is user-facing; the Skill states the safety boundaries.
   One real defect was found by these tests and fixed before packaging: a subject or topic starting with `---` or a code fence could make the saved card unreadable on the next load or silently drop its row. Such sequences are now replaced when a field is cleaned, and the case has a regression test.
3. `tests/host_checks.py` loads the extracted native payload in a real DeepAgent with SkillUseRail, ability manager and Runner: all three tool names are visible with DIRECT exposure and Chinese descriptions; registered invalid input and an unknown field are rejected; log_session, inspect and review run through the Runner (new card, warm-up routing after one day, interval 3 after a solid review, next due 2026-11-10); all tools unload; payload hashes are unchanged. Passed for both the source and the extracted payload. This is real SDK execution, not a stub agent, a frontend conversation or a model-planned tool-choice test.
4. Chinese check of the extracted payload: every file decodes as UTF-8 with no BOM or replacement character; manifest display name, description, tags and quick inputs are Chinese; SKILL.md, README and notices are Chinese; tool descriptions, parameter descriptions, errors, warnings and summaries are Chinese. The bundled license is the unmodified English MIT text.
5. `tools/asset_release.py preflight` on the payload and the native ZIP: 0 JavaScript files, 0 dynamic-execution signatures.
6. `tests/test_adhd_study_coach.py` is the repository discovery entrypoint: native/canonical/source byte contract, license evidence, and the 37-test suite in a fresh process when the SDK exists; without the SDK that case explicitly skips and claims no success.
7. `asset_release.py pack` writes the deterministic canonical ZIP; repacking after this report was finalized reproduces the same ZIP bytes. `asset_release.py check-repo` result: see the final section.

## Real limitations and observed behaviour

- The tools only do date and interval arithmetic and card parsing. Teaching, questioning and grading are done by the model following SKILL.md, so quality depends on the model; this has not been judged automatically.
- Nothing is stored. Memory across sessions exists only if the learner saves and pastes the Progress Card.
- "Shaky" is implemented as "interval unchanged, review again tomorrow"; upstream only says "same interval, review again soon".
- The research citations in the upstream text were not independently verified by this team.
- No frontend conversation and no model-planned tool choice were exercised before user testing; no GitHub CI run exists before an allowed PR.

## User testing in WorkSwarm (2026-11-06, Asia/Singapore)

Nguyen Trung Dung tested the exact native ZIP (SHA-256 67844108ca8f3b498d967be36056f37aad018e8011fe40138fcdc02fa7b47e2d) in WorkSwarm with English prompts, in separate new conversations, and supplied original screenshots: three expanded tool-call panels (`adhd_card_inspect`, `adhd_card_review`, `adhd_card_log_session`) and four full conversation exports. Observed:

- First session: the coach loaded the Skill, took the learner through small chunks one question at a time, named a wrong assumption and replaced it with a concrete example, asked for a teach-back, then called `adhd_card_log_session` and printed a Progress Card (two topics, due 2026-11-07, interval 1).
- Next day (the learner supplied "Today is 7 November 2026" by typing it): `adhd_card_inspect` returned `stage: warm_up` with 2 topics due. After the warm-up, `adhd_card_review` received one topic graded solid and one graded shaky and blank. The result was 1 solid, 0 shaky, 1 blank; the solid topic moved to a 3-day interval (due 2026-11-10, streak 1) and the blank topic was reset to a 1-day interval.
- A pasted card cut off before its closing line was not loaded; the coach asked for the full card instead of guessing.
- A pasted card with version 2 and a damaged closing line: the coach corrected both itself, told the learner what it had changed, and passed the corrected card to the tool. The Skill says not to hand-edit cards, so this is a minor deviation; it was disclosed, and the tool itself rejects both defects (offline tests).
- A request to guarantee better grades was refused, with the evidence split into well-supported, reasonably supported and weak.
- The coach replied in English because the learner wrote in English; SKILL.md says to use Chinese and does not mention other languages, so this is a model choice. The package was not changed.
- A plain "Hi" received the host's generic greeting, not the Skill's three-line greeting, because the Skill loads when the learner asks to study.
- WorkSwarm shows no version string; one screenshot of the plugin switched on was not supplied, and the tool names and the "load the coaching skill" steps tie the evidence to this plugin.
- The model once wrote "the potassium moment" in the van Helmont story; this is model wording, not package content.
- No blocking issues were reported. The learner confirmed the display name ADHD 学习教练 and the scope (one Skill, three tools), and asked to proceed with the package as tested.

## Final repository checks

`asset_release.py check-repo` passes in a clean LF clone of main e8258e9 (core.autocrlf=false) with this asset added: 68 source assets, 81 release ZIPs. `tests/test_adhd_study_coach.py` passes 3/3 with the SDK in the working tree and in that clone. In the developer's own working tree `check-repo` fails with "license evidence hash mismatch: LICENSE" for 47 pre-existing assets because `core.autocrlf=true` checks their LICENSE files out with CRLF; this asset's LICENSE has LF bytes, is covered by a `-text` rule in `.gitattributes`, and is not affected. `tests.test_asset_release` has one Windows-only symlink-privilege error (WinError 1314) that also occurs on a pristine clone of main; it is unrelated to this change.
