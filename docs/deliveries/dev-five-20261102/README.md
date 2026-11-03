# Five developer workbenches: verified delivery

Owner: Song Haoran. Selected 2026-11-02; final verification 2026-11-03 (Asia/Singapore). All tests and screenshots were executed by the agent under the user's explicit delegation; this is not human acceptance.

| Plugin | Final version | Candidate | New application capability |
| --- | --- | --- | --- |
| 接口模拟与联调台 (`api-mock-lab`) | 1.0.3 | CAND-EXT-006 | Normal HTTP 200 (6 ms), delayed HTTP 200 (357 ms) and simulated HTTP 503 (9 ms) were exercised through the installed Chinese UI. |
| 可视化网页搭建台 (`visual-web-studio`) | 1.0.4 | CAND-EXT-007 | Installed GrapesJS editor loads with Chinese text controls, without fetching external icon fonts. |
| 离线 PostgreSQL 实验台 (`postgres-local-lab`) | 1.0.3 | CAND-EXT-008 | The installed UI executed the real PostgreSQL JSONB stock query and rendered three Chinese products. |
| 前端包体积透视台 (`bundle-insight`) | 1.0.4 | CAND-EXT-009 | The installed UI loaded actual Rollup/Visualizer statistics, rendered the treemap, selected /catalog.js and displayed its importer /app.js. |
| 网页 3D 模型瘦身台 (`web3d-asset-lab`) | 1.0.4 | CAND-EXT-010 | The installed Three.js UI rendered both actual models. |

The native WorkSwarm ZIPs are in each plugin's test-packages/. The canonical Hub wrapper ZIPs and artifact records are in releases/agent-plugin/<slug>/<version>/. Both forms contain exactly the same runtime files. See package-verification.json for all ZIP hashes and byte-for-byte source/canonical/native/installed equality.

## Validation

- Actual WorkSwarm 0.2.9b1 at local port 5173 imported and installed the packages through its supported package APIs; an enabled real conversation invoked every native tool. The final status screenshot records all final versions and running services. The host's global/model configuration and unrelated package catalog were unchanged.
- The real-engine suite passed 14 cases from source and 14 from extracted final canonical packages. Repository suite: 595 tests, 504 passed, 91 skipped for unavailable optional dependencies of other assets. No development-workbench case was skipped.
- Repository contract: 61 source assets / 71 release ZIPs passed check-repo after refreshing main through de13a4b. Required real MCP server-development integration also passed.
- Nine real HTTP exports were compared to saved files; Chinese HTML heading/card and resumable one-page project JSON were verified. The actual browser also downloaded the PostgreSQL snapshot; it contains PG_VERSION. GLB original and final exports passed independent gltf-validator: zero errors and zero warnings.
- Seven plugin UI originals and two actual host-session/status originals are indexed in evidence-index.json with hashes. All are original JPEG bytes from the browser, with no resizing or reconstruction. PR evidence supplies the permanent discussion links. Earlier trial images/ZIPs are excluded.
- Source/distribution audit mapped actual bundled inputs to full licenses/notices and fixed package versions. Mockoon includes MPL JMESPath source and availability text; no unreviewed formatting-addon implementation, Sharp/libvips binaries or separately sourced demo models are shipped. PGlite's Apache JS/WASM/data files are unchanged and the PostgreSQL license is retained. No repository-wide relicensing is implied.

## Reproduce verification

Use Python 3.11 with requirements-dev.txt and an existing Node.js 22+ runtime. No runtime package download, cloud account or Docker is required by the shipped workbenches.

```sh
python -m unittest discover -s tests -p test_dev_workbenches.py -v
python tools/dev_five/verify_payloads.py --extract .research/dev-five/check
DEV_WORKBENCH_PAYLOAD_ROOT="$PWD/.research/dev-five/check" python -m unittest discover -s tests -p test_dev_workbenches.py -v
python tools/asset_release.py check-repo
```

