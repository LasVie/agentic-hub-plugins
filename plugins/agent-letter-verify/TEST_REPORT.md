# Functional verification — 代理信件完整性校验 1.0.1

Task AH-20261023-agent-letter-verify; Candidate CAND-DSH-305; owner Cai Zhenze. Mapping: dsh-whale-post#verify → 代理信件完整性校验 → agent-letter-verify. Tests executed 2026-10-23 in the separate feat/agent-letter-verify worktree based on d462c34. These are AI-run functional checks, not user test confirmation or screenshot evidence.

## Environment and source checks

macOS arm64; Python 3.12.14, openJiuwen 0.1.19, PyYAML 6.0.3; Node 22.23.3 for independent JavaScript interoperability only. Runtime requires Linux/macOS Python >=3.11 and the host SDK, no added pip/npm packages. Pinned upstream packages/verify 0.6.1 at d78a82699722f0da6ae3d2b4cbdbaa411f2f67af. The complete MIT license is bundled unchanged; see SOURCE_REVIEW.md.

```sh
PATH=/private/tmp/jiuwenswarm-plugin-dev-2hlu8bh8/node-v22.23.3-darwin-arm64/bin:$PATH AGENT_LETTER_UPSTREAM=/private/tmp/agent-letter-verify-upstream-20261023/packages/verify/index.js /private/tmp/jiuwenswarm-plugin-dev-2hlu8bh8/venv/bin/python -B tests/test_agent_letter_verify.py -v
python tools/asset_release.py check plugins/agent-letter-verify
```

Result: all 23 source functional tests pass with the actual host SDK and Node present; no skips. They cover: valid Chinese/emoji/escaped-text envelope, exact canonical-byte and HMAC agreement with Node, acceptance by the actual pinned upstream createVerify, body/MAC tampering, missing/unknown fields and sender, no shared-key fallback, hello/ack profile, strict integers/UTF-8/JSON keys, input budgets, path traversal/links/permissions, private trust storage, empty allowlists, disabled vs verified, persistent disable and stale revisions, lock preservation, injected atomic-write failure preserving prior configuration, no-network execution, replay limitation disclosure, Chinese CLI exit semantics and actual async SDK invoke/stream. No input/secret/body echo or model call. Current-version log: /private/tmp/agent-letter-functional-1.0.1.log.

Initial failures were corrected before first packaging: CLI help lacked the Chinese word for unchecked; an invalid official category was replaced with 软件开发. Test setup now redirects SDK logs outside the repository. No behavioral test was weakened to hide a failure.

## Isolated host and archive checks

The task-only environment is /private/tmp/agent-letter-verify-workswarm-20261023 with fresh data/tasks/cache/configuration. Tracked host source is pinned to 3ef1de9bf0b4813e2a0e8674dedc499c78e53df2 by read-only git archive. Shared dependencies are read-only; Vite and runtime caches are private. Models/prewarm are disabled and no other environment's credentials/configuration were copied. Main's ports, state and checkout were preserved.

Frontend http://127.0.0.1:6385 returned HTTP 200; backend 29240 and frontend-proxied WebSocket ping/pong, config.get and plugin_packages.list succeeded. Agent 28240 and gateway 30240 are separate. Evidence: runtime/health-result.json. Test server startup required normal localhost sandbox escalation. A first source archive attempt needed the LFS process filter disabled; no checkout was changed.

Final checks completed below; no human test completion is inferred. User testing and original screenshots remain pending. No commit, push, PR, merge, Release or Hub operation is authorized in this Phase 2 handoff.

Before handoff, full original file-header retention was made explicit inside the adapted core. The initial unpublished 1.0.0 preflight archives were moved outside the repository, and the current package is 1.0.1. The same complete functional suite and archive checks are run against this current payload below.

## Current 1.0.1 extracted and installed results

- `python tools/asset_release.py check plugins/agent-letter-verify` and `pack` passed. A deterministic native companion was derived from the canonical ZIP, with every inner byte compared to source.
- Both ZIPs were extracted; all eight runtime files, wrapper shape, CRC, unique safe regular paths, declared files/versions, valid UTF-8/Chinese docs and exact full MIT bytes/original header passed. Extraction/evidence: /private/tmp/agent-letter-verify-extracted-1.0.1/archive-check.json.
- `AGENT_LETTER_PAYLOAD=/private/tmp/agent-letter-verify-extracted-1.0.1/canonical/agent-letter-verify/agent-letter-verify` with the same Node/upstream/SDK command passed all 23 tests again, no skips. Log /private/tmp/agent-letter-extracted-1.0.1.log.
- Packaging regression: `python -B -m unittest discover -s tests -p test_asset_release.py -v`: 18 passed. This is separate from the 23 asset tests.
- Actual Extensions `plugin_packages.import_local` succeeded through this task's localhost WebSocket. Chinese browser My Extensions card rendered correctly; clicking 安装 returned 插件安装成功, and installed details show one Chinese-described Skill and two Chinese tool cards. AI inspection only: /private/tmp/agent-letter-verify-workswarm-20261023/runtime/extensions-details.png. Native OS file-picker upload itself is not claimed.
- Actual installed `find_plugin_manifest -> load_plugin_package -> resolve_plugin_parts` resolved one Skill and two real SDK Tools. Six invoke cases returned verified / body_digest_mismatch / mac_mismatch / sender_not_allowed / unknown_field / duplicate_json_key as applicable. Disabled and persisted re-disabled states were not_checked, stale revisions were refused, and stream returned the same successful verification. Source/canonical/native/installed files matched before and after; input hashes were unchanged. No secret/body/MAC echo, network attempt, agent construction or model invocation occurred. Evidence: runtime/installed-plugin-test-result.json and runtime/test_installed_plugin.py in the isolated environment.
- User fixture workspace is separate from integration fixtures and remains enabled=false/revision=0, containing only public fictional data. Create with `python tests/test_agent_letter_verify.py --write-demo-dir <new-absolute-directory>`; never overwrite another trust directory. MANUAL_TESTING.md supplies exact paths, hash and Chinese copy/paste instructions.

Canonical SHA-256: `c195834594177edaef1516a3be7e725b75c20467454de6b80bb9d0842b64c9e6`.
Native test SHA-256: `a6260d897de78677d64500e11e41e720b940dcc0661a65d3c0576be2e60494a6`.

Known limits: restricted basic v1 profile, POSIX directory behavior tested only on macOS; Windows unsupported/unverified. No replay/freshness, unique-author or content-truth guarantee, message transport or automatic interception. No real keys tested. Fresh instance model is disabled; model-generated conversation and end-to-end browser file picker remain unverified. There are no known blocking payload failures from performed tests. Explicit user testing of this exact package and genuine original screenshots are pending. Main SerialHunt remains Ready for Testing with its own state and ports unchanged.
