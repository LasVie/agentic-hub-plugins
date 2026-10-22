# Exa source and capability review

Reviewed 2026-10-22 for CAND-CLD-017 / AH-20261022-exa-deep-research.
Mode: ported. Version: 1.0.0. Contributor identity was not supplied; tracker
ownership remains Unassigned. Package publisher identifies this repository,
not an inferred individual or Exa endorsement.

## Pinned source and rights

Upstream: https://github.com/exa-labs/exa-mcp-server/tree/0b499f095c4ca145eee07b09137641c037d58449

The pinned repository's package.json and plugin.json declare 3.4.2. Its full
root MIT LICENSE names Copyright (c) 2025 Exa Labs. Recursive inspection found
no additional LICENSE/NOTICE in the reused skill directories. The reused
materials are two Markdown skills and eleven search reference Markdown files.
UPSTREAM_FILES.json maps every reused file to its original and adapted SHA-256.

Complete upstream MIT terms, copyright and disclaimer are preserved verbatim in
the runtime payload at licenses/exa-mcp-server/LICENSE, SHA-256
715e1b754d876f214cba57f6ad09bc6e5e48aab46aa3774b00e82a49ab04c742.
THIRD_PARTY_NOTICES.md records the source, author and changes. No original file
copyright header was removed. Native runtime tool code was written for this
integration; it does not copy the upstream TypeScript implementation.

No logos, icons, fonts, screenshots, result text, Node server/dependencies,
comparison-asset code or other third-party datasets are redistributed. The
separately installed MCP SDK and jsonschema retain their own distribution
licenses. Their presence in a test environment is not bundling. This port does
not relicense repository-owned integration code or grant rights to Exa service
access, trademarks, returned web content or premium data.

## Functional overlap and added scope

Four existing Hub archives were checksum-verified and inspected statically;
COMPARISON_EVIDENCE.json preserves observed versions and archive hashes.

| Existing asset | Actual payload | Relationship |
| --- | --- | --- |
| Recursive Research 1643f00a8e524167b14e99da78baae52@2.2.0 | SKILL.md + LICENSE; selects existing Firecrawl, Context7 and host search tools | Retain its general orchestration. This port supplies an executable web-retrieval capability. |
| multi-source-researcher 599d73928abc4a19a8996a95b0506cf7@1.0.0 | SKILL.md + report template | Reuse its comparison and report entry point; supply native Exa tools underneath it. |
| cue-omni-reader 4ec90e5a10e4419a8f97766613b9d57f@1.0.0 | Instruction-only multimodal parser guide, with references to separate Cue operations | General URL retrieval overlaps. Exa adds semantic open-web discovery and structured research; do not replace its file/OCR/video capability. The payload frontmatter says 1.8.0 although the Hub archive is published as 1.0.0; both facts are retained. |
| consensus-research 5aed0d9ff4ba434c864c9361774bfed5@1.0.0 | MCP package with academic search/thread guide and separate Consensus endpoint | Paper/thread research overlaps, while Exa targets public web pages and general entity discovery; do not replace academic filtering/threads. |

Outcome: Partial Overlap - Extend Existing Capability. The new asset is a
companion Plugin containing native executable tools, not a duplicate generic
research planner. No compared payload contains Exa transport or native Exa
tools. The live ledger was rechecked at kickoff for newly delivered Exa assets.

## Adaptations and dependencies

- Four actual openJiuwen Tool classes: search, fetch, filtered search, managed
  research. No forbidden AgentTemplate fields or Claude marketplace manifest.
- Native SKILL.md IDs exa-search and exa-agent, plus source-grounded references.
- Removed fixed Claude Agent/haiku requirements and fictitious requested-result
  source counts; delegation uses actual authorized host capabilities only.
- MCP transport discovers current tool schemas, validates requests, preserves
  isError/structured results, and supplies the required search objective when
  the hosted schema requests it.
- EXA_API_KEY is read only from the host environment; no credential is written
  to the package. Exceptions and results redact the configured key.
- Anonymous lookup uses the default endpoint. A live probe showed that a URL
  enabling agent_run returns 401 during initialization without credentials.
- The live anonymous service reported version 3.5.0, distinct from the pinned
  3.4.2 source. Hosted service behavior is not pinned by the source commit.
- Managed research is gated by a configured key and explicit approval. Calls
  have a 60-second overall deadline and are never automatically retried.
  Long ZDR streaming runs are outside this adapter's supported scope.
- Runtime: Python 3.11+, a compatible native openJiuwen Plugin/Tool host,
  mcp>=1.26.0,<2 and jsonschema>=4.20,<5, with HTTPS access to mcp.exa.ai.
  No additional model account or Node runtime is supplied.

## Release verification

Completed 2026-10-22: repository checks, nine native tool regressions, real
native import/install/uninstall and live search/fetch/filtering from the
extracted release payload. Every runtime path matches artifact.json and both
ZIP formats; all 19 files and license/notice coverage were inspected. Source
Git blob hashes are distinguished from Windows checkout hashes in
UPSTREAM_FILES.json. No comparison package or upstream server code is shipped.

Canonical ZIP: releases/agent-plugin/exa-deep-research/1.0.0/exa-deep-research-1.0.0.zip

SHA-256: f61bc3d94d3fdb48db5e1f41139cd9450c9f5902cfc992ccf730ea32b27cc8ac

Native test ZIP SHA-256: 589ebbf999a42f0c15e9d98afe47b11d1b4747211c82becebca0ea1cf7f7f548

See TEST_REPORT.md and FUNCTIONAL_RESULTS.json for actual commands, environment,
Windows-only repository-test limitations and untested authenticated features.
No user confirmation exists for this new version/hash. The earlier upstream
tryout does not satisfy the current-package testing gate. No push, PR or
external package upload occurred during Build.
