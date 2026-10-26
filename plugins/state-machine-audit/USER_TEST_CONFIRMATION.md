# Current user test confirmation — 状态机行为审计1.0.1

Task **AH-20261026-state-machine-audit**; candidate **CAND-DSH-214**; owner **Cai Zhenze**; internal ID `repo:agent-plugin:state-machine-audit`.
Mapping: AmethystLuna/logicprobe → 状态机行为审计 → state-machine-audit.

User test confirmation: “I confirm manual testing of 状态机行为审计 1.0.1 is complete and passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md, keeping it isolated from Main.” Confirmed by Cai Zhenze in this conversation on2026-10-26; receipt recorded17:06:53 Asia/Singapore. Exact message timestamp/permalink unavailable; this record identifies the current conversation rather than inventing a link.

- Native tested ZIP SHA-256: `0846461cbb98e2c08398e65df2f8dffac55c96431d883f22867ffc66e05015cb`.
- Canonical Chinese ZIP SHA-256: `9280fb9d391e31136c66f7b088524309e03a257d03ce1a3e833c8bc70e21f212`.
- Both archives and all14 payload files verified unchanged since testing. No runtime, localization, manifest, wrapper or ZIP change followed confirmation.

Five original full-resolution PNGs are byte-for-byte preserved in evidence/1.0.1/. originals.json records original filenames, actual dimensions, SHA-256 and conversation/version association. No image editing, recompression, cropping or fabricated screenshot. No credentials are visible; supplied local test paths are present. The repository's existing visibility is public; these are the exact originals the user authorized for the delivery PR.

|Original|Readable actual evidence|
|---|---|
|01|1.0.1 test instructions, real six-file inspect report, normal model hash/init/variables/properties/full transitions|
|02|Other valid models, explicit init=待支付, hashes and full transition tables|
|03|Guard/fallback semantics, actual schema/duplicate-key refusals, explicit user model/hash/initial-state confirmation and audit instructions|
|04|Actual1.0.1 audit results, normal12configs/11transitions, expected violation/dead-end/domain/limit outcomes and two refusals|
|05|Complete result summary, shortest traces, explicit initial-state fix passing and honest abstract-model scope|

The four actual valid-model hashes match the packaged fixtures. All four inspect results explicitly show init=待支付. User subsequently confirmed those models/hashes and authorized the real audits; the screenshots show seven audit/refusal calls with version1.0.1. Normal order passes completely; unpaid shipment has a one-event counterexample; guard dead end has zero-event trace; domain escape fails with incomplete analysis; state cap is incomplete; unconfirmed/wrong-hash calls are refused. Expected negative tests pass without claiming the affected model passed. Actual implementation conformance, concurrency/time/probability properties remain outside scope, rather than unresolved promised functionality. No known blocking issue remains.

## Preserved prior history

The user separately confirmed1.0.0 complete/passed and supplied12 originals on2026-10-26. Pre-delivery image/source review found inspect omitted init; the original task returned to Build.1.0.1 corrected that field, added a reversed-state-order regression and updated Chinese confirmation guidance. The current explicit1.0.1 pass and five current originals resolve that gate; old confirmation was not relabeled.

Historical native1.0.0 hash `0caa0a0fc9653e8e90b13b0ddfe43a14c06a1da0c2039fce0b84bdd3a070aa4b`; canonical1.0.0 hash `0219fb71c2cb3f879640a434491b8ff9d1cf318718e066a328ed313fa8cb8964`. Original historical files/manifest/confirmation and superseded ZIPs are preserved locally under ignored dist/state-machine-audit/history and in original tracker reports, excluded from this first delivery as superseded/redundant material.

Current confirmation report: RPT-20261026-state-machine-audit-confirmed-101. Latest main AGENTS.md blob e6e315918b1d948ba37bd2a3312c55c05a254d97 checked2026-10-26. Complete materials gate permits GitHub submission; original evidence must be embedded in the PR and its actual permanent comment link verified before tracker screenshot update and merge. Song Haoran acceptance remains separate; no Hub/Release/Asset Ledger operation is authorized.
