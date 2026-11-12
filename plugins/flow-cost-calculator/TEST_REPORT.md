# Functional test report — 流动效率与持续成本测算 1.0.0

Owner Nguyen Trung Dung; Task AH-20261112-agile-forge-praxis; Candidate CAND-CLD-161.
Test date 2026-11-12 Asia/Singapore. Local branch feat/flow-cost-calculator from main 296dce9.

## Exact package identity

- Stable ID repo:agent-plugin:flow-cost-calculator; upstream Agile Forge Praxis -> 流动效率与持续成本测算 -> flow-cost-calculator.
- Native import: test-packages/flow-cost-calculator-1.0.0-native.zip; 49208 bytes; SHA-256 fd00eb2942c388963f6e633e4ca9fca5acf1bcce9e99ae7de89d4b6d937fa802.
- Canonical marketplace archive: releases/agent-plugin/flow-cost-calculator/1.0.0/flow-cost-calculator-1.0.0.zip; SHA-256 a75d6c68f867bb0f8c06c10a76bb542dc6838ce230f98e00508aa107ab1bebb8; 50606 bytes.
- Seven runtime files (README.md, THIRD_PARTY_NOTICES.md, licenses/agile-forge-praxis-plugin/LICENSE, manifest.json, skills/flow-efficiency/SKILL.md, skills/business-case-running-costs/SKILL.md, tools/flow_cost.py) are shared unchanged by source, native and canonical formats. The bundled MIT license (SHA-256 e48574787df82fe240185a85682b0020e066ca48d53810d4ae91d38df7e642be, 1085 bytes, LF) is byte-identical to the raw Git blob of the pinned upstream LICENSE (blob e5513a6bc43501fd0768eba4f8725553860a8b19), compared with `git cat-file blob` and `git hash-object`. No data, image, icon, binary, dependency package, credential or cache is included.

## Scope actually delivered

Two Skills plus two native read-only calculation tools (`flow_cost_flow_efficiency`, `flow_cost_business_case`). The Skills are Chinese adaptations of the instruction text of upstream Agile Forge Praxis 0.1.0 @db7c20facb516b7b7c0c2088882f52368c54468b (MIT); the tools are original and use exact rational arithmetic. No network, no file access, no clock, no stored state. The tools only do arithmetic: no normal values, no discounting, no judgement of good or bad. See SOURCE_REVIEW.md and NATIVE_DESIGN.md.

## Environment and executed checks

Windows 11, CPython 3.11.9, openjiuwen 0.1.20.post1 and pydantic 2.14.3 from PyPI in an isolated venv outside the repository (D:/jiuwen_repos/outputs/pitwall-build/venv); the plugin itself uses only the Python standard library. PYTHONUTF8=1, PYTHONDONTWRITEBYTECODE=1, -B. Extracted payloads and raw host reports live under D:/jiuwen_repos/outputs/flow-build, outside the payload. Zero model calls.

1. `python tools/asset_release.py check plugins/flow-cost-calculator`: format_ok true.
2. `python -B plugins/flow-cost-calculator/tests/test_calculators.py`: 38/38 offline checks pass against the source and, separately, against the exact extracted native payload. Covers: two real ToolCards with closed schemas and Chinese descriptions; stream equals invoke; 32 invalid flow-efficiency argument sets and 32 invalid business-case argument sets rejected with INVALID_ARGUMENTS and a Chinese message (non-object, unknown field, missing field, null, booleans/strings/NaN/inf as numbers, zero/negative/out-of-range values, bad enums, fractional integers, bad currency labels); upper boundaries accepted; both upstream control examples reproduced exactly (3 working days/20 h gives 24 h, 4 h, 83.3%; 42 calendar days/16 h gives 30 working days, 240 h, 224 h wait, 6.7%, lever A 29 days saving 1, lever B 16 days saving 14; 180,000/24,000/150,800 over 3 years gives 72,000, 252,000, 452,400, 200,400, 28.6%, 10,566.67, 17.0 months, 79.5%, 55.7%, +278%, 64,680 = 32%); the numbers quoted in the two SKILL.md check examples equal the tool output; custom lever parameters and lever flip; equal levers; yearly projection labelled as item-days; 100% flow efficiency and the below-5% flag including the exact-5% boundary; CAPACITY_EXCEEDED with the capacity maths (also for calendar days); exact fractional input (0.1 and 0.5 days); "=" only when the shown value is exact, "≈" otherwise; every formula line carries substituted numbers; ZERO_COST refusal; running-cost share bands at the 25% and 60% boundaries; payback "never" when benefit does not exceed running cost, over 50 years, and zero when there is no one-time cost; zero running cost flag and no break-even overrun; negative result without share-of-base and with a flag; custom usage and overrun scenarios; the two-dial comparison for all three outcomes; five-year horizon and currency label; no float noise (0.1/0.1/0.2 gives exactly 0.20); arguments not mutated and deterministic results; internal errors do not leak details; JSON-serialisable Chinese output; the source has no network, file, environment, process, clock or dynamic-execution access; manifest, Skill and tool names agree; every payload file is UTF-8 without BOM and Chinese where user-facing; both Skills state the "no normal values or rules of thumb" rule.
   No defect in the tools was found. Two failures in the first run were wrong expectations in the tests themselves (a lever saving of 1 h is 0.125 days, shown as 0.13; and 6.7% is not below the 5% threshold); the tests were corrected and a real below-5% case and the exact-5% boundary were added.
