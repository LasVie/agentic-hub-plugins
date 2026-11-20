# Source and distribution review

Reviewed 2026-11-20 for Cai Zhenze, task `AH-20261120-tou-bill-review-team`. Candidate Not Applicable. Independent Time-of-Use Electricity Bill Review Team → 分时用电账单复核专家团 → `tou-bill-review-team`. Native design from `origin/main` at `aa29fff6074049737f986df722204e9e12a2c38e`.

Phase 1 and kickoff compared live candidates, ledger, claims, tasks, reports, parallel chats and PRs. 账单分析skill 1.0.0 analyzes transaction categories and trends. 多表合并与对账 1.0.0 standardizes and reconciles existing tables. The warehouse team audits inventory. Joulo candidate CAND-CLD-338 reads account-specific EV charging data. This group reconstructs energy-charge lines from meter intervals and an explicit rate schedule. No matching claim or candidate was identified.

| Source | Use |
| --- | --- |
| [Green Button Alliance interval metering FB04](https://www.greenbuttonalliance.org/fb04), inspected 2026-11-20 | Documented interval start, duration, value and units. The team uses its own small CSV contract. |
| [NREL SAM Help 2025.4.16](https://sam.nrel.gov/images/web_page_files/sam-help-2025-4-16.pdf), Electricity Rates and Load | Background on per-kWh time-of-use rates and distinct charge types. The tariff and data are synthetic. |
| [MetaGPT, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/6507b115562bb0a305f1958ccc87355a-Paper-Conference.pdf) | Structured handoffs are a design reference. The saved independent baseline is this team's adaptation. |
| [WorkSwarm creator package specification](https://github.com/openJiuwen-ai/jiuwenswarm/blob/9843516a165bd9a6ad9c37f394fac90be128e551/jiuwenswarm/resources/agent/workspace/skills/agent-group-creator/references/package-spec.md) and [AgentGroup loader](https://github.com/openJiuwen-ai/agent-core/blob/5a35c39f0163a4e6190800df53ad7e24848756eb/openjiuwen/agent_teams/experts/agent_group.py) | Existing interfaces. Actual local host revision fa91394e42a7af731424222db82b02351e694de9 with preserved local settings. |
| Official SkillHub CLI at c8ee4ef44be0453470114aa5a19f4e1017462907 | External validation and packaging tool only. |

No third-party text, code, media, logos, examples, real utility data or rates are distributed in the payload. Asset-owned tests adapt existing repository packaging and host test harnesses from the timber team at aa29fff; the harnesses are outside both ZIPs. Python standard library only at runtime, with existing WorkSwarm team and shell capabilities. No external application, pricing API, credential, install step or host change. No repository-wide license assigned.
