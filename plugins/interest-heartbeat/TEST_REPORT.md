# Test report — interest-heartbeat (兴趣心跳主动分享)

Task AH-20261028-heartbeat; candidate CAND-DSH-043.

## Local functional tests

2026-10-28; actual openjiuwen native Tool/ToolCard SDK from the local jiuwenswarm venv, CPython 3.12.14, Linux (WSL2); CLI checks run with the system `python3` in a separate process. Command: `python -B tests/interest_heartbeat_functional.py [inner-dir]`, isolated temp data dir via `INTEREST_HEARTBEAT_DATA_DIR`, fixed clock in Asia/Shanghai for time-dependent checks.

- 1.0.1 source payload: 55/55 passed.
- 1.0.1 extracted native ZIP payload: 55/55 passed.
- (1.0.0: 50/50 on source and extracted ZIP; superseded.)

Coverage: status/cron prompt; configure validation with Chinese errors (bad window, number, timezone); interests set/remove; profile add/list with chat confidence cap and invalid kind; gate verdicts for quiet hours, busy window, cooldown, daily cap, pause, cross-midnight left-closed window, next-day reset; pick refusal under gate; browse due/not-due (outside window, min interval, daily sessions), focus rotation with 3-day cooldown; seed add/duplicate/same-topic merge, empty-text error, retire after 2 uses, chat seed retires after 1, news TTL expiry, category cap 16, hand-seed protection; late booking still counted with notice; carry note into pick and clearing; skip; audit events present and free of seed text; UTF-8 Chinese data; reset needs confirm; unknown action; 8 concurrent confirm_send calls with no lost entries; 1.0.1 CLI entry (cron prompt carries absolute CLI path and full flow, CLI beat, shared data with the tool, invalid JSON and unconfirmed reset errors); skill/manifest/tool card Chinese text.

## Host test round 1 (1.0.0)

2026-10-28, desktop WorkSwarm (debug services on WSL2), user-run by Vannes Wijaya; reviewed from session history, gateway log and the plugin audit log.

- Session web_1a1804b3363_1045c2ce2491: "开启心跳…" → status shown in one table and changes asked once (defect: interests stated in the request were asked about instead of saved). Follow-up → interests set; host cron job 兴趣心跳 created (hourly, Asia/Shanghai, bound to the session, cron prompt verbatim). "跑一次心跳" at 10:17 → beat (SPEAK, browse not due) → pick (empty) → skip; user saw only HEARTBEAT_OK.
- Cron run 11:00 (session __cron___1a18073438f_a11033ee971c): fired on schedule; browse due with focus 咖啡; 2 seeds added with URLs; browse_done; pick; one Chinese sentence shared with source link; confirm_send booked 1/10. Defect: host cron sessions are created fresh and do not inherit the session's `plugin_names` (only MCP is inherited, `cron_runtime._inherit_session_mcp`), so the `interest_heartbeat` tool was absent and the agent improvised by importing the engine via bash.

Fixed in 1.0.1: skill saves settings stated in the request and skips the follow-up question when the user says to use defaults; new `runtime/cli.py`; `status` returns a self-contained cron prompt with the absolute CLI path and the full beat flow. Round 1 does not count as confirmation of 1.0.1.

## Host test round 2 (1.0.1)

Pending.