3. `tests/host_checks.py` loads the payload in a real DeepAgent with SkillUseRail, ability manager and Runner: both tool names are visible with DIRECT exposure and Chinese descriptions; registered invalid input and an unknown field are rejected; the capacity and zero-cost refusals are returned; calls through the Runner reproduce 6.7% / lever B and result 200400.0 / payback 17.0 months / share 28.6%; all tools unload; payload hashes are unchanged. Passed for both the source and the extracted native ZIP. This is real SDK execution, not a stub agent, a frontend conversation or a model-planned tool-choice test.
4. Chinese check of the extracted payload: every file decodes as UTF-8 with no BOM or replacement character; manifest display name, description, tags and quick inputs are Chinese; both SKILL.md files, README and notices are Chinese; tool descriptions, parameter descriptions, errors, warnings, formulas and summaries are Chinese. The bundled license is the unmodified English MIT text.
5. `tools/asset_release.py preflight` on the payload and the native ZIP: 0 JavaScript files, 0 dynamic-execution signatures.
6. `tests/test_flow_cost_calculator.py` is the repository discovery entrypoint: native/canonical/source byte contract, license evidence, and the 38-test suite in a fresh process when the SDK exists; without the SDK that case explicitly skips and claims no success. 3/3 pass with the SDK present.
7. `asset_release.py pack` writes the deterministic canonical ZIP; repacking after this report was finalized reproduces the same ZIP bytes (SHA-256 above). `asset_release.py check-repo` result: see the final section.

## Real limitations and observed behaviour

- The tools only do arithmetic. Asking for inputs, explaining results and stating limits are done by the model following the SKILL.md files, so quality depends on the model; this has not been judged automatically.
- The SDK logs "Failed to load description from .../SKILL.md: 'NoneType' object has no attribute 'fs'" for both Skills during the isolated host check. The already delivered adhd-study-coach logs the same warning under the same check, so it is attributed to the isolated no-filesystem check environment, not to the Skill files; whether the Skills load correctly is confirmed only by the user's WorkSwarm test.
- The ASOS flow-efficiency measurement quoted from the upstream text was not independently verified; the Skill calls it the upstream's claim.
- Calendar days are converted with 5/7 and holidays are not removed; the business case has no discounting, no ramp-up, no taxes or depreciation, and compares against an unchanged status quo.
- "Over 1 billion" amounts, more than 5000 days and more than 100000 items per year are refused as probable typing errors, following the upstream text; a legitimate case beyond these limits cannot be calculated.
- No frontend conversation and no model-planned tool choice were exercised before user testing; no GitHub CI run exists before an allowed PR.

## User testing in WorkSwarm (2026-11-12, Asia/Singapore)

Nguyen Trung Dung tested the exact native ZIP (SHA-256 fd00eb2942c388963f6e633e4ca9fca5acf1bcce9e99ae7de89d4b6d937fa802) in WorkSwarm with Chinese prompts (plus one English prompt) in one conversation between 14:51 and 15:07, and supplied original evidence: three screenshots (the plugin 流动效率与持续成本测算 listed and enabled in the Plugins panel with a `flow_cost_flow_efficiency` call behind it; the expanded `flow_cost_flow_efficiency` call and result; the expanded `flow_cost_business_case` call and result) and one full conversation export (2250x78498 px PNG).

Reviewed by the agent on 2026-11-12: all 22 prompts in the export were checked against values computed beforehand by running the same inputs through the tools (6 flow-efficiency, 8 business-case, 4 refusal and 4 behaviour prompts).