To compare a running installation, add --installed-root <the actual host plugin_packages/local directory> to verify_payloads.py. Do not guess or write directly to host installation directories. Each plugin's MANUAL_TESTING.md explains the Chinese UI flow and limits.

The preserved logs are repository-tests.log, verified-final-tests.log and mcp-integration.log. host-install-verification.json contains metadata and configuration hashes only. export-verification.json and gltf-validation.json distinguish endpoint/content checks from browser rendering.

## Build maintenance

tools/dev_five/ contains the source templates, real-engine adapters, browser UI, generator, asset bundler, license collector and read-only payload verifier. Each generated plugin is independent at runtime; none imports a shared development template or another plugin.

For an intentional new release, choose a new asset_version in tools/dev_five_config.json before generating or packaging. Never overwrite these delivery versions. The build-only dependencies are pinned in each build-evidence/npm-build.lock.json (including official registry integrity hashes). Recreate the private .research/dev-five/build workspace from that lock and its root package metadata with npm ci --ignore-scripts and a workspace-local npm cache. These are build dependencies only, not host/global installation steps.

Pinned source inputs needed by the builder:
- GrapesJS core source: https://github.com/GrapesJS/grapesjs/tree/3b2c671c0ab50f052a219b987dea8738ea75886e, extracted into .research/dev-five/grapesjs-source/. The TypeScript transform intentionally follows upstream ES5 class semantics.
- JMESPath source: https://github.com/jmespath-community/typescript-jmespath/tree/f04b204f5919ad607a4945a23331810b07cc13ae, extracted into .research/dev-five/@jmespath-community__jmespath-source/.
- PostgreSQL license: https://github.com/electric-sql/pglite/blob/0974bdf1ab3b100a1b25ffbcb1a15ff6446db6d4/POSTGRES-LICENSE, retained at .research/dev-five/POSTGRES-LICENSE.

Run generate.py, build_assets.mjs and audit_and_pack.py only for the intentional new version, then repeat exact-payload, source/extracted, native host and UI testing. host_verify.mjs mutates only these named package installations through supported APIs and refuses unexpected upgrade versions; it is a local maintainer verification tool, not a production updater.

## Boundaries and handoff

- **接口模拟与联调台:** Loopback deterministic mock APIs only; proxying, callbacks, external references, response files and dynamic templates are disabled. A mock result does not verify a production backend.
- **可视化网页搭建台:** Static HTML/CSS component projects only; no arbitrary React round-trip or automatic website publication. The unreviewed old formatting addon is excluded. The upstream source is transpiled with its ES5 class semantics to preserve Backbone compatibility.
- **离线 PostgreSQL 实验台:** Embedded development database, one bounded worker per operation; 15-second timeout and at most 300 displayed rows. No production concurrency, replication or arbitrary PostgreSQL extension claims.
- **前端包体积透视台:** Rollup/Vite Visualizer raw-data input only, 10 MiB / 5,000 modules; does not execute a user's project configuration. Fixture builds are labeled as fixtures. Per-module gzip/Brotli sums are not whole-response transfer size.
- **网页 3D 模型瘦身台:** Embedded standard GLB <=25 MiB; required decoder extensions/external resources are rejected. Geometry operations are dedup/weld/prune; no universal compression or arbitrary-extension/no-loss guarantee. Only base-color/emissive PNG/JPEG textures are resized; data/normal maps are skipped. The fixture contains no animation, so animation playback is not claimed.

The real GLB fixture is deliberately redundant (16 cubes/textures) to demonstrate measurable engine behavior; its reduction is not a promised rate for arbitrary user models. The fixture has no animations. Rollup fixtures do not claim that an end user's project was built.

The Project Lead requested PR submission only. Leave the PR open; no merge, branch deletion, Release, Hub submission/publication or Asset Ledger update is authorized here. Candidates remain Planned, tasks Submitting after PR creation, acceptance Pending Acceptance, and Hub evidence/completion dates blank. Use the existing tracker, not a copy.
