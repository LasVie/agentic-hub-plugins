# Test report — interest-heartbeat (兴趣心跳主动分享)

Task AH-20261028-heartbeat; candidate CAND-DSH-043.

## Local functional tests

2026-10-28; actual openjiuwen native Tool/ToolCard SDK from the local jiuwenswarm venv, CPython 3.12.14, Linux (WSL2). Command: `python -B tests/interest_heartbeat_functional.py [inner-dir]`, isolated temp data dir via `INTEREST_HEARTBEAT_DATA_DIR`, fixed clock in Asia/Shanghai for time-dependent checks.

- Source payload: 50/50 passed.
- Extracted native ZIP payload: 50/50 passed.

Coverage: status/cron prompt; configure validation with Chinese errors (bad window, number, timezone); interests set/remove; profile add/list with chat confidence cap and invalid kind; gate verdicts for quiet hours, busy window, cooldown, daily cap, pause, cross-midnight left-closed window, next-day reset; pick refusal under gate; browse due/not-due (outside window, min interval, daily sessions), focus rotation with 3-day cooldown; seed add/duplicate/same-topic merge, empty-text error, retire after 2 uses, chat seed retires after 1, news TTL expiry, category cap 16, hand-seed protection; late booking still counted with notice; carry note into pick and clearing; skip; audit events present and free of seed text; UTF-8 Chinese data; reset needs confirm; unknown action; 8 concurrent confirm_send calls with no lost entries; skill/manifest/tool card Chinese text.

Not covered locally: host cron scheduling, host web search, model judgement on whether to speak — these need the desktop WorkSwarm host test.

## Host test

Pending (user, desktop WorkSwarm).
