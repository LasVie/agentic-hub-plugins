# Reproduce: 网页 3D 模型瘦身台 1.0.5

The following actual flow was completed by the root Agent under user delegation on 2026-11-04, WorkSwarm0.2.8/Python3.12.13/Node22.12.0. See GUI_TEST_REPORT.md for the factual result and evidence. These instructions do not claim a personal human test.

1. Import the exact native ZIP and verify the package-verification.json SHA. Install/enable this plugin and confirm 1.0.5. Use a fresh existing dedicated workspace; the actual run used gui-workspace-1.0.5.
2. In a new task request the named workbench; observe actual web3d_asset_lab_workbench status/start confirmed=true and its returned version/url. Open the actual link in the host's internal BrowserWindow.
3. Load demo, rotate/zoom both actual model views, execute optimization and export the geometry GLB before changing textures.
4. Explicitly choose lossy color-texture resize. Compare real views and dimensions, export final optimized GLB/report via native Save panels. The real sample measured 6,114,024→383,548→5,456 bytes; these are fixture results, not promised ratios.
5. Read current data with actual web3d_asset_lab_operate load. Restore/reopen the same installation and verify saved files and model rendering. Stop only the plugin's own service after evidence collection.
6. Compare real browser downloads with saved files; validate original/geometry/resized GLBs. Preserve unedited originals with version/hash association. No animation playback, other OS or arbitrary extension guarantee is inferred.

The UI offers optimized-GLB and report exports. The original stays in the dedicated workspace and is available through the controlled download endpoint, without a separate original-export button.

---

# Historical 1.0.4 reproduction record (original text preserved below)

# Reproduce: 网页 3D 模型瘦身台 1.0.4

1. Install the native companion ZIP through WorkSwarm Extensions; verify its hash. The canonical Hub wrapper and native ZIP have identical inner runtime files.
2. Enable this plugin in a task, choose an existing dedicated local workspace and ask WorkSwarm to open 网页 3D 模型瘦身台. Use its actual returned loopback URL.
3. Exercise the following flow, inspect actual outputs, close/reopen the same installation and verify saved data. Sample data does not represent a user's production project.

The installed Three.js UI rendered both actual models. Geometry/resource deduplication reduced the self-generated GLB from 6,114,024 to 383,548 bytes (16 meshes -> 1, 16 scene nodes retained). An explicit lossy color-texture resize reduced 512x512 to 128x128, yielding 5,456 bytes; the original remains. Both original and final exported GLBs passed gltf-validator with zero errors and zero warnings. Initial loading now disables operations to prevent stale load/operation rendering.

4. Inspect actual exported files and Chinese text, retain original screenshots with version/hash association. These instructions do not claim additional human testing.

Limits: Embedded standard GLB <=25 MiB; required decoder extensions/external resources are rejected. Geometry operations are dedup/weld/prune; no universal compression or arbitrary-extension/no-loss guarantee. Only base-color/emissive PNG/JPEG textures are resized; data/normal maps are skipped. The fixture contains no animation, so animation playback is not claimed.
