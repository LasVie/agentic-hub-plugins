# Satellite.js source and integration review

- Review date: 2026-11-12 (Asia/Singapore).
- Candidate: `CAND-EXT-014`; original task: `AH-20261112-offline-satellite-orbit-workbench`; confirmed owner: Cai Zhenze.
- Mapping: Satellite.js → **离线卫星轨道工作台** → `offline-satellite-orbit-workbench`.
- Stable pre-catalog identity: `repo:agent-plugin:offline-satellite-orbit-workbench`.
- User approved Phase 2 in this conversation and, on 2026-11-13, explicitly confirmed current-version manual testing passed, supplied five original screenshots and authorized Phase 3 GitHub delivery. No Hub operations are authorized.

## Reviewed reuse route

`mode: ported`; permission is verified for the identified Satellite.js JavaScript implementation. The UI, validation and bounded interval search are asset-specific original integration code. The lifecycle wrapper locally adapts the maintained ownership and navigation checks from this repository’s offline-pipe-network-workbench; it does not change that asset. This is not a blanket relicensing of the repository.

Official upstream: <https://github.com/shashwatak/satellite-js>, npm `satellite.js@7.2.0`, commit `02cd3def8cd7a29ad2342c6382bea7d2098a893c`. The official archive's `gitHead` matches this commit. Archive SHA-256: `eebc66f7d16609a9cd67552facb67fa919cb471adbc6823001348195e912a6d2`.

Use only the unchanged published JavaScript dependency closure for `io.js`, `propagation.js`, `transforms.js` and `propagation/SatRec.js`. Its relative imports permit browser-local use without modifying the engine. Omit the root index's optional WebAssembly exports, all WASM/C++ modules, other astronomical functions, cloud/catalog services, upstream development tooling, third-party images/fonts and unrelated test collections. No runtime npm dependency is required.

The pinned root MIT text names **Shashwat Kandadai, UCSC Jack Baskin School of Engineering**. The pinned README identifies the implementation as MIT and as derived from Brandon Rhodes's Python SGP4 and the original Vallado/Crawford/Hujsak/Kelso C++ work. Preserve the complete upstream MIT, Brandon Rhodes MIT, original package information, and applicable Vallado/CelesTrak attribution and permission evidence. The CelesTrak NOTICE at `49df0479c950917c0a2c5ac31f2db6477bba57f6` explicitly retains unrestricted terms for the original C++ SGP4; its other AGPL implementations do not enter this package. Original headers must remain intact. The older Satellite.js 6.0.2 README contained conflicting unmarked-file language; that version is not used.

Licensing references:

- <https://github.com/shashwatak/satellite-js/blob/02cd3def8cd7a29ad2342c6382bea7d2098a893c/LICENSE.md>
- <https://github.com/shashwatak/satellite-js/blob/02cd3def8cd7a29ad2342c6382bea7d2098a893c/README.md>
- <https://github.com/brandon-rhodes/python-sgp4/blob/9442470d5a286b4071ac105fbfe5173ef2b33ab7/LICENSE>
- <https://github.com/CelesTrak/fundamentals-of-astrodynamics/blob/49df0479c950917c0a2c5ac31f2db6477bba57f6/NOTICE>

## Functional distinction and baseline

The existing `offline-observing-planner@1.0.0`, task `AH-20261030-offline-observing-planner` / PR 69, models the Sun, Moon and five planets and explicitly excludes satellites. Generic scientific visualization plots supplied data; it does not provide this orbital propagator. Read-only Phase 1 inspection found Astropy 7.0.0/TEME transforms in the developer shell but no SGP4/Skyfield/PyEphem/orbit-predictor. Astropy's satellite documentation calls for a separate SGP4 implementation. That inventory is not a current running-host A/B conversation and is not presented as universal absence.

The added capability is actual orbital-element → SGP4/SDP4 numerical propagation → observer geometry, with editable inputs and exportable computed results. A model's theoretical ability to implement a replacement is not counted as an installed baseline capability.

## Supported integration and authority

The existing native Plugin package/Tool/ToolCard/Skill interfaces are the only host integration. The plugin owns its loopback static-file server, workspace runtime record and browser worker. It neither rewrites nor monkey-patches host/core/frontend/backend/SDK/dependencies or other plugins. A foreign or malformed runtime record is preserved and rejected; test workspaces are dedicated to this installation. Browser links must be the actual tool-returned URL, with normal same-machine navigation supported.

WorkSwarm 0.2.8 source `fa91394e42a7af731424222db82b02351e694de9` exposes native package installation and public plugin loading. Actual current-package installation, SDK invocation and browser results must be recorded in `TEST_REPORT.md`; source inspection alone does not establish running-host dispatch. No paid/model call is authorized. No other chat's service may be stopped or occupied port reused.

## Numerical and safety boundaries

SGP4 results use TEME coordinates in kilometres and kilometres/second. Observer transforms are geometric; height is not pressure, elevation is not optical visibility and threshold intervals are not a collision/navigation/flight-safety product. The time window is at most 24 hours and remains within seven days of the element epoch. Old elements carry explicit age limitations. Finite time sampling can miss grazing intervals; boundary-refined crossings and clipped-window labels must not imply an exhaustive visible-pass guarantee.

Independent primary reference: <https://celestrak.org/publications/AIAA/2006-6753/>. Its archive SHA-256 `3642043b706c76be87cf012db3f22e04da6b80498d00f515e51879e0ffadc115` contains the satellite 00005 TLE and TEME reference vectors in `sgp4/for/tforverf.out` and `sgp4/cpp/testsgp4/TestSGP4/00005.e`. Position/velocity agreement verifies the implementation against those reference cases, not physical prediction accuracy.

## Delivery audit

Final module/license maps are in `web/vendor/satellite-js/UPSTREAM.json` and `provenance.json`; all 16 modules match the official archive byte for byte. The two CelesTrak legal-text filenames retain the same full official NOTICE grant verbatim, with the naming explanation in THIRD_PARTY_NOTICES.md. No restricted implementation from that repository is bundled.

Both final Chinese ZIPs have identical 36-file payloads; extraction/path/CRC/version/UTF-8/legal hashes passed. Exact native SHA-256 `d554e61da463cfbf6124d776190aafbf407dc8a941396029d5e4c5a7cdb16710`; canonical SHA-256 `3527dcede1c53acb0e556ba9520fb5f22d95f80a4d9be7b43d7d30fe0c923e60`. Exact payload and both ZIP preflights scan 20 scripts with zero known dynamic-execution signatures. The unmodified JavaScript route requires no dynamic-code deletion, obfuscation, WASM loader or dependency patch. Local preflight is not Hub acceptance.

Actual tests and honest limits are in TEST_REPORT.md: 25 engine + six presentation + 11 lifecycle tests passed; exact package imported in isolated WorkSwarm 0.2.5.beta1 and loaded by SDK 0.1.19 and current 0.1.20. Chrome compute/edit/error recovery/actual exports passed. Full WorkSwarm 0.2.8 remains unresolved due to its separate native Swift dependency build failure; no host/dependency modifications were made. The 2026-11-13 original user chat evidence verifies running-chat status/start/reuse/status for version 1.0.0; the user explicitly confirmed manual completion and supplied four original workbench views plus that chat image. Exact package identities are unchanged. See TEST_REPORT.md and evidence/user-testing-1.0.0/originals.json. All required distribution notices are fulfilled; no unresolved source-license condition blocks GitHub handoff. Full fresh WorkSwarm 0.2.8 remains an unverified compatibility limitation, not a claimed test pass. Song Haoran acceptance and Hub operations remain separate.
