# Expert Team Development and Package Guide

Read [AGENTS.md](../AGENTS.md) for the common workflow, source/license review, Chinese editions, evidence, acceptance and tracking. For Build or Submit, also read [Shared Packaging](../docs/PACKAGING.md). Read this guide when creating or changing an **Expert Team**. Read another guide only for a concrete component being changed or integrated.

## Definition and repository location

An Expert Team is a complete **AgentGroup** package: a Leader, complementary member AgentTemplates, their real capabilities, and rules for cooperation and final deliverables. It is not a list of role prompts or a SwarmSkill renamed as a team. Define what users can accomplish, what each member contributes, how work is handed off and independently checked, and which concrete outputs demonstrate the added value.

- Source: `expert-teams/<slug>/asset.json`, `provenance.json`, `SOURCE_REVIEW.md`, `TEST_REPORT.md` and the native directory `expert-teams/<slug>/<slug>/`.
- Repository `asset.json.type` / Hub wrapper `runtime.type`: **`agent-group`**. Native root `package_type`: **`agent_group`**.
- `manifest.name = asset.json.name = plugin.yaml.name = native directory name`. Group versions use `x.y.z` and match metadata/wrapper. Tracker Component Type stays **`Expert Team`** under the existing live options.
- Keep optional development `src/`, `tests/` and `evidence/<version>/` outside the native payload. Wrapped delivery ZIPs and artifact records belong in `expert-teams/<slug>/release/<version>/`; native test ZIPs belong in its `test-packages/`.
- The previously approved `teams/pc-build-team/` source has moved here without payload or ZIP changes. Its 0.2.1 native release remains at `expert-teams/pc-build-team/release/0.2.1/`, using its recorded hash and approval. Do not create a second asset/task or replace that package because of this move.

## Package composition

```text
<slug>/                         # native payload, not development parent
  manifest.json
  README.md
  agents/
    leader/
      manifest.json
      AGENT.md
      persona/leader.md
    researcher/
      manifest.json
      persona/researcher.md
      skills/source-research/SKILL.md
    reviewer/
      manifest.json
      persona/reviewer.md
      tools/                    # optional, real declared implementation
      rails/                    # optional, real declared implementation
  skills/
    evidence-check/SKILL.md      # optional, shared with EVERY member
```

Each member package must be complete. Persona defines scope and judgment; Skill provides reusable knowledge/workflows; Tool implements a discrete operation the host cannot already perform; Rail supplies actual lifecycle interception or dynamic behavior. Include only components that serve the task, not empty files to make a directory look complete. Existing host tools may be used without inventing another tool wrapper.

## Group and member manifests

The following original examples illustrate the schema, not finished personas or tested capabilities.

Root `manifest.json`:

```json
{
  "name": "research-team",
  "version": "1.0.0",
  "package_type": "agent_group",
  "description": "完成资料研究、独立复核与综合交付",
  "display_name": {"zh": "研究复核专家团", "en": "Research and Review Team"},
  "display_description": {"zh": "资料研究与证据复核", "en": "Research with evidence review"},
  "instruction": "leader 明确目标并分派任务；researcher 返回结论和来源；reviewer 检查证据、矛盾与遗漏；leader 消解分歧后交付结果。所有成员默认使用中文。",
  "agents": ["leader", "researcher", "reviewer"],
  "skills": ["evidence-check"]
}
```

`agents/researcher/manifest.json`:

```json
{
  "package_type": "agent_template",
  "name": "researcher",
  "description": "负责资料检索、来源核验与研究结论",
  "display_name": {"zh": "资料研究专家", "en": "Researcher"},
  "display_description": {"zh": "检索资料并核验来源", "en": "Find information and verify sources"},
  "persona": {"dir": "persona"},
  "skills": [{"dir": "skills/source-research", "mode": "all"}]
}
```

## Runtime requirements and capability ownership

