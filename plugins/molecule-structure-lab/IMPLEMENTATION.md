# Implementation and integration boundaries

Candidate `CAND-EXT-002`; task `AH-20261028-molecule-structure-lab`; owner Cai Zhenze. Scope: an offline, editable molecular workbench with descriptors, SMARTS first-match highlighting, and SVG/JSON export. No host modifications are required or included.

## Supported extension route

The native manifest registers two `Tool` / `ToolCard` classes and one Skill through the existing openJiuwen extension loader. The tested WorkSwarm source is commit `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`; its loader resolves manifest `tools[].file/class` and `skills[].dir`. The plugin uses those public extension objects, not host internals, injection or monkey-patches.

WorkSwarm's standard artifact iframe has `sandbox=""`, which blocks interactive scripts. The plugin instead starts its own read-only loopback static server and returns a normal browser URL. All HTML/CSS/JS/WASM is in this plugin. No host frontend, backend, core, SDK, dependency or other plugin is edited. Import/install and optional plugin-local settings use the approved Build configuration scope.

## Shared computation

`engine/core.js` applies the same input bounds, descriptor definitions, canonicalization and first-match semantics in a browser Worker and a fixed Node subprocess. The two upstream RDKit runtime files are unmodified. The browser and Node adapter pass input as data, never as a shell command or JavaScript source.

The Node path is resolved from this plugin's optional `settings.json`, then its dedicated environment setting, then PATH. There is no installer or unrelated-directory search. The subprocess has a 12-second deadline, V8 heap and WASM-memory limits, and bounded request/result sizes. The wrapper limits concurrent calculations to two. Browser work uses a Worker that is terminated on timeout/cancellation. Browser WASM memory remains governed by the browser and upstream module; the Node memory caps are not claimed to apply to the browser.

Eight descriptors are reported with their exact RDKit keys and Chinese labels. `NumHBA` is not interchangeable with `lipinskiHBA`. SMARTS uses default RDKit matching parameters, reports only the first match, and does not claim exhaustive counting or additional chirality enforcement. Zero-based match indices refer to RDKit's normalized parsed graph. Ordinary explicit hydrogens may be removed; implicit hydrogens contribute to mass but are not added to graph atom counts. Molecule SMILES with dummy atoms (*) or unspecified bonds (~) are rejected; those constructs remain allowed in SMARTS queries.

## Local server and exports

The server binds `127.0.0.1` on an OS-allocated port and serves a fixed seven-file allowlist. It checks Host/Origin and uses an unguessable per-instance path; no source-directory browsing, file-writing API, CORS, remote scripts or external API is provided. Lifecycle state is isolated beneath the caller's existing workspace. Start/stop require explicit confirmation; status is read-only. Shutdown verifies the server's token/instance and never kills a persisted arbitrary PID. The server expires after 30 minutes without resource/health requests.

Page CSP disallows string evaluation. Only the plugin worker's response allows `unsafe-eval`, because the unmodified Emscripten Embind loader constructs its own bindings with `new Function`. This requirement was confirmed by an actual browser initialization error, then tested after the narrowly scoped policy change. Worker imports and connections remain same-origin; no host or browser security settings are changed.

SVG is rendered as an image Blob, not inserted into the HTML DOM. Inputs and metadata are displayed as text. Editing invalidates export permission; failed analysis clears prior results. Browser download buttons export the accepted result only. SVG carries UTF-8 metadata; JSON contains the same analysis metadata without duplicating the SVG. Downloads are initiated by user interaction and are not represented as arbitrary host-workspace writes.

## Compatibility and scope limits

The native adapter targets macOS/Linux with Python 3.11+ because it uses POSIX locks and no-follow file operations. Windows is unsupported in this version. Agent-side analysis additionally needs Node.js18+; browser-only analysis does not. Actual test environments and versions are recorded in `TEST_REPORT.md`; unspecified browsers/hosts remain unverified.

The baseline has general file, shell and browser tools, but the inspected installed extensions/runtime lacked an executable molecular-graph engine. This plugin supplies that engine and its repeatable analysis/export workflow. It does not claim that the baseline model cannot discuss chemistry or draw a molecule, and no paid same-model conversation A/B test was run.

No reaction prediction, synthesis planning, molecular dynamics, 3D conformer generation, protein prediction, toxicity/drug efficacy or experimental safety judgment is implemented. Electrical RLC simulation belongs to Main's excluded CircuitJS1 work and is unrelated to this package.
