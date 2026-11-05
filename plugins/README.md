# Plugin Development and Package Guide

Read [AGENTS.md](../AGENTS.md) for the common workflow and [Shared Packaging](../docs/PACKAGING.md) for ZIP layout, locations and tooling. Read this guide when creating or changing a **Plugin**; other asset types have separate guides.

## Identity and layout

Source: `plugins/<slug>/asset.json`, `provenance.json`, `SOURCE_REVIEW.md`, `TEST_REPORT.md` and `plugins/<slug>/<slug>/manifest.json`.

```text
<slug>-<version>.zip
  <slug>/
    plugin.yaml                  # runtime.type: agent-plugin
    <slug>/
      manifest.json              # package_type: plugin
      README.md
      skills/<skill>/SKILL.md     # if declared
      tools/                     # optional; rails/ and mcps/ as needed
```

- `manifest.id = asset.json.name = plugin.yaml.name`; all three versions match. The native `package_type` is `plugin`; the wrapper runtime is `agent-plugin`.
- The root manifest must not contain expert-only `persona`, `agent_card`, `model`, `subagents`, `memories` or `rubrics`. Do not substitute a WorkSwarm Extension, Claude marketplace bundle, Connector or Expert Team manifest.
- Provide at least one real capability through `skills`, `tools`, `rails` or `mcps`. Every declared Skill directory must contain valid `SKILL.md`; every declared Tool/Rail/MCP file must exist. Declared Python classes must actually be implemented and compatible with the target host. Paths are relative to the native payload and must stay inside it.
- When present, manifest tags are localized objects with nonempty `zh` / `en` strings. Preserve compatibility-sensitive schema keys; Chinese display text, usage instructions and default outputs follow AGENTS.md.
- A bundle can include Skills and executable components. A Plugin is not an independent expert persona or a group of member agents. Choose the type from its runtime entry and actual integration, not its marketing name.

## Build and validation

Use `templates/plugin/` as scaffolding only. The repository's `asset_release.py check`, `pack` and `check-repo` support `agent-plugin`; follow the shared packaging procedure. Canonical wrapped releases belong in `releases/agent-plugin/<slug>/<version>/`; native installation ZIPs stay under `plugins/<slug>/test-packages/`.

Structural validation is insufficient even when Hub accepts missing capability files. Install the extracted current package in the target WorkSwarm, verify capability discovery, exercise its actual actions and resulting artifacts, and test meaningful invalid input / error paths. Record which capability expands the host and what was actually executed. Do not simulate a tool call with prose or claim success from a manifest alone. Preserve original license texts/notices in the inner payload when applicable.

The common user-confirmation, current-package screenshot, PR and acceptance rules remain in AGENTS.md. Do not create or advance an Asset Ledger entry from a GitHub merge.

References: [original downloaded Skill/Plugin samples](../docs/FORMAT_RESEARCH.md), [Hub Plugin validator](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/marketplace/plugins_market/validation/types/agent_asset.py).
