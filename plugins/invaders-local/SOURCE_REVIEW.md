# Source and distribution review — 2026-10-23

Task AH-20261023-invaders-local; Candidate CAND-CLD-302; Owner Cai Zhenze.
Mapping: **Invaders → 星际防线 → invaders-local**. Internal ID `repo:agent-plugin:invaders-local`.

## Pinned evidence and permitted scope

Upstream https://github.com/nison/claude-invaders at commit
`d332a1fc97e28e86042fc63d6802c5098733d746`, upstream plugin version0.1.1.
The actual detached checkout, complete tree, manifest, root/inner licenses, complete
engine, upstream behavioral tests, README and original host imports were inspected.
`audit-upstream` detected both complete MIT files; independent content review confirmed
the permission, copyright-retention condition and disclaimer. Both licenses are identical:
SHA-256 `e6614d9422b3f9aec4744b855ff6f01e217cf37e257bca81c4810e28f4e1193f`.
Original rightsholder statement: **Copyright (c) 2026 Nigel Hudson**.
No separate NOTICE or component-specific restrictive license appeared in the pinned tree.

Mode **ported**, permission_status **verified**, limited to the MIT game engine.
Original `invaders/hooks/engine.ts` is the source for packaged `vendor/engine-source.ts`
and generated `assets/engine.mjs`. Original comments remain; a change header was added,
optional English labels localized, and `1UP` changed to `+1`. The compiled JavaScript
removes types using Node24's built-in `stripTypeScriptTypes`; it adds no dependency.
`build_browser_engine.mjs` reproduces this output without installation/network.

New browser UI, storage validation, filesystem export and native Tool/Skill use public
requirements and the permitted engine API. They do not call the upstream shallow
`restore`/`isGame`. Strict save shape/version/seed/bounds validation precedes restore.
No Claude hooks, React/terminal renderer, store, client APIs, icon, promo image/video,
font, hosted data, API credentials or upstream test framework enters the package.
Upstream tests informed expected mechanics; independent standard-library regressions
exercise those mechanics. Promotional-media/branding permissions are not assumed.

## Dependencies and actual delivery behavior

Gameplay: a modern desktop browser, with no external libraries, requests, service or model.
Export: Python3 standard library. Native registration: the target WorkSwarm/openjiuwen
Tool/ToolCard SDK, supplied by the host, not bundled or relicensed here.
Build/tests: Node24.19.0 built-in type stripping (the tested build environment),
Python3, existing repository PyYAML and host SDK. No package download required.

Output is a standalone Chinese HTML keyboard shooter with shields, lives, score,
waves, pause and browser-local resume. This is not a WorkSwarm embedded pane or an
assistant-turn hook. There is no model call, auto-started process or browser, telemetry,
network request, provider dependency or account. Model-backed chat, if the user chooses
it, belongs to the host; it is unnecessary for gameplay or the CLI export path.

## Distribution conditions

The complete upstream MIT text is bundled at `licenses/invaders/LICENSE`, matches the
hash in provenance.json, and is also propagated into every exported HTML derivative.
`THIRD_PARTY_NOTICES.md` records the pinned source, original rightsholder, modified
paths and omitted materials. Original file comments are retained. No unified license
for other repository-owned material is invented; Project Lead policy remains applicable.

The canonical ZIP will have only `invaders-local/plugin.yaml` plus the same-name inner
runtime directory. A root-manifest companion is for the older isolated WorkSwarm
importer only; inner payload equality must be verified. Runtime package excludes tests,
reports, source-audit tooling, browser/host evidence, caches and development tables.
Final archive/path/license verification and exact hashes are recorded in TEST_REPORT.md.
This source review does not establish platform acceptance or manual testing completion.

## Confirmed delivery package

Final Chinese version1.0.2: canonical releases/agent-plugin/invaders-local/1.0.2/invaders-local-1.0.2.zip; exact native companion test-packages/invaders-local-1.0.2-workswarm.zip. All15 source/canonical/native/installed files match, with original full MIT text/hash, valid UTF-8 and declared paths. See package-verification.json and TEST_REPORT.md. User confirmation/original screenshots are recorded in USER_TEST_CONFIRMATION.md. No packaged file or ZIP changed after confirmation.

Original pinned engine.ts SHA-256:548e26d23cccafcb93f85516ac841f8c000eb9766e23c2ecff39eefc284b8b01. Superseded1.0.0/1.0.1 preflight archives remain only in ignored dist/invaders-local/preflight-canonical/; they are not delivery versions. Temporary raw host captures remain outside the commit.
