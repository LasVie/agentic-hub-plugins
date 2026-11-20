# Stocktake v1.0.0 test record

Task `AH-20261120-warehouse-stocktake-reconciliation-team`; Windows, 2026-11-20 (Asia/Singapore). All test inputs are synthetic.

- Local behavior gate: `python -B -m unittest discover -s expert-teams/warehouse-stocktake-reconciliation-team/tests -v`. Nine tests initially failed because the stocktake entry point did not exist, then all nine passed after implementation. Covered both timestamp boundaries and mixed UTC offsets, explained/unexplained/no variance, unconfirmed coverage, duplicate movement IDs, mismatched units, missing rows, offset-free timestamps, handoff tampering, changed source and existing outputs.
- Official Agentic Hub CLI 0.0.1 (`c8ee4ef44be0453470114aa5a19f4e1017462907`): `validate <clean-stage>` and `pack <clean-stage> --output <scratch-output>` passed. Both archives were checked against all 19 source files; the dynamic-JavaScript preflight passed on the source and exact archives (zero JavaScript files). `release/1.0.0/artifact.json` records the ZIP and file SHA-256 digests.
- Extracted native ZIP: the four-stage command flow ran against the packaged Chinese example. The audit recorded one explained timing difference, one recount (-2), and one match. This executes shipped code but not agent routing or WorkSwarm UI.
- Root suite on Windows did not pass: 482 tests ran; 172 failures, 95 errors, 65 skipped. The loaded failures are outside this new asset, including existing macOS/Linux-only tooling and Windows path handling. This is not a release gate result.

## User integration testing, 2026-11-20

Nguyen Trung Dung tested the native v1.0.0 package on the Windows WorkSwarm test machine (installed product reports v0.2.8), with English UI and prompts. [Completion confirmation](USER_TEST_CONFIRMATION.md) and [original evidence](evidence/1.0.0/index.json) are retained. The published payload and both ZIPs are unchanged.

1. Full reconciliation: all four tasks in the WorkSwarm plan show completion. The baseline and final cross-check share an assignee avatar distinct from the reconciler's; the panel does not show role names. The saved baseline was written before forward reconciliation. The source and handoff SHA-256 values in the saved audit were matched against the corresponding files, and forward and reverse rows agree. The Chinese delivery reported one timing explanation (甲, only movement `in`), one recount (乙, 13 expected, 11 observed), and one match (丙, omitted from the exception CSV). The verified deliverables were `review.md`, `exceptions.csv`, and `audit.json`.
2. Missing confirmation: the team asked for movement-coverage and boundary clarification; the case output directory remained empty. It did preliminary exploration before asking, which was noted but did not result in an unconfirmed reconciliation report.
3. Unit mismatch: the packaged validation command reported 件 versus 箱 for 甲/A and rejected input. The team wrote diagnostic notes but did not issue a verified reconciliation, exception CSV, or audit.

These are observations of the user's WorkSwarm integration run, not a separate direct invocation of `register_group.py --validate-only`.
