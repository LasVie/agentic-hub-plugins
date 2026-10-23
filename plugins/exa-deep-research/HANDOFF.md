# Exa Chinese test handoff

Owner: Nguyen Trung Dung. Task AH-20261022-exa-deep-research; CAND-CLD-017.
Current package **Exa 深度研究 1.0.1**, local Ready for Testing.

Native importer ZIP:
`D:/jiuwen_repos/agentic-hub-plugins-exa-submit/.research/test-packages/exa-deep-research-1.0.1-workswarm.zip`

SHA-256: `497d4bd1d51f4476b8cdc8d3dfdcb177c6d052880b73a31e7a79d2c6d2e9b54a`.

Canonical marketplace ZIP:
`releases/agent-plugin/exa-deep-research/1.0.1/exa-deep-research-1.0.1.zip`

SHA-256: `a924aac36f89663c7d02e8a823e13bb28238729b81754b769fa8e0e79e7f9c16`. Both ZIPs contain the same 19 native files.

Twelve source and twelve extracted SDK regressions, actual host admission/tool
registration and three live anonymous service cases passed. Full Windows suite
has the same baseline error/skip IDs as unchanged main; see TEST_REPORT.md.

The user explicitly confirmed full-conversation testing and authorized merging
English 1.0.0. That confirmation is preserved in USER_TEST_CONFIRMATION.md and
the tracker. The original ZIPs remain unchanged in the original worktree.
Current main now requires Chinese packages and original screenshots; therefore
the changed 1.0.1 needs its own user test completion and original test images.
No push, PR, merge or Hub operation has occurred. Existing merge authorization
will be reused after the changed-package materials gate passes.

Follow MANUAL_TESTING.md. Import/install 1.0.1, click Use, run a Chinese
search/fetch conversation and the no-paid guard, capture the displayed version
and actual tool results, then confirm this exact package. The local host
admission fix remains a separate host source change; the package does not fix
an independently installed host executable.
