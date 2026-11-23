# Asana 1.1.0 local Build verification

Functional tests performed 2026-11-19; current unit tests rechecked and report synchronized 2026-11-20 (Asia/Shanghai). Owner: Song Haoran. Original Task: AH-20261117-asana-connector; Candidate: CAND-CLD-323; stable ID: repo:agent-mcp:asana. Chinese display name: Asana 任务连接器.

This independently authored standard stdio MCP adapter retains the original Asana REST/PAT scope. It is not Asana's official hosted MCP and does not require a new MCP OAuth app. Runtime payload uses WorkSwarm's Node and built-in modules, with no Python, pip or npm dependency. These checks do not establish Agentic Hub acceptance of this packaging approach.

## Exact artifacts and packaging

- Native: test-packages/asana-1.1.0-native.zip, 12,584 bytes, SHA-256 `4110e37f8a3ace88263ecffad7ad00d485e4ea5b7b57f58b62f9b4105b2a7d1d`.
- Hub wrapper: release/1.1.0/asana-1.1.0-agent-mcp.zip, 7,072 bytes, SHA-256 `57348470aea2ccc0ea85d733de007e059a636ad10c9f57d67f17fc6ae61d45e6`.
- Official Agentic Hub CLI 0.0.1 clean init/validate/pack, safe ZIP member/size/CRC checks, source/native/wrapper payload identity and all three packaging preflights passed. Details remain in release/1.1.0/artifact.json.
- Actual frozen WorkSwarm 0.2.8 load_mcp_package accepted this exact native ZIP as stdio-mcp with token credentials and one Chinese skill. This loader check is distinct from a GUI ZIP import or market installation.

## Tests and real provider behavior

Four meaningful Node tests cover rejection of unknown/update/path-injection arguments; the exact create payload without assignee/update; missing credentials and sanitized Chinese 401/403/429/503 errors; and no automatic retry after an uncertain write. The current hardened source is rechecked in test-evidence/20261119-standard-1.1.0/unit-tests-current.txt.

Using the actual frozen WorkSwarm executable, stock MCP client and normal credential resolver in the existing authorized QA profile, the exact native package discovered only asana_status, asana_list_tasks, asana_read_task and asana_create_task. Authentication status and an existing QA task read succeeded. A uniquely named Chinese task, `WorkSwarm标准MCP中文验收20261119`, was created once in QA project `1220594404826613`, then independently read back to verify its name and project. Created task: `1220699978994343`; URL: https://app.asana.com/1/1220595506484888/project/1220594404826613/task/1220699978994343 . The client disconnected afterward. No token file was manually read or copied. Machine-readable evidence: test-evidence/20261119-standard-1.1.0/asana-standard-host-test.json.

## Native GUI result and unresolved limits

The currently open native WorkSwarm accepted the exact MCP command/arguments as a custom entry and displayed four tools. Its gpt-6.1-sol Chinese prompt then failed on the first task read with a Chinese 401 authentication error. The agent stopped; no GUI task creation or write was performed. Original connection/error JPEG screenshots and AX text are retained unchanged in test-evidence/20261119-standard-1.1.0/.

This GUI failure does not prove that the authorized QA PAT expired: the separate stock-host QA test succeeded. The native instance's credential/profile resolution remains unresolved. The custom entry was disconnected. Additional loader-verified local installation attempts did not establish a successful GUI native-package import and are not counted as such. Owned temporary QA processes were stopped; other connectors and credentials were left intact.

Fresh-user credential entry, native GUI task read/create/readback, actual GUI ZIP import/market installation and current exact-package user test-completion confirmation remain pending. Unit error simulations do not substitute for real service-outage or expired-auth tests. Original 1.0.0 evidence is historical only. Status remains Local Build / Integration Testing / Pending Acceptance; no delivery PR, Hub upload or publication is claimed.
