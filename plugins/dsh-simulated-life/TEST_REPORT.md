# Test report: dsh-simulated-life 1.0.0

Task: AH-20261022-dsh-simulated-life. Candidate: CAND-DSH-047. Owner: Song Haoran.
Naming: `dsh-simulated-life` -> **本地模拟生活** -> `dsh-simulated-life`.
Date: 2026-10-22 (Asia/Singapore). Stage: Submit authorized; current-package user confirmation is recorded below. PR/evidence links are tracked in delivery.json.

## Environment and installed package

macOS WorkSwarm 0.2.7, configured Deepseek V4 Flash, actual native gateway at127.0.0.1:19000. Host-bundled Node22.11.0. Local Python3.12.14 regression runtime; real openJiuwen SDK smoke used the existing workspace virtualenv with the separate local agent-core source on PYTHONPATH. These SDK callback checks are distinct from the actual installed app/model calls.

Native test ZIP: `dist/dsh-simulated-life/1.0.0/dsh-simulated-life-1.0.0-workswarm.zip`.
Native SHA-256: `d4f8679550432e7a72f9f5f08d13d92f50a5822ad7bb4339048730e00b64d774`. Size: 21670 bytes.
Installed path: `~/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/dsh-simulated-life`.
All source payload file bytes matched the actual installed payload. Native and marketplace wrapper payloads must match, verified in the handoff manifest. The actual host session was `web_1a16309f1ae_e7859305a921`.

## Functional evidence

Actual Deepseek V4 Flash turn invoked native seed_demo, context twice, react and context in one WorkSwarm session. Two active events and one expired breakfast event were correctly separated. The second read returned no new notice; reaction writeback preserved other fields and the final read returned updated_count=1. The agent used read-only shell searches to locate the Skill, not to implement event operations. Regression tests verify exact24-hour/future-skew boundaries, session isolation, forced refresh, corrupt/missing data, symlink refusal and no demo overwrite. A real SDK SystemPromptBuilder callback test verified LifeRail section insertion, stable replacement and cleanup. Automatic Rail injection in a project-bound WorkSwarm GUI conversation was not exercised; the actual GUI/model flow above uses explicit context calls against the chosen fixture directory.

Commands executed (development build tools are not runtime dependencies):

```text
node tools/build_song_plugins.mjs /absolute/path/to/esbuild@0.25.12/lib/main.js
python tools/song_native_test_packages.py
python -m unittest discover -s tests -p test_song_local_plugins.py -v
SONG_PAYLOAD_ROOT=/absolute/path/to/dist/extracted python -m unittest discover -s tests -p test_song_local_plugins.py -v
PYTHONPATH=/local/agent-core python tests/song_local_host_smoke.py
SONG_PAYLOAD_ROOT=/absolute/path/to/dist/extracted PYTHONPATH=/local/agent-core python tests/song_local_host_smoke.py
python -m unittest discover -s tests -v
python tools/asset_release.py check plugins/dsh-simulated-life
python tools/asset_release.py pack plugins/dsh-simulated-life
python tools/asset_release.py check-repo
python tests/run_mcp_server_dev_integration.py
```

Actual results: all15 account-free runtime regressions passed on source and extracted native ZIPs; all three manifests loaded and native Tool invocations passed against the real SDK, including Chinese HTML escaping and restricted master-file permission rejection. Repository unit discovery ran65 tests successfully with26 optional-dependency skips (not65 executed passes). Real MCP App/MCPB integration passed independently. Canonical check-repo is rerun after wrapper packing; final outcome is retained in the handoff verification record.

Original full-resolution JPEG evidence is retained under `outputs/song-three-plugins-20261022/evidence/` in the shared workspace, including `dsh-simulated-life-workswarm.jpg`. WorkSwarm screenshots are3600x2260. Raw JSON gateway events are retained separately; they are logs, not screenshot substitutes. Original screenshot SHA-256 values are recorded in the handoff evidence manifest. PR attachment permalinks will be created only after the current-package user testing gate passes. Both screenshot tracker fields remain empty until real PR evidence exists.

## Limits and pending gate

No autonomous world generator or external service is included. Rail automatically reads only the host workspace.root_path; a different explicit Tool workspace must be read with context. No claim is made that an arbitrary custom Tool directory is auto-injected. Automatic project-bound GUI Rail behavior and Windows locking remain untested; real Tool and local SDK Rail flows are recorded separately.

No external service account, API token or paid plan was required. Testing was performed by the assistant under explicit user delegation, not personally by the user. Song Haoran subsequently confirmed submission of the exact current packages in response to the version1.0.0 test-completion/PR question. This does not assert final Project Lead acceptance or any Hub submission. Actual GitHub/evidence state is recorded in delivery.json.

## User confirmation

User test confirmation: "Submit." (original message: `提交`), replying to the explicit question whether all three current Chinese1.0.0 packages had completed testing and could be submitted as a PR; confirmed by Song Haoran; recorded at 2026-10-22T18:10:42+08:00; Task ID AH-20261022-dsh-simulated-life; version1.0.0; native ZIP SHA-256 `d4f8679550432e7a72f9f5f08d13d92f50a5822ad7bb4339048730e00b64d774`; marketplace ZIP SHA-256 `8e12f48d1afced64e983d3c80f07c75e36ae80ef8021801dbec252d19c235faf`; known blocking issues none; disclosed test coverage limits above remain in effect; evidence/source: current side conversation, immediately after the exact-package handoff. Original screenshots were already collected by the assistant under user delegation. This confirmation is distinct from final contributor acceptance.
