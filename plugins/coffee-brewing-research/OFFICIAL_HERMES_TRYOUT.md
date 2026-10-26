# Optional official Percolate MCP tryout in Hermes

This tests the publisher's original MCP service, not the WorkSwarm ZIP or an English-localized port.
The Claude plugin ZIP is not a Hermes installer. The official bundle README allows using the server alone
in compatible MCP clients; Hermes documents remote HTTP servers in its MCP configuration reference.

Merge this entry into your existing `~/.hermes/config.yaml`, preserving other configuration:

```yaml
mcp_servers:
  percolate:
    url: https://mcp.percolateapp.com/mcp
    enabled: true
    timeout: 60
    supports_parallel_tool_calls: false
```

Restart your normal Hermes session so it discovers the tools. No Percolate API key or sign-in is required.
The service was independently probed with the actual MCP SDK; a Hermes model conversation was not run here.
No local Hermes configuration was edited. The locally found Windows launcher did not produce usable help,
so this guide uses the documented config form rather than assuming that launcher's CLI syntax/version.

Prompt:

```text
Call the Percolate MCP search_coffees tool with exactly
{"category":"espresso","price_max":30,"limit":2}.
Reply in Chinese using only returned records. Include names, prices in USD, source dates,
formats and pods_only. Do not treat capsules as whole beans or invent shopping links.
Do not use web search as a substitute for the tool.
```

Expected: the **original** `search_coffees` tool executes. WorkSwarm's port instead exposes
`coffee_search_coffees`; do not confuse the two names. You may receive a host-generated MCP name prefix.
Real returned names can be used for comparison when a returned ID is not resolved by that service.
On rate limits, respect the returned wait and retry manually only when desired.

Sources:

- https://github.com/bguillow-rgb/timberline-plugins/tree/a9c0c687825e61b567fb1a03cba0992cbf9393bc/percolate
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/mcp-config-reference.md
- https://www.percolateapp.com/mcp
