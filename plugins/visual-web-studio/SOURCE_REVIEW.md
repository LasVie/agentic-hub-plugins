# Source and distribution review: visual-web-studio

Reviewed 2026-11-02. GrapesJS -> 可视化网页搭建台 -> visual-web-studio. Task AH-20261102-visual-web-studio; Candidate CAND-EXT-007; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/GrapesJS/grapesjs . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
- underscore@1.13.8 — MIT；licenses/underscore--1.13.8/LICENSE

GrapesJS源码固定3b2c671c0ab50f052a219b987dea8738ea75886e；构建时排除codemirror-formatting附加件，以独立空模块替代；代码格式化功能不提供。中文界面与保存/导出为本项目新增；核心样式与中文语言文件保持原文。

This asset does not bundle the MPL component used by the mock workbench. No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.

## Concrete tracker comparisons

Compared frontend design fb9e53d490ed4f62af6151509c3bb1ba@1.0.0, screenshot-to-HTML 4e1f2b19a7b94ad49a404054a06dd167@1.0.0, Annotate 70cbbc39a17a426696300ab165e1564c@1.0.3 and existing Playground. Adds direct user editing and resumable page-project state; excludes arbitrary React application round trips.

Main was refreshed through de13a4b (PRs 69/70: offline observing and GeoJSON simplification); those scopes do not overlap these developer engines. Final source/native/canonical/installed file equality and current ZIP hashes are in package-verification.json.
