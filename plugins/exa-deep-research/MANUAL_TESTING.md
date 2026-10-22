# User test plan — Exa Deep Research 1.0.0

Task AH-20261022-exa-deep-research; candidate CAND-CLD-017.

The canonical release ZIP uses the repository's double-directory marketplace
wrapper. The separate local test ZIP has manifest.json at its root for the
native JiuwenSwarm/WorkSwarm importer. Both must contain identical payload bytes.
The final handoff supplies their actual SHA-256 values.

1. In the target host's Plugin page, import the local test ZIP, install/enable
   it, and inspect the card. Expect Exa Deep Research 1.0.0, two skills and four
   native tools; English and Chinese display text should be readable.
   Import/install makes the package available in the library. In the single
   agent conversation, open the **+** menu beside the chat input, choose
   **Extensions**, then **Plugins**, and turn on **Exa Deep Research**. If a
   Connect button appears, connect it first, then check that its switch is on.
   Selection is per conversation; check it again after starting a new one.
2. Start a new conversation. Ask exa_search for three primary sources about
   MCP HTTP transports. Expect an actual Exa tool call, successful content and
   source URLs. No API key is needed for the anonymous quota.
3. Ask exa_fetch to read one result. Expect actual source content and a cited
   summary. A search snippet alone does not establish fetch success.
4. Ask exa_search_advanced to restrict a query to modelcontextprotocol.io.
   Expect actual filtered results or an honest empty/error result.
5. Exercise invalid inputs: empty query, numResults=0 and a file:// URL. Expect
   INVALID_INPUT, with no upstream call for those invalid requests.
6. Ask exa_research without allow_paid. Expect PAID_ACTION_REQUIRES_APPROVAL.
   With approval but no EXA_API_KEY, expect EXA_API_KEY_REQUIRED. Neither starts
   research. Do not spend money merely to complete this baseline test.
7. Optional, only if desired and authorized: set EXA_API_KEY in the host
   environment, restart the host and request a small low-effort managed task.
   Keep any returned runId, structured results and evidence. Do not claim a
   running or timed-out operation completed. This optional path has not been
   live-tested without an authorized account and budget.
8. Disable/uninstall the plugin. Verify the four native tools are removed and
   existing research assets are still available.

Capture original screenshots of the plugin/version, search/fetch results and
the guard cases. Keep API keys/private data out of screenshots. State whether
this exact version and ZIP hash passed or list issues. The upstream Hermes
tryout does not replace testing this native repository package.

Under AGENTS.md, the agent waits for explicit completion of testing of this
package before pushing or creating a delivery PR. After confirmation, test
screenshots are attached to that PR and tracked using evidence permalinks.
Song Haoran handles any later Agentic Hub submission personally.

## Tools absent from the main agent

Installing a package does not select it for a conversation. The host request
must include `plugin_names: ["exa-deep-research"]`. An empty list intentionally
unmounts it. After enabling the switch, send a new message requesting
`exa_search`. If progressive loading is enabled in your host, discover a
deferred tool with `tool_search`, then use its advertised execution mechanism.

Local follow-up on 2026-10-22 reproduced both states through JiuwenSwarm's
actual chat equipment loader. All four tools were present in the main and
inner ReAct registries after selection, and absent before selection and after
unmount. No runtime change or replacement ZIP was required. See
MAIN_AGENT_TEST_REPORT.md for the environment, command and limits.
