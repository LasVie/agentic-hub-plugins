# Functional verification: 立体网格布尔工坊 1.0.0

Task `AH-20261031-solid-mesh-workbench`; owner Cai Zhenze; independent approved route, Candidate ID Not Applicable. Tests performed by agents on 2026-10-31. Cai Zhenze confirmed manual testing passed on 2026-11-05 and supplied seven originals; see [User test confirmation](USER_TEST_CONFIRMATION.md). Project Lead acceptance is separate.

## Environment and boundaries

- Worktree `/Users/IDLE_And_R/.codex/worktrees/4dbb/agentic-hub-plugins`, branch `codex/main3-solid-mesh-workbench-20261031`, base `b3dad00f5049827288eaedbbc87b4cdbce12583c`.
- macOS; Node 24.19.0 for engine/UI tests and Node 22.23.3 for runtime/SDK compatibility. Python 3.12.14; OpenJiuwen 0.1.19 from the unchanged host lock.
- Source host JiuwenSwarm commit `3ef1de9` was inspected read-only. A task-owned copy, build, locked environment, data/home/cache and configuration live under `/private/tmp/main3-solid-mesh-20261031-host6401`.
- Dedicated WorkSwarm UI `http://127.0.0.1:6401/`; gateway 29360; agent server 28360. Plugin workbenches bind dynamically selected loopback ports. No protected Main/Main 2.0 service or dependency was modified.
- No chat/model request, paid call or external geometry service was used. Initial host startup fetched public remote-auth configuration; subsequent isolated startup uses supported `JIUWENSWARM_CONFIG_URL=off`. Plugin geometry and UI assets are local. This is not a claim that every arbitrary host feature operates offline.

## Automated functional checks

| Check | Result and substantive evidence |
| --- | --- |
| Engine (`tests/test_solid_mesh_engine.mjs`) | 15 passing tests against real Manifold JS/WASM. Overlapping 20 mm cubes: union volume 12000 / area 3200; difference and intersection volume 4000 / area 1600. Independent exported-OBJ volume, area and oriented-edge calculations; project and OBJ roundtrips; explicit merge topology; rotated primitives, finite cylinder, empty results and repeated operations. |
| Invalid engine input | Closedness, orientation, vertex links, degenerate faces, nonfinite/oversized values, unknown fields, unsupported OBJ records and malformed UTF-8/JSON rejected in Chinese. No synthetic successful output on error. |
| Runtime (`tests/test_solid_mesh_runtime.py`) | 16 passing tests: real process execution; 20-second timeout and output bounds; cancellation/reaping; status/start/stop; private state ownership; symlink/FIFO/hardlink and foreign-service preservation; HTTP origin/token/host checks; busy behavior; early cancellation and stop acknowledgement race. |
| UI geometry helpers (`tests/test_solid_mesh_ui.mjs`) | 6 passing tests. Real 7744-vertex torus project saves below 2 MiB and reloads with identical geometry; 0.01 mm cube displays a nonzero volume; only visible geometry affects fit; small geometry fits; UTF-8 byte ceiling enforced. |
| Native SDK | Real `DeepAgent.load_plugin` registered two tools and one Skill. 13 source checks and 13 exact-installed-package checks passed, including actual `Tool.invoke` Boolean computations, invalid input, lifecycle/HTTP and unload. No model call. |
| Exact package | Maintained `tools/asset_release.py check` passed. Both archives extracted and all 45 runtime files compared to source and each other. All 25 license/attribution files, vendor hashes, UTF-8, Chinese content and declared paths verified. Extracted engine analytical fixtures, Chinese closed/hole OBJ, project reload and OBJ reimport passed. |
| WorkSwarm installation | Supported `plugin_packages.import_local/install/show/list` on port 6401 installed the exact native ZIP. Installed payload matched all 45 packaged hashes; host model configuration and other catalog/payload records unchanged. Real frontend displayed the Chinese card, two tools and one Skill. |

Relevant commands, from the repository root with an existing suitable interpreter:

```sh
node --max-old-space-size=256 --wasm-max-mem-pages=4096 --disallow-code-generation-from-strings --test tests/test_solid_mesh_engine.mjs tests/test_solid_mesh_ui.mjs
SOLID_MESH_TEST_NODE=/absolute/path/to/node python -B -m unittest discover -s tests -p test_solid_mesh_runtime.py -v
python -B tools/asset_release.py check plugins/solid-mesh-workbench
python -B tools/asset_release.py pack plugins/solid-mesh-workbench
```

