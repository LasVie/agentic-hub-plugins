# Shared Packaging Contract

Read [AGENTS.md](../AGENTS.md) and the matching type guide before Build or Submit. This file covers package layout and checks only. The shared tracker workflow, delivery gates and Project Lead's Hub responsibilities remain in AGENTS.md.

## Repository locations and tool coverage

| Type | Editable source and development records | ZIPs and artifact records | Supported by `tools/asset_release.py` |
| --- | --- | --- | --- |
| Skill / SwarmSkill | `skills/<slug>/` | Canonical wrapped ZIP: `releases/<type>/<slug>/<version>/` | Yes: `skill`, `swarmskill` |
| Plugin | `plugins/<slug>/` | Canonical wrapped ZIP: `releases/agent-plugin/<slug>/<version>/` | Yes: `agent-plugin` |
| Connector | `connectors/<slug>/` | `connectors/<slug>/release/<version>/` | No; use the separate procedure below |
| Expert Team | `expert-teams/<slug>/` | `expert-teams/<slug>/release/<version>/` | No; use the separate procedure below |

Each source directory contains `asset.json`, `provenance.json`, `SOURCE_REVIEW.md`, `TEST_REPORT.md` and a same-name native payload directory `<slug>/`. Keep source/license findings and actual functional-test results under that asset. For new Connector/Expert Team records, use the same metadata vocabulary as existing assets, with `asset.json.type` set to `agent-mcp` / `agent-group`; a descriptive metadata file alone is not tool support. Stable pre-catalog identity remains `repo:<type>:<slug>`.

Native host-installation ZIPs belong in the owning asset's `test-packages/`; retain older, non-current ZIPs byte for byte in `test-packages/history/` and label their actual versions. Editable test inputs belong in the owning asset's `tests/fixtures/`, outside the runtime payload. Cross-asset delivery notes belong in `docs/deliveries/<batch>/` and link to asset-owned files. Do not put ZIPs, runtime test inputs or a global `test-packages/` directory at repository root. Research downloads under `docs/research/` are not team deliverables.

The already-approved `pc-build-team` 0.2.1 native ZIP and its existing `artifact.json` stay together under `expert-teams/pc-build-team/release/0.2.1/`. Its former `teams/` source path has moved; the tested bytes, hashes and historical PR evidence are unchanged. Do not rewrap or silently replace a confirmed historical ZIP to satisfy a new directory convention.

## Native payload versus marketplace wrapper

A native ZIP has the native entry (`SKILL.md` or `manifest.json`) at its archive root. Extract it into a directory named `<slug>` before host loading, especially for Expert Teams whose loader checks the directory name. A marketplace ZIP adds an outer metadata layer:

```text
<outer>/
  plugin.yaml
  icon.png                     # optional, valid PNG
  <slug>/                      # exactly plugin.yaml.name
    SKILL.md or manifest.json
    ...actual runtime files
```

- There is exactly one outer `plugin.yaml`. Its outer directory contains only that file, optional `icon.png`, and one nonempty inner payload directory. Keep `asset.json`, source reviews, test reports, evidence, task data and development caches outside the wrapper. Put required distributable source, license texts and notices inside the inner payload.
- Repository slugs start with a lowercase letter, contain lowercase letters/digits separated by single hyphens, and are at most 64 characters. Repository versions use `x.y.z`. Keep metadata, wrapper, native identity and all applicable versions consistent. Do not silently overwrite a delivered version.
- `plugin.yaml.name` equals the inner directory and `asset.json.name`. The type guide specifies the native identity field and `runtime.type`; these values are not interchangeable across asset types.
- All declared files/directories must exist, resolve inside the appropriate payload/member, and have the declared content. Reject absolute paths, `..` traversal, symlinks, duplicate/aliased archive paths, caches and compiled Python cache files. A filename or a manifest declaration is not evidence of an actual capability.
- For both native and wrapped delivery forms, compare every inner payload path and SHA-256 against the reviewed source and each other. Confirm the exact final Chinese archive(s), version and hashes during user testing. Changing wrapper bytes, localized names or payload after confirmation invokes AGENTS.md's rebuild/retest rule.
- Record local paths, ZIP SHA-256 and a per-file payload SHA-256 map in `artifact.json`; include actual source-review/test-report hashes. Native and wrapped artifacts must be clearly distinguished with their actual filenames/hashes. Never claim tool validation or functional success that did not occur.

An original wrapper illustration, not a completed asset:

