# Reproduce: 前端包体积透视台 1.0.4

1. Install the native companion ZIP through WorkSwarm Extensions; verify its hash. The canonical Hub wrapper and native ZIP have identical inner runtime files.
2. Enable this plugin in a task, choose an existing dedicated local workspace and ask WorkSwarm to open 前端包体积透视台. Use its actual returned loopback URL.
3. Exercise the following flow, inspect actual outputs, close/reopen the same installation and verify saved data. Sample data does not represent a user's production project.

The installed UI loaded actual Rollup/Visualizer statistics, rendered the treemap, selected /catalog.js and displayed its importer /app.js. Snapshot comparison measured 1,508 -> 14,669 rendered module bytes; /catalog.js increased by 13,161 bytes. The engine suite performs real small/large builds and rejects invalid input. The exported interactive HTML is the actual generated file.

4. Inspect actual exported files and Chinese text, retain original screenshots with version/hash association. These instructions do not claim additional human testing.

Limits: Rollup/Vite Visualizer raw-data input only, 10 MiB / 5,000 modules; does not execute a user's project configuration. Fixture builds are labeled as fixtures. Per-module gzip/Brotli sums are not whole-response transfer size.
