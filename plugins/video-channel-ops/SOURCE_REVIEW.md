# Source and distribution review

Reviewed 2026-10-27 for Vannes Wijaya; task AH-20261027-ai-youtube-os; candidate CAND-CLD-225.

Naming: AI YouTube OS (candidate name, package `ai-youtube-os`) → 视频频道日更流水线 (final Chinese display name) → `video-channel-ops` (internal slug). The new name avoids using the YouTube trademark as the product name.

## Pinned source

- https://github.com/channelroom-studio/ai-youtube-os @ a4eb2f9838e99b26060a236ef2196a18bf38bc7a (HEAD of main on 2026-10-27, committed 2026-10-13); `.claude-plugin/plugin.json` version 0.1.4, equal to the candidate research snapshot.

## License coverage (item by item)

| Material | License evidence | Used? |
| --- | --- | --- |
| `scripts/render.py`, `scripts/preflight.py` | Root `LICENSE` and identical `plugins/ai-youtube-os/LICENSE`: MIT, Copyright (c) 2026 Channelroom Studio; plugin.json `license: MIT`; no per-file headers | Adapted into `runtime/media.py` (modification header added) |
| `templates/channel.json`, `state.json`, `OPERATIONS.md` | Same MIT | Translated to Simplified Chinese into `runtime/templates/` |
| `skills/channel-operations/SKILL.md`, `commands/*.md` | Same MIT | Translated/adapted into `skills/video-channel-ops/SKILL.md`; workflow conventions into `runtime/engine.py` |
| `scripts/test_scripts.py` | Same MIT | Not used; new tests written |
| `.claude-plugin/icon.svg` | Same MIT (no separate grant) | Not used |
| README.md / PRIVACY.md (external guide, Notion templates, paid setup-service links) | Same MIT | Not used; privacy facts restated in own words in README |
| Third-party dependencies | None bundled; FFmpeg is a user-installed external program | Not bundled |
| Upstream NOTICE file | None exists upstream | Recorded; none fabricated |

The two LICENSE files are byte-identical (SHA-256 4e41d928703565652945552ff18e00ae69118aa1908be9adde77241118ecef5e). MIT conditions satisfied by bundling the full original text at `licenses/ai-youtube-os/LICENSE` plus `THIRD_PARTY_NOTICES.md` (source, revision, rightsholder, covered files, modification summary).

## Trademark

"YouTube" appears only descriptively (the platform the workflow targets and its Shorts length limit). README and THIRD_PARTY_NOTICES state that YouTube is a Google LLC trademark and that no endorsement by Google or the upstream author is implied.

## New team-written materials

Tool wrapper `tools/plugin_tool.py`, README, enforcement logic in `runtime/engine.py` (slot/duplicate guards, job registry, publish verification, metrics, authorization confirm), and tests are newly written. No unified repository licensing decision is made here (Project Lead decides).

## Functional differences from upstream

- Claude Code slash commands (`new-channel`, `daily`, `preflight`) → one WorkSwarm tool `video_channel` with actions plus a Chinese skill describing the daily flow.
- Guards enforced in code rather than prompt-only: no further production logging on a slot that already has a video ID; duplicate job IDs flagged; upload step can never be logged as complete; publish requires video ID and `verified_on_platform=true`; authorization changes and video-ID overwrite require `confirm=true`; render scene paths confined to the run directory.
- Added: `production/metrics.json` with 24h/72h/7d due reminders and the "fewer than 3 samples" note; Windows drive-path mapping; timezone parameter (default Asia/Shanghai instead of Asia/Seoul).
- Excluded: upstream icon, external guide/template/service links.

Permission conclusion: reuse permitted for the declared paths subject to the bundled full MIT notice. This is an operational source review, not a trademark/service-terms representation.

## Final archive review

2026-10-27, version 1.0.1 (pre-push; supersedes the unpushed local 1.0.0 build, removed): extracted both ZIPs. Hub wrapper `releases/agent-plugin/video-channel-ops/1.0.1/video-channel-ops-1.0.1.zip` (SHA-256 3f7223a7b167d5050221a7bfd1622f4d6f3136b34cf1511adaf46c842393d39c; outer dir holds only plugin.yaml + inner dir) and native test ZIP `dist/video-channel-ops/1.0.1/video-channel-ops-1.0.1-workswarm.zip` (SHA-256 1480f77f1f6074004fbbad0aa1bed7085ea141dc17bed686ea57dc416ebe4ed4) contain byte-identical inner payloads (`diff -r` clean). Reused paths `runtime/media.py` and `runtime/engine.py` carry modification headers; templates and SKILL.md are listed in THIRD_PARTY_NOTICES.md; `licenses/ai-youtube-os/LICENSE` SHA-256 4e41d928703565652945552ff18e00ae69118aa1908be9adde77241118ecef5e matches provenance.json and upstream. No unmet MIT condition. Pending explicit user test completion; no push/PR.
