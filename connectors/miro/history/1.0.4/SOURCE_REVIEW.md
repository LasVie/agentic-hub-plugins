# Source review

Miro → Miro 白板连接器 → `miro`. Song Haoran. AH-20261117-miro-connector.

Independent implementation based on [provider documentation](https://developers.miro.com/changelog/canvas-tools-replace-layout-tools) (official hosted MCP; Claude plugin 2.0.0 reviewed as reference). No third-party code is included in the package. mcp-remote 0.16.6 (MIT) is resolved from the npm registry at runtime, pinned package source punkpeye/mcp-remote@e4dc3713b0d6a727cbeb21f38324d20a6692dc5f. Provider permissions, account terms, and implementation license coverage were considered separately. The pre-icon release bundled no upstream prompts, artwork, account material or logo.

## 1.0.4 brand asset

- [Miro official material](https://developers.miro.com/docs/add-a-logo-to-your-app), retrieved 2026-11-17. [miro-logo-color-square.png](https://files.readme.io/17d4a23-miro-logo-color-square.png) is bundled unchanged as `icon.png` (SHA-256 `8d165ee50fdb031b656084b248333b56c82f292fc3ef7c63291218fdec2cdbdb`).
- [Terms](https://miro.com/legal/developer-terms-of-use/). Section 2.3 allows marks to identify compatibility. The developer icon guide publishes this square color mark for compact displays. Only the unmodified service identifier is used.
- Attribution is included in `THIRD_PARTY_NOTICES.md`. The mark retains its owner and usage terms.
