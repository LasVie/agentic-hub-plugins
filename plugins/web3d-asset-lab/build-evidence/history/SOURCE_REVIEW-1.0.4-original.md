# Source and distribution review: web3d-asset-lab

Reviewed 2026-11-02. glTF Transform -> 网页 3D 模型瘦身台 -> web3d-asset-lab. Task AH-20261102-web3d-asset-lab; Candidate CAND-EXT-010; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/donmccurdy/glTF-Transform . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
- three@0.187.0 — MIT；licenses/three--0.187.0/LICENSE

仅采用glTF Transform的有界模型操作；原生Sharp/libvips及其LGPL二进制不打包。未提供的原生图像I/O入口替换为显式报错模块。彩色贴图缩放由独立浏览器Canvas与SDK实现，属于用户主动选择的有损分辨率调整。演示模型由本插件自行构造，不搬运第三方模型。

This asset does not bundle the MPL component used by the mock workbench. No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.

## Concrete tracker comparisons

Compared parametric modeling 0e1febdb63934c92b64fe4f64d8c2a01@e7bda4f and active solid-mesh Boolean task AH-20261031-solid-mesh-workbench. Targets existing glTF scenes/materials and web delivery costs; excludes CAD construction, STEP/STL conversion and Boolean operations.

Main was refreshed through de13a4b (PRs 69/70: offline observing and GeoJSON simplification); those scopes do not overlap these developer engines. Final source/native/canonical/installed file equality and current ZIP hashes are in package-verification.json.
