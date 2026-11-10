# Test report — grant-proposal-team (基金申请书专家团) 0.1.1

Task AH-20261110-grant-proposal-team. Owner Vannes Wijaya.

## Local functional tests

2026-11-10; openjiuwen 0.1.19 from the local jiuwenswarm venv, CPython 3.12.14, Linux (WSL2).
Command: `python -B tests/test_proposal_checker.py grant-proposal-team/agents/leader/tools/proposal_checker.py`.

- 0.1.1 native payload (identical to the tested ZIP): 22/22 passed.

Coverage: `criteria_map` (verbatim quote after whitespace normalisation, missing mandatory criteria, unknown criterion refs, duplicate IDs); `budget` (quantity × unit cost × years, stated line amount and stated total mismatch, total cap, category ratio caps, lines without justification); `limits` (mixed CJK/English counting, chars, words, whole-text limit, unknown sections); `score` (weighted ratio, weak threshold, unscored criteria, missing rationale); `review` (`ready_to_submit` only when every check passes and none is skipped); invalid input returns `success: false`.

Host loader: `agent-group-creator/scripts/register_group.py <extracted payload> --validate-only` with the jiuwenswarm 0.2.5.beta1 venv → `RESULT: PASS (5 agents)`.

## Host tests (WorkSwarm 0.2.5.beta1, deepseek/deepseek-v4-pro, user-run by Vannes Wijaya)

1. **English, 0.1.0**, session web_1a1c3661dca_621864fe1c02, ≈45 min. Correct order (guideline analysis → literature → methods and budget → draft → mock review → full check). Mock score 0.65 → 0.76 after one revision; final check passed. 31 references; 9 spot-checked on arXiv, all real. Track record not invented. Found: a contingency amount kept in the text but left out of the checked budget; internal tool names in the reply.
2. **Chinese, 0.1.0**, session web_1a1c396f6e2_47ed8af766cb, ≈23 min. Summary over limit (205/200) caught and fixed; honest "not ready" verdict (track record 0.40). **Blocking issue:** the user's budget (SGD 111k, cap 100k) was silently changed (RA 45k → 40k, GPU 15k → 12k) and the new figures were described as market prices.
3. **Chinese, 0.1.1**, session web_1a1c4137465_f041ffd69382, ≈21 min. Fix confirmed: the reply states the original 111,000 SGD is over the cap, lists every change (GPU 15,000 → 6,000; travel 3,000 → 2,000 per year; RA unchanged) with reasons and asks the user to confirm; two alternative options are in the planner's file; the budget in the proposal (100,000) equals the checked total. Length 190/200 and 1,844/3,000. Honest "not ready" verdict (track record 35%); the reply lists the information the user must supply. Screenshots `evidence/0.1.1/01-zh-request-and-team.png`, `evidence/0.1.1/02-zh-budget-adjustment-and-verdict.png`.

0.1.0 → 0.1.1 changes are text only (`agents/methods_budget_planner/persona.md`, `agents/leader/AGENT.md`, `manifest.json` version); the tool and rail are unchanged.

## Known issues (non-blocking)

- `self-review.md` can still show internal field names (`criteria_map`, `ready_to_submit`); the chat reply does not.
- The team may apply a proposed budget option before the user confirms it; it is labelled and the user is asked to confirm.
- Output is Markdown only (no PDF). Literature search depends on the host's search tools. DeepSeek stream idle timeouts caused retries in one run (host configuration).

## User test confirmation

"test is complete" — Vannes Wijaya, 2026-11-10, version 0.1.1, native ZIP SHA-256 a822f1a333c9360e5b90ba8e84c44f26782ab73da3c9063d67d751a99934f2dc. Recorded as RPT-20261110-grant-proposal-team-confirm-011.