The actual packaging/SDK interpreter is `/private/tmp/main3-solid-mesh-20261031-host6401/venv/bin/python`; Node 24 is `/Users/IDLE_And_R/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`. Integration helpers require the explicit task-owned host root and verify service PID arguments and data ownership before any RPC.

## Assistant-operated browser checks

Real Chrome rendered the Chinese UI and computed meshes. Verified union/difference/intersection measurements, cylindrical hole (volume approximately 5744.507 mm³), changing parameters invalidating old exports, empty subtraction with disabled OBJ export, nonzero tiny-solid measurements and visible-result fitting with a distant hidden operand. Refresh restored and recalculated the saved project. A downloaded project was imported through the file chooser in the initial browser pass; an unsafe project with an extra `script` field was rejected with a Chinese message and exports disabled. Reset recovered valid computation. The final service stopped through the UI with acknowledgement and disabled calculation controls.

Browser file-picker automation was slow; this did not indicate a plugin computation timeout. Full manual file-picker, download and interactive-view checks remain in the user checklist. Automated export/reimport tests verify geometry bytes independently. Assistant screenshots are not the user's original test evidence.

After exact-ZIP installation, a fresh workspace was started through the registered installed tool. Its browser computed the default cubes and cylindrical-hole example (5744.507 mm³, 208 triangles); Chinese labels, input outlines, keyboard rotation and zoom were inspected. The isolated test session was provided during the 2026-10-31 handoff. The private session URL is not included here.

## Frozen package evidence

- Canonical ZIP: `releases/agent-plugin/solid-mesh-workbench/1.0.0/solid-mesh-workbench-1.0.0.zip`; SHA-256 `5c3c4315bab1107752220c13e4061d931dfd23a3a3e970519130f51b16904de6`.
- Native WorkSwarm ZIP: `plugins/solid-mesh-workbench/test-packages/solid-mesh-workbench-1.0.0-workswarm.zip`; SHA-256 `6d5bd3e547633f0ba05f1298c8da69fdc180538871d4d937ae891e7a1fe469cb`.
- `package-verification.json` binds extracted checks and source file hashes to both ZIPs; `host-verification.json` binds native installation and unchanged configuration; `sdk-verification.json` records the 13 exact-installed-payload invocations and unchanged bytes. `test-packages/companion-artifact.json` binds native and canonical payloads.
- `verify_package.py`, `verify_workswarm.py` and `verify_sdk.py` reproduce the respective checks. Do not direct the host helper at another task's services; its ownership fences reject that.
- Host verification covers the actual package manager; native tool execution was through the real SDK. The host chat worker was not exercised because this isolated instance deliberately has no working model/credentials. A connected catalog badge alone is not treated as proof of tool execution.

## Review findings resolved

Decimal primitives are canonicalized to saved Float32 geometry before their first operation, preventing metric changes after reload. Early cancellation is recorded so a delayed request cannot start after cancellation. Stop waits for its acknowledgement. UI export is compact bounded JSON; small values use significant digits; fitting ignores hidden operands. Input-read generations discard stale imports. Lifecycle requests are serialized. Cancelled or failed recovery preserves the previous saved JSON and cannot overwrite later lifecycle status.

## Remaining limits and gates

Only closed, oriented triangular OBJ in the documented strict subset is supported. Coordinates are Float32; cylinder measurements describe its polygonal mesh. No general mesh repair, exhaustive geometric self-intersection detection, STEP/STL import or manufacturing certification. Node 22+, Python 3.11+ and macOS/Linux are required; only the above macOS environment was exercised. Removing a host plugin does not synchronously stop its service: explicit Stop or 30 minutes idle ends it. JavaScript heap and WASM each have separate 256 MiB ceilings, not a 256 MiB total-RSS ceiling.

Exact archive inspection and exact-package host installation passed. The Phase 3 recheck ran the 21 engine/UI helper tests on Node 24.22.1 and reverified both unchanged ZIPs, all 45 runtime files and 25 bundled license/attribution files. The installation and operations checklist is in [MANUAL_TESTING.md](MANUAL_TESTING.md).
