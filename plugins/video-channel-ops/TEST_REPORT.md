# Functional test report — video-channel-ops 1.0.1

Task AH-20261027-ai-youtube-os; candidate CAND-CLD-225; display name 视频频道日更流水线.

2026-10-27; actual openjiuwen native Tool/ToolCard SDK from the local jiuwenswarm venv, CPython 3.12.14, Linux (WSL2).

Command: `python -B tests/video_channel_ops_functional.py [payload-dir]` — calls `PluginTool().invoke` with Chinese inputs in a fresh temp directory with a non-ASCII path; no mocks.

- Source payload: 54/54 passed (FFmpeg 8.0.1-3ubuntu2).
- Extracted native ZIP payload: 54/54 passed.
- Real FFmpeg checks included: render two scenes + 4 s narration to 1080x1920 MP4 with last scene stretched; preflight of that MP4 with a Chinese SRT passes (分辨率/时长/音频/字幕 + 5 human checklist items); preflight of a silent 1920x1080 clip returns FAIL and "不要上传". The missing-FFmpeg Chinese error path is also tested.

Covered: Chinese errors before a channel exists; new_channel fills Chinese templates (default 简体中文 / Asia/Shanghai, authorization false), creates directories and empty jobs.json, reports blank fields, refuses to overwrite, escapes JSON special characters; status shows remaining slots, pending jobs and due metrics; log_step records and sorts manifest steps, refuses "完成" for missing files, refuses marking 上传 as 完成, rejects unknown steps; log_job records and flags duplicate job IDs, rejects negative credits; job_done clears pending; publish is two-step: first call returns a question + confirm_token and records nothing, wrong token or changed parameters re-issue a token, second call with the token records; it warns when daily_upload=false, schedules 24h/72h/7d metrics, blocks further production logging on a published slot, requires confirm=true to overwrite a video ID; log_metric requires positive elapsed hours, accepts 0 values, notes fewer-than-3 samples, clears the due item; authorize requires confirm=true; 7 concurrent log_step calls all persist (channel write lock) and the lock file is removed; finish_day sets last_run_date; render refuses run_dir outside the channel and missing scenes.json; preflight missing-file error; plan_durations stretch/no-op/zero rejection; scene path traversal rejection; SRT end parsing; checks() for vertical >180 s, caption gap, silent, no audio track, clipping, and unread volume (marked 未确认).

## Host test round 1 (1.0.0, superseded)

2026-10-27, desktop WorkSwarm on WSL2, session web_1a17c861a55_ae5b83ad82cf, user-run by Vannes Wijaya with 1.0.0 (native ZIP 01bbacd0…), reviewed from session history and channel files. Passed: new_channel (in a retry with all details given), daily run stopping at 待人工 for voice/visuals without claiming tools, real render 1080x1920 8.0 s with last scene stretched, preflight all PASS + 5 human items 未确认, duplicate-slot refusal, authorize asked before changing, status. Defects: (1) assistant asked channel details one field at a time; (2) parallel log_step calls lost entries (画面/渲染/字幕与检查 missing from manifest) — read-modify-write race; (3) assistant set verified_on_platform=true and guessed 已公开 without asking the user; minor: claimed it would schedule uploads without an upload tool, and summarised a 跳过 upload step as done. An earlier attempt with a news topic was blocked by the model provider's content filter (not a plugin error). All fixed in 1.0.1 (ask-once skill text, channel write lock, two-step publish with confirm_token, upload/summary wording). Round 1 does not count as confirmation of 1.0.1.

Not yet done: host UI install in desktop WorkSwarm, and a model-backed session following the daily flow — that is the user test.
