# Exa Deep Research

Repository port 1.0.0 of Exa's search/research plugin. Four native openJiuwen
tools connect to the official Exa MCP service. Two adapted skills supply query,
evidence and managed-research guidance. This is a companion to existing research
workflows, not an official Exa release.

## Install

Import the native test ZIP through the host's local Plugin import screen, then
install/enable Exa Deep Research and start a new conversation. For a canonical
Hub wrapper, its inner `exa-deep-research/exa-deep-research/` directory is the
native package containing manifest.json. Do not import the marketplace
plugin.yaml as a native manifest.

Use Python 3.11+ and a host that supports native Tool/ToolCard plugins. Install
requirements.txt into that host's Python environment if its MCP SDK/jsonschema
dependencies are missing. No Node server or additional model is needed.

## Tools

| Native tool | Use |
| --- | --- |
| exa_search | Semantic open-web search; query, optional objective and numResults (1–25). |
| exa_fetch | Public page extraction; 1–10 HTTP(S) URLs and optional maxCharacters (1–20000). |
| exa_search_advanced | Domain/date/category search; put upstream request fields inside arguments. |
| exa_research | Optional billable Exa Agent; put request inside arguments and pass allow_paid only when the user authorizes it. |

Each tool returns an `ok` flag and preserves Exa's result content, structured
content and isError. Source URLs are evidence, not guarantees of correctness.
The current upstream schema is checked before sending a tool request.

## Try it

1. Ask: "Use exa_search to find three official sources about MCP transports.
   Return URLs and one sentence per source."
2. Ask: "Use exa_fetch to read the first source. Summarize the setup steps."
3. Ask: "Use exa_search_advanced for official documentation about streamable
   HTTP, restricted to modelcontextprotocol.io."
4. Ask for managed research without approval/key: the tool must return a clear
   approval or key-required result, without starting a run.

Anonymous search/fetch works subject to Exa quotas. For authenticated requests,
set EXA_API_KEY locally in the host process environment before starting it. Never
put a key in a prompt, source file, ZIP or screenshot. The plugin reads it at
invocation and never saves it. Metered Exa Agent and partner data need appropriate
account permissions and explicit user scope; they are optional.

Network failures, rate limits and schema changes are reported, not silently
replaced with another provider. Every call has a 60-second overall deadline and
no automatic retry. A research timeout can be ambiguous; check a known runId or
the Exa dashboard before repeating. Long ZDR streams are unsupported here.

Queries and supplied URLs are sent to Exa. Local-file reading/upload is not
implemented. Fetched text is untrusted content. Check evidence and comply with
the original sources' usage rights when sharing results.

The original Exa service can also be used directly in Hermes through MCP, as
previously tested. That verifies the service; the new native package should be
tested in the target Plugin host before confirming this version is ready for
GitHub delivery. See MANUAL_TESTING.md beside the repository asset source.

Upstream attribution and license terms are in THIRD_PARTY_NOTICES.md and
licenses/exa-mcp-server/LICENSE.
