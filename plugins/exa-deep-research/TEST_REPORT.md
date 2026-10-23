# Exa Chinese edition 1.0.1 validation

Owner **Nguyen Trung Dung**; task AH-20261022-exa-deep-research;
candidate CAND-CLD-017. Date 2026-10-23, Asia/Singapore.
Name mapping: Exa Deep Research -> **Exa 深度研究** -> exa-deep-research.

Status: **Chinese 1.0.1 user-confirmed**, original screenshots received on
2026-10-23. The package bytes remain unchanged. Required CI and the actual PR
merge state are recorded on the delivery PR; Project Lead acceptance is pending.

## Package changes and identity

The actual README, two Skills, eleven references, display metadata, four tool
descriptions and 23 local description/error literals are localized. The
references clarify native length limits and evidence interpretation. API/tool
identifiers, schema keys and transport/control structure remain unchanged;
AST comparison with string literals normalized confirms the Python structure.
Original MIT license and copyright bytes are unchanged. Raw remote/source text
is preserved in its source language; Chinese summaries do not replace original
quotations. Explicit end-user language requests are supported by instructions.

| Archive | SHA-256 |
| --- | --- |
| Native exa-deep-research-1.0.1-workswarm.zip | 497d4bd1d51f4476b8cdc8d3dfdcb177c6d052880b73a31e7a79d2c6d2e9b54a |
| Canonical exa-deep-research-1.0.1.zip | a924aac36f89663c7d02e8a823e13bb28238729b81754b769fa8e0e79e7f9c16 |

All 19 source/canonical/native payload files are byte-identical. CRC, safe paths,
UTF-8, declared files and all 13 adapted upstream fingerprints passed; full MIT
SHA-256 remains 715e1b754d876f214cba57f6ad09bc6e5e48aab46aa3774b00e82a49ab04c742.
The original confirmed 1.0.0 archives remain unchanged in the original worktree.

## Exa functional and host checks

- Source: **12/12 passed**, no skips, using actual openJiuwen Tool classes.
- Independently extracted canonical payload: **12/12 passed**, no skips.
- Chinese queries, local errors, card descriptions, instruction defaults and
  lossless UTF-8 result preservation pass. Transport alone is mocked in the
  deterministic unit cases; SDK Tool invocation/streaming are real.
- Actual native import/install, loader/resolver, Smart admission and full
  equipment gate passed with the locally patched host. All four tools register
  in main and inner ReAct registries under direct and progressive exposure.
- Main registry guard dispatch, all four deferred schemas, unload and uninstall
  pass. Permission policy activation is isolated from account setup; the
  admission accounting and equipment gate themselves are real.
- **Actual anonymous search with Chinese query, page fetch and a domain-filtered
  search request passed** from the installed ZIP. Search returned 9,688 content
  characters. No fallback provider, LLM request or authenticated/paid research
  operation was used.

Environment: Python 3.12.6, mcp 1.29.0, jsonschema 4.26.0; SDK source revision
0ab5913b250d565b35bff3828dae438939cb1acd. Loader SHA-256
6d5bdf4c3e7d559c968f090735ab3b70aadbf758c554d5d8e9aee012a72c2262.
Host base 1bd3583934b76dd4b338ca959a6bff6b4cca3a2f plus the local admission
fix, source SHA-256 d53903c7531615c738dade0e59730c1369eb6052602448fc3f62e2495e73051f.
This host fix is separate and is not shipped inside the plugin ZIP.

Bounded evidence: HOST_RESULTS_1.0.1.json and EXTRACTED_PACKAGE_RESULTS_1.0.1.json.
Commands use the existing host virtual environment with -B. Unit command:
`python -B -m unittest discover -s tests -p test_exa_deep_research.py -v`.
For extracted tests set EXA_TEST_PAYLOAD to .research/extracted-exa-1.0.1.
Host command: `python -B tests/exa_plugin_smoke.py --sdk-root
D:/jiuwen_repos/agent-core-latest --host-root D:/jiuwen_repos/jiuwenswarm
--payload plugins/exa-deep-research/exa-deep-research --archive
.research/test-packages/exa-deep-research-1.0.1-workswarm.zip --live
--output .research/exa-zh-host-live.json`.

## Repository verification and limits

`asset_release.py check`, `pack` and `check-repo` pass: **23 assets / 31 release
ZIPs**. The unchanged confirmed English release is preserved outside the current
delivery tree instead of being relabeled as a Chinese release.

The complete Windows suite is **not green**. With PYTHONUTF8=1 and
PYTHONIOENCODING=utf-8: 185 tests, no assertion failures,
23 error records and 60 skips.
Unchanged main 3a57bc0: 173 tests, no assertion failures,
23 error records and 60 skips.
Error-ID occurrence counts and skip IDs/reasons match exactly; the 12 additional
Exa tests all pass. These baseline errors involve fcntl/fchmod, unavailable
symlink privileges, missing Node and resulting cleanup failures. No unrelated
asset was changed to conceal them. The initial default-locale run also hit
CP1258 Unicode errors; UTF-8 configuration removes those assertion failures.
See REPOSITORY_COMPARISON_1.0.1.json and ignored local test logs.

Node/npm is unavailable, so the separate unrelated MCP development integration
was not run locally. GitHub's required Linux CI runs the complete suite,
repository contract and Node integration before merge. The initial 23/31 count
above describes the recorded 3a57bc0 baseline; current-main revalidation is
revalidation after rebasing on d462c34 passes **28 assets / 36 release ZIPs**.
The confirmed canonical/native ZIP hashes and all 19 payload files still match.

The agent's automated checks did not drive the live frontend or evaluate a
model conversation. The user subsequently confirmed the Chinese package works
and supplied the five original screenshots described below.
Paid research remains optional and untested. Historical 1.0.0 service/registry
and 68 host regression results remain versioned in TEST_REPORT_1.0.0.md,
MAIN_AGENT_TEST_REPORT.md and SMART_ADMISSION_FIX.md; they are not new-version
manual evidence. See USER_TEST_CONFIRMATION.md for the actual user statement.

## User conversation evidence received 2026-10-23

Confirmation: "The plugin is working in chinese version too, you can see the
latest 5 screenshots here". The reply follows the exact 1.0.1 package handoff
and Chinese prompts. See evidence/1.0.1/index.json for original image hashes.

| Original | Visible evidence |
| --- | --- |
| 01-fetch.png | Chinese exa_fetch prompt and response, official source URL and Chinese transport summary; visible UI time 14:53. |
| 02-advanced-search.png | Chinese filtered-search prompt with numResults=3 and includeDomains, response reporting three official-domain results; visible UI time 14:54. |
| 03-paid-approval-guard.png | allow_paid=false prompt, PAID_ACTION_REQUIRES_APPROVAL and the current Chinese approval message; visible UI time 14:54. |
| 04-search-summary.png | Chinese search prompt, source links and Chinese summaries with an English introduction; visible UI time 14:53. |
| 05-search-tool-event.png | Expanded exa_search event, actual arguments and successful ok=True/web_search_exa result. |

The first four images show conversation responses, not expanded raw tool
records. The fifth independently corroborates actual search execution, but has
an English query and no visible package version. None displays a version/hash;
current-package attribution relies on the user's explicit reply to the 1.0.1
handoff, with the Chinese guard message matching the new payload. No manual
invalid-input, uninstall or paid-research coverage is inferred. One mixed-language
introduction remains a model-output observation; do not claim universal Chinese
wording. The user accepted the current result. Original full-resolution image
bytes are preserved without processing, and checked for exposed credentials.
