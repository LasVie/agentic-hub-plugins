# Modern Web Guidance 1.0.0 validation

Task: AH-20261027-modern-web-guidance; candidate CAND-CLD-076; owner Gan Mingrui.
Date: 2026-10-27, Asia/Shanghai (same UTC offset as tracker Asia/Singapore).

Environment: Windows, CPython 3.12 from the existing JiuwenSwarm .venv, WorkSwarm 0.2.5b1 with actual openJiuwen 0.1.19 SDK, Node.js v24.22.0. Node 20+ is the declared runtime requirement; only the available Node 24.22.0 was exercised. No fake SDK or model response is substituted.

## Automated checks

Source run: 10 Python tests (including all 12 Chinese top-ranked queries, full guide retrieval, 16 invalid request cases, malformed/oversized input, unrelated queries, hash coverage, no payload writes, relocation, actual SDK loader/Tool/stream calls and missing Node) passed after one relevance fix; 5 Node BM25 tests passed.

The first run caught a database-index query incorrectly matching the generic Chinese term for data in the table guide. The runtime now requires more than one Chinese term in multi-term queries unless an exact API/English keyword matches. This test now passes. This does not promise perfect semantic relevance; the documented lexical search still requires description-based selection.

An additional corrupted-catalog error test was then added with Chinese startup error handling. Final extracted-package rerun and definitive archive hashes are recorded in `test-evidence.json` (11 Python tests + 5 Node tests, including subcases). The asset source, extracted canonical ZIP and native import transport are compared byte for byte. No source payload file is changed by extraction tests.

Final result: **11 Python tests and 5 Node tests passed**, zero skips, on the extracted final payload. All 23 payload files match the source and native transport exactly. Deterministic repack produces identical canonical ZIP bytes.

| Transport | Bytes | SHA-256 |
| --- | ---: | --- |
| Canonical marketplace ZIP | 106884 | `94c518ae4400e5cab1867c68447ba13a78bd9975faf3a74c33deed8c98e7ffd3` |
| Local native-import ZIP | 104548 | `295a9af3d23306068801d3ee7b9f72af78e02e6c792bb97eaf31558839f3101b` |

Native import file relative to the shared workspace: `plugin-builds/modern-web-guidance/1.0.0/modern-web-guidance-1.0.0-native.zip`. Canonical file relative to this repository: `releases/agent-plugin/modern-web-guidance/1.0.0/modern-web-guidance-1.0.0.zip`. Both are version 1.0.0 and differ only in transport layout. The current local importer source `_zip_package_root` requires manifest at root or one child level, so the native ZIP is the local test entry point. The plugin was already installed when browser access became available; its installed state and all 23 payload files were verified below.

Commands from repository root, using the existing host Python environment:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
& '../../jiuwenswarm/.venv/Scripts/python.exe' tools/asset_release.py check plugins/modern-web-guidance
& '../../jiuwenswarm/.venv/Scripts/python.exe' plugins/modern-web-guidance/tests/test_plugin.py
node --test plugins/modern-web-guidance/tests/test_bm25.mjs
& '../../jiuwenswarm/.venv/Scripts/python.exe' tools/asset_release.py pack plugins/modern-web-guidance
```

`MWG_TEST_PAYLOAD` selects an extracted payload for the same test suite. Python UTF-8 mode is needed for Windows terminal evidence; the Tool subprocess boundary always explicitly uses UTF-8. The SDK emits existing Pydantic deprecation warnings and normal registration logs; those do not indicate plugin failures.

## Coverage and limits

- Real native loader resolves one Skill and one Tool from the actual manifest; its Tool executes local Node search/retrieve/help/stream without network downloads.
- Twelve Chinese topics return the expected top guide; all 12 guides have Chinese content, exact source links, modification notices and snapshot caveats. The three full bundled license/notice hashes and mapped guide hashes are verified.
- Invalid IDs/path traversal, unknown actions/fields, empty/long queries, invalid limits, malformed JSON and oversized stdin fail with Chinese messages. Shell-looking query text is passed as JSON data, never shell code.
- Ordinary subprocess calls run with no package installation, model download or service access. Source inspection confirms no network/telemetry import and only local static file reads. This is not a packet-capture audit of the entire host SDK.
- No real IME/Safari/assistive-technology validation or performance benchmark is claimed for the instructional snippets. Host dialogue testing is documented below. The import operation itself predated observation. Explicit user test-completion confirmation is recorded below; PR, merge and Hub submission were not yet performed at confirmation time.

## Delegated host browser test

On 2026-10-27 around 12:05–12:09 Asia/Shanghai, the AI operated the user's connected Chrome tab at `http://localhost:5173` under the user's explicit request to complete testing and screenshots. This is delegated AI testing, not a claim that Gan Mingrui personally executed or accepted the tests. The browser extension connection was restored. WorkSwarm displayed model `deepseek/deepseek-v4.1-flash` in single-agent mode.

