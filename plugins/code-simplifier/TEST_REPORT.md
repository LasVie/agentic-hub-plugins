# Code Simplifier 1.0.1 test report

Date: 2026-10-22 (Asia/Singapore). Owner: Cai Zhenze.
Task AH-20261022-code-simplifier; candidate CAND-ANT-026.

## Validation actually performed

- `python tools/asset_release.py check plugins/code-simplifier`: passed.
- `smoke_load.py <native-zip>` with the actual openJiuwen loader/resolver and
  JiuwenSwarm package manager: **4 passed**. The tests exercise relocated native
  import layout/manifest/README recognition, resolution of one mode-all skill,
  frontmatter discovery in the host ability card, and rejection of a missing
  declared skill directory. See FUNCTIONAL_TEST.log.
- No plugin tools, MCPs, rails or subagents are resolved.
- Original skill bytes preserved: ed4dc434de1fd7c67cd244213a9d590064f245e4e169a58bf53e6eeb48e407b1.
- Full archive integrity, wrapper/manifest identities and all declared paths checked.
- Every inner payload file hash matches the native test archive: 6 files.
- Full Apache-2.0 copies at both declared paths verified; notices/change history reviewed.
- Deterministic repository pack and post-extraction checks are recorded in RELEASE_TEST.log.

Environment: macOS; packaging Python 3.9.6 and PyYAML;
loader smoke Python 3.12.14 from `.runtime/workswarm-venv`. Explicit PYTHONPATH
selected local `/Users/lasvie/Documents/openJiuwen/openJiuwen_OpenCLI/agent-core`
and the JiuwenSwarm checkout. Runtime data/home were isolated under
`/private/tmp/code-simplifier-runtime-audit`. No active profile installation or model
call occurred. No external service or credential was required by the Plugin.

Command for the loader check (from repository root, with the above PythonPATH,
PYTHONDONTWRITEBYTECODE=1 and isolated JIUWENSWARM_DATA_DIR/JIUWENSWARM_HOME):
`../.runtime/workswarm-venv/bin/python plugins/code-simplifier/smoke_load.py
../outputs/code-simplifier/1.0.1/code-simplifier-1.0.1-native.zip`.

An initial exploratory probe accessed a nonexistent PluginSpec.version attribute;
that probe was corrected. The final tests read version from manifest.json and
all four completed successfully. This was a test-probe error, not a package defect.

## Package identity

Marketplace ZIP SHA-256: `b1761a8781c23347c355f44dee9ba322c01a6e0be494deb69ad279ed3198039a`.
Native local-test ZIP SHA-256: `001186450f4ef90d683e163f91831e5bfd662be9a81dbf7caf3322316e0fac65`.
The archive layouts differ; all inner payload hashes are identical.

## User testing still required

Status: Ready for Testing. Use TESTING.md. The package has not been installed in
an interactive host UI here, and no model-generated edit/behavior equivalence test
is claimed. The current local importer recognizes only root or one-level manifests;
use the native ZIP for local Create from file. Existing plugin-ID conflicts require
the host's normal replacement/clean-profile flow.

This is a packaging/attribution change, versioned from the supplied 1.0.0 input.
User confirmation for that old archive does not confirm the new hashes. The user
accepted the known overlap for local testing; Already Covered is retained. No push,
PR, merge, Hub submission, publication or final acceptance occurred.