1. `agents` is a nonempty, unique string list including **`leader`**. Each role ID starts with lowercase `a-z` and then contains lowercase letters, digits, `_` or `-`. These are routing identities and directory names, not paths, objects, Chinese display names or references to separately installed experts. For useful collaboration, design a Leader plus complementary members; the loader merely accepting a Leader-only roster is not evidence of team value.
2. Each `agents/<role>/manifest.json` has `package_type: agent_template`. For newly authored members, `name` matches the role directory; put Chinese names in `display_name.zh`. Supply meaningful descriptions and nonempty `zh/en` display fields. Every member declares a real `persona.dir` relative to **that member**, containing Markdown inside the member package. A compatible existing `persona.dir: "."` is allowed; new packages should normally use `persona/` to control what is loaded.
3. Leader must include `agents/leader/AGENT.md`. It defines clarification, decomposition, assignments with context and acceptance criteria, results review, conflict resolution and final delivery. When necessary, questions to the user must appear in visible output. Normal members must **not** include `AGENT.md`; put their responsibilities in persona. The loader mounts Leader's AGENT.md even when its persona directory is narrower than `.`. Leader cannot use an external runtime.
4. Root `instruction` is a string merged into **all members'** prompts (the current SDK reserves section `agent_group_instruction`, priority 20). Do not impose Leader-only operations on every member or define a conflicting section of that name. There is no fixed root DAG field implied by the group schema; describe real cooperation and verify actual runtime behavior.
5. Root shared Skills use directory-name strings, for example `skills: ["evidence-check"]` → `skills/evidence-check/SKILL.md`. The loader also supports dir mappings, but new packages should follow the official creator's string-list convention. Valid Skill directories under root `skills/` are also auto-discovered; they are shared with **every member**, including Leader. An unlisted root Skill is not private.
6. Member-only Skills live at `agents/<role>/skills/<skill>/SKILL.md` and are declared only in that member as `{"dir": "skills/<skill>", "mode": "all"}`. Paths are relative to the member, not the team root. Do not use `../../skills`, absolute development paths or a team-root `agents/<role>/...` path in a member declaration. Omit unused skills rather than creating empty directories.
7. Tool/Rail declarations belong in the relevant member manifest and must point to real files/classes within that member package. Root `tools/` or `rails/` files do not automatically attach to every member. A prompt mentioning a tool is not tool availability: verify the member's assembled capabilities in the actual host.
8. Members ship inside this group; they do not need separate Hub publication, registration, independent versions or independent expert installation directories. Optional `member_templates` records a real provenance mapping only when templates are reused; it does not replace the member files. Retain applicable source/license notices for every reused component.
9. Follow the official group creator's standard route: do not add independent `agent_card`, `model`, `mcps` or `subagents` configuration by default. If reusing a supported advanced template, review and test its actual target-host assembly and access; do not assume a connector mentioned in a persona is mounted, or expand the user's permissions silently.
10. README explains purpose, member responsibilities, supported inputs, actual outputs, limitations and Chinese usage examples. Every Skill has valid UTF-8 YAML frontmatter, a `name` matching its directory and a nonempty description. No unresolved scaffold placeholders, symlinks, machine-specific paths, credentials or development caches belong in delivery.

## Validation: platform, loader, behavior

Follow Shared Packaging's separate Connector / Expert Team procedure. The current repository `asset_release.py` and CI do **not** validate `agent-group`. The official Hub validator checks root type/identity/version and deliberately permits some incomplete groups; its `init --type agent-group` scaffold lists members but does not generate their packages. CLI `validate` / `pack` success alone is not runnable-team evidence.

Before user testing:

1. Validate the clean wrapper using the official CLI and inspect the exact ZIP and full payload hashes. Load the extracted native payload through the target WorkSwarm/SDK **`load_agent_group_package_bundle`** contract. The official `agent-group-creator/scripts/register_group.py <absolute-native-payload-path> --validate-only`, run using the actual host runtime, additionally checks README, unresolved content placeholders, Skill frontmatter and symlinks. Locate that script in the target installation; do not assume a frozen WorkSwarm executable supports `-c` or substitute an unrelated Python environment. `--validate-only` avoids registration; actual installation is a separate test step.
2. Install/start the group in the actual target WorkSwarm and verify Leader plus complementary members genuinely participate, receive the intended shared/member-only capabilities, exchange usable work and perform independent review. Exercise the real tools and generated artifacts, not only role text or import success.
3. Test the agreed end-to-end deliverable with Chinese input/default outputs, missing inputs, disagreements and relevant tool/service failures. Record real member participation, handoffs, checks, output paths/results, host version and limitations in `TEST_REPORT.md`; preserve usable current-package screenshots.
4. Give the user the exact Chinese package, version/hashes, installation and test steps; collect explicit test-completion confirmation and original screenshots under AGENTS.md before push/PR. All common license, PR, acceptance, cancellation and tracker rules continue unchanged. A new group wrapping already-covered functionality still needs the normal functional deduplication review.

Fixed source references (inspected 2026-11-04, rechecked 2026-11-05): [Hub group fields/validator](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/marketplace/plugins_market/validation/types/agent_asset.py), [official group package and member specification](https://github.com/openJiuwen-ai/jiuwenswarm/blob/9843516a165bd9a6ad9c37f394fac90be128e551/jiuwenswarm/resources/agent/workspace/skills/agent-group-creator/references/package-spec.md), [host creator validation script](https://github.com/openJiuwen-ai/jiuwenswarm/blob/9843516a165bd9a6ad9c37f394fac90be128e551/jiuwenswarm/resources/agent/workspace/skills/agent-group-creator/scripts/register_group.py), [AgentGroup loader](https://github.com/openJiuwen-ai/agent-core/blob/5a35c39f0163a4e6190800df53ad7e24848756eb/openjiuwen/agent_teams/experts/agent_group.py).
