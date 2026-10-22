# Chinese runtime candidate: dsh-smart-download 1.0.1

Date: 2026-10-22 (Asia/Singapore). Task AH-20261022-dsh-smart-download; candidate CAND-DSH-139; existing owner Siu Lok Yin retained. The user explicitly delegated actual local WorkSwarm import/prompt testing and a conditional PR on success. The coordinating agent has now completed actual current-version import/model-prompt tests in the user-open local WorkSwarm desktop app and retained original full-resolution screenshots. Independent installed-file/output verification passed. These are delegated AI-operated tests, not human-performed testing; the historical 1.0.0 confirmation below does not confirm these bytes.

## Current automated verification

- Environment: macOS arm64, actual Python 3.11.17 runtime at `/Users/lasvie/Documents/openJiuwen/openJiuwen_PersistentAgent/.venv/bin/python`; actual OpenJiuwen Tool API imported from the local runtime source. `REQUIRE_OPENJIUWEN=1` rejects fallback stubs in this run.
- `PYTHONDONTWRITEBYTECODE=1 REQUIRE_OPENJIUWEN=1 <runtime-python> tests/run_dsh_smart_download_integration.py`: PASS against a real local ThreadingHTTPServer.
- Functional assertions: default private-network rejection; 4-worker ranged transfer with exact bytes and verified SHA-256; ignored-range fallback to one worker; persisted completed state; Chinese checksum failure with stable CHECKSUM_MISMATCH in both tool and status responses and no final output; existing-output protection; forced interruption followed by real resume with exact final bytes; invalid and missing task IDs; malformed URL as a structured failure; URL credentials/query redacted in rejected-task status; existing output-directory mode 0750 preserved, status file 0600 and plugin-owned status directory 0700.
- `tools/asset_release.py check plugins/dsh-smart-download`: PASS. Native manifest tags retain zh/en objects; outer asset tags remain strings. Machine schemas, IDs, states and error codes retained.
- Prominent modified-file notes present; full MIT license SHA-256 remains `ac0fc870e1cf8671b5beb57e0a58a11b2514076c867318e98b0d2c03db0389e6`. No new dependency or licensed material.
- Final marketplace/native ZIP extraction: PASS, all six payload files match source and both archives byte-for-byte; full MIT license hash unchanged, historical 1.0.0 archive unchanged. The final extracted native payload repeats the real HTTP integration successfully with the actual SDK.
- Isolated real JiuwenSwarm host import/install/load/uninstall: PASS, version 1.0.1, two tools and one Skill, isolated temporary data directory only. Actual desktop UI and model prompt results are documented in the next section.
- Detailed package/hash results and raw source/extracted/isolated-host logs are retained in the delegated host-test output directory; package-verification.json and the current HOST_LOCALIZATION_TEST.json / ACTUAL_HOST_TOOL_EVIDENCE.json records identify the actual delegated desktop/model scope.

## Actual delegated WorkSwarm desktop import and model-prompt results

Recorded 2026-10-22. Session `web_1a162fb4927_ffd2d41deec4`; actual local WorkSwarm desktop UI on `127.0.0.1:5173`, operated by the coordinating AI under the user's explicit delegation and conditional PR authority. Only this session's `history.jsonl` target-tool events were independently read; no adjacent session, system/provider configuration or credential files were read.

