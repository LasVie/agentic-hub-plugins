# Source and distribution review: postgres-local-lab

Reviewed 2026-11-02. PGlite -> 离线 PostgreSQL 实验台 -> postgres-local-lab. Task AH-20261102-postgres-local-lab; Candidate CAND-EXT-008; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/electric-sql/pglite . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
- @electric-sql/pglite@0.5.14 — Apache-2.0；licenses/electric-sql--pglite--0.5.14/LICENSE

PostgreSQL版权与许可见licenses/postgresql/LICENSE。PGlite已发布的WASM、数据及JS运行文件保持原字节，不包含另行分发的可选扩展归档。

This asset does not bundle the MPL component used by the mock workbench. No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.

## Concrete tracker comparisons

Compared local SQLite diagnostics a32a50827aba417cb3b037a198b54bfb@1.0.0 and migration verification f374d5771531477ea880f09618375c99@1.0.0 plus cloud database assistants. Adds a self-contained PostgreSQL runtime and persistent local lab; no production-server or full-extension-compatibility claim.

Main was refreshed through de13a4b (PRs 69/70: offline observing and GeoJSON simplification); those scopes do not overlap these developer engines. Final source/native/canonical/installed file equality and current ZIP hashes are in package-verification.json.
