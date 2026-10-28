# Test report — interest-heartbeat (兴趣心跳主动分享)

Task AH-20261028-heartbeat; candidate CAND-DSH-043.

## Local functional tests

2026-10-28; actual openjiuwen native Tool/ToolCard SDK from the local jiuwenswarm venv, CPython 3.12.14, Linux (WSL2); CLI checks run with the system `python3` in a separate process. Command: `python -B tests/interest_heartbeat_functional.py [inner-dir]`, isolated temp data dir via `INTEREST_HEARTBEAT_DATA_DIR`, fixed clock in Asia/Shanghai for time-dependent checks.

- 1.0.3 source payload: 67/67 passed.
- 1.0.3 extracted native ZIP payload: 67/67 passed.
- (1.0.2: 63/63; 1.0.1: 55/55; 1.0.0: 50/50; all superseded and never pushed.)

Coverage: status/cron prompt; configure validation with Chinese errors (bad window, number, timezone); interests set/remove; profile add/list with chat confidence cap and invalid kind; gate verdicts for quiet hours, busy window, cooldown, daily cap, pause, cross-midnight left-closed window, next-day reset; pick refusal under gate; browse due/not-due (outside window, min interval, daily sessions), focus rotation with 3-day cooldown; seed add/duplicate/same-topic merge, empty-text error, retire after 2 uses, chat seed retires after 1, news TTL expiry, category cap 16, hand-seed protection; late booking still counted with notice; carry note into pick and clearing; skip; audit events present and free of seed text; UTF-8 Chinese data; reset needs confirm; unknown action; 8 concurrent confirm_send calls with no lost entries; 1.0.1 CLI entry (cron prompt carries absolute CLI path and full flow, CLI beat, shared data with the tool, invalid JSON and unconfirmed reset errors); 1.0.2 cron schedule (default hourly skipping 01:00-08:00, cross-midnight quiet hours, 120/30-minute intervals, no quiet hours, configure returns an update notice, status exposes it) and the readable silent line; 1.0.3 cron prompt within the host 500-character limit, `$HOME` CLI path runnable from bash, skip reason requested, search-results URLs rejected as seed sources; skill/manifest/tool card Chinese text.

## Host test round 1 (1.0.0)

2026-10-28, desktop WorkSwarm (debug services on WSL2), user-run by Vannes Wijaya; reviewed from session history, gateway log and the plugin audit log.

- Session web_1a1804b3363_1045c2ce2491: "开启心跳…" → status shown in one table and changes asked once (defect: interests stated in the request were asked about instead of saved). Follow-up → interests set; host cron job 兴趣心跳 created (hourly, Asia/Shanghai, bound to the session, cron prompt verbatim). "跑一次心跳" at 10:17 → beat (SPEAK, browse not due) → pick (empty) → skip; user saw only HEARTBEAT_OK.
- Cron run 11:00 (session __cron___1a18073438f_a11033ee971c): fired on schedule; browse due with focus 咖啡; 2 seeds added with URLs; browse_done; pick; one Chinese sentence shared with source link; confirm_send booked 1/10. Defect: host cron sessions are created fresh and do not inherit the session's `plugin_names` (only MCP is inherited, `cron_runtime._inherit_session_mcp`), so the `interest_heartbeat` tool was absent and the agent improvised by importing the engine via bash.

Further finding (user report plus host code `gateway/cron/scheduler.py` `_push_to_targets`): cron results are not posted into the chat session; WorkSwarm shows them in its scheduled-task panel (calendar icon), with a placeholder card at push time and a result card per run, unfiltered — so silent runs would leave `HEARTBEAT_OK` cards, including hourly through quiet hours. `payload.kind=systemEvent` is converted to `agentTurn` (`cron_runtime.py`), so there is no in-session cron mode for plugins.

Fixed in 1.0.1/1.0.2 (1.0.1 was never host-tested): skill saves settings stated in the request and skips the follow-up question when the user says to use defaults; new `runtime/cli.py`; `status` returns a self-contained cron prompt with the absolute CLI path and the full beat flow; `status` also returns a cron expression and IANA timezone generated from settings that skips quiet hours (user chose "fewer runs + readable note" on 2026-10-28); silent runs reply with one readable Chinese line instead of `HEARTBEAT_OK`; skill, README and descriptions state that shares appear in the scheduled-task panel. Round 1 does not count as confirmation of 1.0.2.

## Host test round 2 (1.0.2)

2026-10-28, same host, user-run by Vannes Wijaya; reviewed from session history and the plugin audit log.

- Setup (session web_1a18092a391_aab22d6696a3): interests stated in the request saved without asking; paused=false and Asia/Shanghai set; one cron job 兴趣心跳 created with `0 0 0,8,...,23 * * ? *`; panel delivery explained. Defect: the first cron add was rejected (`description must be at most 500 characters`); the agent condensed the prompt itself.
- Cron runs 12:00, 13:00, 14:00 fired on schedule, all via the CLI path. 12:00: SPEAK, shared the second coffee seed, confirm_send 2/10. 13:00 and 14:00: both seeds already said today → skip → readable silent line. User confirmed each run appears as a 兴趣心跳 card in the panel and opens to the whole run.
- Defects: the shared link was a DuckDuckGo search-results URL saved by the 11:00 browse; runs posted process narration and a trailing status line; skips were logged as 未说明 because the condensed prompt dropped `reason`.

Fixed in 1.0.3: shorter cron prompt (≤500 characters with a `$HOME`-relative CLI path), asks for the skip reason and for no process narration; `add_seed` rejects search-results URLs; skill updated to match. Round 2 does not count as confirmation of 1.0.3.

## Host test round 3 (1.0.3)

2026-10-28, same host, user-run by Vannes Wijaya; reviewed from session history, gateway log and the plugin audit log. Screenshots in `evidence/1.0.3/`.

- Setup (session web_1a1812549e1_c181b0ea96bc, 14:14): interests saved directly; `status` cron expression and prompt used verbatim; cron job created on the first attempt (prompt 479 characters, `$HOME`-relative CLI path); panel delivery explained. The leftover 1.0.2 job was removed by id from another chat without pausing the heartbeat.
- Cron runs 15:00 and 16:00: CLI path ran from bash; beat → pick → skip with a recorded reason; the only reply was the silent line, with no process narration.
- Browse run (16:11, triggered by hand in the cron session after moving a browse window to 16:00-21:00; the host offered no run-now tool): focus rotated to 独立游戏; 2 seeds stored with article URLs (nintendolife.com, gamesindustry.biz); browse_done; one item shared in two sentences with its link; confirm_send booked 3/10.
- Host display issues, not plugin defects: the 15:00 card kept a running timer although the gateway logged stream end and `push_to_targets ... status=succeeded` at 15:00:31 exactly as for the 16:00 run; the 16:11 reply is rendered twice in the panel while the session history holds one final message.

User confirmed testing of 1.0.3 complete on 2026-10-28 (Hub wrapper ZIP SHA-256 11a86df6170ae62ad06398bae4ad142438a8cca8e7df7083a04fa81beed3d034; native test ZIP 3a75ac0a80d2d352b6e994a296eb9fd566cebb90514e9fadbc8ef3dcebdff2b7).
