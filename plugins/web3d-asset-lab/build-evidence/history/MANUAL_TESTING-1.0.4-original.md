# Reproduce: 网页 3D 模型瘦身台 1.0.4

1. Install the native companion ZIP through WorkSwarm Extensions; verify its hash. The canonical Hub wrapper and native ZIP have identical inner runtime files.
2. Enable this plugin in a task, choose an existing dedicated local workspace and ask WorkSwarm to open 网页 3D 模型瘦身台. Use its actual returned loopback URL.
3. Exercise the following flow, inspect actual outputs, close/reopen the same installation and verify saved data. Sample data does not represent a user's production project.

The installed Three.js UI rendered both actual models. Geometry/resource deduplication reduced the self-generated GLB from 6,114,024 to 383,548 bytes (16 meshes -> 1, 16 scene nodes retained). An explicit lossy color-texture resize reduced 512x512 to 128x128, yielding 5,456 bytes; the original remains. Both original and final exported GLBs passed gltf-validator with zero errors and zero warnings. Initial loading now disables operations to prevent stale load/operation rendering.

4. Inspect actual exported files and Chinese text, retain original screenshots with version/hash association. These instructions do not claim additional human testing.

Limits: Embedded standard GLB <=25 MiB; required decoder extensions/external resources are rejected. Geometry operations are dedup/weld/prune; no universal compression or arbitrary-extension/no-loss guarantee. Only base-color/emissive PNG/JPEG textures are resized; data/normal maps are skipped. The fixture contains no animation, so animation playback is not claimed.
