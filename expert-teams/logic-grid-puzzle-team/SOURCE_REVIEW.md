# Source review

- Task: `AH-20261117-logic-grid-puzzle-team`; owner: Cai Zhenze.
- Mapping: independent Logic Grid Puzzle Authoring and Verification Team → 逻辑网格谜题编制与验解专家团 → `logic-grid-puzzle-team`.
- Mode: **native**. No external implementation is ported. Repository-owned additions receive no invented license grant or new copyright assignment.

## Inspected references and intended use

| Reference | Pinned identity | Actual use / reuse permission |
| --- | --- | --- |
| [CSP explanation paper](https://arxiv.org/abs/2006.06343v1) | arXiv:2006.06343v1, 2020 | Functional research only; zero copied text, code, puzzles or figures. No redistribution grant assumed. |
| [ZebraLogic](https://proceedings.mlr.press/v267/lin25i.html) | ICML2025, PMLR267:37889–37905 | Functional CSP framing only; dataset/software not downloaded or reused. |
| [AutoGen paper](https://arxiv.org/abs/2308.08155v2) / [official repository](https://github.com/microsoft/autogen) | paper v2, 2023 | Historical collaboration precedent only; no prompts/code/data/media reused, no runtime dependency. Current project is archived. |
| [JiuwenSwarm specification](https://github.com/openJiuwen-ai/jiuwenswarm/blob/9843516a165bd9a6ad9c37f394fac90be128e551/jiuwenswarm/resources/agent/workspace/skills/agent-group-creator/references/package-spec.md) | `9843516a165bd9a6ad9c37f394fac90be128e551` | Consulted native schema; no creator implementation bundled. |
| [AgentGroup loader](https://github.com/openJiuwen-ai/agent-core/blob/5a35c39f0163a4e6190800df53ad7e24848756eb/openjiuwen/agent_teams/experts/agent_group.py) | `5a35c39f0163a4e6190800df53ad7e24848756eb` | Consulted interface; actual installed loader tested separately. No SDK bundled. |
| Official Hub CLI | `c8ee4ef44be0453470114aa5a19f4e1017462907` | Validation/build tool only, outside payload; no CLI code redistributed. |

## Material coverage

Code, personas, Skills, documentation, test fixtures and generated demonstration puzzles are independently authored from the approved functional specification. Original fictional labels only; no real-person profile data, trademarks, icons, fonts or puzzle corpus. Runtime uses Python standard library and existing host command/file tools. No dependencies, host code, solver binaries or media are bundled. Consequently no reused path requires a third-party license/NOTICE; permission is not inferred for excluded upstream materials. An independent design is not a general legal clearance claim.

The pre-existing PC/grant team manifests and test reports were inspected to understand maintained host integration; their business source, prompts and artwork are not copied. Main's procurement implementation and package are not source inputs.

## Release review

Final ZIP payload/notice inspection, file hashes and actual CLI/host versions will be recorded after packaging. Until those checks run this document makes no claim that a release is validated.

Final review 2026-11-17: extracted both final Chinese ZIPs; 21 runtime files match source and installed payload. Native SHA-256 e008b203078e53852de51675dc7fc9669b57663a64c33593f8231fc822cdd1a9; wrapper SHA-256 7d81dc589061607be905361e9c71e60058b6b40c0ce947622118ca498f99765e. No copied code, dataset, media, fonts, dependency or upstream notices in payload; no third-party license obligation identified for excluded reference-only material. Official tooling is external and unmodified, not redistributed. All authored runtime instructions/help/errors/examples are Chinese by default; English display fields/protocol keys retain compatibility. Actual CLI0.0.1, WorkSwarm0.2.8/SDK0.1.20 checks and limitations are in TEST_REPORT.md. Main's integration harness was read as protocol reference without copying its implementation.
