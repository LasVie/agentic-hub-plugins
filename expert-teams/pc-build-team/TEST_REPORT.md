# Test report — pc-build-team (装机专家团) 0.2.1

Task AH-20261104-pc-build-team. Owner Vannes Wijaya.

## Local functional tests

2026-11-04; openjiuwen SDK from the local jiuwenswarm venv, CPython 3.12.14, markdown-it-py 4.0.0, Google Chrome 156 headless, Linux (WSL2).
Command: `python -B tests/test_build_checker.py <extracted-zip>/agents/leader/tools/build_checker.py <pdf-dir>`.

- 0.2.1 extracted release ZIP payload: 45/45 passed.

Coverage: hard and soft rules (socket, memory type, GPU and cooler clearance, case form factor, PSU headroom, connectors, M.2 and DIMM slot counts); `user_budget` overrides an inflated per-build budget (5000 → 2000) with a warning; `export` requires `user_budget` and an absolute, existing, bilingual `.md` file with source links; unknown or inline placeholders rejected; raw HTML in Markdown escaped; missing required blocks go to an appendix; no placeholder left in the output; no PDF overwrite; slot-name matching (exact, unique prefix, ambiguous not guessed); headless-Chrome check that no diagram element overflows its frame (sample data and long part names).

## Host tests (WorkSwarm, user-run by Vannes Wijaya)

Same prompt both runs: "Plan a PC for 1440p AAA gaming on a budget of 2000 SGD, buying from Singapore shops. I have no parts yet. Save the PDF to …".

- **deepseek/deepseek-v4-pro**, session web_1a1a46d33cb_ca3796cc4eb1, 10:39–11:20 (≈40 min). Research ≈25 min across ~13 Singapore shops plus maker spec PDFs; `validate` and `export` both called with `user_budget` 2000. Result: 10-page bilingual PDF; main build SGD 1,993.18 within budget, 14/14 rules pass; budget build SGD 1,821.18; performance build SGD 2,780.18 labelled over budget; board map highlights DIMM_A1/B1 and M2_1. Screenshots 01, 02.
- **openai/gpt-6-luna**, session web_1a1a571774f_a26ac82e34a2, 15:23 (28 min). 11-page bilingual PDF exported; all three builds over budget (main SGD 2,501) and clearly flagged as such. Screenshots 03, 04.

## Known issues (non-blocking)

- With gpt-6-luna the leader added a "documenter" member despite the no-extra-members rule.
- Final prices came from Dynacore and TechDeals only, although more shops were researched.
- The WorkSwarm sidebar can keep a running spinner after the team finishes (host UI).

## User test confirmation

"0.2.1 testing passed, no blocking issues." — Vannes Wijaya, 2026-11-04, ZIP SHA-256 8ae7e5705ab994f6ee7fa5eac2035336dd524b817a57e537546f3e0e0ed3e63a.
