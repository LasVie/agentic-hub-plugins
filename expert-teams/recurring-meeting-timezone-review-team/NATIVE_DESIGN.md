# Native design

Audit 1–3 organizer-local weekly start times over 4–12 occurrences for 2–8 participants. Each has explicit IANA zone and weekly same-day windows, with full-date overrides. Exclusions: calendar IO, recurrence rules beyond a weekly cadence, auto-rescheduling and inferred availability. A window crossing midnight is represented as two dated segments. Duration uses elapsed UTC minutes. The report checks the whole half-open interval.

Leader confirms the bounds and scope. The intake analyst documents the source and clarifies contradictions. The planner enumerates valid organizer instants by round-tripping both folds, then maps the elapsed interval into participant windows. The verifier independently searches the UTC timeline for the requested wall minute and checks availability using compiled minute masks. The algorithms share the input contract and a fingerprinted system timezone source, so agreement does not validate the underlying tz database itself.

A gap has no UTC candidate. An overlap has two UTC candidates. Both are reported without selecting an instant. The verifier builds its baseline from confirmed input before reading the plan. Leader checks exact evidence and delivers Chinese Markdown, CSV and JSON. One correction cycle is allowed. A blocked slot is a valid audited result. A discrepancy in evidence prevents a verified delivery.

Actual WorkSwarm AgentGroup loader, agent_templates, host task delegation, file and shell are the integration boundaries. Native scripts use Python 3.10+ standard library. No changes to installed host, SDK, other assets or services.
