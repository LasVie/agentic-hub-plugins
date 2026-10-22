# Test report: dsh-pianist 1.0.0

Task: AH-20261022-dsh-pianist. Candidate: CAND-DSH-192. Owner: Song Haoran.
Naming: `dsh-pianist` -> **离线钢琴演奏** -> `dsh-pianist`.
Date: 2026-10-22 (Asia/Singapore). Stage: Submit authorized; current-package user confirmation is recorded below. PR/evidence links are tracked in delivery.json.

## Environment and installed package

macOS WorkSwarm 0.2.7, configured Deepseek V4 Flash, actual native gateway at127.0.0.1:19000. Host-bundled Node22.11.0. Local Python3.12.14 regression runtime; real openJiuwen SDK smoke used the existing workspace virtualenv with the separate local agent-core source on PYTHONPATH. These SDK callback checks are distinct from the actual installed app/model calls.

Native test ZIP: `dist/dsh-pianist/1.0.0/dsh-pianist-1.0.0-workswarm.zip`.
Native SHA-256: `ab958ffb941b5e94653f250e1cdb33535146ca9cb694178423d961ec95443a1e`. Size: 37101 bytes.
Installed path: `~/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/dsh-pianist`.
All source payload file bytes matched the actual installed payload. Native and marketplace wrapper payloads must match, verified in the handoff manifest. The actual host session was `web_1a163099e9d_1de8293c15e3`.

## Functional evidence

Actual Deepseek V4 Flash turn invoked dsh_pianist with four Chinese-titled notes at 100 BPM. It generated a 2.750023-second mono 22050Hz PCM16 WAV, a score JSON and a standalone Chinese HTML player. The agent used bash only to confirm artifact file existence after native tool generation, not as a replacement implementation. CUA tested Play, Pause, Restart and C4 audition in that actual generated player. Observed audio readyState=4, error=null, paused=false with advancing currentTime; Pause showed the Chinese paused state; Restart returned to the start; 88 key buttons were present. A separate native WorkSwarm Use-button handoff successfully invoked the real tool with MIDI109 and returned the expected Chinese range error. Audio regressions check nonzero PCM, A4 autocorrelation near440Hz, duration/format, deterministic polyphony, transposition and invalid-input rejection. This is synthesized fallback audio, not recorded Salamander samples.

Commands executed (development build tools are not runtime dependencies):

```text
node tools/build_song_plugins.mjs /absolute/path/to/esbuild@0.25.12/lib/main.js
python tools/song_native_test_packages.py
python -m unittest discover -s tests -p test_song_local_plugins.py -v
SONG_PAYLOAD_ROOT=/absolute/path/to/dist/extracted python -m unittest discover -s tests -p test_song_local_plugins.py -v
PYTHONPATH=/local/agent-core python tests/song_local_host_smoke.py
SONG_PAYLOAD_ROOT=/absolute/path/to/dist/extracted PYTHONPATH=/local/agent-core python tests/song_local_host_smoke.py
python -m unittest discover -s tests -v
python tools/asset_release.py check plugins/dsh-pianist
python tools/asset_release.py pack plugins/dsh-pianist
python tools/asset_release.py check-repo
python tests/run_mcp_server_dev_integration.py
```

Actual results: all15 account-free runtime regressions passed on source and extracted native ZIPs; all three manifests loaded and native Tool invocations passed against the real SDK, including Chinese HTML escaping and restricted master-file permission rejection. Repository unit discovery ran65 tests successfully with26 optional-dependency skips (not65 executed passes). Real MCP App/MCPB integration passed independently. Canonical check-repo is rerun after wrapper packing; final outcome is retained in the handoff verification record.

Original full-resolution JPEG evidence is retained under `outputs/song-three-plugins-20261022/evidence/` in the shared workspace, including `dsh-pianist-workswarm.jpg`. WorkSwarm screenshots are3600x2260. Raw JSON gateway events are retained separately; they are logs, not screenshot substitutes. Original screenshot SHA-256 values are recorded in the handoff evidence manifest. PR attachment permalinks will be created only after the current-package user testing gate passes. Both screenshot tracker fields remain empty until real PR evidence exists.

## Limits and pending gate

Node.js22+ is required; the standard macOS WorkSwarm app-bundled Node22.11.0 was used. HTML is opened as a local standalone artifact, not a DeepSeek-specific embedded widget. Browser media state and generated audio samples were checked; no subjective human listening/recorded-sample quality claim is made. Recorded sample packs are excluded.

No external service account, API token or paid plan was required. Testing was performed by the assistant under explicit user delegation, not personally by the user. Song Haoran subsequently confirmed submission of the exact current packages in response to the version1.0.0 test-completion/PR question. This does not assert final Project Lead acceptance or any Hub submission. Actual GitHub/evidence state is recorded in delivery.json.

## User confirmation

User test confirmation: "Submit." (original message: `提交`), replying to the explicit question whether all three current Chinese1.0.0 packages had completed testing and could be submitted as a PR; confirmed by Song Haoran; recorded at 2026-10-22T18:10:42+08:00; Task ID AH-20261022-dsh-pianist; version1.0.0; native ZIP SHA-256 `ab958ffb941b5e94653f250e1cdb33535146ca9cb694178423d961ec95443a1e`; marketplace ZIP SHA-256 `e2bdb718c99a170d64594b6e3c19c75c3c6ffbbe64e1d2c930d8f82930f50e7f`; known blocking issues none; disclosed test coverage limits above remain in effect; evidence/source: current side conversation, immediately after the exact-package handoff. Original screenshots were already collected by the assistant under user delegation. This confirmation is distinct from final contributor acceptance.
