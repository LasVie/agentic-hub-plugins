# Test report — 离线书架阅读器 1.0.0

Task `AH-20261027-offline-ebook-reader`; candidate `CAND-DSH-329`; owner Cai Zhenze; 2026-10-27 Asia/Singapore. Branch `feat/offline-ebook-reader`, base `205de7dd88a0c5407425e30180b3dcc9f776424c`. Build validation is recorded below; user manual testing passed on2026-10-27, explicitly confirmed in the current conversation. See USER_TEST_CONFIRMATION.md. GitHub delivery only is authorized.

## Package and source

Chinese edition, mapping `xrn1997/dsh-novel → 离线书架阅读器 → offline-ebook-reader`; internal ID `repo:agent-plugin:offline-ebook-reader`. Apache-2.0 adaptation pinned to upstream0.8.1 commit `f9a19f5fbd2d76ef5e970c2333a67f9dcb66b31c`; full license, attribution and modification notices inspected. See SOURCE_REVIEW.md.

| Artifact | Path | SHA-256 |
| --- | --- | --- |
| Canonical Agentic Hub wrapper | `releases/agent-plugin/offline-ebook-reader/1.0.0/offline-ebook-reader-1.0.0.zip` | `f6b38c5e1f05055c041971609a6669f5aefcb45d37563722d55e7e12c55b6cf4` |
| Native WorkSwarm test package | `plugins/offline-ebook-reader/test-packages/offline-ebook-reader-1.0.0-workswarm.zip` | `0da0b30a9961bc6ea1fd66b18b8085f1f10446eb14526ca013e6edfaa9669222` |

Canonical79518bytes; native78199bytes. Both extracted and CRC checked. All10 runtime files are byte-identical across source, canonical inner payload, native ZIP and installed WorkSwarm package. Manifest/version/tool/Skill paths, UTF-8 files, full original license hash, modification notices and exclusion of test state/logs/screenshots/caches verified in ignored `dist/offline-ebook-reader/1.0.0/validation/package-verification.json`. Different ZIP hashes reflect only the repository marketplace wrapper/native layout. No package payload was changed after these archives were created.

## Functional tests

- Source:35 tests passed using Python3.12/macOS (`/private/tmp/offline-backup-host-venv/bin/python -B -m unittest discover -s tests -p test_offline_ebook_reader.py -v`). First sandboxed run passed34 but could not start the loopback server under socket restrictions; the authorized run passed all35. This was not treated as a plugin defect.
- Extracted canonical payload:35 tests passed using the same suite with `EBOOK_TEST_PAYLOAD=/private/tmp/offline-ebook-build-20261027/extracted/offline-ebook-reader/offline-ebook-reader`.
- Real installed host SDK: reproducible `tests/offline_ebook_reader_host_smoke.py <installed-payload> <new-evidence-dir>` passed18 actual tool invocations, resolving3 native tools and1 Skill. External socket connections are explicitly rejected by the test. No model method is invoked. Earlier scratch equivalent also passed18; these are the same scope, not36 independent scenarios.
- The host's `validate_plugin_hot_load_worker.py <installed-payload>` passed: DeepAgent bound4 refs (1Skill/3tools) and unloaded them. This is SDK hot-load evidence, separate from running WorkSwarm RPC and a model conversation.
- JavaScript `node --check` passed. `asset_release.py check` and `pack` passed. Packaging-tool unittest18 passed; `check-repo` passed39source assets/48release ZIPs. These structural checks do not replace reader tests.

Functional coverage includes Chinese UTF-8/BOM/UTF-16 and explicit GB18030, original bytes preserved, duplicate import retaining position, chapter text/range continuation, EPUB2/3 spine order and NAV labels, visible omission warnings, settings/progress persistence and stale-revision refusal. Negative cases cover DRM/encryption, fixed layout/image-only/missing references, unsafe ZIP paths/duplicates/symlinks/expansion/malformed archives, XML DTD/entities/limits, file/text bounds, state symlinks/tamper/corruption, missing confirmation and cross-origin refusal. Actual loopback HTTP page/book/CSP/start/status-reuse/stop are tested. Fixtures are original synthetic text, not third-party books.

## Running WorkSwarm and browser

The existing6283 service accepted WebSockets but `config.get` failed with `TypeError: 'NoneType' object is not subscriptable`; required old temporary files/dependencies were also missing. No cause was assumed and no old service/config/plugin was changed. A fresh task-owned instance was prepared under `.research/ebook-workswarm-20261027` from local JiuwenSwarm commit `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`, with isolated data/tasks/cache and frontend6393/web29310/agent28310/gateway30310. Its initial worker failure was directly diagnosed from stderr: Unix socket path too long. Only its own TMPDIR was shortened to `/private/tmp/ebook-ws-20261027`; its launcher permits reuse of closed sockets. Worker then reported agent_ready. No unrelated source or service was modified.

