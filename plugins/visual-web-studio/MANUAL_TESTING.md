# Reproduce: 可视化网页搭建台 1.0.4

1. Install the native companion ZIP through WorkSwarm Extensions; verify its hash. The canonical Hub wrapper and native ZIP have identical inner runtime files.
2. Enable this plugin in a task, choose an existing dedicated local workspace and ask WorkSwarm to open 可视化网页搭建台. Use its actual returned loopback URL.
3. Exercise the following flow, inspect actual outputs, close/reopen the same installation and verify saved data. Sample data does not represent a user's production project.

Installed GrapesJS editor loads with Chinese text controls, without fetching external icon fonts. A Chinese heading was changed to 让插件交付看得见、改得动, a component card was added, mobile and desktop devices were selected, and the project was saved and restored. The exported HTML contains that heading and 协作交付; exported project JSON contains one resumable page.

4. Inspect actual exported files and Chinese text, retain original screenshots with version/hash association. These instructions do not claim additional human testing.

Limits: Static HTML/CSS component projects only; no arbitrary React round-trip or automatic website publication. The unreviewed old formatting addon is excluded. The upstream source is transpiled with its ES5 class semantics to preserve Backbone compatibility.
