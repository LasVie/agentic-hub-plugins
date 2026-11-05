# Source and distribution review

Reviewed 2026-11-04 for Vannes Wijaya; task AH-20261104-pc-build-team; no Plugin Candidate (the team's own design, not a port).

Naming: 装机专家团 (Chinese display name) / PC Build Expert Team (English display name) → `pc-build-team` (internal slug).

## Origin

All files are original work written for this task: the four agent personas and manifests, the `pc-build` skill, the `pc_build_rail.py` rail, the `build_checker` tool (rule checks, SVG charts, board-map diagram, Markdown → HTML → PDF export) and the avatar. No upstream code, text, data or images were copied.

## Runtime dependencies (not bundled)

| Dependency | License | How used |
| --- | --- | --- |
| openjiuwen (WorkSwarm host SDK) | Host-provided | `Tool` / `ToolCard` base classes |
| pydantic | MIT, host-provided | Input validation |
| markdown-it-py | MIT | Renders the team's Markdown report (raw HTML disabled) |
| Google Chrome (headless) or LibreOffice | Installed on the user's machine | Prints the HTML report to PDF |

## Third-party data in outputs

Reports quote retailer prices, product names and links fetched at run time. They are cited with the source URL and check date and are not bundled in the package. Brand and product names are used descriptively only.
