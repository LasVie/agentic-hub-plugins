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
