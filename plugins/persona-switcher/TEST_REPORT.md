# Functional test report — persona-switcher 1.0.0

Task AH-20261027-persona-switcher; candidate CAND-DSH-095; display name 会话人设切换.

2026-10-27; actual openjiuwen native Tool/ToolCard SDK from the local jiuwenswarm venv, CPython 3.12.14, Linux (WSL2).

Command: `python -B tests/persona_switcher_functional.py [payload-dir]` — calls `PluginTool().invoke` with Chinese inputs in a fresh temp workspace (non-ASCII path); no mocks.

- Source payload: 32/32 passed.
- Extracted native ZIP payload: 32/32 passed.

Covered: default no role; empty library message; init adds 2 Chinese samples and never overwrites; use/role-to-role/none notices in Chinese; no notice on no-op switch; state persists across fresh tool instances; invalid/unknown id Chinese errors; create with UTF-8 ROLE.md frontmatter, 0600 permissions, overwrite gate; flat `<id>.md` read with capability fields ignored; empty body skipped with warning; default role; `none` not overridden by default; delete current role falls back to default; delete default clears it; corrupt state preserved as `.corrupt`; relative path rejected; unknown action rejected; symlinked role skipped; delete/overwrite refused without confirm=true; leave-role notice has no stray spaces; Windows drive paths mapped to /mnt/<drive> on WSL/Linux.

Not yet done: host UI install in desktop WorkSwarm and a model-backed session verifying the persona is actually adopted — that is the user test.

## Host test round 1 (superseded build)

2026-10-27, desktop WorkSwarm on WSL2, model deepseek/deepseek-v4-pro, session web_1a17c2f734e_9fc97ad216f1, user-run (Vannes Wijaya) with first 1.0.0 build (native ZIP e2ddb968…). Reviewed from session history: init, list, use tea-master (persona adopted), /role strict-reviewer (persona adopted), create poet + use (seven-character rhyming reply), default, none, model identity answer correct. Defects: delete executed without asking for confirmation; stray spaces in leave-role notice; model claimed default applies to new sessions after none. Fixed in rebuild 2 (tool-enforced confirm=true, notice text, clearer none message, Windows path mapping). Version kept 1.0.0 at user request because nothing was pushed; round 1 does not count as confirmation of the rebuilt package.

## Current package (rebuild 2)

Native test ZIP SHA-256 c75f33a45c1d0cc3f11d52e5f0e2cdbe960c5f9f53de9e045c4455e7a1b0940a; Hub wrapper ZIP SHA-256 995bb3011bf17f35075d0711da17b39ad313a95800e5a0c23542d8892741791a; payloads byte-identical. Assistant self-tests do not establish user completion or acceptance.
- Known non-blocking issue (accepted by user 2026-10-27): after `default` the model may say the default applies to the next new session; later replies corrected it. Round 2 host retest (session web_1a17c38e0c0_7d8311269a55) passed all 8 steps; see USER_TEST_CONFIRMATION.md.