```yaml
name: issue-tracker
version: 1.0.0
display_name: 研发事项连接器
description: 查询并按用户授权更新研发事项
runtime:
  type: agent-mcp
metadata:
  author: REPLACE_WITH_ACTUAL_AUTHOR
  tags: [研发协作]
```

Replace the author and all illustrative values with reviewed, real metadata. Use the exact type from the matching guide. Optional outer icons must be real PNG files; declared native icons must also exist at their declared native paths.

## Skill / SwarmSkill / Plugin procedure

Copy suitable scaffolding from `templates/` into the owning type directory and replace its metadata, authorship, sources and placeholder implementation. Templates are not completed assets.

```bash
python tools/asset_release.py check <asset-directory>
# Run the asset's actual functional tests and Chinese-language checks.
python tools/asset_release.py pack <asset-directory>
python tools/asset_release.py check-repo
```

The packer writes the deterministic wrapped ZIP and `artifact.json` under `releases/<type>/<slug>/<version>/`. It uses uncompressed ZIP members to avoid compression-ratio false positives. Run the asset's own tests, including failure cases, and record the real environment, commands, results and runtime requirements. Packaging-tool tests do not replace functional tests.

## Connector / Expert Team procedure

`asset_release.py check`, `pack`, `inspect` and `check-repo` do not validate these types. `check-repo` currently scans only `skills/`, `plugins/` and supported `releases/` archives. Its passing result or the existing CI is therefore not a Connector/Expert Team sign-off. Keep their releases in the asset-owned paths above until the repository tool explicitly supports them; do not place an unsupported archive under `releases/` or relabel it as a Plugin.

1. Complete the native payload and the matching type guide's host/runtime checks. Keep all development and evidence files outside that payload.
2. Use a separate clean staging directory containing the wrapper and an exact copy of the native payload. The official Agentic Hub CLI supports these types:

   ```text
   agentichub init <slug> --type agent-mcp
   agentichub init <slug> --type agent-group
   agentichub validate <staging-directory>
   agentichub pack <staging-directory>
   ```

   Choose **one** init command for the actual type and consult the installed CLI's help for its path/output options. `init` creates placeholders, not a finished implementation. The current Agent scaffold includes a development README at staging root; the CLI omits that README from the wrapper ZIP. Keep the user README in the inner payload and inspect the actual ZIP layout. Do not pack the repository asset directory containing reviews/tests as if it were clean staging.
3. Extract and inspect the CLI output; check identity, version, allowed outer entries, path safety, size limits and the full payload hash map. Record the installed CLI version and exact commands. The official CLI currently compresses members; do not describe its output as the repository packer's deterministic/uncompressed output. If compression violates the platform ratio limit, rebuild with an appropriate ZIP method before the current-package tests and confirmation.
4. Save the exact wrapped ZIP, any separately delivered native test ZIP and their artifact records at the locations above. Run the matching guide's actual host and business tests against extracted delivery contents; preserve exact tested bytes. The grandfathered native Expert Team ZIP described above remains valid under its recorded approval.

Do not run third-party downloaded research packages as part of packaging research or submit them as team work. Source reuse still needs the common license review.

## Size limits and authoritative references

The repository limits each ZIP to **95 MiB** for GitHub delivery; the Project Lead decides how larger assets are delivered. The inspected Hub limits are **512 MiB** ZIP / cumulative extracted size, **1,000 entries**, compression ratio **50**, and an optional valid PNG icon of at most **5 MiB**. Check both the actual deployed platform and the target host; neither this document nor local validation reproduces every platform security rule.

Format baseline inspected on 2026-11-04 and rechecked for this guide on 2026-11-05:

- [Hub asset types and field contracts](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/docs/zh/5.%20开发指南/Agent资产.md), [wrapper layout validator](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/marketplace/plugins_market/validation/types/wrapped_asset.py), [limits](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/marketplace/plugins_market/validation/constants.py).
- [Official CLI scaffold, validation and pack implementation](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/cli/cli_core/plugin.py).
- [Earlier Skill/Plugin format research](FORMAT_RESEARCH.md); per-type guides link the actual WorkSwarm/SDK loaders.

Platform acceptance, actual host loading and functional acceptance are three separate checks. Upload acceptance does not establish runtime correctness, license permission, Project Lead acceptance or public catalog availability. When formats change, update the affected guide and any implemented templates/tools/contracts together; never claim unsupported types are covered by old checks.
