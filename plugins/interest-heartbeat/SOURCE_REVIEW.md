# Source and distribution review

Reviewed 2026-10-28 for Vannes Wijaya; task AH-20261028-heartbeat; candidate CAND-DSH-043.

Naming: Kanadego/dsh-heartbeat (candidate name, npm `@kanadego/dsh-heartbeat`) → 兴趣心跳主动分享 (final Chinese display name) → `interest-heartbeat` (internal slug). The new name describes the delivered function and drops the DSH host prefix.

## Pinned source

- https://github.com/Kanadego/dsh-heartbeat @ 8880365836fc4247839122aee7b542d73403a532 (the `gitHead` of npm 2.0.0, committed 2026-10-18), equal to the candidate research snapshot version 2.0.0. `main` has since moved (329d73f on 2026-10-28); nothing after the pin is used.

## License coverage (item by item)

| Material | License evidence | Used? |
| --- | --- | --- |
| `src/gate/gate.ts`, `src/core/time-window.ts` | Root `LICENSE` at the pinned commit: MIT, Copyright (c) 2026 Kanadego; no per-file headers | Rule semantics re-implemented in Python in `runtime/engine.py` (modification header added) |
| `src/seeds/pool.ts`, `src/seeds/types.ts` | Same MIT | Same; pool rules, caps, score weights and default confidences |
| `config/policy.json`, `config/interests.json` | Same MIT | Default numbers and browse schedule adopted; upstream interest list not used (replaced with generic items) |
| README.md, DESIGN.md (beat phases, "silence carries a reason") | Same MIT | Adapted in own Chinese words into `skills/interest-heartbeat/SKILL.md` and README |
| `assets/*.ps1` (screen capture, front window, idle, notify, DPAPI vault) | Same MIT | Not used (Windows-only; privacy-heavy) |
| `src/screen`, `src/env`, `src/vault`, `src/weekly`, `src/excerpt`, `src/notepad`, `src/profile/consolidate.ts`, `client.js`, `cordis.patch.yml`, presets | Same MIT | Not used |
| `docs/screenshots/*.png`, badges | Same MIT (no separate grant) | Not used |
| npm dependencies (`@deepseek-ai/dsh-settings`, `@deepseek-ai/schemastery`) | Their own licenses | Not used or bundled |
| Upstream NOTICE file | None exists upstream | Recorded; none fabricated |

The npm manifest for 2.0.0 declares no `license` field; the repository `LICENSE` file at the pinned commit (SHA-256 6d174799b6efe730b5ca9e02e4d9fc19463d91dcaa87c67aa6c9b8b9a043a7d4, last changed 2026-09-06) is the grant relied on. It covers the repository contents used here. MIT conditions satisfied by bundling the full original text at `licenses/dsh-heartbeat/LICENSE` plus `THIRD_PARTY_NOTICES.md` (source, revision, rightsholder, covered files, modification summary).

## Trademark

"DeepSeek" / "DSH" appear only descriptively in notices. THIRD_PARTY_NOTICES states no endorsement by the upstream author or the DeepSeek rightsholder is implied.

## New team-written materials

Tool wrapper `tools/plugin_tool.py`, command-line entry `runtime/cli.py`, README, storage/locking/configuration/profile/ledger code in `runtime/engine.py`, and tests are newly written. No unified repository licensing decision is made here (Project Lead decides).

## Functional differences from upstream

- DSH/Cordis plugin with its own timer, engine-room session and settings card → WorkSwarm native tool `interest_heartbeat` driven by a host cron job created in the user's session; the beat flow is described in a Chinese skill.
- Kept and enforced in code: gate order (pause → quiet hours → busy windows → daily cap → cooldown), re-check at pick and at booking time with "already said still counts" booking, cross-midnight left-closed windows, seed pool (tag TTLs 3/14/60/90 d, same-topic merge, category caps 16/14, score-based eviction with hand-written protection, retire after 2 uses / chat after 1, 21-day cold bench, archive cap 50), browse windows with min interval, daily sessions and 3-day focus cooldown, carry-over note, audit log without content.
- Changed: busy detection is user-declared time windows instead of screen/front-window/presence probes; delivery goes to the host scheduled-task panel (WorkSwarm cron runs in an isolated session and pushes results there; no delivery into chat sessions or multi-session binding); cron schedule generated from settings skips quiet hours; silent runs reply with one readable Chinese line; profile is explicit entries (like/dislike/fact/avoid) recorded by the agent, without model-driven consolidation; data stored unencrypted under `~/.jiuwenswarm/interest-heartbeat/` (README warns against sensitive entries); generic default interests.
- Excluded: screenshots, PowerShell probes, DPAPI vault, settings UI, weekly report, excerpt book, migration, Windows notifications.

Permission conclusion: reuse permitted for the declared paths subject to the bundled full MIT notice. This is an operational source review, not a trademark/service-terms representation.

## Final archive review

2026-10-28, version 1.0.2 (pre-push; supersedes the unpushed local 1.0.0 and 1.0.1 builds, removed): extracted both ZIPs. Hub wrapper `releases/agent-plugin/interest-heartbeat/1.0.2/interest-heartbeat-1.0.2.zip` (SHA-256 552970cad79d5b330871d2d346385227b43c895aad08e23be642b93ee7c6423a; outer dir holds only plugin.yaml + inner dir) and native test ZIP `dist/interest-heartbeat/1.0.2/interest-heartbeat-1.0.2-workswarm.zip` (SHA-256 f564efb5f39d289007d50241369087e1de03a69a4da97059973e2d26766a3e1b) contain byte-identical inner payloads (`diff -r` clean). Reused-semantics file `runtime/engine.py` carries a modification header; SKILL.md is listed in THIRD_PARTY_NOTICES.md; `runtime/cli.py` is new code; `licenses/dsh-heartbeat/LICENSE` SHA-256 6d174799b6efe730b5ca9e02e4d9fc19463d91dcaa87c67aa6c9b8b9a043a7d4 matches provenance.json and upstream. No unmet MIT condition. Pending explicit user test completion; no push/PR.
