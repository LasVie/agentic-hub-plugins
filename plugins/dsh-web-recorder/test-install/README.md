# Test-install package (local host)

`dsh-web-recorder-1.0.2-flat.zip` is the **inner payload with `manifest.json` at the archive root**, for installing into a WorkSwarm/OpenJiuwen host whose plugin uploader expects a root-level `manifest.json` (verified: the host's `find_plugin_manifest` + `load_plugin_package` load it as a `PluginSpec`). This is the form used for the real-host functional test.

- SHA-256: `4fcc08a669c8a63662b510df15aab6df291e06e0277048afb4b3757e8647d2e6`
- Same payload bytes as the canonical package; only the wrapping differs.

The **canonical marketplace deliverable** remains the double-nested wrapper produced by `tools/asset_release.py pack` at `releases/agent-plugin/dsh-web-recorder/1.0.2/dsh-web-recorder-1.0.2.zip` (`<slug>/plugin.yaml` + `<slug>/<slug>/manifest.json`).

Note for the Project Lead: the local host plugin uploader expected the root-level‑manifest form, not the marketplace wrapper. If the Agentic Hub plugin uploader has the same expectation, the repo delivery contract (wrapper vs flat payload) should be reconciled — this affects all plugins, not just this one.
