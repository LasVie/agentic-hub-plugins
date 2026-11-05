# Offline mechanics lab — build verification

Task AH-20261102-offline-mechanics-lab; Candidate CAND-EXT-011; Cai Zhenze.
Display name 离线力学实验室; plugin v1.0.0; Matter.js 0.20.0.
Branch feat/offline-mechanics-lab; base main 856284cb52e1e10f916a1bb98aa43a56254b9e9d.

## Status and boundaries

Build only. User manual testing has not started or passed. No model calls, commits, pushes, PRs, Releases or Hub actions. Implementation is contained in this plugin and its tests/docs/package artifacts. Other plugins and host code are unchanged. Existing parallel worktrees preserved.

## Completed checks (2026-11-02)

- `python tools/asset_release.py check plugins/offline-mechanics-lab`: passed.
- Bundled development Node, `node --test plugins/offline-mechanics-lab/tests/test_engine.cjs`: 10 tests passed. Independent analytic free-flight reference: at t=1s, gravity=100, y0=100, y=150.4166667 vs continuous 150 (declared fixed-step error tolerance 0.42); vx=25, vy=100. Locked 1D equal/unequal mass collision checks agree with momentum and restitution formulas to 1e-6. Resting penetration <0.06 world units; pendulum maximum length error <0.1. Repeated runs/JSON roundtrip reproduce all samples. Full CSV and invalid-input budgets verified. Maximum 32-body/10-second case completed.
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s plugins/offline-mechanics-lab/tests -p 'test_runtime.py' -v`: 8 passed. Real loopback startup/reuse/status/stop, foreign-session refusal, Host/Origin/token checks, static allowlist/CSP, save/explicit overwrite, corruption and symlink preservation, invalid HTTP/scene envelopes. Initial sandbox run could not bind loopback (independent socket probe returned EPERM); identical tests passed with authorized local-network execution. This was a tool sandbox restriction, not a host fix.
- `node plugins/offline-mechanics-lab/tests/browser.cjs` with Playwright from the bundled development runtime: 14 real Chrome/service/worker checks passed. Playback/pause, timeline, actual reference velocity, 722-row CSV, Chinese scene save/reload across page reload, input invalidation, invalid inputs, JSON reimport/recompute, invalid-import invalidation, pointer drag, worker cancellation, injected worker-resource stall timeout, late-load freshness, no page errors or external page requests. The timeout case deliberately delays a worker resource; it is a recovery regression, not a claim that normal simulation timed out. Visual inspection of the generated preview confirmed readable Chinese labels and numerical results.

The service stores a bounded scene envelope, never executes supplied content and does not claim numerical validation. The browser engine performs strict physical/schema validation before calculation, save/export and restored-scene use. Browser calculations run in a bounded worker; the native tool only manages service lifecycle. Neither SDK registration nor HTTP startup proves a model conversation or user manual acceptance.

## Confirmed numerical limitation

The unmodified upstream resolver loses more velocity than ideal theory in some freely rotating multi-contact collisions. Two equal square bodies at ±100 with restitution=1 produce about ∓45.4545 when rotation is free. This is reproduced and explicitly documented, not patched or disguised. The reference 1D example uses public `Body.setInertia(Infinity)` to lock rotation, yielding ∓100; restitution=.5 yields ∓50. General contact results are approximate; low-speed thresholds, tunnelling and constraint drift remain. No engineering/safety accuracy guarantee.

## Packaging and integration

- Canonical `releases/agent-plugin/offline-mechanics-lab/1.0.0/offline-mechanics-lab-1.0.0.zip`: SHA-256 `b69f0177931df25d7103aede52ac8e2177cc5e8e5ff252d36ac48edd724f758b`.
- Native WorkSwarm companion `plugins/offline-mechanics-lab/test-packages/offline-mechanics-lab-1.0.0-workswarm.zip` (also copied to ignored `dist/offline-mechanics-lab/1.0.0/`): SHA-256 `e850a5458ea3fb7ef22b31bdfd79f68482f6144ed17508e1d86e4fa4bdf69319`.
- Format check, canonical pack, companion pack and `verify_package.py` passed. All 13 runtime files are byte-identical across source, canonical ZIP and companion ZIP. Declared paths, version, UTF-8 Chinese instructions, complete MIT license and unchanged engine header/hash verified. No tests, logs, screenshots, workspaces or credentials are inside either ZIP. See `package-verification.json` and canonical `artifact.json`.
- Browser suite was repeated against the final extracted canonical payload; all 14 checks passed. Its report is `browser-verification.json`. Preview images are local testing artifacts under ignored `dist/`, not delivery screenshots or plugin payload.
- `verify_workswarm.py --install` used the running isolated backend's supported local import/install/catalog API. Frontend `http://127.0.0.1:6393/` returned HTTP 200; both frontend-proxy and direct backend WebSocket ping/pong passed. Installed native payload matches all 13 ZIP files; catalog reports version 1.0.0. All seven pre-existing plugin catalog entries and 207 files, plus model configuration, remained unchanged. No service restart or host patch. See `host-verification.json`.
- Live Extensions UI was separately inspected: 我的扩展 lists 离线力学实验室; its detail screen lists mechanics-lab Skill and 本机力学实验室 tool. 创建 exposes 上传文件创建. The UI detail screen does not display a version; version attribution comes from the backend catalog and exact installed payload, not an invented UI label.
- `verify_sdk.py` loaded that installed payload through real `DeepAgent.load_plugin`, resolved the registered Tool instance, and made 8 actual lifecycle calls: status, missing-confirmation rejection, start, same-session status, stop, immediate restart with a new session, stop and final status. Served UI returned HTTP 200; 2 extension references unloaded. External socket connections were denied in the verification subprocess; model calls = 0. This is a standalone SDK check, **not execution through the running WorkSwarm chat worker**. See `sdk-verification.json`.
- No generic native Tool.invoke request exists in the inspected WorkSwarm WebSocket schema. We did not add an endpoint, patch internals, simulate a model conversation or equate installed/connected with actual chat-worker invocation. The latter is explicitly assigned to the user's manual test.

## Manual handoff and engineering review

Ready for Testing; manual test confirmation and original screenshots remain pending. `MANUAL_TESTING.md` supplies the exact companion installation, current-package hashes, real-tool prompt and browser acceptance checks. The already-running isolated WorkSwarm and its model settings are retained. A dedicated empty manual workspace is prepared; no user experiment has been run there.

Maintained scope reviewed: this plugin's source, tests, provenance, verification reports, testing guide, companion and canonical release artifacts only. The loopback lifecycle reuses the established mechanism locally without changing another plugin; the numerical worker and browser state each have one owner. Recovery checks cover edit cancellation, late responses, timeouts, corrupt records and installation identity. No competing implementation, host bypass or obsolete temporary version is included. SDK-generated root logs were identified by the test's unique registration IDs and execution timestamps and preserved under ignored `dist/offline-mechanics-lab/1.0.0/sdk-library-logs/`; browser previews and scratch workspaces also stay outside deliverables. Unaffected checks are reused rather than rerun after report-only edits.