- Tool calls and results matched in every case: 6.7% / lever B 14 days vs 1; 83.3% / lever A 1.25 vs 0.25; 31.3% with 1,650 item-days; custom levers 2.50 vs 5.78; 1.3% with the below-5% check warning; 14.0% for 10 calendar days; 180,000 / 24,000 / 150,800 over 3 years (28.6%, 17.0 months, 79.5%, +278%, 64,680 = 32%); the same case over 5 years (454,000, 151.3%, 39.8%, +378%); the same case given as 18 万 / 2.4 万 / 15.08 万 (the model converted the units correctly); the never-pays-back case (-130,000, "永不"); zero running cost (flag and no break-even overrun); the equal-dials case (360,000 each); a 美元 label; and the 18.4% "below 25%" comment.
- Refusals worked: 3 working days with 30 hours returned CAPACITY_EXCEEDED, both costs 0 returned ZERO_COST, benefit 0 returned INVALID_ARGUMENTS, 6000 days was refused (over 5000); in each case the model explained the refusal in Chinese and asked for corrected input.
- The model followed the Skills: it listed the formulas with substituted numbers, used "≈" for rounded values, stated the limits, declined to give a normal value or industry average, and described the ASOS figures as the upstream's claim from one company that this project has not verified.

Observed behaviour that differs from what was expected, recorded for the Project Lead (none is a tool defect):

1. English prompt: the model answered in English although the Skills say to default to Simplified Chinese. The user accepted this (see the confirmation record below), as for the earlier japan-rain-alert test.
2. Missing day type (20 days): the Skill says to ask, but the model calculated both readings (20 working days 6.3%, 20 calendar days 8.8%) and asked which applies.
3. In the "running cost unknown" prompt the model said running costs on a 500,000 project are "usually a few ten thousand per year", which is the kind of rule of thumb the Skill says not to give.
4. In the lever comparison for 12 working days the model added its own yearly figures from the rounded saving (5.78 x 200 = about 1,156; the exact value is 1,155), marked with "≈".
5. Cosmetic model output: stray `**` characters in one reply and stray quote marks in another; two replies say "记录成立" where "成立" is meant.
6. Correction of the agent's own pre-test prompt sheet: it said the first prompt (42 calendar days, 16 hours) would show the below-5% warning; 6.7% is not below 5% and the tool correctly gave no such warning.

User test confirmation: the user chose "Passed as-is" when asked on 2026-11-12 at about 15:22 Asia/Singapore, meaning testing of this exact ZIP is complete with no blocking issues and the English reply to an English prompt is acceptable. Task AH-20261112-agile-forge-praxis; version 1.0.0; native ZIP SHA-256 fd00eb2942c388963f6e633e4ca9fca5acf1bcce9e99ae7de89d4b6d937fa802; canonical ZIP SHA-256 a75d6c68f867bb0f8c06c10a76bb542dc6838ce230f98e00508aa107ab1bebb8 (same payload bytes). Source: the current Claude Code conversation.

Evidence files (kept outside the repository tree until attached to the delivery PR): `Screenshot 2026-11-12 150836.png`, `Screenshot 2026-11-12 150847.png`, `Screenshot 2026-11-12 150953.png`, `jiuwenswarm-share-20261112-150956.png`.

## Final repository check

- `python tools/asset_release.py check-repo` in the working tree of this Windows machine reports `license evidence hash mismatch: LICENSE`. The machine has `core.autocrlf=true`, which checks out the LICENSE files of some already merged assets with CRLF; the bundled LICENSE of this asset is protected by `-text` rules in `.gitattributes` and was confirmed byte-identical to the pinned upstream blob (`git cat-file blob` compared with `cmp`; `git hash-object` e5513a6bc43501fd0768eba4f8725553860a8b19).
- The same command run in a separate clone with `core.autocrlf=false` (D:/jiuwen_repos/outputs/flow-build/lf-clone) with this asset's files, its release directory, its repository-level test and the updated `.gitattributes` copied in: passed, `source_assets` 72, `release_zips` 85. This is a structural check; functional tests are the items above.
- Repacking the canonical archive after this report was finalized reproduces the same ZIP bytes (SHA-256 a75d6c68f867bb0f8c06c10a76bb542dc6838ce230f98e00508aa107ab1bebb8); only `artifact.json` records a new report hash.
- Not yet done: user testing in WorkSwarm, original screenshots, user test-completion confirmation, push, PR and CI.
