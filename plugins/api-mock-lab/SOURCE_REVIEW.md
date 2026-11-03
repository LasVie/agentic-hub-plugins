# Source and distribution review: api-mock-lab

Reviewed 2026-11-02. Mockoon -> 接口模拟与联调台 -> api-mock-lab. Task AH-20261102-api-mock-lab; Candidate CAND-EXT-006; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/mockoon/mockoon . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
- yaml@2.9.1 — ISC；licenses/yaml--2.9.1/LICENSE

JMESPath采用MPL-2.0；对应可修改源码随licenses/jmespath-community--jmespath--1.4.1/source提供，许可保持MPL-2.0。未修改其源文件，打包转译不改变原许可。

For the MPL component, the full Source Code Form, original license, fixed revision and availability instructions are distributed together. No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.

## Concrete tracker comparisons

Compared API contract regression 0a2a5f70f4aa42d4a3982215cfd89351@1.0.0 and contract review 267aefe470e94632a422a726dc6c1bc0@1.0.0. Adds a runnable mock HTTP service and scenario lifecycle; not another static contract review.

Main was refreshed through de13a4b (PRs 69/70: offline observing and GeoJSON simplification); those scopes do not overlap these developer engines. Final source/native/canonical/installed file equality and current ZIP hashes are in package-verification.json.
