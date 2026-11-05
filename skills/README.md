# Skill and SwarmSkill Development and Package Guide

Read [AGENTS.md](../AGENTS.md) for the common workflow and [Shared Packaging](../docs/PACKAGING.md) for ZIP layout, locations and tooling. Read this guide for **Skill / SwarmSkill** changes; a Plugin, Connector or Expert Team uses its own guide.

Source: `skills/<slug>/asset.json`, `provenance.json`, `SOURCE_REVIEW.md`, `TEST_REPORT.md` and `skills/<slug>/<slug>/SKILL.md`.

```text
<slug>-<version>.zip
  <slug>/
    plugin.yaml                  # runtime.type: skill for BOTH types
    <slug>/
      SKILL.md                   # native entry; no manifest.json required
      scripts/                   # optional
      references/                # optional
      assets/                    # optional; required license/source files may be bundled
```

- `SKILL.md` is UTF-8 Markdown with YAML frontmatter. `name` equals its directory name and `asset.json.name`; `description` is nonempty. Use the shared slug and `x.y.z` version rules. A frontmatter version, if present, matches `asset.json.version` and the wrapper version.
- An ordinary Skill has `asset.json.type: skill`. A SwarmSkill has `asset.json.type: swarmskill`, frontmatter `kind: swarm-skill` and at least two distinct `roles[].id` values. Both use wrapper `runtime.type: skill`; do not infer type from “swarm” in the title.
- A SwarmSkill describes cooperative skill methods/roles in its Skill format. It is not an `agent_group` package containing executable member AgentTemplates; use the Expert Team guide only if that actual asset type is being developed.
- Included scripts, references and resources must exist and be usable from the installed payload. Keep development tests/evidence outside it and bundle applicable license/source materials inside it. Do not copy upstream instructions or media without the common source review.

Use `templates/skill/` as scaffolding only. Run `asset_release.py check`, the Skill's actual functional tests and Chinese checks, then `pack` and `check-repo` as described in Shared Packaging. Wrapped releases belong in `releases/skill/<slug>/<version>/` or `releases/swarmskill/<slug>/<version>/`; native test ZIPs belong in `skills/<slug>/test-packages/`.

Test discovery and invocation in the actual target WorkSwarm, included scripts and resource paths, representative Chinese inputs, outputs and failure cases. For SwarmSkill, exercise the declared roles and handoff behavior instead of checking frontmatter alone. Preserve the exact tested package and collect user confirmation and original screenshots under AGENTS.md.

References: [downloaded format samples](../docs/FORMAT_RESEARCH.md), [Hub Skill validator](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/marketplace/plugins_market/validation/types/skill.py).