- Native import: PASS for 1.0.1. All six actual installed payload files match source, the extracted native directory, native ZIP and marketplace inner payload byte-for-byte. Native SHA-256 `09703b3ebf26336c45920e254d065e29681843e2c19686fb33120d467ddba52c`; marketplace SHA-256 `c5d95dece5001b57cdfd26c0bfab04101c95f3d827c3c8640a077868bcbd3074`.
- Actual `smart_download` and `download_status`: PASS. Task `948d2a9eaa6f497c95780524b6324362` completed with 89 bytes, `verified=true`, one worker and SHA-256 `15db81e9410d16cb0d5efd7bc2473a4925bbde0bad56964f70631f17d90d79b5`; independent downloaded bytes equal the fixture.
- Existing-output protection: PASS. Task `47aa20a2104a4cf28c132f261ab16c73` returned `OUTPUT_EXISTS` with a Chinese message. The original 89-byte output still matches the fixture after the rejected repeat.
- Default private-network protection: PASS. Task `06a01e69908c4a73b0e1c15b796725cf` returned `DOWNLOAD_FAILED` with `默认禁止访问私有、本地或保留地址：127.0.0.1`; independent verification confirms neither the rejected target nor its `.part` file exists.
- Original screenshots retained: `import-list.png` and `prompt-result.png`, both original JPEG bytes at 3600x2260 despite the filenames' `.png` suffix. No conversion/recompression was performed. Their hashes, actual dimensions and paths are recorded in `INSTALLED_PAYLOAD_VERIFICATION.json` and `delivery.json`. Actual PR attachment/comment links remain pending; local images/logs do not substitute for verified screenshot permalinks.
- Limits: this 89-byte desktop test did not trigger acceleration or interrupted-transfer resume (`resumed=false`). The prior real-SDK automated test separately forced interruption/resume and exercised multi-worker/fallback behavior. No public internet success or fixed speed gain is inferred. `current_version_user_test_confirmation` remains null: delegated AI operation is not relabeled as human-performed testing or final Project Lead acceptance. PR #23 is open; no current-version merge or Hub submission/publication is claimed, and Asset Ledger remains unchanged.

## Current boundaries

Local HTTP fixtures explicitly permit loopback solely for approved testing. Public internet behavior, fixed acceleration gains, cloud-drive management and file execution are not claimed. A manually timed interruption is not claimed here; the deterministic automated integration actually interrupts and resumes a transfer. Current screenshots and GitHub/Hub status must be recorded from real actions, not inferred from logs. Publisher, source authorship, owner and historical release 1.0.0 are unchanged.

## Historical 1.0.0 test report

# Test Report

## Candidate under test

- Asset: `dsh-smart-download` 1.0.0
- Candidate/task: `CAND-DSH-139` / `AH-20261022-dsh-smart-download`
- Pinned upstream: `v1.4.6`, commit `e80a6574407fed44a8ad6efde3a789bce119beeb`
- Environment: macOS, Python 3.12 for the native loader check and system Python 3 for functional tests

## Automated results

| Check | Command | Result |
| --- | --- | --- |
| Repository package contract | `uv run --with pyyaml python tools/asset_release.py check plugins/dsh-smart-download` | PASS |
| Native OpenJiuwen loader and path validation | `uv run --with openjiuwen python -c '...load_plugin_package...validate_plugin_paths...'` | PASS: plugin `dsh-smart-download`, 2 tools, 1 Skill |
| Functional HTTP integration | `python3 tests/run_dsh_smart_download_integration.py` | PASS |
| Release-tool regression suite | `uv run --with pyyaml --with pytest python -m pytest -q tests/test_asset_release.py` | PASS: 15 tests |
| Python syntax and diff hygiene | `python3 -m py_compile .../smart_download.py`; `git diff --check` | PASS |

The functional integration used a real local `ThreadingHTTPServer` and verified:

- default loopback/private-network rejection;
- four-connection Range download and exact byte reconstruction;
- server filename sanitization and URL query redaction;
- correct SHA-256 success and deliberate mismatch failure without a final output file;
- persisted completed status lookup;
- a deliberately interrupted single-stream transfer leaving a partial file, followed by a successful conservative Range resume;
- invalid status-task ID rejection.

## Upstream check

The pinned repository, tag, manifest, root MIT license and built `dist/` files were inspected. Its own npm test suite was not rerun because the available host has Node 18 while upstream requires Node 22+, and the installed Corepack launcher could not resolve its pnpm distribution. This does not substitute for the port tests above; the delivered Python implementation has no Node or pnpm dependency.

## Known boundaries and user acceptance

- WorkSwarm desktop import and model-driven calls passed for the exact native ZIP recorded in `USER_TEST_CONFIRMATION.md`.
- Public internet downloads remain subject to host network policy and remote server behavior.
- Servers that do not correctly support ranges use a single-stream fallback.
- No connector, background service, API key, external downloader binary or private-network access is required by default.
- Manual interrupted-transfer timing did not exercise resume because the transfer completed first. The forced automated integration case passed resume with exact bytes; the manual limitation is retained rather than reported as a pass.
- No Hub submission has been made. GitHub delivery begins only for the exact confirmed payload hashes above.
