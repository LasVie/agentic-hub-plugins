# Source and distribution review — 本机环境探针

Reviewed 2026-10-23 after user-authorized autonomous selection/claim; owner Song Haoran.

## Identity and deduplication

CAND-DSH-155 / AH-20261023-environment-inspector. Partial Overlap - Extend Existing Capability. Compared system-guardian-swarm 2e8704aedef0414d823646ce208e47d6@1.0.0 (Linux/open-source OS security/cleanup teams), diagnose 0b0d14a133b54992bd547e7c068a1f8d@e7bda4f (bug diagnosis discipline), MCP Manager 4862208069dc4ed9b1838f6ddfabbcc4@1.0.3 and HarmonyOS checklist 8aca6e7f4076432f8bff1fa2f706e9c2@1.0.0. Add bounded actual local CLI/version/port observations and before/after snapshot comparison on the target macOS host as a read-only companion; no generic diagnosis/security assessment duplicated. Windows remains unsupported unless separately tested.

Original webkubor/dsh-env-inspector -> 本机环境探针 -> environment-inspector@1.0.0. This is a bounded portable subset, not the complete upstream host/plugin.

## Pinned source and actual reuse

Source: webkubor/dsh-env-inspector; exact revision `1dfe519cd7515b6f806302c50e75b0635402dcc2`; license MIT. Full root/subpackage license and actual reused files reviewed.

- Pure lsof parser extracted; per-port representative-row semantics retained and explicitly described.
- New bounded version probes and revisioned snapshot comparison; removed system identity, home/PATH/env-key/profile collection, external IP, browser host hooks and process termination.

## File and license evidence

- Full original license bytes: `licenses/upstream/LICENSE`, SHA-256 `9d319c367eb6246b2755a2ce8f34ad926d9749e619ba28b20d3f0a1d3987fc56`.
- `vendor/ports.mjs`: SHA-256 `9ce2df7b73111cfe90b8f679d3c3c9b468b6b3fef74f15df5779a79151deb5f8`.
- `runtime/engine.mjs`: SHA-256 `796be2f7c9daaf230eec2d3d4f6f29b79c641e2fd839c7f99f5a05429a395ec0`.

Original copyright/attribution and headers remain intact; full notices are inside the runtime payload. For Apache-derived modified files, prominent change notices are in runtime/engine.mjs and vendor/readonly-argv.mjs; unmodified vendor/types.ts is byte-preserved. For MIT sources, original licenses including disclaimers are retained. No root/package NOTICE exists for the selected git graph source; unrelated third-party notices are not represented as applying to excluded components.

No external runtime packages, fonts, media, vocabulary datasets or upstream host runtimes are redistributed. Node and Python/OpenJiuwen are pre-existing host prerequisites, not bundled distributions. Browser layout and adapters are local additions; no additional repository-wide or new-code relicensing decision is made.

Permission status is verified only for the actual paths/subset above. Packaging and automated checks do not grant legal rights or prove full upstream feature parity. Functional/UI/host results are recorded separately in TEST_REPORT.md.
