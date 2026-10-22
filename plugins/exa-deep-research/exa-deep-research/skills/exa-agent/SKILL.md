---
name: exa-agent
description: Use authenticated Exa Agent for explicitly approved managed research, structured discovery, list building and continuation with evidence and coverage checks.
---

# Managed Exa Research

Adapted from Exa's MIT-licensed exa-agent skill. This complements the existing
research workflow with actual service execution. Ordinary search/fetch uses
the exa-search skill and does not need this metered operation.

## Before calling

- The host process must have EXA_API_KEY configured locally. Never ask for a
  key in chat or write it into the plugin, a report, screenshot or source control.
- Obtain the user's explicit authorization for the metered task and its scope.
  Set `allow_paid=true` only when that authorization covers this call. Do not
  repeatedly ask when the same authorization already covers continuation.
- Define objective, qualifying universe, segments/dates, output fields, evidence,
  exclusions and target count. Start with the tool's low effort default.
- Use a top-level object outputSchema with bounded arrays and source URL fields.
  Premium partner data and higher effort require corresponding user scope.

## Native call shape

Call `exa_research` with the upstream request nested inside `arguments`:

```json
{
  "allow_paid": true,
  "arguments": {
    "query": "Find three official sources about the MCP transport specification and cite URLs.",
    "effort": "low",
    "outputSchema": {
      "type": "object",
      "properties": {
        "sources": {
          "type": "array", "maxItems": 3,
          "items": {
            "type": "object",
            "properties": {"title":{"type":"string"},"url":{"type":"string"}},
            "required": ["title","url"]
          }
        }
      },
      "required": ["sources"]
    }
  }
}
```

The wrapper discovers and validates the actual remote schema before execution.
If the service changes its schema, correct the request from the returned schema.

## Run state and output

1. Provide exactly one of query (new run) or runId (resume/status).
2. Preserve the returned run ID and status. A running response is not completion.
   Respect any suggested wait; use the existing runId rather than creating a
   duplicate run. The native call has a 60-second overall deadline.
3. A timeout is ambiguous. Check the Exa dashboard or a known runId before any
   retry. If no ID was returned, do not assume the run never started.
4. On completion inspect both structured output and grounding/citations. Check
   requested count, segment coverage, duplicates and evidence quality.
5. Use previousRunId only for refinement of a completed retained run. Do not use
   it for unrelated work or failed/running runs. Zero Data Retention accounts
   may not support resumption; the current 60-second wrapper is unsuitable for
   long ZDR streaming runs. Use Exa's official client for those cases.
6. Report best-effort discovery and known gaps unless exhaustive coverage was
   defined and checked. Preserve factual uncertainty and source attribution.

No authenticated/billable run is part of this package's anonymous smoke test.
