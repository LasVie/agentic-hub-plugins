# Source and distribution review

Reviewed 2026-11-10 for Vannes Wijaya; task AH-20261110-grant-proposal-team; no Plugin Candidate (the team's own design, not a port).

Naming: 基金申请书专家团 (Chinese display name) / Grant Proposal Expert Team (English display name) → `grant-proposal-team` (internal slug).

## Origin

All files are original work written for this task: the five agent personas and manifests, the `grant-proposal` skill, the `grant_proposal_rail.py` rail, the `proposal_checker` tool (criteria coverage with verbatim-quote check, budget arithmetic and caps, length limits, weighted mock-review score, combined review) and the avatar (drawn with PIL). No upstream code, text, data or images were copied.

## Runtime dependencies (not bundled)

| Dependency | License | How used |
| --- | --- | --- |
| openjiuwen (WorkSwarm host SDK) | Host-provided | `Tool` / `ToolCard` and `DeepAgentRail` base classes |
| pydantic | MIT, host-provided | Input validation |

The tool does no network access and writes no files. Literature search uses whatever search tools the host provides.

## Third-party data in outputs

Proposals cite papers found by the host's search at run time; they are not bundled. Funder names and call text come from the user.

## Release check

Extracted the 0.1.1 native ZIP and the wrapped release ZIP: no reused paths, so no notices or licence files are required; no symlinks, credentials, caches or machine-specific paths in the payload.

## Marketplace packaging follow-up

On 2026-11-16 Song Haoran chose the new proposal-cover artwork for the Agentic Hub card. It was generated for this asset with ImageGen and contains no reference artwork or third-party marks. It replaces the original declared avatar at the same path. The marketplace revision adds the required outer directory. The outer metadata and all 22 other payload files match the approved original bytes. The previous ZIP and artwork remain available in the original delivery.
