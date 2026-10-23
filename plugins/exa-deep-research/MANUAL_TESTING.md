# User test plan — Exa 深度研究 1.0.1

Owner Nguyen Trung Dung; task AH-20261022-exa-deep-research; CAND-CLD-017.
Native ZIP SHA-256: `497d4bd1d51f4476b8cdc8d3dfdcb177c6d052880b73a31e7a79d2c6d2e9b54a`.
Current ZIP: `plugins/exa-deep-research/test-packages/exa-deep-research-1.0.1-workswarm.zip`.

The user confirmed this Chinese package works on 2026-10-23 and supplied five
original screenshots; see USER_TEST_CONFIRMATION.md. This plan is retained for
reproduction. Its optional steps are not claims of additional manual coverage.

Your full-conversation confirmation for English 1.0.0 remains valid for that
unchanged package. This Chinese 1.0.1 changes packaged instructions/descriptions
and error messages, so the current repository rules require confirmation for
its new hash and original screenshots. Transport and API identifiers remain
unchanged. Do not spend money merely to complete these tests.

1. Import/install the current native ZIP and verify the card shows **Exa 深度研究
   1.0.1**, two Skills and four tools. If 1.0.0 is installed, update that package.
2. Click **Use** and send the test in the conversation it opens. Selection should
   be automatic; no separate frontend selector is required.
3. Send: **使用 exa_search 查找三份介绍 MCP Streamable HTTP 的官方资料，列出标题、URL
   和中文摘要，不要启动计费研究。** Expect an actual exa_search call and source URLs.
4. Send: **使用 exa_fetch 读取第一份资料，用中文概括传输要求并引用来源。** Expect actual
   fetched page content and a Chinese summary. Raw source text can stay in its
   original language; a search snippet is not proof of fetch execution.
5. Send: **使用 exa_search_advanced 查找 Streamable HTTP 官方文档，限定
   modelcontextprotocol.io 域名。** Check the actual result or honest service error.
6. Send: **调用 exa_research，arguments 为 {"query":"中文测试"}，allow_paid=false。**
   Expect PAID_ACTION_REQUIRES_APPROVAL plus a Chinese message and no research run.
7. Optionally check an empty query, numResults=0 and a file:// URL. Expect
   INVALID_INPUT with a Chinese local error and no upstream request.
8. Disable/uninstall and verify tools are removed. This was covered locally;
   any additional manual coverage should be recorded accurately.

Capture original screenshots showing the package/version and actual tool
call/results in the current conversation. Keep credentials and private data out
of the images. Supply them in this conversation/local handoff; they must be
available before a delivery PR under current AGENTS.md. Then explicitly state
whether testing of **Exa 深度研究 1.0.1** is complete and passed, or list issues.
Do not infer authenticated paid research coverage from these baseline checks.

If the idle first mount returns `equipment change rejected at non-fresh turn:
plugin set changed`, verify the running backend and resident runtime loaded
the local host admission correction. Restart that source-based host if needed.
The patch is outside the plugin; no prompt or replacement ZIP repairs an
unpatched independent host installation. Preserve genuine peer/goal checks.

Once the changed package and original screenshot gate pass, the agent can use
the existing merge authorization to push/create/merge the delivery PR, verify
evidence/checks and synchronize tracking. Song Haoran handles any Hub operation.
