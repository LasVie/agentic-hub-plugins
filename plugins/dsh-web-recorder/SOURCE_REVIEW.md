# Source & Dedup Review — dsh-web-recorder

## Task and differences
- Task ID: AH-20261023-dsh-web-recorder
- Candidate ID: CAND-DSH-172 (`kakajun/dsh-web-recorder`, npm `dsh-web-recorder@0.6.0`)
- Related historical/new Asset IDs: none reused.
- Functional difference & reuse/independent-implementation conclusion: **Confirmed New Capability, native (clean-room) implementation.** See the dedup comparison below. No upstream code/prompts/assets were copied; the DSH/Cordis runtime is not portable to this host.

## Dedup comparison against the Asset Ledger
Capability under review: **passively record a human-driven browser session (clicks, inputs, navigation, network) → `report.md` timeline + `events.jsonl` → to reverse-engineer flows and build API-level skills.**

Closest adjacent assets examined (Asset Ledger, snapshot 2026-10-22):
- `clawbrowser` (ba015b…): agent **drives** the browser via Playwright CLI (navigation, forms, screenshots, extraction). Input = agent commands; output = scripted browsing. Different paradigm — automation, not passive capture of a human session into a timeline/event log.
- `Chrome DevTools MCP 浏览器调试专家` (2f99a9…): agent **controls** Chrome via chrome-devtools-mcp to trace performance and analyze network. Input = agent control; output = perf/network debugging. MCP-driven; not a user-session recorder producing `report.md`+`events.jsonl` for API-skill construction.
- `网页端到端测试与证据交付` (a5473a…): executes **declarative JSON E2E test plans** via playwright-cli → PASS/FAIL + report.md/json + traces. Input = predefined test plan; output = test verdicts. Not passive capture of an ad-hoc human session.
- `页面验收助手` (747494…): page **acceptance** with explicit steps, assertions and screenshots. Plan/assertion-driven acceptance, not event-stream recording.
- `browser-cdp-macos` (89f888…): macOS CDP compatibility fixes; a enabling skill, not a recorder.

Conclusion: input object (an ad-hoc **human-guided** session), key action (passive capture of UI events **and** network), and output/purpose (chronological timeline + structured event log aimed at **API-level skill construction**) together establish independent functionality. Genuine partial adjacency exists (network capture in Chrome DevTools MCP; "recordings" in clawbrowser; `report.md` in the E2E skill), but none covers this capability. Verdict: **Confirmed New Capability.**

## Materials & permission evidence
Independent implementation (`mode: native`). No code, prompts, documents, icons, fonts, data, or dependencies were copied from upstream.

| Actual used path / material | Upstream URL & pinned version | Applicable license & scope | License file & SHA-256 | Copy/modify status |
| --- | --- | --- | --- | --- |
| (none) | `dsh-web-recorder@0.6.0` npm; `github.com/kakajun/dsh-web-recorder` (README/metadata read only) | upstream declares MIT (not relied upon — nothing copied) | n/a (no bundled upstream material) | No copy; clean-room from public functional description. See NATIVE_DESIGN.md material-exposure record. |

Runtime dependency note: the plugin uses the host's declared `aiohttp` and an OS-installed Chromium-family browser (not bundled). These are environment assumptions the host already makes; they are not upstream materials.

## Final ZIP license re-check
- Location of preserved upstream copyright/headers: not applicable — no upstream code copied.
- `THIRD_PARTY_NOTICES.md` path & per-upstream coverage: not applicable (native mode; no third-party code bundled).
- Full MIT/Apache-2.0 texts path: not applicable (nothing reused).
- Upstream NOTICE: none bundled (nothing reused).
- Apache-2.0 modified-file notices: not applicable.
- Brand assets / data / service-term restrictions: no DSH branding or assets reused; independent implementation is not claimed as an exemption from any upstream trademark/service terms. None are used.
- Unpack check, file inventory & hash verification: `python tools/asset_release.py check plugins/dsh-web-recorder` and `check-repo` pass; payload inventory recorded in the release `artifact.json`.
- Native requirement sources & material-exposure record: NATIVE_DESIGN.md.
- AI conclusion: **original**. No unresolved licensing obligations for bundled material (none is bundled). Open item surfaced to the Project Lead: whether any upstream trademark/service-term considerations apply — none are used here, and no branding is reproduced.

## 2026-11-04 Chinese release review — 1.0.3

The Chinese release translates this repository's own native human-facing metadata, README, Skill, tool descriptions, diagnostics and report labels. It preserves machine identifiers, APIs, schemas, event codes, capture/measurement algorithms, privacy and write protections. No upstream implementation, prompt, documentation or licensed asset is introduced. `mode: native`, `permission_status: original`, empty `sources`/`reused_paths`, original publisher `WorkSwarm`, responsible owner Siu Lok Yin and stable task/candidate IDs remain unchanged. OpenJiuwen, aiohttp and a Chromium-family browser are host dependencies, not redistributed library/browser files. The Google official Chrome for Testing 157.0.8103.38 task-local test dependency is not included in source or release payloads. Historical package hashes and confirmations remain historical. Current-package actual WorkSwarm testing completed under explicit AI delegation on 2026-11-04; see recorded current package, original evidence and authorization scope. No personal human test or fresh verbal pass is invented. Actual PR attachment and delivery checks remain.

Final local verification: both canonical/native archives contain only the same four original runtime files (manifest, Chinese README, Chinese Skill, original tool module). All payload byte hashes agree with current source and artifact.json. The original publisher, responsible owner and stable IDs are preserved. Historical native archives moved to the owning test-packages/history directory without byte changes. Current WorkSwarm GUI recording/status/stop workflow completed under explicit AI delegation with unchanged payload: ten JPEG originals, one native long PNG and raw 25-event output are preserved in GUI_TEST_RECORD_1.0.3.json. The initial model read-offset error and explicit correction are retained. No PR/Hub submission or lead acceptance is implied; source/native design and license scope are unchanged.
