# Smart admission rejected its own plugin mount

Date: 2026-10-22 (Asia/Singapore). Task AH-20261022-exa-deep-research.

## Confirmed cause and local fix

The user supplied the exact error `equipment change rejected at non-fresh
turn: plugin set changed`. JiuwenSwarm Smart permission admission increments
the session's active-request count before calling the equipment gate. That
gate previously treated any positive count as a peer execution, so the first
plugin mount could reject its own request. This happens before plugin loading
and is independent of Exa's network service.

The local host change is in
`D:/jiuwen_repos/jiuwenswarm/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py`.
It tracks the admission reservation by adapter, task, session and nesting
depth. The equipment gate ignores only that request's own reservation. Peer
activity, peer tasks, inherited contexts in another task, attached goals and
actual running agent execution retain their existing checks. The context is
reset on normal exit, exceptions and cancellation. Permission policy itself
is unchanged.

The host change and regression file remain local and uncommitted in the
JiuwenSwarm checkout. Existing staged pyproject.toml and modified uv.lock
were not included or changed by this fix. No service restart was performed.

## Validation

- Before the fix: one regression failed with the user's exact error while
  four genuine-conflict cases passed.
- After the fix: 68 targeted host tests passed, including seven new cases.
  They cover first mount, nested admission cleanup on exception/cancellation,
  peer activity/task rejection, attached goals and child-task ownership.
- The other test modules cover existing equipment mount/unmount behavior,
  permission facade admission and lifecycle cleanup edges.
- The real native Exa ZIP also passed actual import/install, Smart admission,
  fresh-turn gate, main/inner ReAct registration of four tools, guarded main
  registry dispatch, deferred schema discovery, unload and uninstall. It used
  actual host/SDK classes; policy activation was isolated from account setup.
- No LLM, paid research operation or new live Exa request was made in this
  follow-up. The user's browser conversation has not been rerun.

Host tests used Python 3.12.6 and pytest with `--asyncio-mode=auto`, disabled
pytest cache and no coverage reports. The four modules were:

```text
tests/unit_tests/server/extensions/test_equipment_permission_admission.py
tests/unit_tests/server/extensions/test_chat_send_extension_mount.py
tests/unit_tests/agentserver/permissions/test_permission_facade_admission.py
tests/unit_tests/agentserver/permissions/test_permission_admission_edges.py
```

Logs and host data were isolated under the repository's ignored `.research/`.
A temporary pytest fixture redirected projectless Documents allocations to
each test's temp directory. An initial broader run hit 12 sandbox path errors;
the final isolated run completed with 68 passes and no skips. A preceding
invocation omitted asyncio auto mode; it was corrected before the final run.

`tests/exa_plugin_smoke.py` now exercises the actual Smart admission and full
equipment gate before loading the real native ZIP, covering the path absent
from the original smoke test. SMART_ADMISSION_RESULTS.json preserves its
bounded output and the host source hash.

## Retry

Restart the JiuwenSwarm backend, including its resident runtime, to load the
local Python change. Then click **Use** on Exa and send a normal search request
in the conversation it opens. The plugin ZIP remains version 1.0.0 with native
SHA-256 `589ebbf999a42f0c15e9d98afe47b11d1b4747211c82becebca0ea1cf7f7f548`.
No reinstall or repack was required. Current-package user completion remains
pending; the separate IPC failures are not covered by this fix.
