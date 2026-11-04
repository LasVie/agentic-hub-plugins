# Actual WorkSwarm GUI test — 网页 3D 模型瘦身台 1.0.5

- Task: AH-20261102-web3d-asset-lab; Candidate: CAND-EXT-010; owner: Song Haoran.
- Test type: **Agent-operated actual desktop UI under explicit user delegation**. Song Haoran did not personally perform this test; Project Lead acceptance is not inferred.
- Actual session: 2026-11-04 15:30–15:43 Asia/Singapore, task `web_1a1a5770b5f_e53a4b63b88d`, model `gpt-6.1-sol`.
- Current GUI host: **WorkSwarm 0.2.8 / Python 3.12.13 / Node 22.12.0**, macOS. The workbench ran in WorkSwarm's native internal BrowserWindow, **not Safari**. Earlier isolated SDK and 1.0.4 environments remain historical.
- Canonical ZIP SHA-256: `bfa66c5faa59cf88127633e94137de808b16c521a15a196e41ee0fb539384c0a` (1,861,915 bytes).
- Native ZIP SHA-256: `1dafe82986d6cda8b328b463b70b2dcbb01b9fbd16c4b208b2e0c5a02d935cce` (373,986 bytes).

## Actual results

The root Agent imported/installed the exact native ZIP in the actual open WorkSwarm app. All 27 installed runtime files were independently read and matched source, both ZIPs and artifact payload hashes; there were no extra/missing files. Native `web3d_asset_lab_workbench` status returned version 1.0.5/running false, then confirmed start returned the real loopback URL. The Chinese page visibly showed v1.0.5.

The actual demo rendered in Three.js. The root operated both model views, executed geometry optimization and inspected both canvases: 6,114,024 → 383,548 bytes, 16 meshes → 1 and 16 scene nodes retained. It used the native Save panel to export the real geometry GLB before the texture operation.

The root explicitly clicked the lossy color-texture button. The saved final model was 5,456 bytes, with one 128×128 color texture (the original fixture had sixteen 512×512 textures). Both model canvases rendered. Final saved texture data was 2,976 bytes; original bytes remained unchanged. This is an actual fixture result, not a compression guarantee or lossless claim.

The root exported the final GLB and report through actual native Save panels. Independent readback confirmed downloaded final GLB/report were exactly equal to saved workspace files. Three actual GUI GLBs—original, geometry-optimized download and texture-resized download—passed gltf-validator 2.0.0-dev.3.10 with **zero errors, warnings and infos** each. Original SHA-256 remained `5ecb9ead652de1cd9cc52fe569b2dcb3126b69fac50c89969228eb9260555779`.

The second native tool `web3d_asset_lab_operate`, operation=load, arguments={}, confirmed=true, returned actual ok/version1.0.5 and the same bounded 6,114,024 → 5,456-byte, 16 → 1 mesh, 16 → 16 node summary. It did not regenerate the fixture or overwrite the result.

The root clicked restore, stopped/restarted only this installation's own service in the same workspace, opened the actual new URL and visually verified restored rendered results. The native restart reply itself explicitly stopped short of claiming persistence before this independent workbench check; the separate restored-workbench screenshot and saved/downloaded hashes establish that check. Final native stop succeeded; independent port probes confirmed both 53610 and 53972 closed.

## Original evidence and actual file results

- Full raw GUI session: [gui-test-session.json](evidence/1.0.5/gui-test-session.json).
- Installed 27-file comparison: [installed-byte-verification.json](evidence/1.0.5/installed-byte-verification.json).
- Actual saved/downloaded bytes and report: [gui-export-verification.json](evidence/1.0.5/gui-export-verification.json).
- Three actual validator reports: [index](evidence/1.0.5/actual-gui-validator/actual-gui-glb-validation-index.json).
- Original image manifest: [originals.json](evidence/1.0.5/originals.json), **16 unchanged originals** (15 JPEG screenshots plus one native WorkSwarm PNG long image), 9,414,087 bytes total.
- Primary native prompt/result image: [2250×8319 original PNG](evidence/1.0.5/images/jiuwenswarm-share-20261104-154347.png), 1,287,815 bytes, SHA `b214d40ea617bb864bc6e3bd1383532a03669071e1435f7c03e011a2b637da09`.
- Primary workbench originals: [geometry](evidence/1.0.5/images/workbench-geometry-original.jpg), [explicit lossy texture](evidence/1.0.5/images/workbench-texture-original.jpg), [post-restart restored rendering](evidence/1.0.5/images/workbench-restarted-restored-original.jpg).
- Independent evidence readback: [audit](evidence/1.0.5/independent-gui-evidence-audit.json). No cropping, resizing, redrawing or recompression was used for repository copies.

## Limits

The GUI demo contains no animation; separate automated animated-fixture validation proves stored data preservation, not playback. No arbitrary model, unsupported extension, other OS or fixed compression guarantee is claimed. Host-native file chooser labels and some underlying diagnostics remain English. The local GUI pass does not establish GitHub CI, PR merge, Hub compatibility or platform approval. The old 1.0.4 rejection and test history remain valid history.
