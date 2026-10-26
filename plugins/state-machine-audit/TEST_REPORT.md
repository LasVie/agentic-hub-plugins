# Functional test evidence — state-machine-audit 1.0.1

Owner Cai Zhenze; candidate CAND-DSH-214; original task AH-20261026-state-machine-audit; 状态机行为审计. Local feat/state-machine-audit worktree only; Main untouched. Cai Zhenze explicitly confirmed current1.0.1 complete/passed and supplied five original screenshots on2026-10-26; see USER_TEST_CONFIRMATION.md and evidence/1.0.1/. Prior1.0.0 confirmation and12 originals remain preserved in original tracker history and ignored local dist/state-machine-audit/history.

## Pre-delivery finding and bounded correction

User screenshots02-06 explicitly report inspect1.0.0 did not return the initial state. Source confirms missing top-level init. A new regression reverses the state array in each of the four valid Chinese models; it failed against1.0.0 with KeyError:init in all four cases, then passed after the fix. It verifies the explicit model initial state regardless of array order, the actual byte hash, input immutability, and no inspect audit verdict. This is a real missed preflight assertion, not an invented user failure or a test only of source text.

Runtime diff against preserved tested1.0.0: VERSION1.0.1 and added `init: m["init"]` in inspect response. Four accompanying payload files update manifest/version and Chinese review instructions/tool description. No exploration algorithm, schema, limits, fixture or license change. Old1.0.0 ZIPs are preserved locally, excluded from this first delivery as superseded material.

## Current verification

- Python3.12.14/macOS arm64. `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p test_state_machine_audit.py -q`: **55 passed**. The same55 passed independently against both extracted canonical and native payloads via STATE_MACHINE_AUDIT_PAYLOAD.
- Full repository regression: **378 run;377 passed,1 optional historical prosody comparison skipped**. Existing Node22 runtime on PATH; local SDK environment; no model calls.
- Native WorkSwarm1.0.0 inventory matched its tested14 files before replacement and was backed up under this task's runtime/package-backups/. Only state-machine-audit was uninstalled/reimported/installed with1.0.1 through real backend RPCs. Other local plugin entries and host configuration files remained unchanged. No server restart or Main/previous-instance changes.
- Frontend HTTP200, direct29290 and frontend6392 WebSocket ping/pong/config/catalog passed. CUA verified Chinese extension, one Skill/two Tools. This setup screenshot is not user evidence. The current host configuration retains its disabled test-model placeholder; the agent does not call it or copy user credentials.
- Real installed SDK load/resolve returned two Tool instances and one Skill. **14 invoke/stream calls passed**, now asserting actual init=待支付 in all four inspected fixtures. Normal orderpass/complete12configs11edges; unpaidfail/complete shortest1-event trace; guard dead endfail/complete zero-event trace; domain escapefail/incomplete; max_states1incomplete; unknown/duplicate/confirmation/hash refusals correct; stream equals invoke. Input and installed payload hashes unchanged; **0 socket-connect attempts and0 model requests** during tool invocation tests. Full actual results in host-verification.json.
- Source/canonical/native/installed14-file hashes equal. AllUTF-8; original MIT/header bytes exact; notices/licenses/fixtures unchanged. CLI Chinese help/error and actual Chinese results covered by55 tests. package-verification.json records archive identity and extraction. New native/canonical ZIPs reproduced their unchanged hashes; `check plugins/state-machine-audit`, `pack` and `check-repo` passed (35 source assets,45 release ZIPs, including preserved historical versions).

Native ZIP `plugins/state-machine-audit/test-packages/state-machine-audit-1.0.1-workswarm.zip`: SHA-256 `0846461cbb98e2c08398e65df2f8dffac55c96431d883f22867ffc66e05015cb`.
Canonical ZIP `releases/agent-plugin/state-machine-audit/1.0.1/state-machine-audit-1.0.1.zip`: SHA-256 `9280fb9d391e31136c66f7b088524309e03a257d03ce1a3e833c8bc70e21f212`.

## Manual handoff and gate

MANUAL_TESTING.md supplies current Chinese1.0.1 installation, fixture paths/hashes and two-stage inspect/confirm test prompts. Inspect must explicitly display init; all four bundled valid fixtures use待支付. The initial state must not be inferred from states order. User then confirms the complete model and actual hash before auditing.

Finite user-supplied abstraction only; no actual-source/concurrency/time/probability proof. macOS tested; Linux untested; Windows unsupported. Original1.0.0 confirmation/results remain valid history. AGENTS Phase2 rules4/8 require new1.0.1 manual completion and applicable original screenshots because the payload/version/ZIP changed. Cai Zhenze has now completed1.0.1 testing and supplied five applicable originals showing the repaired init and real audit/refusal results. No remaining blocker. Original task proceeds to GitHub submission; after verified merge it remains Awaiting Acceptance with candidate Planned, lead acceptance Pending Acceptance and completion date blank until Song Haoran accepts. No Hub/Release or Asset Ledger operation.


## Current-main pre-push validation (2026-10-26)

Fast-forwarded only this task branch to main68e231af7fe3a6fdc34c2983fcf19167309ce0aa; AGENTS blob unchanged. Full SDK/Node22 regression on that base plus this plugin: **381 run,380 passed,1 optional historical baseline skipped**. `check`, `pack`, `check-repo` passed:36 source assets/45 release ZIPs after excluding superseded local1.0.0 artifacts. Canonical and native1.0.1 ZIP hashes and all14 payload files remain exactly the user-confirmed bytes. Five original current-version PNGs are readable and hash-verified; no credential/private key found in the images. Delivery review excludes old packages/images, temporary environments, logs, caches and unrelated work.
