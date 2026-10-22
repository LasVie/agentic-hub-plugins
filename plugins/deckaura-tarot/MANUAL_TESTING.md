# Testing and local import — Deckaura Tarot 1.0.2

Candidate `CAND-CLD-140`; task `AH-20261022-deckaura-tarot`; owner Cai Zhenze. On 2026-10-22, the user explicitly confirmed testing complete for unchanged version 1.0.2 and authorized Phase 3 in the current conversation; the exact time is unavailable. The task is `Submitting` and the candidate remains `Planned`. These instructions support reproducing the tests and do not claim a PR merge, Hub submission/publication or final acceptance.

## Package identity

- Canonical Hub ZIP: `releases/agent-plugin/deckaura-tarot/1.0.2/deckaura-tarot-1.0.2.zip`.
- Canonical SHA-256: `b98f0bf8a1284f8671445339c61137719662b3a4df1686c5e0fbcc5778f2aeb4`.
- Generated WorkSwarm companion: `deckaura-tarot-1.0.2-workswarm.zip`.
- Companion SHA-256: `8c8fd7ccc0316e341071b9f88ef8b36a8af7cad12ae67b4714bd88e1b21f8ee7`.

All 13 runtime files are byte-identical across source, both archives and the tested installed copy. The canonical ZIP has the required market wrapper. The tested WorkSwarm importer accepts a root or single-directory manifest, so it uses the generated companion. The companion and its generated metadata are local testing outputs; only the canonical ZIP is a release artifact.

## Prerequisites

Use Node.js >=18 on `PATH` and a compatible openJiuwen/WorkSwarm Python environment. Recorded tests used Node.js 22.23.3, Python 3.12.14, openJiuwen 0.1.19 and PyYAML 6.0.3 on macOS arm64. PyYAML is needed by the repository packaging tool; the plugin itself requires only Node built-ins, Python's standard library and the host's `Tool`/`ToolCard` API. No runtime npm installation, credentials or model calls are required for the checks below.

## Reproduce packaging and functional tests

Run from the repository root with the compatible Python environment active:

```sh
python tools/asset_release.py check plugins/deckaura-tarot
python tools/asset_release.py pack plugins/deckaura-tarot
python plugins/deckaura-tarot/build_local_test_package.py
tarot_extract_dir="$(mktemp -d)"
python -m zipfile -e releases/agent-plugin/deckaura-tarot/1.0.2/deckaura-tarot-1.0.2.zip "$tarot_extract_dir"
DECKAURA_PAYLOAD="$tarot_extract_dir/deckaura-tarot/deckaura-tarot" \
  python -B tests/test_deckaura_tarot.py
```

The helper writes `plugins/deckaura-tarot/local-testing/1.0.2/deckaura-tarot-1.0.2-workswarm.zip` and its hash inventory. Both builders refuse to replace different bytes under the same version. Any change to the confirmed source payload, packaging or final ZIP requires a new version/package and renewed manual-test completion confirmation. Outside-payload documentation changes do not invalidate an unchanged confirmed ZIP.

Expected functional result: 26 passing tests with zero skipped. They exercise the actual native host Tool API and Node CLI, including data validation, lookup, all six spreads, deterministic and full-deck draws, invalid inputs, async invocation/streaming and relocation. Environments without SDK/Node explicitly skip this suite; a skipped suite does not verify functionality. `FUNCTIONAL_TEST.log` preserves the recorded passing run, and `TEST_REPORT.md` separates package, functional, website and user-testing evidence.

## Upload through WorkSwarm Extensions

Start an isolated local WorkSwarm instance using that host revision's startup instructions, separate frontend/backend ports and a separate data/workspace directory. Ensure the backend inherits the Node executable on `PATH`. Preserve existing services and keep paid model calls disabled unless separately authorized.

