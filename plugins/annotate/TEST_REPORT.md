# Annotate / 网页圈选与批注 1.0.3 development validation

Date: 2026-10-22 (Asia/Singapore). Candidate CAND-CLD-264; original task AH-20261022-annotate; owner Wang Jie. Naming map: Annotate (claude-annotate) → 网页圈选与批注 → unchanged slug annotate.

## Scope and user instruction

Version 1.0.3 localizes the previously developed 1.0.2 package to Simplified Chinese as required by current main AGENTS.md. First-use automatic initialization is preserved. Tool names, parameters, structured status enums, dependency versions and original license text are preserved; human-facing wording changes.

The user declined another manual test round and subsequently explicitly accepted proceeding with the current package and instructed immediate PR creation. USER_TEST_CONFIRMATION.md records that instruction separately from the observed 1.0.2 manual test, hashes, accepted limitations and untested cases. No new 1.0.3 WorkSwarm manual run is claimed. The seven user screenshots were subsequently recovered as the exact conversation-saved PNG bytes, uploaded and verified in the dedicated PR evidence comment: https://github.com/LasVie/agentic-hub-plugins/pull/28#issuecomment-6338983543. No image was generated, recreated or recompressed; dimensions are the actual conversation-saved dimensions.

## Environment and commands

- macOS arm64, system Python 3.9.6, installed Chrome, application-bundled Node 22.11.0.
- The test driver uses isolated development Node 22.23.2. The target plugin starts with PATH `/usr/bin:/bin`, no explicit Node override, no installed dependencies and no prior runtime.json; it discovers the application's Node itself.
- Dependencies remain @modelcontextprotocol/sdk 1.32.0 and playwright-core 1.63.0. All 95 dependency versions, resolved URLs and integrity records match the reviewed 1.0.2 lock, excluding the changed root package version.
- Unit/static checks: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_*.py'` and `node --check` for both server JavaScript files.
- Functional automation: `ANNOTATE_PYTHON=/usr/bin/python3 node tests/run_annotate_integration.mjs`. This is developer-run automation, not a repeated user test.
- The independent MCP test client is not part of the deliverable. The development default uses the previously installed research SDK; on another macOS machine set ANNOTATE_TEST_SDK to an independent installation's `node_modules/@modelcontextprotocol/sdk/dist/esm` directory. It must not be installed into the target before its cold-start test.

## Results

The unit run contains 67 tests: 41 pass and 26 existing non-Annotate cases are skipped by their environment guards. All 17 Annotate tests run and pass, including dependency-inventory preservation, Chinese metadata/Skill/UI/tool descriptions, license preservation and bootstrap concurrency/failure handling. JavaScript syntax checks pass.

After syncing the submission branch to current main feef362, the full unit suite was rerun: 74 tests, 46 passed and 28 existing environment skips. All 17 Annotate tests still passed. Runtime ZIP bytes were not changed by submission documentation updates.

The actual MCP/Chrome harness passes 13 check groups:

1. Offline cold npm installation fails clearly in Chinese, leaves no readiness stamp and can be retried.
2. Two simultaneous real MCP starts share one installation.
3. WorkSwarm Node discovery, automatic preparation and protocol-safe stderr work without manual setup or Conda activation in the target.
4. Default MCP instructions and every exposed tool description are Chinese; version and identifiers remain valid.
5. Standard MCP handshake works without Claude-specific channels.
6. Empty retrieval and public/non-HTTP URL rejection behave correctly.
7. Real Chrome displays the Chinese annotation UI; waiting remains bounded.
8. Rectangle/note interaction and Send return Chinese user text, DOM context and two inline PNGs.
9. Unknown notes and premature batch completion produce Chinese validation errors.
10. The actual toolbar reads 发送给智能体, 智能体处理中 and 全部完成; tooltips and batch descriptions are Chinese. Automated screenshots were visually inspected for UTF-8 rendering.
11. Per-note progress reaches the page, explicit completion works and temporary batch screenshots are removed.
12. Clear, close, closed-state response and unchanged fixture source are verified.
13. A second MCP process reuses dependencies without npm reinstall.

Source-payload automation passed at 2026-10-22T10:23:21Z. Evidence is in `.research/annotate/1.0.3/`, including integration-report.json, failure/runtime stderr and automated PNGs. These files are development evidence, not user screenshots.

## Final archive checks

Canonical: `releases/agent-plugin/annotate/1.0.3/annotate-1.0.3.zip` and artifact.json. Local native companion: `/Users/dashing/Desktop/huaweisg/local-tests/annotate/1.0.3/annotate-1.0.3-workswarm.zip` and local-test-artifact.json. Both payload inventories must match; hashes are recorded in the artifacts. The canonical marketplace wrapper is not claimed to have been directly imported by the desktop host.

The final canonical ZIP is extracted for the same automated harness, using an initially empty online npm cache. The exact extracted Chinese payload, declared files, notices and original MIT text are checked. The MIT SHA-256 remains 560cb98de97e83fc25542efdd90e7ab60fa0f824bb9a3d0152c0141b97935da3. ZIPs exclude node_modules, caches, developer tests and task records. Old 1.0.1/1.0.2 archives remain local and unchanged, not silently overwritten.

Final extracted-payload automation passed at 2026-10-22T10:26:02Z: all 13 groups pass and npmCacheInitiallyEmpty is true. Canonical SHA-256: 68849b9d4ef7ab1886974c35de7450dd5870c44a7aa9c8719945051b7be7df9a. Native companion SHA-256: 65063bf4ebc0b6639a85d9dd9c8a04f7f5d1eb71c3e2b435275375c96d5f1fa0. The companion builder confirms identical payload inventories; legal text remains byte-identical. These are automated development results, not renewed user test completion.

## Limits and delivery state

Automatic preparation runs at first use, not ZIP import, and requires network plus writable plugin/cache directories. Python, Chrome and Node are prerequisites, not downloaded by the plugin. Target is macOS desktop; Windows and remote deployment are not promised. Third-party diagnostic details, required legal texts, protocol identifiers/values and names are intentionally retained rather than mistranslated.

Actual WorkSwarm model-level image visibility remains host-dependent. The prior user report says inline PNGs were visible but read_file multimodal input was disabled; this is disclosed, not treated as unrestricted image support. The user did not execute clear, close-then-read, public-URL rejection or warm-reuse cases in their earlier round; developer coverage does not rewrite that history.

The user accepts submission of the current package without another manual round and explicitly directs PR creation now, superseding the earlier local-only hold. The previously unavailable screenshot attachments have now been recovered, attached and verified; the evidence receipt is in USER_TEST_CONFIRMATION.md and the dedicated PR comment. Do not merge automatically or claim Project Lead acceptance. Song Haoran handles any later Hub operations.
