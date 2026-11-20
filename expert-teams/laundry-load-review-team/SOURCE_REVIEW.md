# Source and distribution review

Reviewed 2026-11-20 for Cai Zhenze, task `AH-20261120-laundry-load-review-team`, Candidate Not Applicable. Independent Everyday Laundry Load Review Team → 日常洗衣分批复核专家团 → `laundry-load-review-team`. Native design at base `df95878c7670e93ab38fda6066aa58253f3097b8`.

The live tracker, recent parallel work, existing assets and PRs showed no matching claim. The household rota assigns household work to people, and iLife documents household item inventory and locations. This team assigns one basket's garment groups to compatible machine programs, verifies drying independently, and issues an immediately usable checklist.

| Reference reviewed | Actual use and distribution |
| --- | --- |
| [GINETEX care guidance for ISO 3758:2023](https://www.ginetex.net/share/article/4201/care-symbols) and [trademark statement](https://www.ginetex.net/gb/labelling/care-labelling/) | Public descriptions of treatment limits inform the contract. Protected symbols, official artwork, standard text and reference photos are excluded. |
| [Whirlpool sorting guide](https://www.whirlpool.com/blog/washers-and-dryers/how-to-sort-separate-laundry.html), inspected 2026-11-20 | Context for color separation and separate drying. No manufacturer's text, code, media or appliance presets are distributed. |
| [MetaGPT, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/6507b115562bb0a305f1958ccc87355a-Paper-Conference.pdf) | Structured handoffs inform the design. No framework, prompts, code or figures are copied. |
| [WorkSwarm native package format](https://github.com/openJiuwen-ai/jiuwenswarm/blob/9843516a165bd9a6ad9c37f394fac90be128e551/jiuwenswarm/resources/agent/workspace/skills/agent-group-creator/references/package-spec.md) and [AgentGroup loader](https://github.com/openJiuwen-ai/agent-core/blob/5a35c39f0163a4e6190800df53ad7e24848756eb/openjiuwen/agent_teams/experts/agent_group.py) | Use existing interfaces on local host `fa91394e42a7af731424222db82b02351e694de9`. Official SkillHub CLI `c8ee4ef44be0453470114aa5a19f4e1017462907` is external build tooling. |

Runtime prompts, code, report styles and sample data are authored for this task. There are no bundled third-party assets, external services, libraries or credentials. Test and packaging infrastructure adapts repository-owned Team harnesses from the electricity bill team at the base above. Those files remain outside both ZIPs. No repository-wide license is assigned.
