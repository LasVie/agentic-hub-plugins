# Source and distribution review

Reviewed 2026-10-27 for Vannes Wijaya; task AH-20261027-persona-switcher; candidate CAND-DSH-095.

Naming: yupaoa/dsh-persona-switcher (candidate name) → 会话人设切换 (final Chinese display name) → `persona-switcher` (internal slug).

## Pinned source

- https://github.com/yupaoa/dsh-persona-switcher @ 563854472ae7fe3b2e96f6cbcb53428d3af81e1c (HEAD of main on 2026-10-27; equals npm dsh-persona-switcher@0.3.1 `gitHead`).
- npm 0.3.1 tarball contents matched the repository files at that commit (`diff -rq`: npm package is a subset, no differing files).

## License coverage (item by item)

| Material | License evidence | Used? |
| --- | --- | --- |
| Code `lib/index.js` (role parsing/scan/notice logic) | Root `LICENSE` MIT, Copyright (c) 2026 yupaoa; package.json `license: MIT`; no per-file headers | Adapted into `runtime/engine.py` (Python rewrite, modification header added) |
| `lib/persona-binding.js`, `lib/session-state.js`, `lib/client.js`, `src/client/*` | Same root MIT | Not used (DSH/Cordis-specific); behavior described only |
| `locale/*.json`, `docs/how-it-works.svg` | Same root MIT | Not used |
| Mascot images / fonts | None bundled upstream | N/A |
| Runtime dependency `@deepseek-ai/schemastery`, DSH peer packages | Not bundled | Not used; no dependency in this package |
| Upstream NOTICE file | None exists upstream | Recorded; none fabricated |

No subdirectory licenses found. MIT conditions satisfied by bundling the full original text at `licenses/dsh-persona-switcher/LICENSE` and `THIRD_PARTY_NOTICES.md` with author/revision/modification summary.

## New team-written materials

Prompt section, SKILL.md, README, tool wrapper, sample roles (茶馆掌柜, 严谨评审官) and tests are newly written. No unified repository licensing decision is made here (Project Lead decides).

## Functional differences from upstream

- State scoped per workspace directory (`.persona-switcher/state.json`), not per DSH session id.
- Persona applied via a static prompt section instructing the model to call `persona_switch status` each turn, instead of an agent-scoped DSH prompt section registration.
- Excluded: web role picker, settings page, mascot art + flip animation, `role_probe` diagnostic tool, `$DSH_HOME` / `cordis.patch.yml` default-role storage.
- Retained: ROLE.md format (directory form wins over flat `<id>.md`), id rule, identity-fields-only parsing (capability fields ignored), `none` not overridden by default role, explicit role-change notice, model must not self-switch.
- Added: `init` sample roles, 32 KiB size cap, symlink refusal, corrupt-state preservation.

Permission conclusion: reuse permitted for the declared path subject to the bundled full MIT notice. This is an operational source review, not a trademark/service-terms representation.

## Final archive review

2026-10-27 (rebuild 2, same version 1.0.0 at user request, pre-push): extracted both ZIPs. Hub wrapper `releases/agent-plugin/persona-switcher/1.0.0/persona-switcher-1.0.0.zip` (SHA-256 995bb3011bf17f35075d0711da17b39ad313a95800e5a0c23542d8892741791a) and native test ZIP `persona-switcher-1.0.0-workswarm.zip` (SHA-256 c75f33a45c1d0cc3f11d52e5f0e2cdbe960c5f9f53de9e045c4455e7a1b0940a) contain byte-identical inner payloads (13 files). The only reused path `runtime/engine.py` carries its modification header; `licenses/dsh-persona-switcher/LICENSE` SHA-256 74ceca0db0d67b681613a3281cb06baaf00bedcbc4ec006fb51f6ff83af1d717 matches provenance.json and the upstream file; THIRD_PARTY_NOTICES.md present. No unmet MIT condition. Pending explicit user test completion; no push/PR.
