# Source review — 代理信件完整性校验 1.0.1

Candidate CAND-DSH-305; original task AH-20261023-agent-letter-verify; explicitly supplied owner Cai Zhenze. Reviewed 2026-10-23, Asia/Singapore, after explicit Phase 2 approval and verified claim/task registration. Mapping: dsh-whale-post#verify → 代理信件完整性校验 → agent-letter-verify. Internal identity: repo:agent-plugin:agent-letter-verify.

## Pinned source and permission

Source: https://github.com/deepsleepAquarium/dsh-whale-post/tree/d78a82699722f0da6ae3d2b4cbdbaa411f2f67af/packages/verify ; package 0.6.1. This exact main commit is the pin, not the different v0.6.1 tag commit. Six selected files were retrieved as raw base64 and checked against exact Git blob identities. Phase 1 complete-tree license inspection applies to the unchanged pin; no conflicting nested license or applicable NOTICE was found. The selected directory contains code/text only.

Root and package LICENSE are identical complete MIT, Copyright (c) 2026 The Tank, covering software and associated documentation. Full permission, conditions and disclaimer were inspected. index.js imports only Node built-ins; package.json declares no third-party runtime dependencies. audit-upstream reports automatic unknown; the verified conclusion comes from actual content/coverage review, not that detector.

| Source material | Pinned Git blob | Actual use |
| --- | --- | --- |
| packages/verify/index.js | a65a038b493f49b527eff4b39d9388a74cf2a861 | runtime/verifier.py: adapted ordered JSON pairs, decoded hexadecimal HMAC key, body SHA-256, field/allowlist checks and explicit disabled state; translated and substantially hardened |
| packages/verify/README.md | 0e881db25c84efedc51c18f59f6c948fa29153f0 | README.md: adapted description; replaces DSH setup and incorrect recipient wording |
| package/root LICENSE | e1f13ed44dc24d9163850b294ce30d73de6743c0 | unchanged licenses/whale-post-verify/LICENSE; SHA-256 8d5ee4ed2408d928530d0515bfa8f8d1976f468f355a19aaa7f71921c4dce08d |
| package.json / selftest.mjs | 1ee0a91081c3a48203a8d9677c9e884aeb878926 / 176f1145eaaf722e0b787e283ea12c6cdfda4dac | dependency/test review only; not bundled or translated as tests |

Conclusion: mode ported / permission_status verified for listed code/docs. Preserve original attribution and full MIT. THIRD_PARTY_NOTICES.md lists scope/modifications. No selected Apache material; Apache-specific obligations not applicable. No new repository-wide license is assigned. New host integration and tests are not represented as an independent clean-room implementation of the seen core.

## Boundary decided before adaptation

The host provides Python/openJiuwen. Use Python >=3.11 standard library instead of requiring a Node subprocess at runtime. Preserve the upstream 14-field canonical ordered-pair JSON and decoded 32-byte hex HMAC semantics; test JavaScript/Python interoperability with Chinese/emoji/control characters and safe integers. Node is test-only. Do not include optional bus injection, DSH/Cordis registration, transport, reminder policy, binaries, service API or third-party data/media.

Define whale-post-basic-v1: v=1; kind msg/hello/ack; primitive bounded fields documented in README. Reject unsupported versions/types/fields, duplicate JSON keys, nonfinite numbers and invalid Unicode. Harden sender-derived paths, static symlinks, file budgets, policy persistence and enable/disable behavior. Keys remain local private per-sender files; no shared fallback, secret tool arguments, key-return API or real-key generation. Empty allowlists must not silently trust everyone. Revision checks and atomic policy writes must report failures honestly.

Separate verified/rejected/not_checked; ok alone does not mean authenticated. No replay/time-freshness/unique-author identity guarantee, automatic WorkSwarm interception or production authorization gate. No message is sent. Same-user compromise and malicious concurrent directory replacement are not covered by a general security guarantee. Independently authored Chinese Skill/adapter treat envelope content as untrusted data.

## Comparison and isolation

Reuse Phase 1 findings, with no newer conflicting verifier delivery at kickoff: agent-team-orchestration b68e551f74ec46818b51492be6efb83c@e7bda4f (roles/handoffs); Discord 桥接卫士 04d23729393a4070a80dd38bc6ce1cab@1.0.0 (channel allowlists/relay); 本地凭据保险库 2c760446a88c433aaff1bf94f046701a@1.0.0 (encrypted CRUD/TOTP); 智能下载 repo:agent-plugin:dsh-smart-download@1.0.1 (download hashes). They do not supply canonical envelope authentication. Main's SerialHunt files/branch/runtime remain isolated.

## Distribution review gate

Before handoff extract canonical and native ZIPs: verify all paths, Chinese text/messages, exact full license bytes, notices, payload equality and actual SDK flows. Record actual results and final identities in TEST_REPORT.md/artifact.json. Real credentials, fixtures, upstream research, environments and runtime state stay outside ZIPs. Final extraction results are recorded below; human manual confirmation remains pending.

Pre-handoff correction: preserve the complete original index.js file header verbatim inside the Python module docstring, explicitly labelled as historical upstream interface documentation. Initial unpublished preflight 1.0.0 archives are archived outside the repository; handoff advances to 1.0.1 without overwriting a packaged version. No user has tested or confirmed that preflight build.

## Final extracted distribution review — 2026-10-23

Current canonical: releases/agent-plugin/agent-letter-verify/1.0.1/agent-letter-verify-1.0.1.zip, SHA-256 c195834594177edaef1516a3be7e725b75c20467454de6b80bb9d0842b64c9e6. Native test companion: dist/agent-letter-verify/1.0.1/agent-letter-verify-1.0.1-workswarm.zip, SHA-256 a6260d897de78677d64500e11e41e720b940dcc0661a65d3c0576be2e60494a6. Both were extracted into /private/tmp/agent-letter-verify-extracted-1.0.1 and inspected. CRCs, unique safe regular paths, UTF-8, eight-file equality with source and installed payload, manifest/version, declared components and Chinese instructions/results passed. No caches, fixtures, secrets, upstream downloads or runtime state are in either ZIP.

Both reused paths have matching full MIT coverage. licenses/whale-post-verify/LICENSE is byte-identical to both pinned upstream license copies and matches provenance SHA-256 8d5ee4ed2408d928530d0515bfa8f8d1976f468f355a19aaa7f71921c4dce08d. The complete original index.js leading file header is retained verbatim as explicitly historical documentation inside runtime/verifier.py, with clear port/change attribution. THIRD_PARTY_NOTICES.md identifies the actual code/docs, rightsholder, exact pin and modifications. New Skill/adapter/CLI are Chinese original integration material; no graphics/fonts/data/dependency binaries were reused. Python/host SDK are environment-provided, not bundled. No selected dependency license or NOTICE condition remains unresolved for this scope. No repository-wide relicensing or Hub acceptance is claimed.
