# Functional Test Report

Date: 2026-10-22

Asset: `dsh-latex-guard` 1.0.0

Environment: macOS, WorkSwarm Python 3.12/OpenJiuwen installed; host default Node 18.

## Upstream verification

At fixed revision `8046f75141ddcf70a6eae4e61f20525d892e0176`, Node 20 and pnpm 10 were supplied through `npx`. `pnpm install --frozen-lockfile`, `pnpm test`, and `pnpm build` passed. Result: 8 test files and 85 tests passed; the build produced both CLI and DSH plugin bundles.

## Port functional tests

`tests/run_dsh_latex_guard_integration.py` directly instantiated all three delivered native WorkSwarm tools and passed:

- citation audit reported a missing key and an uncited BibTeX entry;
- BibTeX lint found duplicate/missing-field issues, preserved the file in preview mode, and removed the later duplicate only with `write=true`;
- an incomplete BibTeX input refused a write;
- mocked Crossref metadata filled blank author/journal/year fields without writing in preview mode.

## Package/load tests

The WorkSwarm plugin validator passed L0 quality, L1 static validation, and L2 real harness load/bind/invoke/unload after required-input calls were made graceful. It bound one Skill and three Tools. Repository `asset_release.py check` and deterministic pack/unpack verification were also run before handoff.

## Scope correction

The initial test package exposed upstream `latex_check`, but the user correctly observed that it only returned `skipped` on a WorkSwarm host without `latexmk`. A full TeX distribution cannot be made self-contained within this package's portable size/platform constraints. Before merge, `latex_check` and all compile claims were removed. The delivered 1.0.0 scope is the three working BibTeX/citation tools only.

Replacement three-tool WorkSwarm ZIP SHA-256: `a7f580891765a0c29e6a158dcc483e8be2551d0f51f1aeae0621833c0767e4d2`. Canonical market ZIP SHA-256: `8816e3c333a9f29d4f93a0d79617145519c20258720112fe28310e435ab008e8`. The WorkSwarm validator and direct integration suite passed after the removal.

## User host confirmation

On 2026-10-22, the user confirmed that the earlier four-tool WorkSwarm ZIP with SHA-256 `28a11cbe37026d4d21b2a4d575e533fcc90545765907e02bce7f11621080952c` worked for the available operations and that `latex_check` returned `skipped`. That confirmation motivated removal of the nonfunctional compile surface. Because the payload changed, this confirmation does not automatically accept the replacement three-tool ZIP. See `USER_TEST_CONFIRMATION.md`; no screenshot link was supplied.
