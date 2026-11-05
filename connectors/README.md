# Connector Development and Package Guide

Read [AGENTS.md](../AGENTS.md) for Review → Build → Submit, source/license review, Chinese editions, user confirmation, screenshots and tracking. For Build or Submit, also read [Shared Packaging](../docs/PACKAGING.md). Read this guide for a **Connector**, not the Plugin guide unless a Plugin is also being changed.

## Definition, identity and source

A Connector packages access to an external MCP service, a local MCP process, a CLI, or a Skill-based external integration. Configuration alone does not implement the service or prove access works. State the actual operations it adds, supported runtime, required account/permissions, network access and any service costs in its Chinese README and test report.

- Source directory: `connectors/<slug>/`; keep `asset.json`, `provenance.json`, `SOURCE_REVIEW.md`, `TEST_REPORT.md`, tests and evidence outside its same-name native payload `<slug>/`.
- Repository `asset.json.type` and Hub wrapper `runtime.type`: **`agent-mcp`**.
- Native `manifest.json.package_type`: **`mcp`**. `manifest.id = asset.json.name = plugin.yaml.name = payload directory name`; versions match and use `x.y.z`.
- Use the existing live tracker `Component Type` option for Connector; read headers/options as AGENTS.md requires. Do not add new tracker columns, statuses or update timing for this type.

```text
connectors/<slug>/
  asset.json
  provenance.json
  SOURCE_REVIEW.md
  TEST_REPORT.md
  <slug>/
    manifest.json
    README.md
    mcp.json                     # MCP forms; cli.json for CLI
    token-schema.json            # only for token authentication
    icon.png                     # optional; mandatory if declared
    skills/<skill>/SKILL.md       # optional except skill-only
  tests/                         # development tests, outside payload
  test-packages/                 # native host-test ZIPs
  release/<version>/             # wrapped ZIP and artifact record
```

## Integration forms

| `integration.type` | `integration.file` | Actual configuration |
| --- | --- | --- |
| `remote-mcp` | Relative path, normally `mcp.json` | One `mcpServers` entry using the service's supported HTTP(S) transport |
| `stdio-mcp` | Relative path, normally `mcp.json` | One `mcpServers` entry with the real local `command`, `args` and environment |
| `cli` | Relative path ending in `cli.json` | CLI initialization, version checks, authentication when needed and status detection |
| `skill-only` | Omit | At least one declared, real Skill that guides use of the integration |

Hub requires native `version`, `package_type`, `id`, `name`, `description` and `integration.type`. The inspected WorkSwarm loader additionally requires nonempty `display_name.zh/en` and `display_description.zh/en`; include them. All declared paths must exist inside the native payload.

The following is an original schema illustration. `example.com` is not a working service; replace it and implement/test the actual integration before delivery.

```json
{
  "version": "1.0.0",
  "package_type": "mcp",
  "id": "issue-tracker",
  "name": "研发事项连接器",
  "description": "查询研发事项并按用户授权更新指定事项",
  "display_name": {"zh": "研发事项连接器", "en": "Issue Tracker"},
  "display_description": {"zh": "连接研发事项服务", "en": "Connect to an issue-tracking service"},
  "integration": {"type": "remote-mcp", "file": "mcp.json"},
  "credentials": {"type": "token", "file": "token-schema.json"},
  "skills": [{"dir": "skills/issue-tracker-guide", "mode": "all"}]
}
```

Example `mcp.json`:

```json
{
  "mcpServers": {
    "issue-tracker": {
      "url": "https://example.com/mcp",
      "headers": {"Authorization": "Bearer ${ISSUE_TRACKER_TOKEN}"}
    }
  }
}
```

Example `token-schema.json`:

```json
{
  "fields": [
    {"key": "ISSUE_TRACKER_TOKEN", "label": "访问令牌", "type": "password", "required": true}
  ]
}
```

## Host and platform rules

1. A legacy directory containing only `mcp.json` is insufficient: include the Connector manifest. The inspected host requires **exactly one** server in `mcpServers`; Hub may accept several and infer the integration from the first. Use the stricter host contract and verify that the declared integration type matches the actual transport.
2. For token authentication, `credentials.file` points to the token schema. Each `${VAR}` used by MCP/CLI configuration must have a matching schema field under the platform's token-placeholder rules. Do not bundle actual credentials in config, schemas, examples, logs, screenshots or ZIPs; schema entries must not contain `value`, `default` or `defaultValue`. Secret-bearing environment/header fields use placeholders.
3. With no authentication, omit `credentials`; do not invent `type: none`. The inspected current host recognizes `token`, `cli-oauth` and `oauth`. Older deployed hosts may support only `token` / `cli-oauth`; verify the actual target version. OAuth variants do not use `credentials.file`. Hub has a special placeholder exemption for `cli-oauth`; do not assume a remote service's OAuth support establishes compatibility with the host or Hub. Validate the actual configuration on both.
4. For `cli`, `cli.json` requires `init`, `versionCheck.command` and `status` command maps for `darwin`, `linux`, `win32`, nonempty `versionCheck.minVersion`, and `statusMatch` or `statusMatchJson`. Use the platform's structured `auth` steps when applicable. Every declared platform command must be real; document which platforms were actually tested rather than treating a populated map as compatibility evidence.
5. Every `skills[].dir` resolves within the payload and contains valid `SKILL.md`; use `mode: all`. `skill-only` omits `integration.file` and must declare at least one real Skill, even though the Hub validator is more permissive. Declared icons must exist as valid PNGs.
6. A bundled `npx` command can still download software. Record actual runtime versions, network/account requirements and authorized actions. Review the external implementation and bundled materials separately under the common license rules; permission to use an API is not permission to redistribute its client or brand assets.

## Validation and delivery

Follow Shared Packaging's **Connector / Expert Team procedure**. The current repository packer and CI do not validate `agent-mcp`; save the wrapped ZIP and hash record under `connectors/<slug>/release/<version>/`, and native test ZIPs under its `test-packages/`. Validate clean staging with the official CLI and load the extracted native directory with the target WorkSwarm `load_mcp_package` implementation before exercising real behavior. Do not run a random system Python and report that as a host compatibility test.

Record actual install/configuration, connection and capability discovery, a real read operation, any supported write operation with user authorization, and errors for missing/expired credentials, denied access and service unavailability. Check disable/uninstall behavior as applicable. Avoid destructive service tests; use authorized test data. Confirm Chinese usage/help/results and the exact delivery payload and hashes. Logs and mocked responses alone do not prove a live integration works.

Then use the unchanged AGENTS.md gates for user test completion, original screenshots, PR and acceptance. Contributors deliver through GitHub; Hub submission and catalog checks remain the Project Lead's responsibility.

Fixed source references (inspected 2026-11-04, rechecked 2026-11-05): [Hub Connector contract](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/docs/zh/5.%20开发指南/Agent资产.md), [Hub validator](https://github.com/openJiuwen-ai/skillhub/blob/c8ee4ef44be0453470114aa5a19f4e1017462907/marketplace/plugins_market/validation/types/agent_mcp.py), [WorkSwarm Connector loader](https://github.com/openJiuwen-ai/jiuwenswarm/blob/9843516a165bd9a6ad9c37f394fac90be128e551/jiuwenswarm/common/mcp_package_manifest.py).
