# Functional Test Report

Date: 2026-10-22

Asset: `dsh-latex-guard` 1.0.0

Environment: macOS, WorkSwarm Python 3.12/OpenJiuwen installed; host default Node 18; no `latexmk` on PATH.

## Upstream verification

At fixed revision `8046f75141ddcf70a6eae4e61f20525d892e0176`, Node 20 and pnpm 10 were supplied through `npx`. `pnpm install --frozen-lockfile`, `pnpm test`, and `pnpm build` passed. Result: 8 test files and 85 tests passed; the build produced both CLI and DSH plugin bundles.

## Port functional tests

`tests/run_dsh_latex_guard_integration.py` directly instantiated all four native WorkSwarm tools and passed:

- citation audit reported a missing key and an uncited BibTeX entry;
- BibTeX lint found duplicate/missing-field issues, preserved the file in preview mode, and removed the later duplicate only with `write=true`;
- an incomplete BibTeX input refused a write;
- mocked Crossref metadata filled blank author/journal/year fields without writing in preview mode;
- LaTeX check produced an honest `skipped` result with a citation audit when `latexmk` was absent;
- project-directory traversal was rejected;
- a mocked `latexmk` failure parsed an error and source line.

## Package/load tests

The WorkSwarm plugin validator passed L0 quality, L1 static validation, and L2 real harness load/bind/invoke/unload after required-input calls were made graceful. It bound one Skill and four Tools. Repository `asset_release.py check` and deterministic pack/unpack verification were also run before handoff.

## Known limitation

This machine has no LaTeX distribution, so a real TeX engine compilation could not be demonstrated locally. The actual subprocess path is covered by upstream tests and the port's mocked failure-path test. User acceptance should test `latex_check` on a WorkSwarm host with `latexmk` installed if real compilation is required.

## User host confirmation

On 2026-10-22, the user confirmed that the exact WorkSwarm ZIP with SHA-256 `28a11cbe37026d4d21b2a4d575e533fcc90545765907e02bce7f11621080952c` worked in their host test. They reported that the final `latex_check` test returned `status: skipped` because `latexmk` was unavailable. This is the expected graceful-degradation result and is not recorded as a successful LaTeX compilation. See `USER_TEST_CONFIRMATION.md`; no screenshot link was supplied.
