# Functional test report — 物理解题审校 1.0.1

Task `AH-20261023-physics-assumption-check`; Candidate `CAND-CLD-250`; owner Cai Zhenze.

Verified 2026-10-23, Asia/Singapore. **Ready for Testing**; user manual testing and original screenshot collection remain pending. Automated verification did not invoke an agent/model or send a paid request.

## Environment and executed checks

- macOS arm64; Python 3.12.14, Pillow 12.2.0, openJiuwen 0.1.19, PyYAML 6.0.3. Interpreter: `/private/tmp/jiuwenswarm-plugin-dev-2hlu8bh8/venv/bin/python`.
- Host source: WorkSwarm snapshot `3ef1de9bf0b4813e2a0e8674dedc499c78e53df2`. Own instance root `/private/tmp/physics-assumption-check-workswarm-20261023`; fresh state and no copied provider credentials. Existing environments are read-only dependencies only.
- `python tests/test_physics_assumption_check.py -v`: **20/20 passed**, no skips, including real SDK Tool invocation and streaming.
- Extract canonical ZIP, set `PHYSICS_PAYLOAD` to its inner payload, then `python -B tests/test_physics_assumption_check.py -v`: **20/20 passed**, no skips.
- `python -B -m unittest discover -s tests -p test_asset_release.py -v`: **18/18 packaging regressions passed**. These are separate from the plugin tests.
- `python -B tools/asset_release.py check plugins/physics-assumption-check` and `pack`: passed. `check-repo`: **14 source assets / 22 release ZIPs** passed structural verification.
- AST/JSON parsing, UTF-8/Chinese content, local Markdown link targets, legal files, safe archive paths, CRC, native/canonical/source payload equality and `git diff --check`: passed.

The standalone CLI returns a single UTF-8 JSON result (exit 0) or Chinese error JSON (exit 2), with clean stderr; `--help` is Chinese. Tool/schema identifiers and original MIT text are intentionally retained. Source/extracted tests exercise Chinese paths and messages, known-color crop geometry, enlarge-only behavior, optional enhancement, alpha preservation, EXIF orientation/metadata removal, byte/pixel budgets, malformed/multiframe/unsupported inputs, invalid parameters, and existing-file/hardlink/symlink refusal. The input bytes remain unchanged. Regressions cover cyclic input links and corrupt EXIF metadata. SDK imports emit pre-existing Pydantic deprecation/info messages; these are not CLI output or plugin failures.

## Package identity and extracted license audit

| Package | Bytes | SHA-256 |
| --- | ---: | --- |
| Canonical `releases/agent-plugin/physics-assumption-check/1.0.1/physics-assumption-check-1.0.1.zip` | 43,156 | `e363550695bda9524f5f1c3e3d6764f35ab36a2111fe5f4d5e7275dd7be5b06f` |
| Native `dist/physics-assumption-check/1.0.1/physics-assumption-check-1.0.1-workswarm.zip` | 41,755 | `9eb25694e42a1c9b952cb32f6c511bd4921a867a2e5f12c31430880077794707` |

All **9 runtime files** are identical across source, canonical inner payload, native ZIP and actual installation. Canonical adds only its marketplace `plugin.yaml` wrapper. The extracted unchanged `licenses/fisica/LICENSE` matches pinned Git blob `91a1890c91bde3c25fabf7c12b9975cf0c9474c5` and SHA-256 `b273a3590e2290ab4e55acdd824bb37f19940cea6c01cfef271c32f2628005d2`. The four reused/adapted text/script paths have matching MIT/attribution coverage in `THIRD_PARTY_NOTICES.md`; no applicable upstream NOTICE exists. No icon, external image/font/data, Pillow binaries, credentials, tests, host state, logs or caches are in the runtime ZIP.

Unpublished 1.0.0 preflight material is archived locally in ignored `dist/`; it is outside the delivery source/release tree. The user-test edition is 1.0.1, which includes the reviewed error-handling fixes. No user confirmation applies to either version yet.

## Actual isolated WorkSwarm integration

URL **http://127.0.0.1:6383/**; own frontend/agent/backend/gateway ports **6383 / 28220 / 29220 / 30220**, listening on loopback. Frontend HTTP 200, direct and frontend-proxied WebSocket ping/pong, `config.get` and `plugin_packages.list` passed after install. Main's existing ports/processes were preserved.

Actual `plugin_packages.import_local` and `plugin_packages.install` WebSocket RPCs imported the native 1.0.1 package. Real installed `find_plugin_manifest → load_plugin_package → resolve_plugin_parts` resolved one Skill and `PhysicsFigureTool`; all installed runtime files matched the confirmed local build bytes before/after testing. Import used actual host RPCs, not an automated native OS file-picker completion.

Installed `invoke` and `stream` transformed the original Chinese-named **800×500** synthetic slope diagram into identical **1600×1000** PNGs with `enhanced=false`, reporting version 1.0.1 and Chinese messages. Input SHA-256 stayed `fffd8543225c782125dbf35a9c45ce6c87edc98e949c0a385a7abd24c4f81edd`; output SHA-256 was `e7b082b2f97a67b7bfa97396c1d7ba1633f2ad094d5a6ff61f7067b1698ee0e2`. Reusing the output returned `output_exists`; damaged input returned `invalid_image`, both in Chinese. Network connection attempts during SDK invocation: **0**. No model/agent invocation occurred.

Chinese Extensions card and details were visually inspected. Plugin/tool display names and descriptions render in Chinese; the Skill retains technical ID `physics-review`. The generated PNG was visually inspected against its source. Diagnostic screenshots and machine results remain under the isolated instance's `runtime/`; they are **AI diagnostics, not user test screenshots**. Reproduction command: `python -B /private/tmp/physics-assumption-check-workswarm-20261023/runtime/test_installed_plugin.py`; it preserves existing outputs on a second run. Exact integration/health results are in that directory's `INTEGRATION_RESULT.md`, `installed-plugin-test-result.json` and `health-result.json`.

## Remaining manual scope

`MANUAL_TESTING.md` provides install steps, exact hashes, original synthetic fixtures, prompts and expected results. The isolated instance needs the user's authorized provider configuration for natural-language/image reasoning tests. No provider credentials were copied and no paid model requests were made. Quality of diagram interpretation, assumption handling, numerical solutions and response behavior remains for manual testing; code/SDK success does not establish those outcomes.

Input scope: static PNG/JPEG, 25 MiB and 20 million pixels; output at most 32 million pixels/64 MiB. No OCR, symbolic solver or numerical simulator is bundled. Interpolation cannot recover missing diagram details. No known blocking code/integration issue remains, but explicit exact-package user completion and genuine original screenshots are still absent, so pushing, opening a delivery PR and merging remain gated. CI has not been run for an unpublished branch. No Hub or GitHub Release action was performed.