1. Open Extensions > My Extensions > Create > Create from file.
2. Select the generated `deckaura-tarot-1.0.2-workswarm.zip` from the `local-testing/1.0.2/` directory above.
3. Confirm the native file selection, then click Confirm in WorkSwarm.
4. Open Deckaura Tarot and verify the description, tags, `tarot-reading` Skill and Deckaura Tarot tool. Install it if offered, then attach it to the intended Agent session.
5. If an existing installation blocks the same ID, inspect that installed copy or uninstall only Deckaura Tarot in the isolated instance before re-importing.

The recorded automated checks exercised the browser dialog and native picker request, but could not complete native macOS file selection. The actual backend import/install and displayed installed card/details passed. This limitation is separate from the user's subsequent explicit manual-test completion confirmation. A local import is not an Agentic Hub submission.

The task-specific instance was launched at `http://127.0.0.1:6283/`, with backend WebSocket `ws://127.0.0.1:29110/ws`, agent port 28110 and gateway port 30110, from JiuwenSwarm snapshot `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`. Those addresses identify the original local environment, not portable dependencies or a promise that the services remain running. Existing services and original JiuwenSwarm source were preserved. Its model endpoint was disabled at `127.0.0.1:9`, and no paid model calls were made. The prior 6173 frontend log showed backend-29000 refusal/disconnection; backend unavailability explains the observed WebSocket/config failures, while the earlier launcher's termination cause remains unknown.

## Model-free examples

From the repository root:

```sh
node plugins/deckaura-tarot/deckaura-tarot/skills/tarot-reading/scripts/tarot.mjs validate
node plugins/deckaura-tarot/deckaura-tarot/skills/tarot-reading/scripts/tarot.mjs lookup "The Star" --orientation reversed
node plugins/deckaura-tarot/deckaura-tarot/skills/tarot-reading/scripts/tarot.mjs spread three-card --seed project-demo --reversals true
```

Expected: validation reports 78 cards and dataset SHA-256 `4b47fc22b3220a23a5d9ac06065698315de338a2265fe5491f6fdaa0f0c447c9`; lookup returns The Star's reversed meaning and exact guide URL; the seeded spread returns Justice upright, King of Wands upright and Strength reversed. Repeating the same seed/options yields the same cards, positions and orientations. These CLI checks do not by themselves prove the host UI invoked the tool; the portable Python suite tests the native adapter separately.

To invoke the installed `deckaura_tarot` tool through a host that supports direct tool execution, use:

```json
{"action":"lookup","card":"The Star","orientation":"reversed"}
{"action":"spread","spread":"three-card","seed":"project-demo","reversals":true}
{"action":"draw","count":79}
```

The first two requests should succeed; count 79 must return `ok: false` with an `invalid_input` error. An unknown card also returns a structured error. Do not put private questions in seeds. Conversational interpretation requires separate model configuration/authorization and was not exercised by the automated tests. Tarot output is reflective material, not factual prediction or professional advice.

## Confirmation and delivery evidence

The original user screenshot SHA-256 is `d2561650a539ad64f7825fd51b1a4487e214b9a14eee17fa9d3e6b5a17c0dc2d`. Its result matches the `project-demo` example above. It does not display a version or independently prove backend invocation; association with 1.0.2 is corroborated by the user's declaration and verified installed-payload hashes. `TEST_REPORT.md` records this distinction.

The existing explicit completion confirmation authorizes Phase 3 for the unchanged canonical hash above; it need not be requested again. Attach the original test screenshot to the delivery PR and record its verified evidence permalink in the tracker. Actual Hub-submission evidence and Song Haoran's final acceptance remain separate delivery requirements. Preserve historical local evidence outside the delivery tree and record actual PR/Hub results only after they occur.

## Current submission boundary

The user subsequently limited authorization to pushing the reviewed source and unchanged canonical ZIP and opening the delivery PR. Stop at that PR handoff. Merging, creating a Release, and uploading/submitting/publishing to Agentic Hub require a new explicit user authorization. Earlier Phase 3 authorization does not override this latest boundary.