Actual running backend checks passed: frontendHTTP200, direct/proxied WebSocket ping/pong, successful `config.get`, nativeZIP `plugin_packages.import_local`, `install` and `show` returning installed1.0.0/connected. Source/installed payload hashes match; model configuration and other-package inventory hashes before/after import match. UI Extensions → My Extensions displays the Chinese plugin, Skill and3 tools; Create → Upload File opens the .zip/.tar dialog. Backend import/install was exercised; OS file-chooser upload was not separately completed because the package was already installed.

Separate actual browser actions on synthetic books passed: open book, check correct2-chapter Chinese order/text and format warnings, jump to chapter2, scroll, save position (~18%), reload and restore. Font24/night preference save/reload persisted. Source reader stopped and installed native tool restarted the same shelf; a new URL restored chapter2/~18% and preferences. This tests real reader UI, not just HTTP success. It does not establish human acceptance or a model-to-tool conversation.

A separate manual shelf has the Chinese3-chapter TXT and2-chapter EPUB imported using installed tools. Its reader is running; current local URL/session is stored only in ignored `dist/offline-ebook-reader/1.0.0/manual-reader-session.json`. Native ZIP is already installed at http://127.0.0.1:6393/. The new host deliberately has `disabled-local-test` pointing to localhost port9 and no real API key. No paid/model conversation was run. The reader can be manually tested directly without a model; any chat test requires the user to configure their own model first.

## Evidence and limitations

Raw task-specific source/extracted logs, installed SDK JSON, hot-load result, host baselines/import/readback, original upstream audit and AI browser screenshots are preserved under ignored `dist/offline-ebook-reader/1.0.0/validation/`; development evidence is outside both ZIPs. These AI screenshots are not user screenshots. The original upstream archive/license hashes are in SOURCE_REVIEW.md. Host launcher/setup notes are in ignored `.research/ebook-workswarm-20261027/README.md`.

Bounded macOS/Linux desktop reader; Windows/touch/large books/full-fidelity EPUB unsupported. EPUB projects text, excludes CSS/fonts/media/math detail and rejects encrypted/fixed layout; no online sources, TTS, translation, editing or deletion. Chapter/offset is approximate, not a stable page number. Save explicitly before closing; pagehide save is best effort. Same-user malicious filesystem races are outside support; private local state is not encrypted. User must supply books they may use. Independent reader30minidle/4hmax timeout is separate from WorkSwarm.

No known blocker remains for manual testing. Await Cai Zhenze's explicit confirmation of this exact1.0.0 package and original screenshots of actual import/results and reading/resumption. Task Ready for Testing; candidate Planned. No commit, push, PR, merge, Release or Hub action; no user pass or Project Lead acceptance claimed.

## Phase 3 confirmation and unchanged-package verification

2026-10-27: Cai Zhenze explicitly confirmed manual testing of this exact1.0.0 package passed and supplied four readable originals. USER_TEST_CONFIRMATION.md preserves the faithful confirmation, image dimensions/hashes and evidence limits. Reused valid source/extracted/SDK/browser results above. Current canonical/native archives and all ten payload files were hash-compared again and match the tested bytes. Only outer delivery documentation/confirmation changed; no package payload, names, localization, wrapper or ZIP changed. Project Lead acceptance is pending. The task-owned manual reader session shown in images was stopped before public upload; other WorkSwarm/model services remain untouched.

Local Phase3 repository regressions: initial host environment without Node produced16errors/60skips; adding existing Node22.23.3 resolved those Node-dependent errors. Mixed host-SDK environment then ran449tests with2errors/1skip: unittest.assertWarns accesses a lazy SDK module's __warningregistry__, raising ModuleNotFoundError in the backup and ebook duplicate-entry tests before their bodies. No payload change was justified. A fresh Python3.12 environment with only declared requirements-dev.txt (PyYAML6.0.3) and existing Node ran439tests successfully,66optional-dependency skips, matching the dependency shape of CI. Separate ebook source/extracted35tests and installed SDK18calls/hot-load pass remain valid. Local prescribed MCP integration could not start because the old Node bundle's npm CLI target is missing; remote CI supplies Node24/npm and must pass this integration before merge. Raw outputs preserved locally; no unrelated SDK/runtime modifications made.
