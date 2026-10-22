# Source and Duplicate Review

## Task and capability difference

- Task: `AH-20261022-dsh-smart-download`
- Candidate: `CAND-DSH-139`
- Related assets: cue-omni-reader Skill `4ec90e5a10e4419a8f97766613b9d57f`, cue-omni-reader Connector `d9665968537247718932825ef3417b25`, and Baidu Netdisk Connector `5806cbee80c4460584e65308217abfe8`.
- Difference: cue-omni-reader extracts readable content from URLs and Baidu Netdisk manages one cloud service. Neither provides general HTTP(S) file transfer with range acceleration, conservative resume and SHA-256 verification. This is a new Plugin capability.

## Source and permission evidence

| Used material/path | Pinned upstream | License and scope | Packaged evidence | Reuse/modification |
| --- | --- | --- | --- | --- |
| Download probing, range-worker selection, status concepts and user-facing behavior | https://github.com/LeiSureYu/dsh-smart-download at `e80a6574407fed44a8ad6efde3a789bce119beeb`, tag `v1.4.6` | Root MIT license covers the repository software; copyright is `Copyright (c) 2026 dsh-smart-dl contributors` | `dsh-smart-download/licenses/dsh-smart-download/LICENSE`, SHA-256 `ac0fc870e1cf8671b5beb57e0a58a11b2514076c867318e98b0d2c03db0389e6` | Ported and substantially modified. Replaced DSH/Cordis UI and Node subprocess design with OpenJiuwen Python tools. |
| Optional aria2 platform npm packages | Declared by upstream package 1.4.6 | Separately packaged binary dependencies; not copied or distributed | Not applicable | Excluded. The port uses Python standard-library HTTP workers. |
| Upstream UI, icons and screenshots | Same source | No need to determine separate asset rights because none are copied | Not applicable | Excluded. |
| Runtime dependencies | Python standard library and host `openjiuwen` tool API | Host/runtime dependencies are not redistributed in the ZIP | Manifest/tool imports | No vendored dependencies. |

The exact npm 1.4.6 manifest was also checked. Its integrity is `sha512-cx+eHrJbpr9rgbFPl9eo6T7QYlnSwy5jVVH8lxHP859oN9/Tyn5p9Tl7/m0MGq0K5ibkK265Fl5YMxJPrFGPfA==`. The Git tag and npm version agree.

## Compatibility decision

The original Cordis web client and DSH session/UI injections are not directly compatible with WorkSwarm. The adapted payload is compatible as a native Agent Plugin because it exposes explicit OpenJiuwen tools and has no connector, background service, Node.js runtime or bundled executable. Network policy still applies, and acceleration depends on correct remote HTTP Range behavior.

## Final ZIP license review

- Original attribution and modified-file notice: header in `tools/smart_download.py`, plus `THIRD_PARTY_NOTICES.md`.
- Third-party summary: `dsh-smart-download/THIRD_PARTY_NOTICES.md` covers the single upstream.
- Full MIT text: `dsh-smart-download/licenses/dsh-smart-download/LICENSE`, byte-identical to the pinned upstream root license.
- Upstream NOTICE: none at pinned revision.
- Apache modification notices: not applicable.
- Brand assets, datasets and service credentials: none included. Remote HTTP service terms remain the user's responsibility.
- Final unpacked ZIP check: `dsh-smart-download-1.0.0.zip` contains seven expected runtime/market files and no development files. ZIP SHA-256 is `77873887154682d3419ed68d95e3d0269aa21ec27237735882b07c794ba2aa0d`. Streaming the packaged license produced SHA-256 `ac0fc870e1cf8671b5beb57e0a58a11b2514076c867318e98b0d2c03db0389e6`, matching `provenance.json` and upstream exactly.
- Conclusion: `ported`; permission status `verified` for the included material. No unresolved licensed material is included.


## Chinese runtime edition 1.0.1 (2026-10-22)

The Project Lead requested Chinese editions of all assets currently in the repository, including the newly merged dsh-smart-download 1.0.0 from main 49acfa795cb6964f06a16cd30594efb7055272d0. Reuse original task AH-20261022-dsh-smart-download and candidate CAND-DSH-139; preserve owner Siu Lok Yin, publisher and upstream copyright. The historical 1.0.0 confirmation, release ZIP and evidence remain unchanged and do not confirm these new bytes.

Modified payload paths: README.md, skills/smart-download/SKILL.md, manifest.json and tools/smart_download.py, plus an appended Chinese summary in THIRD_PARTY_NOTICES.md. Localized actual Skill/default outputs, tool descriptions, metadata and human-readable errors. Machine names/parameters, HTTP headers/protocol values, error codes, task states, range-worker/resume/checksum/output algorithms are retained. A dedicated internal checksum exception replaces the old English-message substring match so localization cannot change CHECKSUM_MISMATCH classification. URL status formatting now hides rejected URL user credentials and handles malformed URLs inside the structured error path; real integration covers both. The original JSON metadata helper also changed an existing user-selected output directory to mode 0700; directory chmod is now restricted to the plugin-owned status directory. A regression test preserves an existing output-directory mode 0750 while verifying status file mode 0600 and status-directory mode 0700. No new upstream implementation or runtime dependency is introduced. All changed ported paths stay covered by the same fixed MIT source and prominent dated changes; full original MIT bytes and copyright remain unchanged.

The final marketplace/native packages are unpacked and checked against the source payload, license SHA-256 and each other; final hashes are recorded in artifact.json/package.json outside the runtime payload. Source and final extracted payload functional tests use the actual installed OpenJiuwen SDK and a real local HTTP server, covering Chinese errors, correct checksum classification, private-network rejection, 4-worker download, single-stream fallback, forced-interruption resume, existing-output protection, malformed URLs and status credential redaction. Separate actual WorkSwarm import/prompt screenshots and final user/lead decisions are recorded by the coordinating agent; this note does not assert they have occurred.


## Final delegated desktop evidence (2026-10-22)

The coordinating agent performed actual native desktop import and model-driven tool tests for the unchanged 1.0.1 ZIPs under the user's explicit delegation. Independent verification compared all six installed payload files to source and both final packages, checked the 89-byte downloaded fixture and verified the rejected private-network target is absent. These observations supplement the automated checks above and do not imply human-performed current-version confirmation, final acceptance, PR merge or any Hub operation. Original full-resolution screenshot bytes remain local pending actual PR attachment. No payload, full license text or ZIP byte changed in this evidence-only update. Under latest AGENTS.md blob 77f1082183ed59b3f60271106c06db2d08e445ad, Asset Ledger remains unchanged without successful Hub submission evidence.
