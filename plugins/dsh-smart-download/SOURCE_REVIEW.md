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
