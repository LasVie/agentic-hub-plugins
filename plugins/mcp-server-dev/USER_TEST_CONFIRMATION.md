# User test completion — mcp-server-dev 1.0.1

- Task: AH-20261022-mcp-server-dev
- Candidate: CAND-ANT-011
- Owner: Vannes Wijaya
- Confirmation source: the current requesting human user in the Codex conversation; no separate identity is inferred from the GitHub login.
- Recorded: 2026-10-22 16:09 Asia/Singapore; the exact message timestamp is not exposed.
- Linked progress report: RPT-20261022-mcp-server-dev-101-confirmed

The user explicitly stated: “按照最新的agents.md 测试完成，提交合入，提交的版本要是市场版本” — testing is complete; submit and merge the marketplace version under the latest AGENTS.md.

## Confirmed artifacts

| Purpose | Version | SHA-256 |
| --- | --- | --- |
| Native ZIP used for user testing | 1.0.1 | aa93012b28f254015fbd0744a80b44ada6a54e373df73be9533c70e58a21e0ab |
| Marketplace ZIP for this PR | 1.0.1 | acd7f7b1c2fecb6ac1887e80cce5f86e0a7502fd60c6dc546f77ef909249701f |

All 17 runtime files are byte-identical between the two variants. The marketplace ZIP, including its wrapper, is unchanged from the candidate supplied before the user's completion confirmation. The PR ships the marketplace ZIP at `releases/agent-plugin/mcp-server-dev/1.0.1/mcp-server-dev-1.0.1.zip`; the separate native testing ZIP is not a release artifact in this PR.

## Original test screenshot

The user supplied `Screenshot 2026-10-22 at 16.06.51.png`: 3600 × 2338 pixels, 1,167,566 bytes, SHA-256 `5e1c90134e1e1913229aacc1b216bcf791f277964825ea0a8a24d64069e91985`. The original is preserved locally for attachment to the PR. A verified PR evidence permalink is recorded in the tracker after attachment; a local file path is not screenshot evidence in that table.

The screenshot labels the installed plugin as 1.0.1 and generated examples as 0.1.0. It reports successful real App stdio add(2,3)=5, invalid-input rejection/recovery and MCPB validate/pack/unpack/relocated execution, plus dependency license collection. Its stated user environment is Python 3.9.6, Node v22.11.0 and npm 10.9.0. These are user-reported host results; the separate automated regression evidence remains in TEST_REPORT.md.

No known blocking issue remains reported. MCP Apps host visual rendering and remote deployment were explicitly untested, matching the existing documented scope. The old blank-card regression is covered by native card/localization checks and the replacement package. This confirmation does not claim final Project Lead acceptance or Agentic Hub publication.

## GitHub handoff

Under the latest AGENTS.md, deliver the unchanged marketplace package through a checked and merged PR, attach the original test screenshot, verify branch cleanup and synchronize the original records. Song Haoran personally owns subsequent Agentic Hub submission/publication and its evidence. Hub work is not a contributor completion prerequisite; final acceptance of the GitHub handoff is still separate.
