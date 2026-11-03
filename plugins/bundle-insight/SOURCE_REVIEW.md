# Source and distribution review: bundle-insight

Reviewed 2026-11-02. Rollup Plugin Visualizer -> 前端包体积透视台 -> bundle-insight. Task AH-20261102-bundle-insight; Candidate CAND-EXT-009; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/btd/rollup-plugin-visualizer . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
- wsl-utils@1.0.1 — MIT；licenses/wsl-utils--1.0.1/LICENSE

使用官方统计采集插件与Rollup WASM进行真实构建；本项目独立实现中文交互图和对比界面，不分发上游预编译图表客户端。未包含可选fsevents监听器；不提供watch模式。

This asset does not bundle the MPL component used by the mock workbench. No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.

## Concrete tracker comparisons

Compared Chrome DevTools 2f99a9222dce41f4bd5ac440bf4496f4@1.0.0 and frontend performance team cad456b08b8d4ab59e3cad4beaca8374@1.0.0. Adds build-artifact module composition/dependency evidence and persistent comparison. No generic browser/E2E replacement; first release Rollup/Vite only.

Main refreshed through de13a4b. Final exact-byte verification is in package-verification.json.
