# Source and distribution review

Reviewed 2026-10-30 for Cai Zhenze. Candidate CAND-EXT-005; Task AH-20261030-offline-observing-planner. Astronomy Engine → 离线观星规划台 → offline-observing-planner v1.0.0; repo:agent-plugin:offline-observing-planner.

## Pinned material and permission

Repository https://github.com/cosinekitty/astronomy at 865d3da7d8112bbc7911238052c6af4aaf877181; Python setup.py declares2.1.19. Ported mode: only source/python/astronomy/astronomy.py is copied, byte-identical Git blob1a48fdf620540df22fcf421d0df0c2c016999e52, SHA25641248c7b1edbf9d11119528eef7455a6dc55abde9f1aab40d363015e956c1729. Its full MIT headerCopyright2019–2025Don Cross is retained. RootLICENSE and source/python/LICENSE are both bundled unchanged (distinct2019–2025/2019–2022 notices) with exact hashes in provenance.json. No separate upstream NOTICE applies to the single Python module.

The MIT grants permission to copy/distribute/modify subject to retaining copyright and permission/disclaimer text. Full texts are inside the runtime payload, not only linked. No modifications to the vendored module. Adapter/UI are original repository work; lifecycle security is adapted from the maintained offline-optics-lab mechanism within this plugin, with no changes to its source. No new umbrella license is asserted.

The module imports math,datetime,enum,re,abc,typing only. Embedded ephemeris coefficient tables are part of the licensed source. No npm/pip downloads, binaries, online services, star catalog, photos, icons, external fonts, documentation translations or upstream demo content enter the runtime. Host openjiuwen Tool/ToolCard is an existing supported runtime interface, not bundled or modified. Original MIT license text intentionally remains English.

## Integration and scope

Existing WorkSwarm native manifest loader and public DeepAgent.load_plugin load two Tool/ToolCard declarations and one Skill. A plugin-owned loopback service supplies the UI; calculation uses a killable isolated Python subprocess with a10second wall deadline, bounded input/results and explicit error output. No host/core/SDK/installed dependency/other-plugin edits or preload hooks. Explicit workspace authorization; private state, tokenized127.0.0.1 endpoint, Host/Origin checks, fixed static routes, no network calls or arbitrary path API.

Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn only; UTC2000–2100, latitude±80°,longitude±180°,elevation−500..10000m; 1second..24hour interval and integer5..60minute sample spacing. Airless topocentric coordinates are separate from standard-refraction/limb rise-set events. Fixed display offset is not inferred time-zone/DST. No weather/terrain/navigation/guaranteed visibility claims.

Known upstream issues404(reduced maintenance/extreme polar future event sensitivity),378(tinyPython cross-language drift),383(unresolved report of Mercury/Mars differences),411(refraction convention),414(JSnegativeTT nontermination) were reviewed in Phase1. Boundaries are safeguards, not claims of fixing every issue. This wrapper exposes UTC only and no rawTT conversion; finite event searches and a subprocess deadline bound work. IndependentJPL/USNO checks are required and reported separately in TEST_REPORT.md. FutureUTC/ΔT assumptions differ between systems, especially Moon near2100; no universal accuracy guarantee.

Numerical reference tests contain only a small selection of factual observations and request/hash provenance, not copied descriptive reports or a redistributed ephemeris database. Original raw responses are local research evidence, outside the runtime ZIP. No permission is inferred to redistribute JPL website documents under MIT.

## Distribution verification

The canonical ZIP must contain the unmodified module and both full license texts plus THIRD_PARTY_NOTICES.md; verification checks exact payload hashes, declared paths, UTF-8 Chinese files and equality with the WorkSwarm native companion. Actual commands/results are in TEST_REPORT.md and package-verification.json. These package checks are distinct from numerical, SDK, backend, browser and user acceptance tests.


Phase 3 reinspection (2026-11-02): canonical `releases/agent-plugin/offline-observing-planner/1.0.0/offline-observing-planner-1.0.0.zip` and native `plugins/offline-observing-planner/test-packages/offline-observing-planner-1.0.0-workswarm.zip` retain the tested hashes recorded in TEST_REPORT.md. The extracted `runtime/astronomy.py`, `licenses/astronomy-engine/LICENSE`, and `licenses/astronomy-engine/PYTHON_LICENSE` exactly match provenance.json; `THIRD_PARTY_NOTICES.md` covers the sole reused module. The canonical inner prefix is `offline-observing-planner/offline-observing-planner/`; the native companion contains the same 13 files at its root. Complete MIT notices, original headers and disclaimers are present. No upstream NOTICE or modified-upstream-file notice is applicable. All reviewed distribution conditions for the included materials are satisfied; no unknown-permission materials, screenshots, test fixtures or host dependencies enter the ZIP.