The installed extension details show the Chinese display name, one Skill and the query Tool. All 23 installed payload files under `C:/Users/Gary/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/modern-web-guidance` exactly match the source previously compared with both ZIPs. No packaged files changed.

Conversation: `http://localhost:5173/chat/web_1a17b892dac_f543033b14ff`.

| Check | Observed result |
| --- | --- |
| Actual help tool call | `ok=True`, version `1.0.0`, guide count `12` |
| Chinese IME search and retrieve | `ime-safe-enter-submit`; Chinese response correctly preserves composition before preventDefault, Shift+Enter, and the Safari/keyCode caveat |
| Dialog search and retrieve | `light-dismiss-a-dialog`; response distinguishes fixed compatibility snapshot, feature detection and internal blank-space boundary |
| LCP search and retrieve | `optimize-image-priority`; response prohibits lazy-loading the LCP image and distinguishes ordinary below-fold from hidden carousel images |
| Uncovered PostgreSQL index query | Tool returns `results=[]` and Chinese scope message; response does not invent a guide |

The UI execution panels were expanded to verify real tool inputs and returned results, rather than accepting the model's claim alone. The first turn had 7 displayed tool events (schema discovery plus wrapper/native events); the second had 10 (wrapper/native events for five operations). No plugin error appeared. Earlier historical conversation loading and catalog-cache notices did not recur in the new completed test conversation.

Original JPEG screenshots and DOM/AX observations are stored relative to the shared workspace at `plugin-builds/modern-web-guidance/1.0.0/host-test-20261027/`. `host-test.json` and `test-evidence.json` record screenshot hashes and scope. Screenshots show installed details, actual help execution/results, and dialog/LCP/uncovered-topic conclusions. These are original browser captures, not generated mockups. The host's long-image export was attempted, but no downloaded artifact was verified and none is counted as evidence.

## User test confirmation

Submission preparation: `check-repo` passed 42 source assets and 51 release ZIPs in an isolated `git -c core.autocrlf=false archive origin/main` plus this asset. Ordinary Windows checkout/archive conversion produces unrelated pre-existing license hash failures. Scoped `.gitattributes` preserves this plugin's exact confirmed payload bytes. A broader Windows run of the existing repository suite ran 428 tests with 172 failures, 102 errors and 3 skips; it is not a pass (including existing assets reporting `unsupported_platform`). The repository's Ubuntu CI is required before merge; no unrelated asset implementation was changed to mask these platform failures.

Gan Mingrui explicitly confirmed in the current conversation: **“1.0.0 测试通过”** (version 1.0.0 testing passed), recorded 2026-10-27 14:02:24 Asia/Shanghai. No message permalink is available. Confirmation report: `RPT-20261027-modern-web-guidance-confirmed-100`; task `AH-20261027-modern-web-guidance`. Both exact ZIP hashes above were rechecked unchanged after confirmation. Known blocking issues: none.

The user's confirmation follows review of the delegated AI browser results and original screenshots. It does not claim personal execution of the tests or actual Safari/IME/performance validation. All pre-submission materials are available. GitHub delivery proceeds under AGENTS.md Phase 3; final Project Lead acceptance and Hub operations remain separate.
