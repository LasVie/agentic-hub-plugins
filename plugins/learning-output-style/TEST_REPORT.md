# Learning Output Style 1.0.1 validation

Date: 2026-10-22. Task: `AH-20261022-learning-output-style`. Owner: Gan Mingrui.

## Environment and commands

- Package checks: Python 3.12.14, PyYAML 6.0.3, current `tools/asset_release.py` Git blob `4578aa751424aeddb452646631d76e8694be8265` (matches current remote main).
- Native loader: Python 3.11.17, PyYAML 6.0.3, pydantic 2.12.5, local openJiuwen checkout commit `c6c24c44af424a13fa630ff3b64dc407dd9acc1f`. Loader file SHA-256 `6be28814009ad0a0b54e99bcb98d92facf7ab817848329052d70f302a2224875`.
- `python tools/asset_release.py check plugins/learning-output-style`: passed for 1.0.1.
- `python tests/validate_learning_output_style.py plugins/learning-output-style/learning-output-style`: eight checks passed against the actual openJiuwen loader. The first test harness assertion treated localized prompt content as a string; it was corrected to assert both `cn` and `en` content. No payload change was needed.

## Native loader results

The actual loader accepts the manifest, normalizes the Skill path inside the package, loads the prompt at priority 100, and preserves the original teaching text after its attribution notice. It rejects a missing prompt, missing Skill file, wrong package type, and a prompt path escaping the package. Full license copies match and no executable upstream hook ships.

## Archive and host import results

- `python tools/asset_release.py pack plugins/learning-output-style`: passed. Marketplace ZIP SHA-256: `065afa71ff915c2d9ab494046e64edd2d47b1e7470f332bd8339922c0a1fc47d` (40,986 bytes).
- The marketplace wrapper and every extracted payload file match `artifact.json`; both archives pass their CRC checks, contain no runtime caches/hidden files/unused upstream hooks, and include the required notices and exact full license text.
- Native test transport SHA-256: `ae36a586495e015b028dda8e35c5a04af4854bc9cf4e05f174b27cadb7a031a9` (39,691 bytes). Every payload file hash equals the corresponding inner marketplace file hash.
- The same eight native-loader checks passed again on the final extracted marketplace payload, including all four rejection cases.
- `python tests/learning_output_style_host_smoke.py <JiuwenSwarm checkout> <native-test.zip> --output <result.json>`: four lifecycle checks passed using the real JiuwenSwarm package manager: import, install/state lookup, installed prompt/Skill loading, and uninstall/state removal. All changes occurred in a temporary data directory; the user's active installation was untouched. The first attempt lacked the host's `ruamel.yaml` dependency; ruamel.yaml 0.19.1 was supplied in an isolated temporary test dependency directory and the rerun passed. This is a host test dependency, not a bundled Plugin dependency.

`package-verification.json` records the complete payload inventories and machine-readable results. The JiuwenSwarm local importer only searches a root or one child for manifest.json, so the native test transport is supplied for its file-upload UI. The later Hub upload uses the marketplace archive, whose inner payload is identical. Both archives were produced before requesting current-version user confirmation; no archive or payload may be changed afterward without renewed testing.

## User-test boundary

Gan Mingrui's explicit test confirmation covers only the original 1.0.0 ZIP (`7e119eb95893e2a379c100d69f349a619a342c44dcf658c9ca80124020e96631`). It does not cover this changed 1.0.1 package. Automated package/loader checks do not establish live model behavior, successful end-user testing, or Hub approval. Gan Mingrui subsequently confirmed 1.0.1 testing complete and submission authorized in the current conversation on 2026-10-22; see USER_TEST_CONFIRMATION.md and report RPT-20261022-learning-output-style-user-confirmed. A real original test PNG was supplied. It is a limited visible example, not proof of every behavioral scenario. Hub evidence and final Project Lead acceptance remain pending.
