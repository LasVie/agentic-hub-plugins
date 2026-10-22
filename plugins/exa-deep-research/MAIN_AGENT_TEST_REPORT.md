# Main-agent tool visibility follow-up

Date: 2026-10-22 (Asia/Singapore).
Task: AH-20261022-exa-deep-research; candidate: CAND-CLD-017.

User reported that the tools were not visible in JiuwenSwarm single-agent
mode after importing the native test ZIP. The original smoke test resolved
the native package but did not hot-load it onto the main agent. This follow-up
extends that test through the real chat equipment loader and real DeepAgent.

## Result

No runtime defect was reproduced. In an isolated host data directory, the
actual JiuwenSwarm `_load_plugins_for_request` method behaved as follows:

- Installed package with `plugin_names: []`: no Exa tools in the main registry.
- `plugin_names: ["exa-deep-research"]`: all four tools registered in both
  the main DeepAgent and its inner ReActAgent.
- A guarded research request executed through the main agent's actual
  AbilityManager and returned `PAID_ACTION_REQUIRES_APPROVAL`; no research
  run, model request or paid operation was started.
- In direct mode, all four cards had direct exposure. With the SDK's
  progressive policy explicitly enabled, all four were deferred and the real
  JiuwenSwarm ToolRetrievalToolkit returned each one's parameter schema.
- Unmount removed all four tools. Import/install/uninstall also passed.

Read-only inspection of the user's local installation confirmed Exa 1.0.0 is
installed and its tool file SHA-256 matches the tested ZIP. Saved session
equipment selections contained no Exa mount; the recent single-agent sessions
had empty plugin selections. This establishes a missing mount, but does not
establish why it was missing.
The app's existing state was not edited. No conversation content is included
in these records.

The host source currently disables its tool-retrieval feature via
`is_tool_retrieval_enabled`; the forced progressive-policy case above verifies
schema compatibility, not that progressive mode was active in the user's chat.
The UI/model conversation itself has not been driven by this test. The user
reported that no manual plugin selector is available. The frontend's **Use**
action should automatically carry its selection. That browser-to-chat handoff
was not covered by this backend test; see FRONTEND_USE_DIAGNOSIS.md.

## Environment and command

Actual JiuwenSwarm virtual environment: Python 3.12.6, openjiuwen 0.1.19,
jiuwenswarm 0.2.4b4, mcp 1.29.0, jsonschema 4.26.0. Actual source loader
SHA-256: cf7f3ab694574ed771cba8b78899631bebd050814ed9b909acfee5ae246c4fc4.
No fake Tool classes, host loader or AbilityManager were used. A real agent
was created with SkillUseRail, matching the host's skill-capable setup.

```powershell
D:\jiuwen_repos\jiuwenswarm\.venv\Scripts\python.exe -B tests/exa_plugin_smoke.py --sdk-root D:\jiuwen_repos\agent-core-latest --host-root D:\jiuwen_repos\jiuwenswarm --payload .research/extracted-exa --archive .research/test-packages/exa-deep-research-1.0.0-workswarm.zip --output .research/exa-main-agent-venv.json
```

Exit 0. Bounded output is preserved in MAIN_AGENT_RESULTS.json. This follow-up
does not repeat the earlier live network cases or establish user test completion.
The package payload and both ZIP hashes remain unchanged:

- Native: 589ebbf999a42f0c15e9d98afe47b11d1b4747211c82becebca0ea1cf7f7f548
- Canonical: f61bc3d94d3fdb48db5e1f41139cd9450c9f5902cfc992ccf730ea32b27cc8ac
