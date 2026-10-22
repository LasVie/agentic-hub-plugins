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
