# Test report: dsh-vault 1.0.0

Task: AH-20261022-dsh-vault. Candidate: CAND-DSH-036. Owner: Song Haoran.
Naming: `dsh-vault` -> **本地凭据保险库** -> `dsh-vault`.
Date: 2026-10-22 (Asia/Singapore). Stage: Submit authorized; current-package user confirmation is recorded below. PR/evidence links are tracked in delivery.json.

## Environment and installed package

macOS WorkSwarm 0.2.7, configured Deepseek V4 Flash, actual native gateway at127.0.0.1:19000. Host-bundled Node22.11.0. Local Python3.12.14 regression runtime; real openJiuwen SDK smoke used the existing workspace virtualenv with the separate local agent-core source on PYTHONPATH. These SDK callback checks are distinct from the actual installed app/model calls.

Native test ZIP: `dist/dsh-vault/1.0.0/dsh-vault-1.0.0-workswarm.zip`.
Native SHA-256: `2911404a57c3a55fe8f46973ec80bfe9d719e8b0d9d94854c03453dc8b3026a6`. Size: 20430 bytes.
Installed path: `~/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/dsh-vault`.
All source payload file bytes matched the actual installed payload. Native and marketplace wrapper payloads must match, verified in the handoff manifest. The actual host session was `web_1a1630960bc_5d14de7c10aa`.

## Functional evidence

Actual Deepseek V4 Flash turn searched/loaded dsh_vault and invoked its native demo action. Four returned checks were true: encrypted_at_rest, masked_query, totp_known_vector, wrong_password_rejected. Only a synthetic example.invalid account was used; no real master password, credential or OTP was read. Source regressions also cover masked CRUD, explicit delete/overwrite, nonce freshness, reinitialization refusal, ciphertext tampering, file mode and hostile KDF parameters.

Commands executed (development build tools are not runtime dependencies):

```text
node tools/build_song_plugins.mjs /absolute/path/to/esbuild@0.25.12/lib/main.js
python tools/song_native_test_packages.py
python -m unittest discover -s tests -p test_song_local_plugins.py -v
SONG_PAYLOAD_ROOT=/absolute/path/to/dist/extracted python -m unittest discover -s tests -p test_song_local_plugins.py -v
PYTHONPATH=/local/agent-core python tests/song_local_host_smoke.py
SONG_PAYLOAD_ROOT=/absolute/path/to/dist/extracted PYTHONPATH=/local/agent-core python tests/song_local_host_smoke.py
python -m unittest discover -s tests -v
python tools/asset_release.py check plugins/dsh-vault
python tools/asset_release.py pack plugins/dsh-vault
python tools/asset_release.py check-repo
python tests/run_mcp_server_dev_integration.py
```

Actual results: all15 account-free runtime regressions passed on source and extracted native ZIPs; all three manifests loaded and native Tool invocations passed against the real SDK, including Chinese HTML escaping and restricted master-file permission rejection. Repository unit discovery ran65 tests successfully with26 optional-dependency skips (not65 executed passes). Real MCP App/MCPB integration passed independently. Canonical check-repo is rerun after wrapper packing; final outcome is retained in the handoff verification record.

Original full-resolution JPEG evidence is retained under `outputs/song-three-plugins-20261022/evidence/` in the shared workspace, including `dsh-vault-workswarm.jpg`. WorkSwarm screenshots are3600x2260. Raw JSON gateway events are retained separately; they are logs, not screenshot substitutes. Original screenshot SHA-256 values are recorded in the handoff evidence manifest. PR attachment permalinks will be created only after the current-package user testing gate passes. Both screenshot tracker fields remain empty until real PR evidence exists.

## Limits and pending gate

This port deliberately implements a smaller encrypted CRUD/search/TOTP scope, not the upstream settings UI, browser autofill or all upstream features. list/get never return the raw credential. Real use requires the user to configure a strong master password locally; a same-user process able to read both password file and vault remains outside the protection boundary. Windows-specific file-lock behavior was not tested.

No external service account, API token or paid plan was required. Testing was performed by the assistant under explicit user delegation, not personally by the user. Song Haoran subsequently confirmed submission of the exact current packages in response to the version1.0.0 test-completion/PR question. This does not assert final Project Lead acceptance or any Hub submission. Actual GitHub/evidence state is recorded in delivery.json.

## User confirmation

User test confirmation: "Submit." (original message: `提交`), replying to the explicit question whether all three current Chinese1.0.0 packages had completed testing and could be submitted as a PR; confirmed by Song Haoran; recorded at 2026-10-22T18:10:42+08:00; Task ID AH-20261022-dsh-vault; version1.0.0; native ZIP SHA-256 `2911404a57c3a55fe8f46973ec80bfe9d719e8b0d9d94854c03453dc8b3026a6`; marketplace ZIP SHA-256 `9d6065d4c8a2d49b803bfd48c5863daa2c9317599532e2aea234c734c7ccb4f3`; known blocking issues none; disclosed test coverage limits above remain in effect; evidence/source: current side conversation, immediately after the exact-package handoff. Original screenshots were already collected by the assistant under user delegation. This confirmation is distinct from final contributor acceptance.
