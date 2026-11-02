# User test confirmation — 1.0.1

- Owner / confirming user: **Cai Zhenze**.
- Candidate: **CAND-EXT-004**; task: **AH-20261030-geojson-simplification-lab**.
- Naming: **Mapshaper → 离线地图简化工作台 → geojson-simplification-lab**.
- Internal asset ID: `repo:agent-plugin:geojson-simplification-lab`.
- Confirmation date: **2026-11-02, Asia/Singapore**. Exact message timestamp is unavailable; recorded during this delivery turn. Source: the current Main 2.0 conversation; no message permalink has been invented.

The user explicitly stated:

> I confirm manual testing of **离线地图简化工作台 1.0.1** is complete and passed. Use my attached original screenshots and proceed to Phase 3 under the latest AGENTS.md, keeping it isolated from Main.

This authorizes GitHub delivery of the current tested package. No known blocking issue remains. It does not constitute Project Lead acceptance, permission to publish a GitHub Release, or permission to submit/publish on Agentic Hub.

## Exact package identity

| Package | Retained path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| WorkSwarm native ZIP | `test-packages/geojson-simplification-lab-1.0.1-workswarm.zip` | 6280345 | `32b0bb79a8881d184ea5ad5f01a19357c3c6dfb313fe63dc769795d6f9753e1a` |
| Canonical marketplace ZIP | `../../releases/agent-plugin/geojson-simplification-lab/1.0.1/geojson-simplification-lab-1.0.1.zip` | 6288928 | `5bc7e39e5db5fd92cfc07ad9638fd225f6a4c7cb5b0eaf26c3eaff1d1fa79141` |

Both ZIPs retain the exact tested bytes. All 75 inner payload files match each other and the source directory. Delivery adds only outer records and evidence; no packaged name, instruction, wrapper or runtime changed. Internal 1.0.0 packages remain local historical evidence and are excluded from this delivery.

## Original screenshot evidence

The seven user-provided PNGs are preserved at full original resolution, without cropping, resizing or recompression. See [the originals manifest](evidence/1.0.1/originals.json) for filenames, dimensions, byte counts and SHA-256 values.

| File | Visible evidence |
| --- | --- |
| `user-test-01.png` | WorkSwarm 1.0.1 tool status, startup, safe reuse and final status; actual returned URL. |
| `user-test-02.png` | Adjacent regions at 7%; 206 → 14 vertices, two features, Chinese properties and `id`. |
| `user-test-03.png` | Adjacent regions at 80%; 206 → 168 vertices. |
| `user-test-04.png` | Three-feature input at 4%; 1784 → 80 vertices, explicit loss of one ring/component. |
| `user-test-05.png` | Same larger input at 78%; 1784 → 1423 vertices, ring/component counts retained. |
| `user-test-06.png` | 25-feature input at 5%; 11520 → 668 vertices, explicit loss of four rings/components. |
| `user-test-07.png` | Same 25-feature input at 96%; 11520 → 11047 vertices, 48 rings and 36 components retained. |

Public-repository evidence check: the screenshot contains no account/API credential. Its temporary loopback-only URL was confirmed no longer listening at 2026-11-02 22:34:06 Asia/Singapore (TCP connection refused, errno 61). No request refreshed it and no service was stopped or record changed. The original image remains unmodified.

The screenshots establish the operations visible in them. They do not separately demonstrate every download, rejection, cancellation or re-import step. The user's explicit overall completion statement and the earlier actual engine/runtime/installation/browser evidence are distinct supporting evidence, not interchangeable claims.

Attach these originals in the delivery PR with immutable commit image URLs, verify the image bytes/readability, then save the specific PR evidence-comment permalink in the original task. Lead acceptance remains pending; leave Hub evidence and Asset Ledger unchanged.
